"""Cobertura del histórico y conciliación de sus evidencias con archivos locales."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from src.ingestion.acquire_range import months
from src.utils.common import ROOT, digest, now, read_json, write_json


def validate(report, start, end, root=None, verify_files=False):
    checks = []
    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
    requested = months(start, end)
    observed = report.get('months', [])
    check('complete', report.get('complete') is True and not report.get('errors'))
    check('period', report.get('start') == start and report.get('end') == end)
    check('coverage', [x.get('period') for x in observed] == requested)
    check('month_counts', report.get('requested_months') == len(requested) == report.get('completed_months'))
    check('not_sampled', report.get('sample') is False)
    check('positive_months', all(type(x.get('rows')) is int and x['rows'] > 0 and x.get('columns', 0) >= 21 for x in observed))
    check('hashes_recorded', all(re.fullmatch(r'[0-9a-f]{64}', x.get(key, '')) for x in observed for key in ('zip_sha256', 'csv_sha256')))
    check('unique_zip_hashes', len({x.get('zip_sha256') for x in observed}) == len(observed))
    for key, field in [('rows', 'rows'), ('zip_bytes', 'zip_bytes'), ('csv_bytes', 'csv_bytes')]:
        check(key + '_total', report.get(key) == sum(x.get(field, 0) for x in observed))
    if verify_files:
        root = Path(root or ROOT).resolve()
        try:
            manifest = read_json(root / 'data/raw/manifest.json')
            for row in observed:
                item = manifest['files'][row['period']]
                check(row['period'] + '_count_manifest', item['csv_rows'] == row['rows'])
                for path_key, hash_key, report_key, size_key in [('path', 'sha256', 'zip_sha256', 'bytes'),
                                                                ('csv_path', 'csv_sha256', 'csv_sha256', 'csv_bytes')]:
                    relative = Path(item[path_key])
                    path = (root / relative).resolve()
                    safe = not relative.is_absolute() and path.is_relative_to(root)
                    check(row['period'] + '_' + path_key + '_path', safe)
                    if not safe:
                        continue
                    check(row['period'] + '_' + path_key + '_integrity', path.is_file() and
                          digest(path) == item[hash_key] == row[report_key] and path.stat().st_size == item[size_key])
        except Exception:
            check('raw_manifest_and_files_readable', False)
    return dict(executed_at=now(), start=start, end=end, verify_files=verify_files,
                passed=all(x['passed'] for x in checks), checks=checks)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT / 'reports/tables/acquisition_full.json')
    parser.add_argument('--verify-files', action='store_true')
    args = parser.parse_args(argv)
    config = yaml.safe_load((ROOT / 'config/project.yaml').read_text(encoding='utf-8'))
    result = validate(read_json(args.report), **config['period'], verify_files=args.verify_files)
    write_json(ROOT / 'reports/tables/acquisition_validation.json', result)
    print('Adquisición completa verificada' if result['passed'] else 'Adquisición incompleta o inconsistente')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
