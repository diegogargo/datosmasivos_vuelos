"""Ingesta mensual completa, reanudable y por bloques. Sin descargas al importar."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import re
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.compute as pc
import yaml

from src.ingestion.bts import acquire, validate_zip
from src.processing.contracts import COLUMNS
from src.utils.common import ROOT, digest, now, read_json, write_json


def months(start, end):
    def ordinal(value):
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', value):
            raise ValueError('Usar periodo YYYY-MM')
        year, month = map(int, value.split('-'))
        if not 1987 <= year <= 2100:
            raise ValueError('Año fuera del contrato BTS')
        return year * 12 + month - 1
    first, last = ordinal(start), ordinal(end)
    if first > last:
        raise ValueError('Inicio posterior al fin')
    return [f'{n // 12:04d}-{n % 12 + 1:02d}' for n in range(first, last + 1)]


def csv_summary(path, period):
    """Escanea todas las filas; Arrow mantiene bloques de 4 MiB, no todo el mes."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        header = next(csv.reader(stream))
    if set(COLUMNS) - set(header):
        raise ValueError('Faltan campos del contrato BTS')
    if header.count('FlightDate') != 1:
        raise ValueError('FlightDate ambiguo')
    rows = 0
    with pa.OSFile(str(path), 'rb') as source, pacsv.open_csv(source, read_options=pacsv.ReadOptions(block_size=4 * 1024 * 1024),
                        convert_options=pacsv.ConvertOptions(
                            include_columns=['FlightDate'], column_types={'FlightDate': pa.string()})) as reader:
        for batch in reader:
            dates = batch.column(0)
            valid = pc.match_substring_regex(dates, pattern=r'^' + period + r'-\d{2}( 00:00:00)?$')
            # Además del prefijo, parsear el día detecta fechas inexistentes como febrero 30.
            parsed = pc.strptime(pc.utf8_slice_codeunits(dates, 0, 10), format='%Y-%m-%d', unit='s', error_is_null=True)
            roundtrip = pc.equal(pc.strftime(parsed, format='%Y-%m-%d'), pc.utf8_slice_codeunits(dates, 0, 10))
            if dates.null_count or pc.any(pc.invert(pc.fill_null(valid, False))).as_py() or parsed.null_count or pc.any(pc.invert(pc.fill_null(roundtrip, False))).as_py():
                raise ValueError(f'FlightDate nulo, inválido o fuera de {period}')
            rows += batch.num_rows
    if rows == 0:
        raise ValueError('Mes sin vuelos')
    return dict(csv_rows=rows, csv_columns=len(header), csv_header=header)


def extract_csv(zip_path, item, root):
    """Escritura atómica del CSV original; no aplica tipos, filtros ni muestreo."""
    root = Path(root)
    target = root / 'data/raw/csv' / item['period'] / 'flights.csv'
    if target.exists():
        if digest(target) != item.get('csv_sha256') or item.get('csv_path') != target.relative_to(root).as_posix():
            raise ValueError('CSV existente sin trazabilidad válida; no sobrescribir')
        return dict(item, csv_cache_hit=True, **csv_summary(target, item['period']))
    member = validate_zip(zip_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix('.csv.part')
    hasher = hashlib.sha256()
    try:
        with zipfile.ZipFile(zip_path) as archive, archive.open(member) as source, part.open('wb') as output:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                hasher.update(block)
                output.write(block)
        summary = csv_summary(part, item['period'])
        size = part.stat().st_size
        os.replace(part, target)
    finally:
        part.unlink(missing_ok=True)
    return dict(item, csv_path=target.relative_to(root).as_posix(), csv_sha256=hasher.hexdigest(),
                csv_bytes=size, csv_member=member, csv_cache_hit=False, **summary)


@contextmanager
def ingestion_lock(root):
    path = Path(root) / 'data/raw/.ingestion.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError('Ya hay otra ingesta o un lock pendiente de inspección') from exc
    try:
        with os.fdopen(handle, 'w') as stream:
            stream.write(f'pid={os.getpid()} started_at={now()}')
        yield
    finally:
        path.unlink(missing_ok=True)


def run(start, end, root=ROOT, output=None):
    requested = months(start, end)
    root = Path(root).resolve()
    output = Path(output) if output else root / 'reports/tables/acquisition_full.json'
    manifest_path = root / 'data/raw/manifest.json'
    report = dict(start=start, end=end, requested_months=len(requested), started_at=now(),
                  sample=False, complete=False, months=[], errors=[])
    started = time.perf_counter()
    with ingestion_lock(root):
        for period in requested:
            began = time.perf_counter()
            try:
                year, month = map(int, period.split('-'))
                path, item = acquire(year, month, root=root)
                item = extract_csv(path, item, root)
                item.update(status='complete', inspected_at=now())
                manifest = read_json(manifest_path)
                manifest['files'][period] = item
                manifest.get('errors', {}).pop(period, None)
                manifest['updated_at'] = now()
                write_json(manifest_path, manifest)
                report['months'].append(dict(period=period, rows=item['csv_rows'], columns=item['csv_columns'],
                    zip_bytes=item['bytes'], csv_bytes=item['csv_bytes'], zip_sha256=item['sha256'],
                    csv_sha256=item['csv_sha256'], zip_cache_hit=item['cache_hit'],
                    csv_cache_hit=item['csv_cache_hit'], seconds=time.perf_counter() - began))
                print(f"{period}: {item['csv_rows']:,} filas completas; ZIP {item['bytes']:,} bytes", flush=True)
            except Exception as exc:
                error = dict(period=period, type=type(exc).__name__, message=str(exc), at=now())
                report['errors'].append(error)
                print(f'{period}: ERROR {exc}', flush=True)
                manifest = read_json(manifest_path) if manifest_path.exists() else {'files': {}}
                manifest.setdefault('errors', {})[period] = error
                write_json(manifest_path, manifest)
            report.update(completed_months=len(report['months']), rows=sum(x['rows'] for x in report['months']),
                          zip_bytes=sum(x['zip_bytes'] for x in report['months']),
                          csv_bytes=sum(x['csv_bytes'] for x in report['months']),
                          seconds=time.perf_counter() - started, finished_at=now())
            report['complete'] = len(report['months']) == len(requested) and not report['errors']
            write_json(output, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/project.yaml')
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true', help='Sin esta bandera solo muestra el plan')
    args = parser.parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding='utf-8'))
    start, end = args.start or config['period']['start'], args.end or config['period']['end']
    requested = months(start, end)
    print(f'Plan: {start} a {end}, {len(requested)} meses completos, sin muestreo', flush=True)
    if not args.execute:
        return 0
    return 0 if run(start, end, args.root, args.output)['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
