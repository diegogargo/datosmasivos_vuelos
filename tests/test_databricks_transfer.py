import importlib.util
import io
import zipfile

import pytest

from src.ingestion.acquire_range import extract_csv
from src.ingestion.bronze import materialize_csv
from src.processing.contracts import COLUMNS
from src.utils.common import ROOT, digest, write_json

spec = importlib.util.spec_from_file_location('run_databricks', ROOT / 'scripts/run_databricks.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def acquired(tmp_path):
    path = tmp_path / 'data/raw/bts/month.zip'
    path.parent.mkdir(parents=True)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('flights.csv', ','.join(COLUMNS) + '\n2025-01-10,' + ','.join([''] * (len(COLUMNS) - 1)) + '\n')
    item = dict(period='2025-01', path='data/raw/bts/month.zip', sha256=digest(path), bytes=path.stat().st_size)
    item = extract_csv(path, item, tmp_path)
    item['status'] = 'complete'
    write_json(tmp_path / 'data/raw/manifest.json', {'files': {'2025-01': item}})
    return item


def test_zip_only_transfer_reconstructs_original_csv_with_same_hash(tmp_path):
    item = acquired(tmp_path)
    (tmp_path / item['csv_path']).unlink()
    rebuilt = materialize_csv(tmp_path, '2025-01', item)
    assert rebuilt['csv_sha256'] == item['csv_sha256'] and rebuilt['csv_rows'] == 1


def test_reconstruction_refuses_different_expected_content(tmp_path):
    item = acquired(tmp_path)
    item['csv_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        materialize_csv(tmp_path, '2025-01', item)


def test_transfer_manifest_only_includes_requested_period_and_rejects_bad_zip(tmp_path):
    item = acquired(tmp_path)
    path, manifest = driver.prepare_manifest('2025-01', '2025-01', tmp_path)
    assert list(manifest['files']) == ['2025-01'] and path.is_file()
    with pytest.raises(ValueError, match='Primero adquirir'):
        driver.prepare_manifest('2025-01', '2025-02', tmp_path)
    (tmp_path / item['path']).write_bytes(b'tampered')
    with pytest.raises(ValueError, match='alterado'):
        driver.prepare_manifest('2025-01', '2025-01', tmp_path)
