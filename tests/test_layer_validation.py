"""Errores inyectados sobre Spark real; estas tablas pequeñas NO son Gold ejecutado."""
from datetime import datetime
import pytest


@pytest.fixture(scope='module')
def spark():
    pytest.importorskip('pyspark')
    from pyspark.sql import SparkSession
    session = (SparkSession.builder.master('local[2]').appName('Cross-layer-injected-errors')
               .config('spark.ui.enabled', 'false').config('spark.sql.shuffle.partitions', '2')
               .config('spark.driver.bindAddress', '127.0.0.1').getOrCreate())
    session.conf.set('spark.sql.session.timeZone', 'UTC')
    yield session
    session.stop()


@pytest.fixture(scope='module')
def layers(spark):
    from pyspark.sql import functions as F
    from pyspark.sql.types import StructType, StructField, StringType, TimestampType
    from src.processing.contracts import COLUMNS
    from src.processing.silver import IDS, prepare_silver
    from src.ingestion.bronze import METADATA
    from src.processing.historical_features import prepare_history, FEATURES, COUNTS
    from src.validation.validate_layers import expected_monthly, expected_distribution
    rows = []
    for number, delay, cancelled, origin in [(1, '-5', '0', 'JFK'), (2, '20', '0', 'JFK'),
                                             (3, None, '1', 'JFK'), (4, '50', '0', 'ZZZ')]:
        row = {c: None for c in COLUMNS + IDS + sorted(METADATA)}
        row.update(FlightDate='2025-01-10', Reporting_Airline='AA', Flight_Number_Reporting_Airline=str(number),
            Origin=origin, Dest='LAX', Tail_Number='N' + str(number), Distance='1000',
            CRSDepTime='1200', CRSArrTime='1400', CRSElapsedTime='120', DepDelay=delay,
            Cancelled=cancelled, Diverted='0', OriginAirportID='12478', DestAirportID='12892',
            DOT_ID_Reporting_Airline='19805', _source_period='2025-01', _source_zip_sha256='a' * 64,
            _source_csv_sha256='b' * 64, _source_url='https://example.invalid/synthetic.zip',
            _source_file='synthetic.csv', _source_downloaded_at='2025-01-01T00:00:00Z',
            _run_id='synthetic', _ingested_at=datetime(2025, 1, 1))
        rows.append(row)
    rows.append(dict(rows[0]))
    schema = StructType([StructField(c, TimestampType() if c == '_ingested_at' else StringType(), True) for c in rows[0]])
    bronze = spark.createDataFrame(rows, schema)
    mapping = spark.createDataFrame([('JFK', 'America/New_York', 'US')],
                                    'Origin string, origin_timezone string, origin_country string')
    prepared = prepare_silver(bronze, mapping)
    # Materializar SOLO los cuatro registros sintéticos; no usar collect sobre datos BTS.
    materialized = spark.createDataFrame(prepared.collect(), prepared.schema)
    silver = materialized.where(F.size('_quality_errors') == 0).drop('_quality_errors', '_raw_payload')
    quarantine = materialized.where(F.size('_quality_errors') > 0)
    history = prepare_history(silver, '2025-01', '2025-01')
    features = silver.join(history.select('flight_id', *FEATURES, *COUNTS,
        'history_availability_mode', 'history_operational_validity'), 'flight_id')
    return bronze, silver, quarantine, history, features, expected_monthly(silver), expected_distribution(silver)


def test_complete_synthetic_layers_reconcile_exact_duplicate_and_cancelled(layers):
    from src.validation.validate_layers import validate_layer_frames
    result = validate_layer_frames(*layers[:3], '2025-01', '2025-01', *layers[3:])
    assert result['passed'] and result['complete'], [c for c in result['checks'] if not c['passed']]
    assert result['months'] == [dict(period='2025-01', source_rows=5, unique_source_rows=4,
                                   silver_rows=3, quarantine_rows=1, exact_duplicate_exclusions=1)]


def test_detects_wrong_labels_cutoff_and_lineage(layers):
    from pyspark.sql import functions as F
    from src.validation.validate_layers import validate_silver_frame, _compare_rows
    source = layers[1]
    bad = (source.withColumn('delay15', F.when(F.col('Cancelled') == 1, 0).otherwise(F.col('delay15')))
           .withColumn('prediction_cutoff_utc', F.col('scheduled_utc'))
           .withColumn('_source_csv_sha256', F.lit('c' * 64)))
    checks = validate_silver_frame(bad, '2025-01', '2025-01')
    failures = {c['check'] for c in checks if not c['passed']}
    assert {'cancelled_label_null', 'label_matches_outcome', 'cutoff_exactly_three_hours'} <= failures
    assert not _compare_rows(source, bad, ['_source_csv_sha256'], 'injected')[0]['passed']


def test_detects_bad_monthly_rate_duplicate_groups_and_distribution(layers):
    from pyspark.sql import functions as F
    from src.validation.validate_layers import compare_aggregate, MONTH_KEYS
    monthly = layers[5]
    bad_monthly = monthly.withColumn('delay_rate', F.lit(0.0)).unionByName(monthly)
    checks = compare_aggregate(monthly, bad_monthly, MONTH_KEYS,
        ['total_rows', 'eligible_departures', 'delayed_departures', 'delay_rate'], 'monthly')
    assert all(not c['passed'] for c in checks)
    distribution = layers[6]
    bad_distribution = distribution.withColumn('eligible_departures', F.col('eligible_departures') + 1)
    checks = compare_aggregate(distribution, bad_distribution, ['_source_period', 'delay_bin'],
                               ['eligible_departures'], 'distribution')
    assert not checks[-1]['passed']


def test_missing_gold_never_reports_full_success(layers):
    from src.validation.validate_layers import validate_layer_frames
    result = validate_layer_frames(*layers[:3], '2025-01', '2025-01', history=layers[3])
    assert result['bronze_silver_passed']
    assert result['passed'] is False and result['complete'] is False
    assert set(result['pending']) == {'gold_features', 'gold_monthly', 'gold_distribution'}


def test_history_injected_operational_claim_and_disabled_rate_are_rejected(layers):
    from pyspark.sql import functions as F
    from src.processing.historical_features import FEATURES
    from src.validation.validate_layers import validate_history_frame
    bad = layers[3].withColumn('history_operational_validity', F.lit(True)).withColumn(FEATURES[0], F.lit(.5))
    failed = {c['check'] for c in validate_history_frame(layers[1], bad) if not c['passed']}
    assert 'history_no_operational_claim' in failed
    assert 'history_disabled_null_' + FEATURES[0] in failed


def test_string_aggregate_and_fractional_history_schema_are_rejected(layers):
    from pyspark.sql import functions as F
    from src.processing.historical_features import COUNTS
    from src.validation.validate_layers import compare_aggregate, validate_history_frame, MONTH_KEYS
    actual = layers[5].withColumn('total_rows', F.col('total_rows').cast('string'))
    checks = compare_aggregate(layers[5], actual, MONTH_KEYS,
        ['total_rows', 'eligible_departures', 'delayed_departures', 'delay_rate'], 'monthly')
    assert checks[0]['check'] == 'monthly_types' and not checks[0]['passed']
    bad = layers[3].withColumn(COUNTS[0], F.lit(1.5))
    checks = validate_history_frame(layers[1], bad)
    assert checks[0]['check'] == 'history_types' and not checks[0]['passed']
