"""Recorrido local reproducible y estado explícito de integración del equipo."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from src.ingestion.acquire_range import months
from src.utils.common import now, read_json, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-acquisition', action='store_true', help='Verificar además hashes de todos los ZIP/CSV locales')
    parser.add_argument('--require-team', action='store_true', help='Fallar si faltan evidencias completas Bronze/Silver/Gold')
    args = parser.parse_args(argv)
    modules = ['src.ingestion.validate_provenance', 'src.validation.audit_sample',
               'src.processing.build_dataset', 'src.validation.validate_dataset']
    commands = [[sys.executable, '-m', module] for module in modules]
    commands.append([sys.executable, 'scripts/check_repository.py'])
    if args.full_acquisition:
        commands.append([sys.executable, '-m', 'src.validation.validate_acquisition', '--verify-files'])
    checks = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        name = ' '.join(command[1:])
        checks.append(dict(command=name, passed=result.returncode == 0))
        print(name + ': ' + ('correcto' if result.returncode == 0 else 'FALLO'), flush=True)
        if result.returncode:
            print(result.stderr[-1200:] or result.stdout[-1200:])
    config = yaml.safe_load((ROOT / 'config/project.yaml').read_text(encoding='utf-8'))
    requested = months(**config['period'])
    layers = {}
    for layer in ('bronze', 'silver', 'gold'):
        path = ROOT / f'reports/tables/databricks_{layer}_result.json'
        evidence = read_json(path) if path.is_file() else {}
        observed = [row.get('period') for row in evidence.get('months', [])]
        layers[layer] = dict(report_exists=path.is_file(), complete_report=evidence.get('complete') is True,
                             covers_project_period=observed == requested)
    local_passed = all(item['passed'] for item in checks)
    team_complete = local_passed and all(item['complete_report'] and item['covers_project_period'] for item in layers.values())
    report = dict(executed_at=now(), period=config['period'], local_components_passed=local_passed,
                  raw_hashes_requested=args.full_acquisition, checks=checks, databricks_evidence=layers,
                  team_integration_complete=team_complete,
                  limitation='La presencia de código o un piloto de un mes no demuestra integración de los 24 meses. Las reviews se verifican en GitHub.')
    write_json(ROOT / 'reports/tables/delivery_validation.json', report)
    print('Componentes locales correctos.' if local_passed else 'Hay fallos locales.')
    print('Evidencia de integración completa.' if team_complete else 'Integración del equipo pendiente de evidencia completa Bronze/Silver/Gold.')
    return 0 if local_passed and (team_complete or not args.require_team) else 1


if __name__ == '__main__':
    raise SystemExit(main())
