"""Silver Spark Connect: tipificación, cuarentena, DST y conciliación por mes."""
import csv,json,uuid
from pathlib import Path
from zoneinfo import ZoneInfo
from src.ingestion.acquire_range import months
from src.ingestion.bronze import METADATA,table_identifier,volume_root_path
from src.processing.contracts import COLUMNS,KEY
from src.processing.delta_io import write_month,drop_stage
from src.utils.common import ROOT,digest,now,read_json,write_json

IDS=['OriginAirportID','DestAirportID','DOT_ID_Reporting_Airline']
TEXT={'FlightDate','Reporting_Airline','Tail_Number','Origin','Dest'}
NUMERIC=[c for c in COLUMNS if c not in TEXT]
COUNTRIES={'US','PR','VI','GU','AS','MP'}

def load_airports(root=ROOT):
    root=Path(root);path=root/'data/reference/airport_timezones.csv'
    proof=read_json(path.with_suffix('.provenance.json'))
    if digest(path)!=proof['artifact_sha256']:raise ValueError('Dimensión de aeropuertos alterada')
    with path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    if len({row['iata'] for row in rows})!=len(rows):raise ValueError('IATA duplicado en la dimensión')
    for row in rows:
        if row['country'] in COUNTRIES:ZoneInfo(row['timezone'])
    return rows,proof

