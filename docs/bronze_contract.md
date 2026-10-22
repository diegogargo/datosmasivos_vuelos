# Contrato de entrada Bronze para Silver

Fuente: ZIP mensual completo de BTS Reporting Carrier. Alcance: 2024–2025, 24 meses; enero 2025 es el piloto. Una fila continúa siendo un vuelo reportado. No se muestrea, filtra, imputa ni deduplica en Bronze.

Los campos originales se leen con esquema explícito de cadenas para conservar su representación antes de tipificarlos en Silver. Enero 2025 tiene 110 campos originales, incluidos los que no se usaron en el EDA de 21 variables. Un encabezado vacío conserva su posición con el nombre `_bts_column_INDICE`; el reporte conserva el mapeo original. CSV vacío se interpreta como nulo en la lectura Spark; el ZIP y CSV exactos permanecen conservados para auditoría.

Metadatos añadidos: `_source_period`, `_source_zip_sha256`, `_source_csv_sha256`, `_source_url`, `_source_file`, `_source_downloaded_at`, `_run_id` (cadenas) y `_ingested_at` (timestamp UTC). La partición es `_source_period`. `_source_downloaded_at` indica adquisición del archivo, no disponibilidad operacional de cada resultado de vuelo a tres horas.

El programa coteja SHA256, tamaño, esquema y número de filas. Delta se escribe por mes con `replaceWhere`. La tabla debe tener las propiedades `vuelos.layer=bronze` y `vuelos.source=bts_reporting_carrier`; se rechaza una tabla ajena o un esquema incompatible. No se aplica migración automática de columnas.

Salida propuesta: `CATALOGO.bronze.vuelos_raw`. El catálogo real se selecciona en la cuenta. El reporte de cada ejecución queda en el Volume y el ejecutor guarda una copia pequeña para revisión.

Jose Miguel transformará tipos, reglas de nulos, duplicados, cuarentena, zona horaria y elegibilidad en Silver. Santiago construirá Gold y agregados sobre esas salidas. Sus implementaciones y ejecuciones son necesarias para afirmar integración completa. Ninguna carpeta Parquet local se presenta como Delta ni como ejecución de Spark.
