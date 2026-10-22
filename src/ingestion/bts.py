"""Descarga verificable BTS. Solo descarga los meses solicitados explícitamente."""
from __future__ import annotations
import argparse,csv,io,json,logging,os,time,urllib.request,zipfile
from pathlib import Path
import pandas as pd
from src.processing.contracts import COLUMNS
from src.utils.common import ROOT,digest,now,read_json,write_json

BASE='https://transtats.bts.gov/PREZIP/'
def validate_zip(path):
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1:raise ValueError('Se esperaba exactamente un CSV BTS')
        if z.testzip() is not None:raise ValueError('ZIP con CRC inválido')
        with z.open(names[0]) as stream:
            fields=next(csv.reader(io.TextIOWrapper(stream,encoding='utf-8-sig')))
        missing=set(COLUMNS)-set(fields)
        if missing:raise ValueError(f'Faltan campos BTS: {sorted(missing)}')
        return names[0]
def fetch(url,target,old=None,opener=urllib.request.urlopen,sleeper=time.sleep):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if old is None or old.get('url')!=url or digest(target)!=old.get('sha256'):
            raise ValueError('Original existente sin trazabilidad válida; no sobrescribir')
        validate_zip(target)
        return dict(old,cache_hit=True,checked_at=now())
    part=target.with_suffix('.zip.part')
    for attempt in range(3):
        try:
            with opener(urllib.request.Request(url,headers={'User-Agent':'DatosMasivos-academic/0.1'}),timeout=120) as response:
                headers=dict(response.headers)
                with part.open('wb') as f:
                    for block in iter(lambda:response.read(1024*1024),b''):f.write(block)
            validate_zip(part);os.replace(part,target)
            return dict(url=url,sha256=digest(target),bytes=target.stat().st_size,
                downloaded_at=now(),cache_hit=False,last_modified=headers.get('Last-Modified'),
                etag=headers.get('ETag'))
        except Exception:
            logging.exception('Fallo descargando %s, intento %s',url,attempt+1)
            part.unlink(missing_ok=True)
            if attempt==2:raise
            sleeper(2**attempt)
def acquire(year,month):
    if not 1987<=year<=2100 or not 1<=month<=12:raise ValueError('Periodo inválido')
    path=ROOT/'data/raw/bts'/f'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip'
    manifest_path=ROOT/'data/raw/manifest.json'
    manifest=read_json(manifest_path) if manifest_path.exists() else {'files':{}}
    period=f'{year}-{month:02d}'
    item=fetch(BASE+path.name,path,manifest['files'].get(period))
    item.update(path=path.relative_to(ROOT).as_posix(),period=period)
    manifest['files'][period]=item;manifest['updated_at']=now()
    write_json(manifest_path,manifest)
    return path,item
def make_sample(year,month,size=5000,seed=42):
    if size<1:raise ValueError('Tamaño debe ser positivo')
    path,item=acquire(year,month)
    member=validate_zip(path)
    with zipfile.ZipFile(path) as z,z.open(member) as f:
        source=pd.read_csv(f,low_memory=False)
    chosen=source.sample(n=min(size,len(source)),random_state=seed).reset_index(drop=True)
    sample=chosen[COLUMNS].copy()
    dest=ROOT/'data/sample';dest.mkdir(parents=True,exist_ok=True)
    csv_path=dest/'flights_2025_01.csv' if (year,month)==(2025,1) else dest/f'flights_{year}_{month:02d}.csv'
    sample.to_csv(csv_path,index=False)
    sample.to_parquet(csv_path.with_suffix('.parquet'),index=False)
    write_json(csv_path.with_suffix('.provenance.json'),dict(created_at=now(),
      description='Muestra regenerada con el procedimiento del notebook original; no es el Parquet histórico de 120000 filas',
      period=f'{year}-{month:02d}',source_url=item['url'],source_sha256=item['sha256'],
      original_rows=len(source),original_columns=len(source.columns),sample_rows=len(sample),
      sample_columns=len(sample.columns),seed=seed,selection='pandas DataFrame.sample sobre CSV completo, luego proyección de 21 columnas',
      versions={'pandas':pd.__version__},csv_sha256=digest(csv_path),
      parquet_sha256=digest(csv_path.with_suffix('.parquet'))))
    print(f'Muestra: {len(sample):,} filas; original: {len(source):,}; periodo {year}-{month:02d}')
    return csv_path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--year',required=True,type=int);p.add_argument('--month',required=True,type=int)
    p.add_argument('--sample',action='store_true');p.add_argument('--size',type=int,default=5000)
    a=p.parse_args()
    if a.sample:make_sample(a.year,a.month,a.size)
    else:
        path,item=acquire(a.year,a.month);print(path.name,item['bytes'],'bytes','caché' if item['cache_hit'] else 'descargado')
if __name__=='__main__':main()
