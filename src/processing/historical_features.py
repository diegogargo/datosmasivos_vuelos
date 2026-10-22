"""Históricos de 28 días; disponibilidad operacional no acreditada por BTS mensual."""
from pathlib import Path
import uuid

from src.ingestion.acquire_range import months
from src.ingestion.bronze import table_identifier, volume_root_path, identifier
from src.utils.common import now, write_json

WINDOW_SECONDS = 28 * 24 * 60 * 60
MIN_HISTORY = 30
FEATURES = ('origin_hour_delay_rate_28d', 'airline_delay_rate_28d')
COUNTS = ('origin_hour_history_count_28d', 'airline_history_count_28d')
REQUIRED = {'flight_id', '_source_period', '_source_csv_sha256', '_record_sha256',
            'OriginAirportID', 'DOT_ID_Reporting_Airline', 'scheduled_hour_local',
            'scheduled_utc', 'prediction_cutoff_utc', 'DepDelay', 'delay15', 'eligible_departure'}


def check_mode(mode):
    if mode == 'publication_aware':
        raise ValueError('publication_aware exige available_at real y su procedencia; no implementado con BTS mensual')
    if mode not in {'disabled', 'retrospective_ideal'}:
        raise ValueError('Modo de disponibilidad desconocido: ' + str(mode))


def prepare_history(silver, start, end, availability_mode='disabled', min_history=MIN_HISTORY):
    """Plan distribuido, sin escritura. El modo ideal supone disponibilidad al salir de puerta.

    La ventana contiene salidas reales estimadas en [cutoff-28 días, cutoff),
    según scheduled_utc + DepDelay. Excluye el propio vuelo incluso con adelantos
    superiores a tres horas. Laplace Beta(1,1) es fijo: no aprende del futuro.
    """
    from pyspark.sql import functions as F, Window
    check_mode(availability_mode)
    months(start, end)
    if not isinstance(min_history, int) or isinstance(min_history, bool) or min_history < 1:
        raise ValueError('min_history debe ser entero positivo')
    missing = REQUIRED - set(silver.columns)
    if missing:
        raise ValueError('Faltan columnas Silver: ' + str(sorted(missing)))
    selected = silver.where(F.col('_source_period').between(start, end))
    base = selected.select('flight_id', '_source_period', '_source_csv_sha256', '_record_sha256',
                           'scheduled_utc', 'prediction_cutoff_utc')
    base = (base.withColumn('history_availability_mode', F.lit(availability_mode))
            .withColumn('history_operational_validity', F.lit(False))
            .withColumn('history_min_observations', F.lit(min_history))
            .withColumn('history_window_start_utc', F.col('prediction_cutoff_utc') - F.expr('INTERVAL 28 DAYS'))
            .withColumn('history_window_end_exclusive_utc', F.col('prediction_cutoff_utc')))
    if availability_mode == 'disabled':
        for name in FEATURES:
            base = base.withColumn(name, F.lit(None).cast('double'))
        for name in COUNTS:
            base = base.withColumn(name, F.lit(None).cast('long'))
        return base

    # Silver HHMM y DepDelay de BTS tienen resolución de minuto. La expresión
    # usa segundos enteros sin truncar resultados de otras fuentes silenciosamente.
    def event_seconds():
        return F.col('scheduled_utc').cast('long') + (F.col('DepDelay') * 60).cast('long')

    bounds = selected.agg(F.min('prediction_cutoff_utc').cast('long').alias('low'),
                          F.max('prediction_cutoff_utc').cast('long').alias('high')).first()
    if bounds['low'] is None:
        # Mantener esquema idéntico en un rango vacío; run_* lo rechaza antes de escribir.
        for name in FEATURES:
            base = base.withColumn(name, F.lit(None).cast('double'))
        for name in COUNTS:
            base = base.withColumn(name, F.lit(None).cast('long'))
        return base
    eligible = (F.col('eligible_departure') & F.col('delay15').isin(0, 1)
                & F.col('DepDelay').isNotNull() & ~F.isnan('DepDelay')
                & (F.abs('DepDelay') != F.lit(float('inf'))))
    outcomes = (silver.where(eligible).withColumn('_event_sec', event_seconds())
                .where(F.col('_event_sec').between(bounds['low'] - WINDOW_SECONDS, bounds['high'] - 1)))

    def group_key(kind):
        if kind == 'origin_hour':
            return F.concat_ws('|', F.col('OriginAirportID').cast('string'),
                               F.col('scheduled_hour_local').cast('string'))
        return F.col('DOT_ID_Reporting_Airline').cast('string')

    streams = []
    for kind in ('origin_hour', 'airline'):
        cutoff = F.col('prediction_cutoff_utc').cast('long')
        own = F.coalesce(eligible & event_seconds().between(cutoff - WINDOW_SECONDS, cutoff - 1), F.lit(False))
        queries = selected.select(F.lit(kind).alias('_kind'), group_key(kind).alias('_group'),
            'flight_id', '_source_period', F.lit(True).alias('_query'),
            F.lit(None).cast('int').alias('_label'),
            own.cast('long').alias('_own_count'),
            F.when(own, F.col('delay15')).otherwise(0).alias('_own_delayed'),
            F.explode(F.array(
                F.struct((cutoff - 1).alias('second'), F.lit(1).alias('sign')),
                F.struct((cutoff - WINDOW_SECONDS - 1).alias('second'), F.lit(-1).alias('sign'))
            )).alias('_boundary')).select('_kind', '_group', F.col('_boundary.second').alias('_event_sec'),
                'flight_id', '_source_period', '_query', '_label', '_own_count', '_own_delayed',
                F.col('_boundary.sign').alias('_sign'))
        events = outcomes.select(F.lit(kind).alias('_kind'), group_key(kind).alias('_group'), '_event_sec',
            F.lit(None).cast('string').alias('flight_id'), F.lit(None).cast('string').alias('_source_period'),
            F.lit(False).alias('_query'), F.col('delay15').alias('_label'),
            F.lit(0).cast('long').alias('_own_count'), F.lit(0).alias('_own_delayed'), F.lit(0).alias('_sign'))
        streams.append(queries.unionByName(events))
    stream = streams[0].unionByName(streams[1])
    # Diferencia de prefijos acumulados: evita reevaluar miles de antecedentes
    # en cada ventana móvil. Los peers del mismo segundo comparten prefijo.
    window = Window.partitionBy('_kind', '_group').orderBy('_event_sec').rangeBetween(
        Window.unboundedPreceding, Window.currentRow)
    prefixes = (stream.withColumn('_prefix_n', F.count('_label').over(window))
                   .withColumn('_prefix_delayed', F.coalesce(F.sum('_label').over(window), F.lit(0)))
                   .where('_query'))
    candidates = prefixes.groupBy('flight_id', '_source_period', '_kind').agg(
        (F.sum(F.col('_sign') * F.col('_prefix_n')) - F.max('_own_count')).alias('_n'),
        (F.sum(F.col('_sign') * F.col('_prefix_delayed')) - F.max('_own_delayed')).alias('_delayed'))
    candidates = (candidates
                   .withColumn('_rate', F.when(F.col('_n') >= min_history,
                                               (F.col('_delayed') + 1.0) / (F.col('_n') + 2.0))))
    aggregate = candidates.groupBy('flight_id', '_source_period').agg(
        *[F.max(F.when(F.col('_kind') == kind, F.col(value))).alias(name)
          for kind, value, name in [('origin_hour', '_rate', FEATURES[0]), ('airline', '_rate', FEATURES[1]),
                                    ('origin_hour', '_n', COUNTS[0]), ('airline', '_n', COUNTS[1])]])
    return base.join(aggregate, ['flight_id', '_source_period'], 'left')