def prepare_silver(bronze,airports):
    """Devuelve un plan Spark con motivos de cuarentena; no escribe ni recolecta vuelos."""
    from pyspark.sql import functions as F,Window
    required=set(COLUMNS+IDS)|METADATA
    missing=required-set(bronze.columns)
    if missing:raise ValueError('Faltan columnas Bronze: '+str(sorted(missing)))
    raw_columns=[c for c in bronze.columns if c not in METADATA]
    unique=bronze.dropDuplicates(raw_columns)
    payload=F.to_json(F.struct(*[F.col(c).alias(c) for c in sorted(raw_columns)]),{'ignoreNullFields':'false'})
    frame=unique.withColumn('_raw_payload',payload).withColumn('_record_sha256',F.sha2(payload,256))
    errors=[]
    def mark(name,bad):errors.append(F.when(F.coalesce(bad,F.lit(False)),F.lit(name)))
    # Evaluar validación numérica sobre el original antes de convertir a tipos analíticos.
    for c in NUMERIC+IDS:
        number=F.expr(f'try_cast(`{c}` as double)')
        finite=number.isNotNull()&~F.isnan(number)&(F.abs(number)!=F.lit(float('inf')))
        mark('invalid_numeric_'+c,F.col(c).isNotNull()&~finite)
        if c in IDS or c=='Flight_Number_Reporting_Airline':
            integral=F.expr(f'try_cast(try_cast(`{c}` as decimal(38,12)) as bigint)')
            mark('positive_integer_'+c,~finite|(number<=0)|(number%1!=0)|integral.isNull())
        if c in ('CRSDepTime','CRSArrTime','DepTime','ArrTime'):
            valid=finite&(number%1==0)&((number==2400)|((number>=0)&(number<=2359)&(number%100<60)))
            required_time=c in ('CRSDepTime','CRSArrTime')
            mark('invalid_hhmm_'+c,~valid if required_time else F.col(c).isNotNull()&~valid)
        if c in ('Cancelled','Diverted'):mark('binary_'+c,~number.isin(0.0,1.0)|number.isNull())
        if c=='Distance':mark('distance_positive',~finite|(number<=0))
    date=F.expr('try_cast(FlightDate as date)')
    mark('invalid_date',date.isNull()|~F.col('FlightDate').rlike(r'^\d{4}-\d{2}-\d{2}$'))
    mark('date_outside_source_period',F.date_format(date,'yyyy-MM')!=F.col('_source_period'))
    for c in ('Origin','Dest'):
        mark('invalid_'+c,~F.upper(F.trim(F.col(c))).rlike('^[A-Z]{3}$')|F.col(c).isNull())
    mark('required_airline',F.col('Reporting_Airline').isNull()|(F.length(F.trim(F.col('Reporting_Airline')))==0))
    frame=frame.withColumn('_quality_errors_base',F.filter(F.array(*errors),lambda x:x.isNotNull()))
    for c in ('Reporting_Airline','Tail_Number','Origin','Dest'):frame=frame.withColumn(c,F.upper(F.trim(F.col(c))))
    frame=frame.withColumn('FlightDate',F.expr('try_cast(FlightDate as date)'))
    for c in NUMERIC+IDS:
        kind='bigint' if c in IDS or c=='Flight_Number_Reporting_Airline' else ('int' if c in ('CRSDepTime','CRSArrTime','Cancelled','Diverted') else 'double')
        # BTS serializa banderas como 0.00/1.00. El cast STRING -> INT
        # devuelve NULL para esas cadenas; convertir primero el valor numérico.
        if kind=='bigint':expression=f'try_cast(try_cast(`{c}` as decimal(38,12)) as bigint)'
        elif kind=='int':expression=f'try_cast(try_cast(`{c}` as double) as int)'
        else:expression=f'try_cast(`{c}` as double)'
        frame=frame.withColumn(c,F.expr(expression))
    frame=frame.select(*COLUMNS,*IDS,*sorted(METADATA),'_raw_payload','_record_sha256','_quality_errors_base')
    frame=frame.withColumn('_key_count',F.count('*').over(Window.partitionBy(*KEY)))
    frame=frame.join(F.broadcast(airports),'Origin','left')
    dep=F.col('CRSDepTime')
    minutes=F.when(dep==2400,F.lit(1440)).otherwise((F.floor(dep/100)*60+dep%100).cast('int'))
    frame=frame.withColumn('_dep_minutes',minutes)
    frame=frame.withColumn('scheduled_local',F.expr('cast(FlightDate as timestamp) + make_interval(0,0,0,0,0,_dep_minutes,0)').cast('timestamp_ntz'))
    convertible=F.col('origin_timezone').isNotNull()&F.col('scheduled_local').isNotNull()&F.col('origin_country').isin(*sorted(COUNTRIES))
    frame=frame.withColumn('scheduled_utc',F.when(convertible,F.to_utc_timestamp('scheduled_local',F.col('origin_timezone'))))
    round_trip=F.from_utc_timestamp('scheduled_utc',F.col('origin_timezone')).cast('timestamp_ntz')
    before=F.from_utc_timestamp(F.col('scheduled_utc')-F.expr('INTERVAL 1 HOUR'),F.col('origin_timezone')).cast('timestamp_ntz')
    after=F.from_utc_timestamp(F.col('scheduled_utc')+F.expr('INTERVAL 1 HOUR'),F.col('origin_timezone')).cast('timestamp_ntz')
    additional=[F.when(F.col('_key_count')>1,F.lit('contradictory_key')),
        F.when(F.col('origin_timezone').isNull(),F.lit('unknown_origin_timezone')),
        F.when(~F.col('origin_country').isin(*sorted(COUNTRIES)),F.lit('airport_outside_US_reporting_scope')),
        F.when(round_trip!=F.col('scheduled_local'),F.lit('nonexistent_local_time_DST')),
        F.when((before==F.col('scheduled_local'))|(after==F.col('scheduled_local')),F.lit('ambiguous_local_time_DST')),
        F.when((F.col('Cancelled')==0)&(F.col('DepDelay').isNull()|F.isnan('DepDelay')|(F.abs('DepDelay')==F.lit(float('inf')))),F.lit('operated_without_finite_outcome'))]
    for c in ['FlightDate','Flight_Number_Reporting_Airline',*IDS,'Cancelled','Diverted',
              'CRSDepTime','CRSArrTime','scheduled_local','scheduled_utc']:
        additional.append(F.when(F.col(c).isNull(),F.lit('null_after_conversion_'+c)))
    frame=frame.withColumn('_quality_errors',F.concat('_quality_errors_base',F.filter(F.array(*additional),lambda x:x.isNotNull())))
    finite_delay=F.col('DepDelay').isNotNull()&~F.isnan('DepDelay')&(F.abs('DepDelay')!=F.lit(float('inf')))
    frame=frame.withColumn('eligible_departure',(F.col('Cancelled')==0)&finite_delay)
    frame=frame.withColumn('delay15',F.when(F.col('eligible_departure'),(F.col('DepDelay')>=15).cast('int')))
    frame=frame.withColumn('prediction_cutoff_utc',F.col('scheduled_utc')-F.expr('INTERVAL 3 HOURS'))
    frame=frame.withColumn('scheduled_hour_local',F.hour('scheduled_local'))
    frame=frame.withColumn('flight_id',F.sha2(F.to_json(F.struct(*[F.col(c) for c in KEY]),{'ignoreNullFields':'false'}),256))
    return frame.drop('_quality_errors_base','_key_count','_dep_minutes')


