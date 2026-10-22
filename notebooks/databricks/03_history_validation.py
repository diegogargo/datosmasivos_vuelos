# Databricks notebook source
import sys,json
from pathlib import Path

for name, default in [('project_root', ''), ('output_root', ''), ('catalog', 'workspace'),
                      ('start', '2025-01'), ('end', '2025-01'), ('availability_mode', 'disabled')]:
    dbutils.widgets.text(name, default)
root = Path(dbutils.widgets.get('project_root'))
if not root.is_absolute() or not (root / 'src/processing/historical_features.py').is_file():
    raise ValueError('Falta el código de históricos en project_root')
sys.path.insert(0, str(root))
from src.ingestion.bronze import identifier
from src.processing.historical_features import run_historical_features
from src.validation.validate_layers import run_layer_validation

catalog = dbutils.widgets.get('catalog')
identifier(catalog)
start, end = dbutils.widgets.get('start'), dbutils.widgets.get('end')
output_root = dbutils.widgets.get('output_root')
history = run_historical_features(spark, catalog + '.silver.vuelos_clean',
    catalog + '.silver.vuelos_history', start, end, output_root,
    availability_mode=dbutils.widgets.get('availability_mode'))
validation = run_layer_validation(spark, catalog + '.bronze.vuelos_raw',
    catalog + '.silver.vuelos_clean', catalog + '.silver.vuelos_quarantine',
    catalog + '.silver.vuelos_history', catalog + '.gold.flight_features',
    catalog + '.gold.delay_monthly', catalog + '.gold.delay_distribution',
    start, end, output_root, require_gold=False)
if not validation['passed']:
    raise ValueError('Falla validación de capas disponibles; revisar reports/validation/latest.json')
result = dict(history=history, validation=validation)
print('Históricos completos. Integración total:', validation['complete'])
dbutils.notebook.exit(json.dumps(result, ensure_ascii=False, default=str))
