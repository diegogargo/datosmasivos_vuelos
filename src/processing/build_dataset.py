"""Construye interim y processed de la muestra, sin suponer disponibilidad a 3 h."""
import argparse
from pathlib import Path
import pandas as pd
from src.processing.contracts import COLUMNS,KEY,scheduled_local,label_delay15
from src.utils.common import ROOT,now,digest,write_json
from src.validation.audit_sample import audit_frame


def transform(source):
    missing=set(COLUMNS)-set(source.columns)
    if missing:raise ValueError(f'Faltan columnas: {sorted(missing)}')
    df=source[COLUMNS].copy()
    duplicates=int(df.duplicated().sum())
    df=df.drop_duplicates().reset_index(drop=True)
    if df.duplicated(KEY).any():raise ValueError('Clave natural repetida con datos distintos; revisar, no borrar')
    for c in ['Reporting_Airline','Tail_Number','Origin','Dest']:
        df[c]=df[c].astype('string').str.strip().str.upper()
    df['FlightDate']=pd.to_datetime(df.FlightDate,errors='raise').dt.normalize()
    for c in set(COLUMNS)-{'FlightDate','Reporting_Airline','Tail_Number','Origin','Dest'}:
        df[c]=pd.to_numeric(df[c],errors='raise')
    proof=audit_frame(df)
    if not proof['passed']:raise ValueError(f'Calidad de entrada inválida: {proof["checks"]}')
    for c in ['Flight_Number_Reporting_Airline','CRSDepTime','CRSArrTime','Cancelled','Diverted']:
        df[c]=df[c].astype('Int64')
    df['scheduled_departure_local']=pd.to_datetime([scheduled_local(d,h) for d,h in zip(df.FlightDate,df.CRSDepTime)])
    df['prediction_cutoff_local']=df.scheduled_departure_local-pd.Timedelta(hours=3)
    df['delay15']=pd.Series([label_delay15(c,d) for c,d in zip(df.Cancelled,df.DepDelay)],dtype='Int8')
    df['eligible_departure']=df.delay15.notna()
    df['year']=df.FlightDate.dt.year.astype('int16')
    df['month']=df.FlightDate.dt.month.astype('int8')
    return df,duplicates


def aggregate(df):
    eligible=df[df.eligible_departure]
    return eligible.groupby(['year','month'],observed=True).agg(
        eligible_departures=('delay15','size'),delayed_departures=('delay15','sum'),
        delay_rate=('delay15','mean')).reset_index()


def build(path=None,root=ROOT):
    root=Path(root);path=Path(path) if path else root/'data/sample/flights_2025_01.csv'
    source=pd.read_csv(path);df,duplicates=transform(source)
    interim=root/'data/interim/sample/flights_clean.parquet';interim.parent.mkdir(parents=True,exist_ok=True)
    df.to_parquet(interim,index=False)
    target=root/'data/processed/sample';target.mkdir(parents=True,exist_ok=True)
    # Actualizar únicamente las particiones presentes en esta muestra.
    paths=[]
    for (year,month),group in df.groupby(['year','month'],observed=True):
        p=target/f'flights/year={year}/month={month}/part-0.parquet';p.parent.mkdir(parents=True,exist_ok=True)
        group.drop(columns=['year','month']).to_parquet(p,index=False);paths.append(p.relative_to(root).as_posix())
    monthly=aggregate(df);monthly.to_parquet(target/'delay_monthly.parquet',index=False)
    proof=dict(created_at=now(),mode='sample_local',source=path.name,source_sha256=digest(path),
        input_rows=len(source),output_rows=len(df),exact_duplicates_removed=duplicates,
        cancellations=int(df.Cancelled.eq(1).sum()),eligible_departures=int(df.eligible_departure.sum()),
        partitions=paths,monthly_file='data/processed/sample/delay_monthly.parquet',
        note='Tiempos locales sin zona; cutoff no certifica disponibilidad operativa. No es una ejecución Delta/Spark.')
    write_json(target/'build_manifest.json',proof)
    print(f'Procesado local: {len(df):,} filas, {len(paths)} partición(es)')
    return df,monthly,proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--path');a=p.parse_args();build(a.path)
