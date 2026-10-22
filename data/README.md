# Datos del proyecto

Git incluye únicamente `sample/`: 5,000 vuelos BTS de enero de 2025 en CSV y Parquet, más su procedencia. Ambos formatos contienen las mismas 21 columnas del notebook original.

`raw/` conserva localmente ZIP completos sin modificar y manifiestos de descarga. `interim/` y `processed/` son productos regenerables excluidos de Git. Los comandos de adquisición y construcción están en el README principal.

El Parquet histórico de 120,000 filas mencionado en el notebook original no fue entregado. Los resultados extraídos de ese notebook son evidencia guardada, no una nueva descarga. No subir los ZIP de 24 meses ni tablas completas al repositorio.
