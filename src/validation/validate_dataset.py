"""Comprueba datos procesados y consistencia de agregados de la muestra."""
import pandas as pd
from src.processing.contracts import COLUMNS,label_delay15
from src.processing.build_dataset import aggregate
from src.validation.audit_sample import audit_frame
from src.utils.common import ROOT,now,read_json,write_json


def validate_frames(df,monthly,manifest):
    result=audit_frame(df[COLUMNS]);checks=result['checks']
    def add(name,ok):checks.append(dict(check=name,passed=bool(ok),violations=int(not ok)))
    add('expected_volume',len(df)==manifest['output_rows'] and len(df)==manifest['input_rows']-manifest['exact_duplicates_removed'])
    add('processed_types',pd.api.types.is_datetime64_any_dtype(df.FlightDate) and pd.api.types.is_numeric_dtype(df.DepDelay))
    add('prediction_cutoff_3h',((df.scheduled_departure_local-df.prediction_cutoff_local)==pd.Timedelta(hours=3)).all())
    expected=pd.Series([label_delay15(c,d) for c,d in zip(df.Cancelled,df.DepDelay)],dtype='Int8')
    add('label_matches_business_rule',df.delay15.reset_index(drop=True).astype('Int8').equals(expected))
    add('eligibility_matches_label',df.eligible_departure.reset_index(drop=True).equals(expected.notna()))
    add('partition_date_consistency',df.year.eq(df.FlightDate.dt.year).all() and df.month.eq(df.FlightDate.dt.month).all())
    try:
        pd.testing.assert_frame_equal(aggregate(df).sort_values(['year','month']).reset_index(drop=True),
            monthly.sort_values(['year','month']).reset_index(drop=True),check_dtype=False,check_exact=False,rtol=1e-12)
        consistent=True
    except AssertionError:consistent=False
    add('monthly_aggregates_match_rows',consistent)
    result['passed']=all(c['passed'] for c in checks);result['mode']='sample_local';result['validated_at']=now()
    return result


def validate():
    base=ROOT/'data/processed/sample';manifest=read_json(base/'build_manifest.json')
    # Leer cada archivo evita depender de inferencias de tipo de Hive entre versiones de Arrow.
    frames=[]
    for name in manifest['partitions']:
        p=ROOT/name;df=pd.read_parquet(p)
        df['year']=int(p.parents[1].name.split('=')[1]);df['month']=int(p.parent.name.split('=')[1]);frames.append(df)
    df=pd.concat(frames,ignore_index=True)
    result=validate_frames(df,pd.read_parquet(base/'delay_monthly.parquet'),manifest)
    write_json(ROOT/'reports/tables/processed_validation.json',result)
    print(f'Validación procesada: {sum(c["passed"] for c in result["checks"])}/{len(result["checks"])} comprobaciones')
    return result
if __name__=='__main__':
    if not validate()['passed']:raise SystemExit(1)
