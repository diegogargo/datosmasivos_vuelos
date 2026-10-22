# Databricks notebook source
import sys,json
from pathlib import Path
for name, default in [('project_root', ''), ('output_root', ''), ('catalog', 'workspace'),
                      ('start', '2025-01'), ('end', '2025-01'), ('availability_mode', 'disabled')]:
    dbutils.widgets.text(name, default)
root=Path(dbutils.widgets.get('project_root'))
if not root.is_absolute() or not (root/'src/processing/historical_features.py').is_file():
    raise ValueError('Falta historical_features.py en project_root')
sys.path.insert(0,str(root))
from src.ingestion.bronze import identifier
from src.processing.historical_features import run_historical_features
catalog=dbutils.widgets.get('catalog');identifier(catalog)
report=run_historical_features(spark, catalog+'.silver.vuelos_clean',
    catalog+'.silver.vuelos_history', dbutils.widgets.get('start'), dbutils.widgets.get('end'),
    dbutils.widgets.get('output_root'), availability_mode=dbutils.widgets.get('availability_mode'))
print('Históricos:',report['rows'],'filas. Validez operacional:',report['operational_validity'])
dbutils.notebook.exit(json.dumps(report,ensure_ascii=False,default=str))
