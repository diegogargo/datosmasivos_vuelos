import pytest

from src.ingestion.bronze import column_names, contained_file, table_identifier, verify_source, volume_root_path
from src.processing.contracts import COLUMNS
from src.utils.common import digest


def source(tmp_path):
    zip_path, csv_path = tmp_path / 'raw.zip', tmp_path / 'flights.csv'
    zip_path.write_bytes(b'zip contents verified by acquisition')
    csv_path.write_bytes(b'original CSV bytes\n')
    return dict(period='2025-01', status='complete', path='raw.zip', sha256=digest(zip_path),
                csv_path='flights.csv', csv_sha256=digest(csv_path), csv_bytes=csv_path.stat().st_size,
                csv_header=COLUMNS + [''], csv_columns=len(COLUMNS) + 1, csv_rows=1)


def test_empty_header_preserves_column_position():
    names = column_names(COLUMNS + [''])
    assert names[:-1] == COLUMNS and names[-1] == f'_bts_column_{len(COLUMNS)}'


@pytest.mark.parametrize('header', [COLUMNS[:-1], COLUMNS + ['Origin'], COLUMNS + ['_run_id']])
def test_incompatible_header_rejected(header):
    with pytest.raises(ValueError):
        column_names(header)


def test_complete_source_both_hashes_and_column_mapping(tmp_path):
    item = source(tmp_path)
    path, names = verify_source(tmp_path, '2025-01', item)
    assert path == tmp_path / 'flights.csv' and len(names) == len(COLUMNS) + 1


@pytest.mark.parametrize('field,value', [('sha256', 'bad'), ('csv_sha256', 'bad'),
    ('period', '2024-01'), ('status', 'partial'), ('csv_rows', 0), ('csv_columns', 1),
    ('csv_bytes', 0), ('csv_path', '../outside.csv')])
def test_bad_source_fails_before_spark_write(tmp_path, field, value):
    item = source(tmp_path)
    item[field] = value
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_source(tmp_path, '2025-01', item)


def test_path_and_sql_restrictions(tmp_path):
    assert table_identifier('workspace.bronze.vuelos_raw') == '`workspace`.`bronze`.`vuelos_raw`'
    for table in ['bronze.raw', 'cat.bronze.raw;DROP', 'cat.bronze.*']:
        with pytest.raises(ValueError):
            table_identifier(table)
    for path in ['dbfs:/invented', '/tmp/source', '/Volumes/catalog/schema/volume/../outside']:
        with pytest.raises(ValueError):
            volume_root_path(path)
    with pytest.raises(ValueError):
        contained_file(tmp_path, '../outside.csv')
    with pytest.raises(FileNotFoundError):
        contained_file(tmp_path, 'missing.csv')