def summarize_silver(frame):
    """Comprueba tipos derivados antes de acreditar una partición como completa."""
    from pyspark.sql import functions as F
    required=['flight_id','FlightDate','Flight_Number_Reporting_Airline',*IDS,'Cancelled','Diverted',
        'CRSDepTime','CRSArrTime','scheduled_local','scheduled_utc','prediction_cutoff_utc',
        'scheduled_hour_local','eligible_departure','_source_period','_source_csv_sha256',
        '_source_zip_sha256','_record_sha256']
    missing=F.lit(False)
    for c in required:missing=missing|F.col(c).isNull()
    finite=F.col('DepDelay').isNotNull()&~F.isnan('DepDelay')&(F.abs('DepDelay')!=F.lit(float('inf')))
    eligible=(F.col('Cancelled')==0)&finite
    expected=F.when(eligible,(F.col('DepDelay')>=15).cast('int'))
    def count_if(condition):return F.coalesce(F.sum(F.when(condition,1).otherwise(0)),F.lit(0)).cast('long')
    result=frame.agg(F.count('*').alias('silver_rows'),F.count('delay15').alias('labelled_departures'),
        count_if(F.col('eligible_departure')).alias('eligible_departures'),
        count_if(F.col('Cancelled')==1).alias('cancelled_rows'),
        count_if(F.col('delay15')==1).alias('delayed_departures'),
        count_if(missing).alias('null_required_typed_rows'),
        count_if(~F.col('delay15').eqNullSafe(expected)|~F.col('eligible_departure').eqNullSafe(eligible)).alias('invalid_label_rows')).first().asDict()
    result['quality_passed']=(result['null_required_typed_rows']==0 and result['invalid_label_rows']==0
        and result['labelled_departures']==result['eligible_departures']
        and result['silver_rows']==result['eligible_departures']+result['cancelled_rows'])
    return result

