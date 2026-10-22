# Databricks notebook source
"""Silver de Jose Miguel, con asistencia de Codex; ejecución integrada de Diego."""
dbutils.widgets.text('project_root','')
dbutils.widgets.text('output_root','/Volumes/workspace/bronze/vuelos_raw/vuelos')
dbutils.widgets.text('catalog','workspace')
dbutils.widgets.text('start','2025-01')
dbutils.widgets.text('end','2025-01')

# COMMAND ----------
from pathlib import Path
import json,sys
project=Path(dbutils.widgets.get('project_root'))
if not project.is_absolute() or not (project/'src/processing/silver.py').is_file():
    raise ValueError('El ejecutor debe indicar la carpeta absoluta real del proyecto')
sys.path.insert(0,str(project))
from src.processing.silver import run_silver
from src.ingestion.bronze import identifier
catalog=dbutils.widgets.get('catalog');identifier(catalog)
report=run_silver(spark,bronze_table=catalog+'.bronze.vuelos_raw',
    silver_table=catalog+'.silver.vuelos_clean',quarantine_table=catalog+'.silver.vuelos_quarantine',
    start=dbutils.widgets.get('start'),end=dbutils.widgets.get('end'),
    output_root=dbutils.widgets.get('output_root'))
print(json.dumps(dict(complete=report['complete'],rows=report['rows'],months=len(report['months'])),indent=2))
dbutils.notebook.exit(json.dumps(report,ensure_ascii=False))
