from datetime import datetime, timedelta
import pytest

from src.processing.historical_features import check_mode, prepare_history, FEATURES, COUNTS


@pytest.mark.parametrize('mode', ['publication_aware', 'inventado'])
def test_unproven_availability_fails_before_spark(mode):
    with pytest.raises(ValueError):
        check_mode(mode)


@pytest.fixture(scope='module')
def spark():
    pytest.importorskip('pyspark')
    from pyspark.sql import SparkSession
    session = (SparkSession.builder.master('local[2]').appName('History-temporal-boundaries')
               .config('spark.ui.enabled', 'false').config('spark.sql.shuffle.partitions', '2')
               .config('spark.driver.bindAddress', '127.0.0.1').getOrCreate())
    session.conf.set('spark.sql.session.timeZone', 'UTC')
    yield session
    session.stop()


def dataset(spark, change_future=False):
    from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, DoubleType, BooleanType, TimestampType
    cutoff = datetime(2025, 1, 31, 12)
    rows = []

    def row(name, departure, delay=0.0, origin=1, airline=10, eligible=True):
        scheduled = departure - timedelta(minutes=delay)
        rows.append((name, '2025-01', 'a' * 64, 'b' * 64, origin, airline, 15,
                     scheduled, scheduled - timedelta(hours=3), float(delay),
                     int(delay >= 15) if eligible else None, eligible))

    # El propio resultado ocurre antes del cutoff: debe excluirse de AMBOS grupos.
    row('query', cutoff - timedelta(minutes=1), delay=-181)
    row('inclusive_lower', cutoff - timedelta(days=28), delay=20)
    row('one_second_too_old', cutoff - timedelta(days=28, seconds=1), delay=80)
    row('last_previous', cutoff - timedelta(seconds=1), delay=0)
    row('at_cutoff', cutoff, delay=70 if change_future else 0)
    row('future', cutoff + timedelta(minutes=1), delay=90 if change_future else 0)
    row('different_origin_same_airline', cutoff - timedelta(hours=1), delay=20, origin=2)
    row('cancelled', cutoff - timedelta(hours=1), delay=20, eligible=False)
    row('no_history', cutoff + timedelta(hours=1), origin=3, airline=30)
    schema = StructType([StructField(name, kind, True) for name, kind in [
        ('flight_id', StringType()), ('_source_period', StringType()), ('_source_csv_sha256', StringType()),
        ('_record_sha256', StringType()), ('OriginAirportID', LongType()),
        ('DOT_ID_Reporting_Airline', LongType()), ('scheduled_hour_local', IntegerType()),
        ('scheduled_utc', TimestampType()), ('prediction_cutoff_utc', TimestampType()),
        ('DepDelay', DoubleType()), ('delay15', IntegerType()), ('eligible_departure', BooleanType())]])
    return spark.createDataFrame(rows, schema)


def test_disabled_preserves_rows_lineage_and_nulls(spark):
    rows = prepare_history(dataset(spark), '2025-01', '2025-01').collect()
    assert len(rows) == 9
    for row in rows:
        assert row['history_availability_mode'] == 'disabled'
        assert row['history_operational_validity'] is False
        assert row['_source_csv_sha256'] == 'a' * 64
        assert all(row[c] is None for c in FEATURES + COUNTS)


@pytest.mark.parametrize('minimum,origin_rate', [(1, .5), (3, None)])
def test_boundaries_own_flight_groups_minimum_and_smoothing(spark, minimum, origin_rate):
    result = {r['flight_id']: r for r in prepare_history(dataset(spark), '2025-01', '2025-01',
                                                       'retrospective_ideal', minimum).collect()}
    row = result['query']
    assert row[COUNTS[0]] == 2  # lower incluido, último anterior; propio y >=cutoff fuera.
    assert row[COUNTS[1]] == 3  # otra procedencia con la misma aerolínea sí participa.
    assert row[FEATURES[0]] == origin_rate
    assert row[FEATURES[1]] == pytest.approx(3 / 5)  # Beta(1,1): (2+1)/(3+2).
    assert row['history_window_end_exclusive_utc'] == datetime(2025, 1, 31, 12)
    assert row['history_window_start_utc'] == datetime(2025, 1, 3, 12)
    assert row['history_operational_validity'] is False
    assert result['no_history'][COUNTS[0]] == 0
    assert result['no_history'][FEATURES[0]] is None


def test_future_outcomes_cannot_change_previous_query(spark):
    def result(changed):
        return prepare_history(dataset(spark, changed), '2025-01', '2025-01',
                               'retrospective_ideal', 1).where("flight_id='query'").first()
    before, after = result(False), result(True)
    for column in FEATURES + COUNTS:
        assert before[column] == after[column]


def test_missing_columns_and_invalid_minimum_fail(spark):
    source = dataset(spark)
    with pytest.raises(ValueError, match='Faltan columnas'):
        prepare_history(source.drop('OriginAirportID'), '2025-01', '2025-01')
    with pytest.raises(ValueError, match='entero positivo'):
        prepare_history(source, '2025-01', '2025-01', min_history=0)


def test_dense_equal_timestamps_match_independent_bruteforce(spark):
    import random
    randomizer = random.Random(2024)
    rows = []
    start = datetime(2025, 1, 1)
    for index in range(100):
        # Muchos eventos comparten el mismo segundo: probar inclusión/exclusión
        # de peers y los dos grupos sin depender de un orden físico de filas.
        event = start + timedelta(hours=randomizer.choice([0, 24, 48, 672, 696, 720]))
        delay = randomizer.choice([-240.0, -181.0, -5.0, 0.0, 20.0, 60.0])
        scheduled = event - timedelta(minutes=delay)
        eligible = index % 7 != 0
        rows.append(dict(flight_id=str(index), _source_period=scheduled.strftime('%Y-%m'),
            _source_csv_sha256='a' * 64, _record_sha256='b' * 64,
            OriginAirportID=randomizer.choice([1, 2]), DOT_ID_Reporting_Airline=randomizer.choice([10, 20]),
            scheduled_hour_local=scheduled.hour, scheduled_utc=scheduled,
            prediction_cutoff_utc=scheduled - timedelta(hours=3), DepDelay=delay,
            delay15=int(delay >= 15) if eligible else None, eligible_departure=eligible))
    source = spark.createDataFrame(rows, dataset(spark).schema)
    actual = {r['flight_id']: r for r in prepare_history(source, '2024-12', '2025-02',
                                                        'retrospective_ideal', 3).collect()}
    for query in rows:
        for index, group in enumerate([('OriginAirportID', 'scheduled_hour_local'), ('DOT_ID_Reporting_Airline',)]):
            previous = []
            lower = query['prediction_cutoff_utc'] - timedelta(days=28)
            for row in rows:
                event = row['scheduled_utc'] + timedelta(minutes=row['DepDelay'])
                if (row['flight_id'] != query['flight_id'] and row['eligible_departure']
                        and all(row[key] == query[key] for key in group)
                        and lower <= event < query['prediction_cutoff_utc']):
                    previous.append(row)
            expected = (sum(r['delay15'] for r in previous) + 1) / (len(previous) + 2) if len(previous) >= 3 else None
            assert actual[query['flight_id']][COUNTS[index]] == len(previous)
            observed = actual[query['flight_id']][FEATURES[index]]
            if expected is None:
                assert observed is None
            else:
                assert observed == pytest.approx(expected)