def _write_range(spark, frame, table, start, end):
    """Un solo commit Delta para el rango, conservando particiones exteriores."""
    months(start, end)
    quoted = table_identifier(table)
    if not spark.catalog.tableExists(table):
        fields = ', '.join(identifier(f.name) + ' ' + f.dataType.simpleString() for f in frame.schema)
        spark.sql(f'CREATE TABLE {quoted} ({fields}) USING DELTA PARTITIONED BY (`_source_period`) '
                  "TBLPROPERTIES ('vuelos.layer'='silver_history', 'vuelos.source'='bts_reporting_carrier')")
    props = {r['key']: r['value'] for r in spark.sql('SHOW TBLPROPERTIES ' + quoted).collect()}
    if props.get('vuelos.layer') != 'silver_history' or props.get('vuelos.source') != 'bts_reporting_carrier':
        raise ValueError('Se conserva una tabla ajena: ' + table)
    if {f.name: f.dataType.simpleString() for f in spark.table(table).schema} != {
            f.name: f.dataType.simpleString() for f in frame.schema}:
        raise ValueError('Esquema de históricos incompatible; tabla conservada')
    frame.write.format('delta').mode('overwrite').option(
        'replaceWhere', f"_source_period >= '{start}' AND _source_period <= '{end}'").saveAsTable(table)
    return spark.sql('DESCRIBE HISTORY ' + quoted + ' LIMIT 1').first()['version']


