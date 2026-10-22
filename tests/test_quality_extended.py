import pandas as pd
import pytest
from src.validation.audit_sample import audit_frame
from src.utils.common import ROOT

@pytest.fixture
def frame():return pd.read_csv(ROOT/'data/sample/flights_2025_01.csv').head(3).copy()

@pytest.mark.parametrize('column,value,check',[
    ('CRSArrTime',1260,'arrival_scheduled_hhmm'),('CRSArrTime',12.5,'arrival_scheduled_hhmm'),
    ('Flight_Number_Reporting_Airline',0,'flight_number_positive_integer'),
    ('Flight_Number_Reporting_Airline',-1,'flight_number_positive_integer'),
    ('Flight_Number_Reporting_Airline',1.5,'flight_number_positive_integer'),
    ('DepDelay',float('inf'),'finite_observed_DepDelay'),
    ('Distance',float('inf'),'finite_observed_Distance'),('WeatherDelay',float('-inf'),'finite_observed_WeatherDelay'),
    ('ArrTime',2401,'observed_hhmm_ArrTime')])
def test_reject_quality_error(frame,column,value,check):
    frame[column]=frame[column].astype(float);frame.loc[frame.index[0],column]=value
    report=audit_frame(frame)
    assert not report['passed']
    assert any(c['check']==check and not c['passed'] for c in report['checks'])

def test_null_rate_and_allowed_missingness(frame):
    frame['Cancelled']=1;frame['DepDelay']=None
    frame['Tail_Number']=None;frame['WeatherDelay']=None
    frame['CRSArrTime']=2400
    result=audit_frame(frame)
    assert result['passed'] and result['delay_rate'] is None
    assert result['eligible_departures']==0

def test_valid_midnight_arrival_and_negative_departure(frame):
    frame['CRSArrTime']=0;frame['DepDelay']=-12;frame['Cancelled']=0
    result=audit_frame(frame)
    assert result['passed'] and result['delay_rate']==0

def test_non_numeric_observed_value_is_rejected(frame):
    frame['CarrierDelay']=frame['CarrierDelay'].astype(object)
    frame.loc[frame.index[0],'CarrierDelay']='no_es_numero'
    result=audit_frame(frame)
    assert not result['passed']
    assert any(c['check']=='finite_observed_CarrierDelay' and not c['passed'] for c in result['checks'])
