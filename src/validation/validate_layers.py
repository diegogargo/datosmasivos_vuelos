"""Comprobaciones distribuidas de calidad, procedencia y conciliación entre capas.

Los resultados describen el rango leído; una capa ausente nunca se acredita.
"""
from pathlib import Path
from src.ingestion.acquire_range import months
from src.ingestion.bronze import METADATA, table_identifier, volume_root_path
from src.processing.contracts import KEY
from src.processing.historical_features import FEATURES, COUNTS, MIN_HISTORY
from src.utils.common import now, write_json

SILVER_TYPES = {'flight_id': 'string', '_source_period': 'string', '_source_csv_sha256': 'string',
    '_source_zip_sha256': 'string', '_record_sha256': 'string', 'FlightDate': 'date',
    'Reporting_Airline': 'string', 'Flight_Number_Reporting_Airline': 'bigint',
    'Origin': 'string', 'Dest': 'string', 'OriginAirportID': 'bigint', 'DestAirportID': 'bigint',
    'DOT_ID_Reporting_Airline': 'bigint', 'Cancelled': 'int', 'Diverted': 'int',
    'DepDelay': 'double', 'Distance': 'double', 'CRSDepTime': 'int', 'CRSArrTime': 'int',
    'scheduled_utc': 'timestamp', 'prediction_cutoff_utc': 'timestamp',
    'scheduled_hour_local': 'int', 'eligible_departure': 'boolean', 'delay15': 'int'}
MONTH_KEYS = ['_source_period', 'Reporting_Airline', 'Origin']
BINS = ['negative', '0_14', '15_59', '60_179', '180_plus']


def _check(name, violations, **details):
    return dict(check=name, passed=violations == 0, violations=int(violations), **details)


def _bad_counts(frame, rules):
    from pyspark.sql import functions as F
    result = frame.agg(*[F.coalesce(F.sum(F.when(F.coalesce(bad, F.lit(True)), 1).otherwise(0)), F.lit(0)).alias(str(i))
                         for i, (_, bad) in enumerate(rules)]).first()
    return [_check(name, result[str(i)]) for i, (name, _) in enumerate(rules)]


def _duplicates(frame, keys):
    return frame.groupBy(*keys).count().where('count > 1').count()


def _finite(column):
    from pyspark.sql import functions as F
    return column.isNotNull() & ~F.isnan(column) & (F.abs(column) != F.lit(float('inf')))


def validate_silver_frame(frame, start, end):
    from pyspark.sql import functions as F
    months(start, end)
    actual = {f.name: f.dataType.simpleString() for f in frame.schema}
    mismatches = {c: dict(expected=t, actual=actual.get(c)) for c, t in SILVER_TYPES.items() if actual.get(c) != t}
    checks = [_check('silver_schema', len(mismatches), mismatches=mismatches)]
    if mismatches:
        return checks
    finite = _finite(F.col('DepDelay'))
    eligible = (F.col('Cancelled') == 0) & finite
    expected_label = F.when(eligible, (F.col('DepDelay') >= 15).cast('int'))
    hhmm = lambda c: (F.col(c) == 2400) | (F.col(c).between(0, 2359) & (F.col(c) % 100 < 60))
    rules = [('source_period_range', ~F.col('_source_period').between(start, end)),
        ('source_date_matches_period', F.date_format('FlightDate', 'yyyy-MM') != F.col('_source_period')),
        ('cancelled_binary', ~F.col('Cancelled').isin(0, 1)), ('diverted_binary', ~F.col('Diverted').isin(0, 1)),
        ('operated_finite_outcome', (F.col('Cancelled') == 0) & ~finite),
        ('eligibility_matches_outcome', ~F.col('eligible_departure').eqNullSafe(eligible)),
        ('label_matches_outcome', ~F.col('delay15').eqNullSafe(expected_label)),
        ('cancelled_label_null', (F.col('Cancelled') == 1) & F.col('delay15').isNotNull()),
        ('distance_positive_finite', ~(_finite(F.col('Distance')) & (F.col('Distance') > 0))),
        ('cutoff_exactly_three_hours', F.col('prediction_cutoff_utc') != F.col('scheduled_utc') - F.expr('INTERVAL 3 HOURS')),
        ('scheduled_hour_range', ~F.col('scheduled_hour_local').between(0, 23)),
        ('scheduled_hhmm_departure', ~hhmm('CRSDepTime')), ('scheduled_hhmm_arrival', ~hhmm('CRSArrTime'))]
    for c in ['flight_id', '_source_csv_sha256', '_source_zip_sha256', '_record_sha256']:
        rules.append(('sha256_' + c, ~F.col(c).rlike('^[0-9a-f]{64}$')))
    for c in ['OriginAirportID', 'DestAirportID', 'DOT_ID_Reporting_Airline', 'Flight_Number_Reporting_Airline']:
        rules.append(('positive_' + c, F.col(c) <= 0))
    for c in ['Origin', 'Dest']:
        rules.append(('airport_code_' + c, ~F.col(c).rlike('^[A-Z]{3}$')))
    for c in KEY:
        rules.append(('required_key_' + c, F.col(c).isNull()))
    # Resultados opcionales observados también deben ser finitos; no se imputan.
    for c in ['DepDelay', 'ArrDelay', 'CRSElapsedTime', 'DepTime', 'ArrTime',
              'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay']:
        if c in frame.columns:
            rules.append(('finite_when_observed_' + c, F.col(c).isNotNull() & ~_finite(F.col(c))))
    checks += _bad_counts(frame, rules)
    checks += [_check('unique_flight_id', _duplicates(frame, ['flight_id'])),
               _check('unique_natural_key', _duplicates(frame, KEY))]
    return checks


