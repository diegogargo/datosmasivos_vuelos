from datetime import datetime,timezone
import json
import pytest
from src.processing.temporal import strict_scheduled_utc
from src.processing.silver import load_airports
from src.utils.common import ROOT,digest

@pytest.mark.parametrize('date,time,zone,expected',[
    ('2025-01-10',1200,'America/New_York',datetime(2025,1,10,17,tzinfo=timezone.utc)),
    ('2025-07-10',1200,'America/New_York',datetime(2025,7,10,16,tzinfo=timezone.utc)),
    ('2025-01-31',2400,'America/New_York',datetime(2025,2,1,5,tzinfo=timezone.utc)),
    ('2025-01-10',0,'Pacific/Honolulu',datetime(2025,1,10,10,tzinfo=timezone.utc))])
def test_utc_strict(date,time,zone,expected):assert strict_scheduled_utc(date,time,zone)==expected

@pytest.mark.parametrize('date,time,message',[
    ('2024-03-10',230,'inexistente'),('2024-11-03',130,'ambigua'),('2025-01-10',1260,'inválido')])
def test_strict_rejects_ambiguous_or_invalid_time(date,time,message):
    with pytest.raises(ValueError,match=message):strict_scheduled_utc(date,time,'America/New_York')

def test_dimension_integrity_and_duplicates(tmp_path):
    rows,proof=load_airports()
    assert rows and proof['commit'] and any(r['iata']=='JFK' for r in rows)
    directory=tmp_path/'data/reference';directory.mkdir(parents=True)
    path=directory/'airport_timezones.csv'
    path.write_text('iata,timezone,icao,country\nJFK,America/New_York,KJFK,US\nJFK,America/New_York,KJFK,US\n',encoding='utf-8')
    path.with_suffix('.provenance.json').write_text(json.dumps(dict(artifact_sha256=digest(path))),encoding='utf-8')
    with pytest.raises(ValueError,match='duplicado'):load_airports(tmp_path)
    path.write_text('tampered',encoding='utf-8')
    with pytest.raises(ValueError,match='alterada'):load_airports(tmp_path)

@pytest.fixture(scope='module')
def spark():
    pytest.importorskip('pyspark')
    from pyspark.sql import SparkSession
    session=(SparkSession.builder.master('local[2]').appName('Silver-real-transform-test')
             .config('spark.ui.enabled','false').config('spark.sql.shuffle.partitions','2')
             .config('spark.driver.bindAddress','127.0.0.1').getOrCreate())
    session.conf.set('spark.sql.session.timeZone','UTC')
    yield session
    session.stop()

