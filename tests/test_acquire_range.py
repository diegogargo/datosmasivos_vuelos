import csv
import io
import zipfile

import pytest

from src.ingestion import acquire_range as module
from src.ingestion import bts
from src.processing.contracts import COLUMNS
from src.utils.common import digest, read_json, write_json


def zip_month(root, period='2025-01', date='2025-01-10'):
    path = root / 'month.zip'
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    row = dict.fromkeys(COLUMNS, '')
    row.update(FlightDate=date, Origin='JFK', Dest='LAX', Tail_Number='N1', Cancelled='1')
    writer.writerow([row[c] for c in COLUMNS])
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('../unsafe.csv', stream.getvalue())
    return path, dict(period=period, sha256=digest(path), bytes=path.stat().st_size)


def test_periods_inclusive_and_year_boundary():
    assert module.months('2022-01', '2025-12')[0::47] == ['2022-01', '2025-12']
    assert len(module.months('2022-01', '2025-12')) == 48
    assert module.months('2024-12', '2025-01') == ['2024-12', '2025-01']


@pytest.mark.parametrize('start,end', [('2025-13', '2025-12'), ('2025-2', '2025-03'),
    ('2025-02', '2025-01'), ('1986-12', '1987-01')])
def test_bad_range(start, end):
    with pytest.raises(ValueError):
        module.months(start, end)


def test_stream_preserves_all_rows_fields_and_prevents_zip_slip(tmp_path):
    path, item = zip_month(tmp_path)
    item = module.extract_csv(path, item, tmp_path)
    assert item['csv_rows'] == 1 and item['csv_columns'] == len(COLUMNS)
    with zipfile.ZipFile(path) as archive:
        assert (tmp_path / item['csv_path']).read_bytes() == archive.read('../unsafe.csv')
    assert not (tmp_path.parent / 'unsafe.csv').exists()
    assert module.extract_csv(path, item, tmp_path)['csv_cache_hit']
    (tmp_path / item['csv_path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='trazabilidad'):
        module.extract_csv(path, item, tmp_path)


@pytest.mark.parametrize('date', ['2024-01-10', '2025-01-32', ''])
def test_wrong_or_invalid_date_not_committed(tmp_path, date):
    path, item = zip_month(tmp_path, date=date)
    with pytest.raises(ValueError):
        module.extract_csv(path, item, tmp_path)
    assert not list(tmp_path.rglob('*.part'))
    assert not list(tmp_path.rglob('flights.csv'))


def test_lock_excludes_second_writer_and_releases_on_error(tmp_path):
    with pytest.raises(ValueError):
        with module.ingestion_lock(tmp_path):
            with pytest.raises(RuntimeError):
                with module.ingestion_lock(tmp_path):
                    pass
            raise ValueError('simulated failure')
    with module.ingestion_lock(tmp_path):
        pass


def test_resume_failed_month_without_redownloading_success(tmp_path, monkeypatch):
    path, item = zip_month(tmp_path)
    calls = []
    def fake_fetch(url, target, old=None):
        calls.append(target.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if '_2025_2.zip' in target.name:
            raise OSError('BTS no disponible')
        if not target.exists():
            target.write_bytes(path.read_bytes())
        if old:
            return dict(old, cache_hit=True)
        return dict(url=url, sha256=digest(target), bytes=target.stat().st_size, cache_hit=old is not None)
    monkeypatch.setattr(bts, 'fetch', fake_fetch)
    first = module.run('2025-01', '2025-02', root=tmp_path)
    assert not first['complete'] and first['rows'] == 1 and len(first['errors']) == 1
    second = module.run('2025-01', '2025-01', root=tmp_path)
    assert second['complete'] and second['months'][0]['csv_cache_hit']
    assert read_json(tmp_path / 'data/raw/manifest.json')['files']['2025-01']['csv_rows'] == 1


def test_default_cli_only_plans(monkeypatch, tmp_path):
    config = tmp_path / 'project.yaml'
    config.write_text("period:\n  start: '2022-01'\n  end: '2025-12'\n", encoding='utf-8')
    monkeypatch.setattr(module, 'run', lambda *args, **kwargs: pytest.fail('No ejecutar sin bandera'))
    assert module.main(['--config', str(config)]) == 0
