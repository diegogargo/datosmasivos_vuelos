# Databricks notebook source
# MAGIC %md
# MAGIC # Preparación del proyecto de vuelos
# MAGIC Ejecutar desde la carpeta Git del repositorio. Los parámetros son nombres
# MAGIC propuestos; seleccionar el catálogo disponible de la cuenta antes de ejecutar.

# COMMAND ----------
dbutils.widgets.text('catalog', 'workspace')
dbutils.widgets.text('volume', 'vuelos_raw')
catalog = dbutils.widgets.get('catalog')
volume = dbutils.widgets.get('volume')

# COMMAND ----------
from src.ingestion.bronze import identifier
spark.sql('SHOW CATALOGS').show(truncate=False)
for schema in ['bronze', 'silver', 'gold']:
    spark.sql(f'CREATE SCHEMA IF NOT EXISTS {identifier(catalog)}.{identifier(schema)}')
spark.sql(f'CREATE VOLUME IF NOT EXISTS {identifier(catalog)}.`bronze`.{identifier(volume)}')
print(f'Raíz del proyecto: /Volumes/{catalog}/bronze/{volume}/vuelos')

# COMMAND ----------
spark.sql(f'SHOW SCHEMAS IN {identifier(catalog)}').show(truncate=False)
spark.sql(f'SHOW VOLUMES IN {identifier(catalog)}.`bronze`').show(truncate=False)
print('Spark:', spark.version)
