"""Validación local de la muestra; no certifica tablas Spark o Delta."""
import argparse,json
from pathlib import Path
import pandas as pd
import numpy as np
from src.processing.contracts import COLUMNS,KEY,hhmm_minutes,label_delay15
from src.utils.common import ROOT,now,write_json,digest,read_json

def audit_frame(df):
    checks=[]
    def add(name,n):checks.append({'check':name,'violations':int(n),'passed':int(n)==0})
    missing=set(COLUMNS)-set(df.columns);add('required_columns',len(missing))
    if missing:return {'passed':False,'rows':len(df),'checks':checks}
    dates=pd.to_datetime(df.FlightDate,errors='coerce')
    add('valid_dates',dates.isna().sum())
    add('required_keys',df[KEY].isna().any(axis=1).sum())
    add('unique_natural_key',df.duplicated(KEY).sum())
    numeric={c:pd.to_numeric(df[c],errors='coerce') for c in set(COLUMNS)-{'FlightDate','Reporting_Airline','Tail_Number','Origin','Dest'}}
    for column,values in sorted(numeric.items()):
        add('finite_observed_'+column,(df[column].notna()&(~np.isfinite(values))).sum())
    add('cancelled_binary',(~numeric['Cancelled'].isin([0,1])).sum())
    add('diverted_binary',(~numeric['Diverted'].isin([0,1])).sum())
    add('scheduled_hhmm',df.CRSDepTime.map(hhmm_minutes).isna().sum())
    add('arrival_scheduled_hhmm',df.CRSArrTime.map(hhmm_minutes).isna().sum())
    for column in ('DepTime','ArrTime'):
        add('observed_hhmm_'+column,(df[column].notna()&df[column].map(hhmm_minutes).isna()).sum())
    flight=numeric['Flight_Number_Reporting_Airline']
    add('flight_number_positive_integer',(~(np.isfinite(flight)&flight.gt(0)&flight.mod(1).eq(0))).sum())
    distance=pd.to_numeric(df.Distance,errors='coerce')
    add('distance_positive',((distance<=0)|distance.isna()).sum())
    add('origin_format',(~df.Origin.astype(str).str.fullmatch('[A-Z]{3}')).sum())
    add('destination_format',(~df.Dest.astype(str).str.fullmatch('[A-Z]{3}')).sum())
    y=pd.Series([label_delay15(c,d) for c,d in zip(df.Cancelled,df.DepDelay)],dtype='Int8')
    add('cancelled_without_label',int(y[df.Cancelled.eq(1)].notna().sum()))
    add('operated_with_observed_outcome',int((df.Cancelled.eq(0)&pd.to_numeric(df.DepDelay,errors='coerce').isna()).sum()))
    return dict(validated_at=now(),passed=all(c['passed'] for c in checks),rows=len(df),
      columns=len(df.columns),checks=checks,cancellations=int(df.Cancelled.eq(1).sum()),
      eligible_departures=int(y.notna().sum()),delayed_departures=int(y.sum()),
      delay_rate=float(y.mean()) if y.notna().any() else None,
      delay_rate_denominator='Cancelled == 0 y DepDelay finito observado',
      missingness=df.isna().sum().astype(int).to_dict())
def audit(path=None):
    path=Path(path) if path else ROOT/'data/sample/flights_2025_01.csv'
    df=pd.read_csv(path);result=audit_frame(df)
    provenance=path.with_suffix('.provenance.json')
    if provenance.exists():
        proof=read_json(provenance)
        ok=digest(path)==proof['csv_sha256']
        result['checks'].append(dict(check='sample_sha256',passed=ok,violations=int(not ok)))
        result['passed']=result['passed'] and ok
    result['source_file']=path.name
    write_json(ROOT/'reports/tables/sample_validation.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['missingness','checks']},indent=2,ensure_ascii=False))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--path');a=p.parse_args()
    if not audit(a.path)['passed']:raise SystemExit(1)
