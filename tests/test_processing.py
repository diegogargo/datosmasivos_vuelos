from datetime import datetime
import pandas as pd
import pytest
from src.processing.contracts import hhmm_minutes,scheduled_local,label_delay15
from src.processing.build_dataset import transform,aggregate,build
from src.validation.validate_dataset import validate_frames
from src.utils.common import ROOT

@pytest.mark.parametrize('cancelled,delay,expected',[(0,14,0),(0,15,1),(0,-12,0),(1,75,None),(1,0,None),(0,None,None),(0,float('inf'),None),(.5,20,None)])
def test_label(cancelled,delay,expected):
    assert label_delay15(cancelled,delay)==expected

@pytest.mark.parametrize('value,expected',[(0,0),(5,5),(1259,779),(2359,1439),(2400,1440),(1260,None),(-1,None),(2401,None),(123.5,None),(None,None),('oops',None)])
def test_hhmm(value,expected):assert hhmm_minutes(value)==expected

def test_midnight_rollover():assert scheduled_local('2025-01-31',2400)==datetime(2025,2,1)

@pytest.fixture
def sample():return pd.read_csv(ROOT/'data/sample/flights_2025_01.csv')

def test_real_sample_preserves_cancellations_and_negatives(sample):
    df,removed=transform(sample)
    assert len(df)==5000 and removed==0
    assert df.Cancelled.eq(1).sum()==164
    assert df.loc[df.Cancelled.eq(1),'delay15'].isna().all()
    assert df.eligible_departure.sum()==4836
    assert df.delay15.sum()==896
    assert (df.DepDelay<0).sum()==(sample.DepDelay<0).sum()

def test_duplicate_policies(sample):
    df,n=transform(pd.concat([sample,sample.iloc[[0]]],ignore_index=True))
    assert n==1 and len(df)==len(sample)
    conflict=sample.iloc[[0]].copy();conflict['DepDelay']=9999
    with pytest.raises(ValueError,match='Clave natural'):
        transform(pd.concat([sample,conflict],ignore_index=True))

def test_write_read_and_cross_table_validation(tmp_path,sample):
    source=tmp_path/'input.csv';sample.to_csv(source,index=False)
    df,monthly,manifest=build(source,tmp_path)
    result=validate_frames(df,monthly,manifest)
    assert result['passed']
    bad=monthly.copy();bad.loc[0,'delayed_departures']+=1
    assert not validate_frames(df,bad,manifest)['passed']
    bad_df=df.copy();bad_df.loc[0,'prediction_cutoff_local']+=pd.Timedelta(hours=1)
    assert not validate_frames(bad_df,monthly,manifest)['passed']
    paths=list((tmp_path/'data/processed/sample/flights').rglob('*.parquet'))
    assert sum(len(pd.read_parquet(p)) for p in paths)==len(sample)
