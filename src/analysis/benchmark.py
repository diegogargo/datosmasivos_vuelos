"""CSV frente a Parquet: lectura de las mismas 21 columnas y agregación idéntica.
La memoria reportada es tamaño profundo del DataFrame, no pico RSS del proceso.
"""
import json,platform,time
import pandas as pd
import pyarrow
from src.utils.common import ROOT,now,write_json

def run():
    paths=[ROOT/'data/sample/flights_2025_01.csv',ROOT/'data/sample/flights_2025_01.parquet']
    results=[];reference=None
    for p in paths:
        for repeat in range(6):
            start=time.perf_counter()
            df=pd.read_csv(p) if p.suffix=='.csv' else pd.read_parquet(p)
            eligible=df[df.Cancelled.eq(0)&df.DepDelay.notna()]
            result=(len(df),len(eligible),int(eligible.DepDelay.ge(15).sum()))
            duration=time.perf_counter()-start
            if reference is None:reference=result
            assert result==reference,'Resultados no equivalentes'
            results.append(dict(format=p.suffix[1:],repeat=repeat,warmup=repeat==0,rows=len(df),
                file_bytes=p.stat().st_size,seconds=duration,dataframe_bytes=int(df.memory_usage(deep=True).sum()),
                eligible=result[1],delayed=result[2],correct=True))
    table=pd.DataFrame(results);folder=ROOT/'reports/tables';folder.mkdir(parents=True,exist_ok=True)
    table.to_csv(folder/'benchmark_runs.csv',index=False)
    summary=table[~table.warmup].groupby('format').agg(rows=('rows','first'),file_bytes=('file_bytes','first'),
        median_seconds=('seconds','median'),min_seconds=('seconds','min'),max_seconds=('seconds','max'),
        dataframe_bytes=('dataframe_bytes','first'),correct=('correct','all')).reset_index()
    summary.to_csv(folder/'benchmark_summary.csv',index=False)
    write_json(folder/'benchmark_environment.json',dict(executed_at=now(),platform=platform.platform(),python=platform.python_version(),
        pandas=pd.__version__,pyarrow=pyarrow.__version__,repeats=5,warmup_per_format=1,cache='SO caliente; no se vació caché',
        operation='lectura completa de 5000 filas x 21 columnas + filtro operados + conteo retraso >=15',
        memory='DataFrame.memory_usage(deep=True); no pico de memoria ni cómputo distribuido',limits='Muestra local; no extrapolar a 24 meses o Databricks'))
    print(summary.to_string(index=False))
if __name__=='__main__':run()
