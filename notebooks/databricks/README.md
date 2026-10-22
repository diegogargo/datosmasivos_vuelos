# Notebooks Databricks

`00_setup.py` crea esquemas y Volume dentro del catálogo elegido. `01_bronze.py` verifica los originales, reconstruye el CSV desde su ZIP, carga Bronze Delta y concilia los conteos. Son notebooks en formato fuente de Databricks.

Desde PowerShell se pueden cargar y ejecutar con `python scripts/run_databricks.py --profile vuelos --execute`. Por defecto se limita a enero 2025. Consultar `docs/databricks_setup.md` y `docs/bronze_contract.md` antes de ampliar a los 24 meses de 2024–2025.

Las pruebas locales verifican contratos, transferencia y errores; no prueban una ejecución Spark. La evidencia real se genera cuando el job termina correctamente. Silver y Gold se añadirán mediante las tareas de sus responsables.