def expected_monthly(silver):
    from pyspark.sql import functions as F
    return silver.groupBy(*MONTH_KEYS).agg(F.count('*').alias('total_rows'),
        F.sum(F.col('eligible_departure').cast('long')).alias('eligible_departures'),
        F.sum(F.coalesce(F.col('delay15'), F.lit(0))).alias('delayed_departures')).withColumn(
            'delay_rate', F.when(F.col('eligible_departures') > 0,
                                 F.col('delayed_departures') / F.col('eligible_departures')))


def expected_distribution(silver):
    from pyspark.sql import functions as F
    delay = F.col('DepDelay')
    label = (F.when(delay < 0, BINS[0]).when(delay < 15, BINS[1]).when(delay < 60, BINS[2])
             .when(delay < 180, BINS[3]).otherwise(BINS[4]))
    return silver.where('eligible_departure').withColumn('delay_bin', label).groupBy(
        '_source_period', 'delay_bin').agg(F.count('*').alias('eligible_departures'))


def compare_aggregate(expected, actual, keys, values, name):
    from pyspark.sql import functions as F
    missing = set(keys + values) - set(actual.columns)
    if missing:
        return [_check(name + '_schema', len(missing), missing=sorted(missing))]
    expected_types = {f.name: f.dataType.simpleString() for f in expected.schema}
    actual_types = {f.name: f.dataType.simpleString() for f in actual.schema}
    wrong_types = [c for c in keys + values if expected_types[c] != actual_types[c]]
    if wrong_types:
        return [_check(name + '_types', len(wrong_types), columns=wrong_types)]
    checks = [_check(name + '_unique_keys', _duplicates(actual, keys))]
    left = expected.select(*keys, *[F.col(c).alias('_expected_' + c) for c in values]).withColumn('_expected_row', F.lit(1))
    right = actual.select(*keys, *[F.col(c).alias('_actual_' + c) for c in values]).withColumn('_actual_row', F.lit(1))
    joined = left.join(right, keys, 'full')
    bad = F.col('_expected_row').isNull() | F.col('_actual_row').isNull()
    for c in values:
        a, b = F.col('_expected_' + c), F.col('_actual_' + c)
        same = a.eqNullSafe(b)
        if c == 'delay_rate':
            same = (a.isNull() & b.isNull()) | (_finite(b) & (F.abs(a - b) <= 1e-12))
        bad = bad | ~F.coalesce(same, F.lit(False))
    checks += _bad_counts(joined, [(name + '_matches_silver', bad)])
    return checks


