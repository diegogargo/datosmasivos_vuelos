"""Benchmark CSV/Parquet sobre muestra y un mes completo, en procesos separados."""
from __future__ import annotations

import argparse
import ctypes
import json
import platform
import statistics
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow

from src.ingestion.bts import validate_zip
from src.processing.contracts import COLUMNS
from src.utils.common import ROOT, digest, now, read_json, write_json


def peak_process_bytes():
    """Máximo del proceso desde su inicio, incluidos Python y librerías."""
    if sys.platform == 'win32':
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
                'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(counters.PeakWorkingSetSize)
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value * 1024)


def measure(path):
    path = Path(path)
    start = time.perf_counter()
    frame = pd.read_csv(path) if path.suffix == '.csv' else pd.read_parquet(path)
    delay = pd.to_numeric(frame.DepDelay)
    eligible = frame.Cancelled.eq(0) & delay.notna() & np.isfinite(delay)
    result = dict(rows=len(frame), eligible=int(eligible.sum()), delayed=int((eligible & delay.ge(15)).sum()),
                  cancelled=int(frame.Cancelled.eq(1).sum()), eligible_delay_sum=float(delay[eligible].sum()))
    seconds = time.perf_counter() - start
    return dict(result=result, seconds=seconds, peak_process_bytes=peak_process_bytes(),
                dataframe_bytes=int(frame.memory_usage(deep=True).sum()))


def prepare_full_month(zip_path, output_dir):
    """Proyecta los 21 campos de TODOS los vuelos; no muestrea ni limpia."""
    zip_path, output_dir = Path(zip_path), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / 'benchmark_input.json'
    csv_path, parquet_path = output_dir / 'flights.csv', output_dir / 'flights.parquet'
    if manifest_path.exists():
        meta = read_json(manifest_path)
        if (meta['source_zip_sha256'] != digest(zip_path) or
            any(digest(path) != meta[path.suffix[1:] + '_sha256'] for path in (csv_path, parquet_path))):
            raise ValueError('Entrada del benchmark alterada; no reutilizar')
        return csv_path, parquet_path, meta
    member = validate_zip(zip_path)
    with zipfile.ZipFile(zip_path) as archive, archive.open(member) as stream:
        frame = pd.read_csv(stream, usecols=COLUMNS, low_memory=False)[COLUMNS]
    frame.to_csv(csv_path, index=False)
    frame.to_parquet(parquet_path, index=False)
    pd.testing.assert_frame_equal(pd.read_csv(csv_path), pd.read_parquet(parquet_path),
                                  check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-9)
    meta = dict(created_at=now(), sample=False, rows=len(frame), columns=list(frame.columns),
                source_zip_sha256=digest(zip_path), csv_sha256=digest(csv_path),
                parquet_sha256=digest(parquet_path), verification='igualdad completa de valores, orden y nulos; rtol=1e-12, atol=1e-9')
    write_json(manifest_path, meta)
    return csv_path, parquet_path, meta


def run(full_month=False, repeats=5, root=ROOT):
    if repeats < 2:
        raise ValueError('Usar al menos dos repeticiones medidas')
    root = Path(root)
    sample = root / 'data/sample/flights_2025_01'
    datasets = [('sample_2025_01', sample.with_suffix('.csv'), sample.with_suffix('.parquet'))]
    full_meta = None
    if full_month:
        raw_zip = root / 'data/raw/bts/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1.zip'
        csv_path, parquet_path, full_meta = prepare_full_month(raw_zip, root / 'data/interim/benchmark/2025-01')
        datasets.append(('full_2025_01', csv_path, parquet_path))
    runs, summaries, inputs = [], [], []
    for name, csv_path, parquet_path in datasets:
        reference = None
        for path in (csv_path, parquet_path):
            inputs.append(dict(dataset=name, format=path.suffix[1:], sha256=digest(path), file_bytes=path.stat().st_size))
        # Alternar formatos reduce el sesgo de ejecutar siempre todas las lecturas CSV primero.
        for repeat in range(repeats + 1):
            paths = (csv_path, parquet_path) if repeat % 2 == 0 else (parquet_path, csv_path)
            for path in paths:
                process = subprocess.run([sys.executable, '-m', 'src.analysis.benchmark_scale', '--worker', str(path)],
                                         capture_output=True, text=True, encoding='utf-8', check=True, timeout=120)
                item = json.loads(process.stdout)
                if reference is None:
                    reference = item['result']
                if item['result'] != reference:
                    raise ValueError('Resultados de la operación no equivalentes')
                runs.append(dict(dataset=name, format=path.suffix[1:], repeat=repeat, warmup=repeat == 0,
                                 file_bytes=path.stat().st_size, **item['result'], seconds=item['seconds'],
                                 peak_process_bytes=item['peak_process_bytes'], dataframe_bytes=item['dataframe_bytes'], correct=True))
        for kind in ('csv', 'parquet'):
            measured = [x for x in runs if x['dataset'] == name and x['format'] == kind and not x['warmup']]
            summaries.append(dict(dataset=name, format=kind, rows=reference['rows'], file_bytes=measured[0]['file_bytes'],
                median_seconds=statistics.median(x['seconds'] for x in measured),
                min_seconds=min(x['seconds'] for x in measured), max_seconds=max(x['seconds'] for x in measured),
                median_peak_process_bytes=statistics.median(x['peak_process_bytes'] for x in measured), correct=True))
    folder = root / 'reports/tables'
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(runs).to_csv(folder / 'benchmark_scale_runs.csv', index=False)
    pd.DataFrame(summaries).to_csv(folder / 'benchmark_scale_summary.csv', index=False)
    write_json(folder / 'benchmark_scale_environment.json', dict(executed_at=now(), python=platform.python_version(),
        platform=platform.platform(), pandas=pd.__version__, pyarrow=pyarrow.__version__, repeats=repeats,
        warmup_per_format=1, process='proceso nuevo por lectura; imports fuera del tiempo, dentro del pico',
        memory='Máximo del proceso: PeakWorkingSetSize en Windows; ru_maxrss en Unix. No incremento neto ni memoria Spark.',
        operation='lectura de 21 campos de todos los vuelos del archivo + elegibles finitos + conteo >=15 + suma retrasos elegibles',
        cache='Caché de archivos del SO sin vaciar; procesos nuevos y formatos alternados',
        scope='Benchmark local de muestra y/o enero 2025 completo. No mide Databricks ni extrapola a dos años.',
        inputs=inputs, full_month_preparation=full_meta))
    print(pd.DataFrame(summaries).to_string(index=False))
    return summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-month', action='store_true')
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        print(json.dumps(measure(args.worker)))
    else:
        run(args.full_month, args.repeats)


if __name__ == '__main__':
    main()
