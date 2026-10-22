# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze de vuelos completos
# MAGIC Requiere el ZIP, CSV y manifiesto de la adquisición local en el Volume.
# MAGIC Empezar por 2025-01. Ampliar a 2022-01 / 2025-12 tras verificar la primera ejecución.

# COMMAND ----------
from pathlib import Path
import sys
for candidate in [Path.cwd(), *Path.cwd().parents]:
    if (candidate / 'src/ingestion/bronze.py').is_file():
        sys.path.insert(0, str(candidate))
        break

dbutils.widgets.text('catalog', 'workspace')
dbutils.widgets.text('volume', 'vuelos_raw')
dbutils.widgets.text('start', '2025-01')
dbutils.widgets.text('end', '2025-01')

# COMMAND ----------
from src.ingestion.bronze import run_bronze
import json

catalog = dbutils.widgets.get('catalog')
volume = dbutils.widgets.get('volume')
report = run_bronze(spark, f'/Volumes/{catalog}/bronze/{volume}/vuelos',
                    f'{catalog}.bronze.vuelos_raw',
                    dbutils.widgets.get('start'), dbutils.widgets.get('end'))
print(json.dumps(report, indent=2, ensure_ascii=False))

# COMMAND ----------
from src.ingestion.bronze import table_identifier
spark.sql(f'SELECT _source_period, COUNT(*) AS vuelos FROM '
          f'{table_identifier(catalog + ".bronze.vuelos_raw")} '
          'GROUP BY _source_period ORDER BY _source_period').show(60, truncate=False)

# COMMAND ----------
dbutils.notebook.exit(json.dumps(report))