def validate_history_frame(silver, history):
    from pyspark.sql import functions as F
    required = {'flight_id', '_source_period', '_source_csv_sha256', '_record_sha256',
        'scheduled_utc', 'prediction_cutoff_utc', 'history_availability_mode', 'history_operational_validity',
        'history_min_observations', 'history_window_start_utc', 'history_window_end_exclusive_utc', *FEATURES, *COUNTS}
    missing = required - set(history.columns)
    if missing:
        return [_check('history_schema', len(missing), missing=sorted(missing))]
    expected_types = {**{c: 'double' for c in FEATURES}, **{c: 'bigint' for c in COUNTS},
                      'history_min_observations': 'int', 'history_operational_validity': 'boolean',
                      'history_availability_mode': 'string', 'history_window_start_utc': 'timestamp',
                      'history_window_end_exclusive_utc': 'timestamp'}
    actual_types = {f.name: f.dataType.simpleString() for f in history.schema}
    wrong_types = [c for c, t in expected_types.items() if actual_types[c] != t]
    if wrong_types:
        return [_check('history_types', len(wrong_types), columns=wrong_types)]
    checks = [_check('history_unique_flight_id', _duplicates(history, ['flight_id']))]
    checks += _compare_rows(silver, history, ['_source_period', '_source_csv_sha256', '_record_sha256',
                                            'scheduled_utc', 'prediction_cutoff_utc'], 'history')
    disabled = F.col('history_availability_mode') == 'disabled'
    rules = [('history_declared_mode', ~F.col('history_availability_mode').isin('disabled', 'retrospective_ideal')),
        ('history_no_operational_claim', ~F.col('history_operational_validity').eqNullSafe(F.lit(False))),
        ('history_minimum_contract', ~F.col('history_min_observations').eqNullSafe(F.lit(MIN_HISTORY))),
        ('history_window_lower', F.col('history_window_start_utc') != F.col('prediction_cutoff_utc') - F.expr('INTERVAL 28 DAYS')),
        ('history_window_upper', F.col('history_window_end_exclusive_utc') != F.col('prediction_cutoff_utc'))]
    for rate, count in zip(FEATURES, COUNTS):
        r, n = F.col(rate), F.col(count)
        rules += [('history_disabled_null_' + rate, disabled & (r.isNotNull() | n.isNotNull())),
            ('history_count_' + count, ~disabled & (n.isNull() | (n < 0))),
            ('history_insufficient_null_' + rate, ~disabled & (n < MIN_HISTORY) & r.isNotNull()),
            ('history_rate_' + rate, ~disabled & (n >= MIN_HISTORY) & (~_finite(r) | ~r.between(0.0, 1.0))) ]
    return checks + _bad_counts(history, rules)


def _compare_rows(expected, actual, columns, name):
    from pyspark.sql import functions as F
    missing = {'flight_id', *columns} - set(actual.columns)
    if missing:
        return [_check(name + '_schema', len(missing), missing=sorted(missing))]
    expected_types = {f.name: f.dataType.simpleString() for f in expected.schema}
    actual_types = {f.name: f.dataType.simpleString() for f in actual.schema}
    wrong_types = [c for c in ['flight_id', *columns] if expected_types[c] != actual_types[c]]
    if wrong_types:
        return [_check(name + '_types', len(wrong_types), columns=wrong_types)]
    left = expected.select('flight_id', *[F.col(c).alias('_left_' + c) for c in columns]).withColumn('_left_row', F.lit(1))
    right = actual.select('flight_id', *[F.col(c).alias('_right_' + c) for c in columns]).withColumn('_right_row', F.lit(1))
    joined = left.join(right, 'flight_id', 'full')
    bad = F.col('_left_row').isNull() | F.col('_right_row').isNull()
    for c in columns:
        bad = bad | ~F.col('_left_' + c).eqNullSafe(F.col('_right_' + c))
    return _bad_counts(joined, [(name + '_rows_match', bad)])


