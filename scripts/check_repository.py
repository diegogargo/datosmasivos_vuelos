"""Verifica estructura, sintaxis y portabilidad de notebooks actuales."""
from pathlib import Path
import ast,json
import nbformat
root=Path(__file__).resolve().parents[1]
required=['README.md','CONTRIBUTING.md','docs/project_scope.md','docs/data_dictionary.md',
'docs/architecture.md','docs/validation.md','docs/decisions.md','docs/team_workplan.md',
'data/sample/flights_2025_01.csv','notebooks/01_exploration.ipynb','tests/test_processing.py']
for name in required:
    if not (root/name).is_file():raise AssertionError(f'Falta {name}')
for folder in ['src','scripts','tests']:
    for p in (root/folder).rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
for p in (root/'config').glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
for p in (root/'notebooks').glob('*.ipynb'):
    nb=nbformat.read(p,as_version=4);nbformat.validate(nb)
    for cell in nb.cells:
        if cell.cell_type=='code':
            assert not any(o.output_type=='error' for o in cell.get('outputs',[])),p
            assert '/content/' not in cell.source and 'C:\\' not in cell.source,p
print('Estructura y sintaxis correctas')
