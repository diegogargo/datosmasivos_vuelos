import pandas as pd
from src.validation.audit_sample import audit_frame
from src.utils.common import ROOT

def test_missing_columns():assert not audit_frame(pd.DataFrame({'FlightDate':[]}))['passed']

def test_quality_checks_reject_bad_values():
    df=pd.read_csv(ROOT/'data/sample/flights_2025_01.csv').iloc[:5].copy()
    df.loc[0,'CRSDepTime']=1260
    df.loc[1,'Cancelled']=2
    df.loc[2,'Distance']=-5
    df.loc[3,'Origin']='x'
    result=audit_frame(df)
    failed={c['check'] for c in result['checks'] if not c['passed']}
    assert {'scheduled_hhmm','cancelled_binary','distance_positive','origin_format'}<=failed
