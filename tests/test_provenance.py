import json

import pandas as pd
import pytest

from src.ingestion.validate_provenance import main, validate
from src.utils.common import ROOT, digest, write_json


@pytest.fixture
def sample(tmp_path):
    csv, parquet, manifest = (tmp_path / name for name in ('s.csv', 's.parquet', 's.json'))
    source = ROOT / 'data/sample/flights_2025_01'
    frame = pd.read_parquet(source.with_suffix('.parquet')).head(12)
    frame.to_csv(csv, index=False)
    frame.to_parquet(parquet, index=False)
    meta = json.loads(source.with_suffix('.provenance.json').read_text(encoding='utf-8'))
    meta.update(sample_rows=len(frame), csv_sha256=digest(csv), parquet_sha256=digest(parquet))
    write_json(manifest, meta)
    return csv, parquet, manifest, meta


def test_equivalent_formats_with_nulls(sample):
    assert validate(*sample[:3])['passed']


@pytest.mark.parametrize('field,value', [
    ('period', '2024-01'), ('sample_rows', 999), ('sample_columns', 22),
    ('csv_sha256', '0' * 64), ('parquet_sha256', '0' * 64),
    ('source_url', 'https://example.com/unverified.zip'), ('original_rows', 1),
])
def test_false_metadata_rejected(sample, field, value):
    csv, parquet, path, meta = sample
    meta[field] = value
    write_json(path, meta)
    assert not validate(csv, parquet, path)['passed']


@pytest.mark.parametrize('change', ['values', 'order', 'nulls', 'date', 'columns'])
def test_changed_content_with_matching_hash_still_rejected(sample, change):
    csv, parquet, path, meta = sample
    frame = pd.read_parquet(parquet)
    if change == 'values':
        frame.loc[0, 'Distance'] += 1
    elif change == 'order':
        frame = frame.iloc[::-1].reset_index(drop=True)
    elif change == 'nulls':
        frame.loc[0, 'Origin'] = None
    elif change == 'date':
        frame.loc[0, 'FlightDate'] = '2024-01-01'
    else:
        frame = frame.drop(columns='Distance')
    frame.to_parquet(parquet, index=False)
    meta['parquet_sha256'] = digest(parquet)
    write_json(path, meta)
    assert not validate(csv, parquet, path)['passed']


def test_missing_file_and_invalid_period_return_report(sample):
    sample[0].unlink()
    assert not validate(*sample[:3])['passed']
    assert not validate(*sample[:3], expected_period='2025-13')['passed']


def test_cli_failure_writes_json_and_nonzero(sample, tmp_path):
    output = tmp_path / 'result.json'
    assert main(['--csv', str(sample[0]), '--parquet', str(sample[1]), '--manifest', str(sample[2]),
                 '--expected-period', '2024-01', '--output', str(output)]) == 1
    assert not json.loads(output.read_text(encoding='utf-8'))['passed']