def run_silver(spark,bronze_table,silver_table,quarantine_table,start,end,output_root):
    from pyspark.sql import functions as F
    requested=months(start,end)
    if not set(requested).issubset(months('2024-01','2025-12')):raise ValueError('Alcance verificado: solo 2024–2025')
    output_root=volume_root_path(output_root)
    for table in (bronze_table,silver_table,quarantine_table):table_identifier(table)
    if len({bronze_table,silver_table,quarantine_table})!=3:raise ValueError('Las tablas de las capas deben ser distintas')
    spark.conf.set('spark.sql.session.timeZone','UTC')
    source_properties={r['key']:r['value'] for r in spark.sql('SHOW TBLPROPERTIES '+table_identifier(bronze_table)).collect()}
    if source_properties.get('vuelos.layer')!='bronze' or source_properties.get('vuelos.source')!='bts_reporting_carrier':
        raise ValueError('La entrada no pertenece al Bronze de BTS del proyecto')
    source_version=spark.sql('DESCRIBE HISTORY '+table_identifier(bronze_table)+' LIMIT 1').first()['version']
    airports,proof=load_airports()
    mapping=spark.createDataFrame([(r['iata'],r['timezone'],r['country']) for r in airports],
                                  'Origin string, origin_timezone string, origin_country string')
    run_id=uuid.uuid4().hex
    stage=silver_table.rsplit('.',1)[0]+'.vuelos_stage_'+run_id
    report=dict(layer='silver',run_id=run_id,start=start,end=end,started_at=now(),complete=False,months=[],quality_summary_passed=False,
        spark_version=spark.version,timezone_dimension=proof,source_delta_version=source_version,
        policies=dict(exact_duplicates='Sobre todos los campos originales; exclusiones contadas.',
                      conflicting_keys='Todas las filas contradictorias se envían a cuarentena.',
                      DST='Horas inexistentes o ambiguas se envían a cuarentena; ámbito US/territorios 2024–2025.',
                      timezone_mapping='Dimensión actual comunitaria, sin certificación histórica de cada código IATA. IDs BTS preservados.'),
        staging_table=stage)
    root=Path(output_root)/'reports/silver';path=root/'latest.json'
    write_json(path,report)
    try:
        for period in requested:
            source=spark.read.option('versionAsOf',source_version).table(bronze_table).where(F.col('_source_period')==period)
            source_rows=source.count()
            if not source_rows:raise ValueError('Bronze no contiene '+period)
            prepared=(prepare_silver(source,mapping).withColumn('_silver_run_id',F.lit(run_id))
                      .withColumn('_silver_ingested_at',F.current_timestamp()))
            write_month(spark,prepared,stage,period,'silver_stage')
            staged=spark.table(stage).where(F.col('_source_period')==period)
            unique_rows=staged.count()
            accepted=staged.where(F.size('_quality_errors')==0).drop('_raw_payload','_quality_errors')
            rejected=staged.where(F.size('_quality_errors')>0)
            silver_version=write_month(spark,accepted,silver_table,period,'silver')
            quarantine_version=write_month(spark,rejected,quarantine_table,period,'silver_quarantine')
            quality=summarize_silver(spark.table(silver_table).where(F.col('_source_period')==period))
            silver_rows=quality['silver_rows']
            if not quality['quality_passed']:raise ValueError('Silver tipificado no cumple su contrato: '+str(quality))
            quarantine_rows=spark.table(quarantine_table).where(F.col('_source_period')==period).count()
            duplicates=source_rows-unique_rows
            if silver_rows+quarantine_rows+duplicates!=source_rows:raise ValueError('No concilian los conteos de '+period)
            if silver_rows==0:raise ValueError('Ningún vuelo aceptado; revisar reglas de '+period)
            errors={r['reason']:r['count'] for r in rejected.select(F.explode('_quality_errors').alias('reason')).groupBy('reason').count().collect()}
            report['months'].append(dict(period=period,source_rows=source_rows,silver_rows=silver_rows,
                quarantine_rows=quarantine_rows,exact_duplicate_exclusions=duplicates,violations_by_reason=errors,
                quality_summary=quality,
                silver_delta_version=silver_version,quarantine_delta_version=quarantine_version))
            write_json(path,report)
        drop_stage(spark,stage)
        report.update(complete=True,quality_summary_passed=True,finished_at=now(),rows=sum(r['silver_rows'] for r in report['months']),
                      quarantine_rows=sum(r['quarantine_rows'] for r in report['months']),staging_removed=True)
    except Exception as exc:
        report.update(finished_at=now(),error=f'{type(exc).__name__}: {exc}')
        write_json(path,report);raise
    write_json(path,report);write_json(root/(run_id+'.json'),report)
    return report