def run_historical_features(spark, silver_table, target_table, start, end, output_root,
                            availability_mode='disabled'):
    from pyspark.sql import functions as F
    check_mode(availability_mode)
    requested = months(start, end)
    if not set(requested).issubset(months('2024-01', '2025-12')):
        raise ValueError('Alcance verificado: 2024–2025')
    for table in (silver_table, target_table):
        table_identifier(table)
    if silver_table == target_table:
        raise ValueError('Entrada y salida deben ser distintas')
    output_root = volume_root_path(output_root)
    spark.conf.set('spark.sql.session.timeZone', 'UTC')
    props = {r['key']: r['value'] for r in spark.sql('SHOW TBLPROPERTIES ' + table_identifier(silver_table)).collect()}
    if props.get('vuelos.layer') != 'silver' or props.get('vuelos.source') != 'bts_reporting_carrier':
        raise ValueError('La entrada debe ser Silver de BTS del proyecto')
    source_version = spark.sql('DESCRIBE HISTORY ' + table_identifier(silver_table) + ' LIMIT 1').first()['version']
    source = spark.read.option('versionAsOf', source_version).table(silver_table)
    selected = source.where(F.col('_source_period').between(start, end))
    context_counts = {r['_source_period']: r['count'] for r in source.groupBy('_source_period').count().collect()}
    source_counts = {p: context_counts.get(p, 0) for p in requested}
    if any(source_counts.get(p, 0) == 0 for p in requested):
        raise ValueError('Faltan meses Silver completos para históricos')
    if selected.groupBy('flight_id').count().where('count != 1').limit(1).count():
        raise ValueError('flight_id duplicado; no escribir históricos')
    required_rules=[]
    for col in ['flight_id', 'OriginAirportID', 'DOT_ID_Reporting_Airline', 'scheduled_hour_local',
                'scheduled_utc', 'prediction_cutoff_utc', 'eligible_departure']:
        required_rules.append(('null_'+col,F.col(col).isNull()))
    invalid_label = F.col('eligible_departure') & (
        F.col('delay15').isNull() | ~F.col('delay15').isin(0, 1) | F.col('DepDelay').isNull()
        | F.isnan('DepDelay') | (F.abs('DepDelay') == F.lit(float('inf')))
        | ((F.col('DepDelay') * 60) % 1 != 0))
    required_rules.append(('invalid_outcome',invalid_label))
    audited=source.agg(*[F.coalesce(F.sum(F.when(bad,1).otherwise(0)),F.lit(0)).alias(name)
                         for name,bad in required_rules]).first().asDict()
    violations={name:count for name,count in audited.items() if count}
    if violations:
        raise ValueError('Silver no cumple el contrato de históricos: '+str(violations))
    report = dict(layer='silver_history', run_id=uuid.uuid4().hex, start=start, end=end,
        complete=False, started_at=now(), spark_version=spark.version, source_delta_version=source_version,
        availability_mode=availability_mode, rates_computed=availability_mode == 'retrospective_ideal',
        algorithm='Cumulative counts at cutoff-1s minus cutoff-28days-1s, own-flight subtraction',
        source_context_months=context_counts,
        operational_validity=False, min_history=MIN_HISTORY, smoothing='Beta(1,1): (delayed+1)/(n+2)',
        window='Estimated actual gate departures in [prediction_cutoff_utc-28 days, prediction_cutoff_utc); own flight excluded',
        assumption='Ideal immediate outcome at scheduled_utc + DepDelay; BTS monthly publication is NOT historical event availability',
        context_limits='Only accepted Silver rows available; January 2024 has no December 2023 context; quarantined flights excluded',
        months=[])
    root = Path(output_root) / 'reports/history'
    write_json(root / 'latest.json', report)
    try:
        frame = prepare_history(source, start, end, availability_mode)
        version = _write_range(spark, frame, target_table, start, end)
        persisted = spark.table(target_table).where(F.col('_source_period').between(start, end))
        summary = persisted.groupBy('_source_period').agg(F.count('*').alias('rows'),
            F.count(FEATURES[0]).alias('origin_hour_nonnull'), F.count(FEATURES[1]).alias('airline_nonnull')).collect()
        indexed = {r['_source_period']: r.asDict() for r in summary}
        for period in requested:
            item = indexed.get(period, {})
            if item.get('rows') != source_counts[period]:
                raise ValueError('No concilian los históricos de ' + period)
            report['months'].append(dict(period=period, source_rows=source_counts[period],
                history_rows=item['rows'], origin_hour_nonnull=item['origin_hour_nonnull'],
                airline_nonnull=item['airline_nonnull']))
        report.update(complete=True, rows=sum(source_counts.values()), target_delta_version=version, finished_at=now())
    except Exception as exc:
        report.update(error=f'{type(exc).__name__}: {exc}', finished_at=now())
        write_json(root / 'latest.json', report)
        raise
    write_json(root / 'latest.json', report)
    write_json(root / (report['run_id'] + '.json'), report)
    return report