def test_real_spark_types_quarantine_labels_dst_and_duplicates(spark):
    from pyspark.sql import functions as F
    from pyspark.sql.types import StructType,StructField,StringType,TimestampType
    from src.processing.contracts import COLUMNS
    from src.processing.silver import IDS,prepare_silver,summarize_silver
    from src.ingestion.bronze import METADATA
    def row(case,number,**changes):
        r={c:None for c in COLUMNS+IDS+sorted(METADATA)}
        r.update(FlightDate='2025-01-10',Reporting_Airline='AA',Flight_Number_Reporting_Airline=str(number),
            Tail_Number=case,Origin='JFK',Dest='LAX',Distance='1000',CRSDepTime='1200',CRSArrTime='1400',
            CRSElapsedTime='120',DepTime='1200',ArrTime='1400',DepDelay='20',ArrDelay='20',Cancelled='0',Diverted='0',
            OriginAirportID='12478',DestAirportID='12892',DOT_ID_Reporting_Airline='19805',
            _source_period='2025-01',_source_zip_sha256='0'*64,_source_csv_sha256='1'*64,
            _source_url='https://example.invalid/bts.zip',_source_file='synthetic.csv',
            _source_downloaded_at='2025-01-01T00:00:00Z',_run_id='synthetic',_ingested_at=datetime(2025,1,1))
        r.update(changes);return r
    rows=[row('BASE',1),row('NEGATIVE',2,DepDelay='-5'),row('CANCELLED',3,Cancelled='1',DepDelay='45'),
          row('CANCELLED_NULL',4,Cancelled='1',DepDelay=None),
          row('GAP',5,FlightDate='2024-03-10',CRSDepTime='230',_source_period='2024-03'),
          row('FOLD',6,FlightDate='2024-11-03',CRSDepTime='130',_source_period='2024-11'),
          row('MIDNIGHT',7,FlightDate='2025-01-31',CRSDepTime='2400'),
          row('INFINITE',8,Distance='Infinity'),row('BAD_FLIGHT',0),row('BAD_TIME',10,CRSDepTime='1260'),
          row('UNKNOWN',11,Origin='ZZZ'),row('CONFLICT_A',9000,DepDelay='0'),row('CONFLICT_B',9000,DepDelay='60'),
          row('DECIMAL_NEGATIVE',20,Cancelled='0.00',Diverted='0.00',DepDelay='-7.00'),
          row('DECIMAL_CANCELLED',21,Cancelled='1.00',Diverted='0.00',DepDelay='45.00'),
          row('DECIMAL_IDS_TIMES','22.00',OriginAirportID='12478.00',DestAirportID='12892.00',
              DOT_ID_Reporting_Airline='19805.00',CRSDepTime='0659.00',CRSArrTime='1020.00'),
          row('FRACTIONAL_FLIGHT','23.50')]
    rows.append(dict(rows[0]))
    schema=StructType([StructField(c,TimestampType() if c=='_ingested_at' else StringType(),True) for c in rows[0]])
    bronze=spark.createDataFrame(rows,schema)
    airports=spark.createDataFrame([('JFK','America/New_York','US')],'Origin string, origin_timezone string, origin_country string')
    prepared=prepare_silver(bronze,airports)
    result={r['Tail_Number']:r.asDict() for r in prepared.select('Tail_Number','_quality_errors','delay15','Cancelled','Diverted',
        'eligible_departure',F.date_format('scheduled_utc','yyyy-MM-dd HH:mm:ss').alias('utc'),
        F.date_format('prediction_cutoff_utc','yyyy-MM-dd HH:mm:ss').alias('cutoff')).collect()}
    assert len(result)==len(rows)-1
    assert result['BASE']['_quality_errors']==[] and result['BASE']['delay15']==1
    assert result['BASE']['utc']=='2025-01-10 17:00:00' and result['BASE']['cutoff']=='2025-01-10 14:00:00'
    assert result['NEGATIVE']['delay15']==0 and result['NEGATIVE']['_quality_errors']==[]
    assert result['CANCELLED']['delay15'] is None and result['CANCELLED']['_quality_errors']==[]
    assert result['CANCELLED_NULL']['delay15'] is None and result['CANCELLED_NULL']['_quality_errors']==[]
    assert result['MIDNIGHT']['utc']=='2025-02-01 05:00:00' and result['MIDNIGHT']['_quality_errors']==[]
    assert result['DECIMAL_NEGATIVE']['Cancelled']==0 and result['DECIMAL_NEGATIVE']['Diverted']==0
    assert result['DECIMAL_NEGATIVE']['eligible_departure'] is True and result['DECIMAL_NEGATIVE']['delay15']==0
    assert result['DECIMAL_NEGATIVE']['_quality_errors']==[]
    assert result['DECIMAL_CANCELLED']['Cancelled']==1 and result['DECIMAL_CANCELLED']['delay15'] is None
    assert result['DECIMAL_CANCELLED']['eligible_departure'] is False and result['DECIMAL_CANCELLED']['_quality_errors']==[]
    assert result['DECIMAL_IDS_TIMES']['_quality_errors']==[] and result['DECIMAL_IDS_TIMES']['utc']=='2025-01-10 11:59:00'
    expected={'GAP':'nonexistent_local_time_DST','FOLD':'ambiguous_local_time_DST','INFINITE':'invalid_numeric_Distance',
              'BAD_FLIGHT':'positive_integer_Flight_Number_Reporting_Airline','BAD_TIME':'invalid_hhmm_CRSDepTime',
              'UNKNOWN':'unknown_origin_timezone','CONFLICT_A':'contradictory_key','CONFLICT_B':'contradictory_key',
              'FRACTIONAL_FLIGHT':'positive_integer_Flight_Number_Reporting_Airline'}
    for case,reason in expected.items():assert reason in result[case]['_quality_errors'],(case,result[case])
    summary=summarize_silver(prepared.where(F.size('_quality_errors')==0))
    assert summary['quality_passed'] and summary['null_required_typed_rows']==0 and summary['invalid_label_rows']==0
    assert summary['silver_rows']==8 and summary['eligible_departures']==5
    assert summary['cancelled_rows']==3 and summary['delayed_departures']==3