def validate_layer_frames(bronze, silver, quarantine, start, end, history=None,
                          features=None, monthly=None, distribution=None, require_gold=True):
    from pyspark.sql import functions as F
    requested = months(start, end)
    def scoped(frame):
        if frame is not None and '_source_period' in frame.columns:
            return frame.where(F.col('_source_period').between(start, end))
        return frame
    bronze, silver, quarantine, history, features, monthly, distribution = map(scoped,
        [bronze, silver, quarantine, history, features, monthly, distribution])
    checks = validate_silver_frame(silver, start, end)
    if not checks[0]['passed']:
        return dict(passed=False, complete=False, checks=checks, pending=['Silver schema'])
    checks += _bad_counts(quarantine, [('quarantine_has_reason', F.size('_quality_errors') <= 0),
        ('quarantine_payload_hash', F.sha2('_raw_payload', 256) != F.col('_record_sha256'))])
    raw_columns = sorted(c for c in bronze.columns if c not in METADATA)
    payload = F.to_json(F.struct(*[F.col(c).alias(c) for c in raw_columns]), {'ignoreNullFields': 'false'})
    keys = ['_source_period', '_record_sha256', '_source_csv_sha256']
    source_records = bronze.withColumn('_record_sha256', F.sha2(payload, 256)).select(*keys).dropDuplicates()
    output_records = silver.select(*keys).unionByName(quarantine.select(*keys))
    checks += [_check('output_record_unique', _duplicates(output_records, keys)),
        _check('bronze_records_missing_from_outputs', source_records.join(output_records, keys, 'left_anti').count()),
        _check('outputs_without_bronze_record', output_records.join(source_records, keys, 'left_anti').count())]
    counts = lambda frame: {r['_source_period']: r['count'] for r in frame.groupBy('_source_period').count().collect()}
    b, u, s, q = map(counts, [bronze, source_records, silver, quarantine])
    periods = []
    for period in requested:
        item = dict(period=period, source_rows=b.get(period, 0), unique_source_rows=u.get(period, 0),
                    silver_rows=s.get(period, 0), quarantine_rows=q.get(period, 0))
        item['exact_duplicate_exclusions'] = item['source_rows'] - item['unique_source_rows']
        ok = item['source_rows'] > 0 and item['silver_rows'] > 0 and item['unique_source_rows'] == item['silver_rows'] + item['quarantine_rows']
        checks.append(_check('volume_' + period, int(not ok)))
        periods.append(item)
    bronze_silver_passed = all(c['passed'] for c in checks)
    pending = []
    if history is None:
        pending.append('silver_history')
    else:
        checks += validate_history_frame(silver, history)
    if features is None:
        pending.append('gold_features')
    elif history is None:
        pending.append('gold_features_history_comparison')
    else:
        checks += [_check('gold_unique_flight_id', _duplicates(features, ['flight_id']))]
        checks += _compare_rows(silver, features, ['_source_period', '_source_csv_sha256', '_record_sha256',
            'eligible_departure', 'delay15', 'scheduled_utc', 'prediction_cutoff_utc'], 'gold')
        checks += _compare_rows(history, features, [*FEATURES, *COUNTS,
            'history_availability_mode', 'history_operational_validity'], 'gold_history')
    if monthly is None:
        pending.append('gold_monthly')
    else:
        checks += compare_aggregate(expected_monthly(silver), monthly, MONTH_KEYS,
            ['total_rows', 'eligible_departures', 'delayed_departures', 'delay_rate'], 'monthly')
    if distribution is None:
        pending.append('gold_distribution')
    else:
        checks += compare_aggregate(expected_distribution(silver), distribution,
            ['_source_period', 'delay_bin'], ['eligible_departures'], 'distribution')
    complete = not pending
    return dict(passed=all(c['passed'] for c in checks) and (complete or not require_gold),
                complete=complete, bronze_silver_passed=bronze_silver_passed, checks=checks,
                months=periods, pending=pending, scope='all_layers' if require_gold else 'available_layers',
                temporal_limit='Checks validate declared bounds and null policies; algorithm leakage is tested separately. No real-time publication availability certified.')


def run_layer_validation(spark, bronze_table, silver_table, quarantine_table, history_table,
                         features_table, monthly_table, distribution_table, start, end,
                         output_root, require_gold=True):
    output_root = volume_root_path(output_root)
    spark.conf.set('spark.sql.session.timeZone', 'UTC')
    names = [bronze_table, silver_table, quarantine_table, history_table, features_table, monthly_table, distribution_table]
    if len(set(names)) != len(names):
        raise ValueError('Las siete tablas deben ser distintas')
    versions, frames = {}, []
    for i, table in enumerate(names):
        quoted = table_identifier(table)
        if not spark.catalog.tableExists(table):
            if i < 3:
                raise ValueError('Falta capa necesaria: ' + table)
            frames.append(None)
            continue
        version = spark.sql('DESCRIBE HISTORY ' + quoted + ' LIMIT 1').first()['version']
        versions[table] = version
        frames.append(spark.read.option('versionAsOf', version).table(table))
    result = validate_layer_frames(*frames[:3], start, end, *frames[3:], require_gold=require_gold)
    result.update(layer='cross_layer_validation', start=start, end=end, validated_at=now(),
                  spark_version=spark.version, delta_versions=versions)
    write_json(Path(output_root) / 'reports/validation/latest.json', result)
    return result
