"""Carga Bronze desde PowerShell con la sesión segura de la CLI oficial.

Sin --execute muestra el plan. No lee tokens ni cambia cómo se almacenan.
Todos los cambios remotos quedan en la carpeta y Volume de este proyecto.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ingestion.acquire_range import extract_csv, months
from src.ingestion.bronze import identifier
from src.utils.common import digest, now, read_json, write_json


class Client:
    def __init__(self, cli, profile):
        self.cli, self.profile = cli, profile

    def call(self, *args, payload=None):
        command = [self.cli, *args, '--profile', self.profile, '--output', 'json']
        env = dict(os.environ)
        # Una variable dejada por un intento anterior no debe ocultar el perfil válido.
        if env.get('DATABRICKS_CONFIG_FILE') and not Path(env['DATABRICKS_CONFIG_FILE']).is_file():
            env.pop('DATABRICKS_CONFIG_FILE')
        with tempfile.TemporaryDirectory(prefix='vuelos_cli_') as folder:
            if payload is not None:
                path = Path(folder) / 'request.json'
                path.write_text(json.dumps(payload), encoding='utf-8')
                command += ['--json', '@' + str(path)]
            result = subprocess.run(command, env=env, capture_output=True, text=True, encoding='utf-8', timeout=1800)
        if result.returncode:
            raise RuntimeError(result.stderr[-2000:])
        return json.loads(result.stdout) if result.stdout.strip() else {}


def prepare_manifest(start, end, root=ROOT):
    root = Path(root)
    source = read_json(root / 'data/raw/manifest.json')
    selected = {}
    for period in months(start, end):
        if period not in source['files']:
            raise ValueError(f'Primero adquirir el mes completo {period}')
        item = dict(source['files'][period])
        relative = Path(item['path'])
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('Ruta ZIP fuera del repositorio o inexistente')
        if digest(path) != item['sha256']:
            raise ValueError(f'ZIP alterado: {period}')
        if not item.get('csv_sha256'):
            stage = root / 'data/interim/databricks_transfer'
            item = extract_csv(path, item, stage)
        item['status'] = 'complete'
        selected[period] = item
    result = dict(files=selected, updated_at=now(), selection=dict(start=start, end=end))
    path = root / 'data/interim/databricks_transfer/manifest.json'
    write_json(path, result)
    return path, result


def upload_code(client, base):
    files = sorted((ROOT / 'src').rglob('*.py')) + [ROOT / 'config/project.yaml']
    files += [ROOT / 'notebooks/databricks/00_setup.py', ROOT / 'notebooks/databricks/01_bronze.py']
    folders = {base}
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        parent = str(Path(relative).parent).replace('\\', '/')
        folders.add(base + '/' + parent)
    for folder in sorted(folders, key=lambda value: value.count('/')):
        client.call('workspace', 'mkdirs', folder)
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        is_notebook = relative.startswith('notebooks/')
        destination = base + '/' + (relative.removesuffix('.py') if is_notebook else relative)
        args = ['workspace', 'import', destination, '--file', str(path), '--overwrite',
                '--format', 'SOURCE' if is_notebook else 'AUTO']
        if is_notebook:
            args += ['--language', 'PYTHON']
        client.call(*args)
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in files}


def submit_and_wait(client, notebook, parameters, name):
    submitted = client.call('jobs', 'submit', '--no-wait', payload=dict(run_name=name,
        tasks=[dict(task_key='run', notebook_task=dict(notebook_path=notebook, source='WORKSPACE',
                    base_parameters=parameters), timeout_seconds=3600)],
        performance_target='STANDARD'))
    run_id = submitted['run_id']
    deadline = time.monotonic() + 4000
    previous = None
    while time.monotonic() < deadline:
        run = client.call('jobs', 'get-run', str(run_id))
        state = run.get('state', {})
        life = state.get('life_cycle_state')
        if life != previous:
            print(f'{name}: {life}', flush=True)
            previous = life
        if life in {'TERMINATED', 'SKIPPED', 'INTERNAL_ERROR'}:
            if state.get('result_state') != 'SUCCESS':
                raise RuntimeError(f'Ejecución {run_id}: {state}')
            task_id = run.get('tasks', [{}])[0].get('run_id', run_id)
            output = client.call('jobs', 'get-run-output', str(task_id))
            return run, output
        time.sleep(10)
    raise TimeoutError(f'La ejecución {run_id} sigue activa. Consultar en Jobs & Pipelines; no lanzar duplicados.')


def execute(args):
    identifier(args.catalog)
    identifier(args.volume)
    requested = months(args.start, args.end)
    cli = args.cli or shutil.which('databricks')
    if not cli:
        raise ValueError('Indicar --cli con la ruta de la CLI oficial instalada')
    manifest_path, manifest = prepare_manifest(args.start, args.end)
    client = Client(cli, args.profile)
    me = client.call('current-user', 'me')
    catalogs = client.call('catalogs', 'list')
    catalogs = catalogs if isinstance(catalogs, list) else catalogs.get('catalogs', [])
    available = [item['name'] for item in catalogs]
    if args.catalog not in available:
        raise ValueError(f'Catálogo {args.catalog} no disponible. Elegir --catalog entre {available}')
    username = me['userName']
    if '/' in username or '\\' in username or username in {'', '.', '..'}:
        raise ValueError('Nombre de usuario incompatible con la ruta del workspace')
    base = f'/Users/{username}/datosmasivos_vuelos_diego'
    code_hashes = upload_code(client, base)
    params = dict(catalog=args.catalog, volume=args.volume)
    print('Preparando esquemas y Volume del proyecto...', flush=True)
    setup = None
    if not args.resume:
        setup, _ = submit_and_wait(client, base + '/notebooks/databricks/00_setup', params, 'Vuelos Diego - preparación')
    volume_root = f'/Volumes/{args.catalog}/bronze/{args.volume}/vuelos'
    print(f'Transfiriendo {len(requested)} ZIP completos y su manifiesto...', flush=True)
    if not args.resume:
        client.call('fs', 'mkdirs', 'dbfs:' + volume_root + '/data/raw/bts')
        for period, item in manifest['files'].items():
            client.call('fs', 'cp', str(ROOT / item['path']), 'dbfs:' + volume_root + '/' + item['path'], '--overwrite')
            print(f'ZIP transferido: {period}', flush=True)
        client.call('fs', 'cp', str(manifest_path), 'dbfs:' + volume_root + '/data/raw/manifest.json', '--overwrite')
    print('Ejecutando Bronze Delta...', flush=True)
    run, output = submit_and_wait(client, base + '/notebooks/databricks/01_bronze',
        dict(params, start=args.start, end=args.end), 'Vuelos Diego - Bronze')
    result = json.loads(output.get('notebook_output', {}).get('result', '{}'))
    if not result.get('complete') or len(result.get('months', [])) != len(requested):
        raise ValueError('Bronze no devolvió evidencia completa de los meses solicitados')
    for item in result['months']:
        expected = manifest['files'][item['period']]['csv_rows']
        if item['source_rows'] != expected or item['bronze_rows'] != expected or item['csv_sha256'] != manifest['files'][item['period']]['csv_sha256']:
            raise ValueError('Conteos de adquisición y Bronze no conciliados')
    # Direcciones privadas y usuario quedan en raw, excluido de Git.
    write_json(ROOT / 'data/raw/databricks_runs_private.json', dict(setup=setup, bronze=run, volume_root=volume_root))
    result['local_code_sha256'] = code_hashes
    write_json(ROOT / 'reports/tables/databricks_bronze_result.json', result)
    print(f"BRONZE CORRECTO: {result['rows']:,} filas, {len(result['months'])} meses. Reporte guardado.", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', help='Ruta al ejecutable oficial databricks')
    parser.add_argument('--profile', default='vuelos')
    parser.add_argument('--catalog', default='workspace')
    parser.add_argument('--volume', default='vuelos_raw')
    parser.add_argument('--start', default='2025-01')
    parser.add_argument('--end', default='2025-01')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true', help='Solo después de preparar entorno y transferir esos mismos meses')
    parser.add_argument('--diagnose-run', type=int, help='Guardar detalles de una ejecución fallida sin modificar el workspace')
    args = parser.parse_args(argv)
    if args.diagnose_run:
        cli = args.cli or shutil.which('databricks')
        if not cli:
            raise ValueError('Indicar --cli')
        client = Client(cli, args.profile)
        run = client.call('jobs', 'get-run', str(args.diagnose_run))
        task_id = run.get('tasks', [{}])[0].get('run_id', args.diagnose_run)
        output = client.call('jobs', 'get-run-output', str(task_id))
        write_json(ROOT / 'data/raw/databricks_diagnostic_private.json', dict(run=run, output=output))
        print('Diagnóstico guardado para revisión local.')
        print(output.get('error', ''))
        print(output.get('error_trace', '')[-10000:])
        return
    periods = months(args.start, args.end)
    print(f'Plan Databricks: {len(periods)} meses, {args.start} a {args.end}; Bronze solamente.', flush=True)
    if args.execute:
        execute(args)
    else:
        print('Añadir --execute para transferir archivos y ejecutar usando el perfil autenticado.')


if __name__ == '__main__':
    main()
