import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from src.analysis.benchmark_scale import measure, prepare_full_month
from src.processing.contracts import COLUMNS


def test_operation_matches_formats_and_excludes_cancelled_and_nonfinite(tmp_path):
    frame = pd.DataFrame(dict(Cancelled=[0, 0, 1, 0, 0, 0], DepDelay=[-5, 15, 70, None, np.inf, 25]))
    results = []
    for suffix in ('.csv', '.parquet'):
        path = tmp_path / ('input' + suffix)
        frame.to_csv(path, index=False) if suffix == '.csv' else frame.to_parquet(path, index=False)
        result = measure(path)
        assert result['peak_process_bytes'] > 0
        results.append(result['result'])
    assert results[0] == results[1] == dict(rows=6, eligible=3, delayed=2, cancelled=1, eligible_delay_sum=35.0)


def test_complete_projection_cached_input_detects_tampering(tmp_path):
    frame = pd.DataFrame([{**dict.fromkeys(COLUMNS, None), 'FlightDate': '2025-01-10', 'Cancelled': 1, 'DepDelay': 70},
                          {**dict.fromkeys(COLUMNS, None), 'FlightDate': '2025-01-11', 'Cancelled': 0, 'DepDelay': -5}])
    frame['ExtraOriginal'] = 'preserved only in raw'
    archive = tmp_path / 'source.zip'
    with zipfile.ZipFile(archive, 'w') as stream:
        stream.writestr('all.csv', frame.to_csv(index=False))
    csv, parquet, meta = prepare_full_month(archive, tmp_path / 'benchmark')
    assert meta['rows'] == 2 and meta['sample'] is False and list(pd.read_parquet(parquet).columns) == COLUMNS
    assert len(pd.read_csv(csv)) == 2
    assert prepare_full_month(archive, tmp_path / 'benchmark')[2] == meta
    csv.write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='alterada'):
        prepare_full_month(archive, tmp_path / 'benchmark')
