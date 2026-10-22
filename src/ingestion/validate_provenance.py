"""Verifica la muestra entre formatos y su manifiesto, sin modificarla."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from src.processing.contracts import COLUMNS
from src.utils.common import ROOT, digest, now, read_json, write_json

TEXT = {'FlightDate', 'Reporting_Airline', 'Tail_Number', 'Origin', 'Dest'}


def validate(csv_path, parquet_path, manifest_path, expected_period='2025-01'):
    """Retorna un reporte de comprobaciones; nunca convierte un fallo en �xito."""
    checks = []

    def check(name, passed, detail=''):
        checks.append(dict(name=name, passed=bool(passed), detail=str(detail)))

    check('expected_period_valid', bool(re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', expected_period)))
    paths = dict(csv=Path(csv_path), parquet=Path(parquet_path), manifest=Path(manifest_path))
    for name, path in paths.items():
        check(f'{name}_exists', path.is_file(), path.name)
    report = dict(executed_at=now(), expected_period=expected_period, checks=checks,
                  scope='Integridad de muestra y coherencia de metadatos; no vuelve a contar el ZIP original',
                  numeric_tolerance=dict(rtol=1e-12, atol=1e-9))
    if not all(x['passed'] for x in checks):
        return dict(report, passed=False)
    try:
        manifest = read_json(paths['manifest'])
        check('manifest_period', manifest.get('period') == expected_period)
        for kind in ('csv', 'parquet'):
            check(f'{kind}_sha256', digest(paths[kind]) == manifest.get(f'{kind}_sha256'))
        source = urlparse(manifest.get('source_url', ''))
        year, month = map(int, expected_period.split('-'))
        expected_name = f'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip'
        check('source_url', source.scheme == 'https' and source.hostname in
              {'transtats.bts.gov', 'www.transtats.bts.gov'} and
              source.path == '/PREZIP/' + expected_name and not source.query and not source.fragment)
        check('source_sha256_recorded', bool(re.fullmatch(r'[0-9a-f]{64}', manifest.get('source_sha256', ''))))
        frames = {'csv': pd.read_csv(paths['csv']), 'parquet': pd.read_parquet(paths['parquet'])}
        for name, frame in frames.items():
            check(f'{name}_columns', list(frame.columns) == COLUMNS)
            check(f'{name}_rows', len(frame) > 0 and len(frame) == manifest.get('sample_rows'))
            check(f'{name}_column_count', len(frame.columns) == manifest.get('sample_columns'))
            dates = pd.to_datetime(frame['FlightDate'], errors='coerce')
            check(f'{name}_dates', dates.notna().all() and dates.dt.strftime('%Y-%m').eq(expected_period).all())
        source_rows, source_cols = manifest.get('original_rows'), manifest.get('original_columns')
        check('source_dimensions_coherent', type(source_rows) is int and type(source_cols) is int and
              source_rows >= len(frames['csv']) and source_cols >= len(COLUMNS))
        normalized = []
        for frame in frames.values():
            copy = frame.copy()
            for column in COLUMNS:
                copy[column] = copy[column].astype('string') if column in TEXT else pd.to_numeric(copy[column], errors='raise')
            normalized.append(copy)
        try:
            pd.testing.assert_frame_equal(*normalized, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-9)
            check('formats_same_values_order_and_nulls', True)
        except AssertionError as exc:
            check('formats_same_values_order_and_nulls', False, str(exc)[:600])
        report['observed_rows'] = len(frames['csv'])
        report['observed_columns'] = len(frames['csv'].columns)
    except Exception as exc:
        check('readable_and_valid_structure', False, f'{type(exc).__name__}: {exc}')
    return dict(report, passed=all(x['passed'] for x in checks))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    default = ROOT / 'data/sample/flights_2025_01'
    parser.add_argument('--csv', type=Path, default=default.with_suffix('.csv'))
    parser.add_argument('--parquet', type=Path, default=default.with_suffix('.parquet'))
    parser.add_argument('--manifest', type=Path, default=default.with_suffix('.provenance.json'))
    parser.add_argument('--expected-period', default='2025-01')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/tables/provenance_validation.json')
    args = parser.parse_args(argv)
    report = validate(args.csv, args.parquet, args.manifest, args.expected_period)
    write_json(args.output, report)
    failed = [x['name'] for x in report['checks'] if not x['passed']]
    print('Procedencia correcta' if report['passed'] else 'Fallo de procedencia: ' + ', '.join(failed))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
