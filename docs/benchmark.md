# Benchmark de muestra y mes completo

## Método nuevo de P2-07
`python -m src.analysis.benchmark_scale --full-month` compara los mismos 21 campos de enero 2025: la muestra pública de 5,000 vuelos y los 539,747 vuelos completos del ZIP original. La preparación comprueba igualdad de valores, orden y nulos entre CSV y Parquet (rtol=1e-12, atol=1e-9). No se muestrea el mes completo ni se cambia su población.

La operación medida lee el archivo y obtiene totales, cancelados, elegibles con retraso finito, retrasos >=15 y suma de retrasos elegibles. Cada lectura usa un proceso nuevo; una repetición de calentamiento y cinco medidas por formato, alternados. Los imports del programa quedan fuera del tiempo y dentro del pico del proceso. La caché del sistema operativo no se vacía. Las mediciones se hicieron mientras se descargaban otros meses; una comparación aislada puede variar.

| Conjunto | Formato | Filas | Bytes del archivo | Mediana segundos | Mediana pico proceso MiB |
|---|---|---:|---:|---:|---:|
| sample_2025_01 | csv | 5,000 | 477,547 | 0.030872 | 88.70 |
| sample_2025_01 | parquet | 5,000 | 162,501 | 0.078905 | 96.97 |
| full_2025_01 | csv | 539,747 | 51,538,953 | 1.301639 | 211.08 |
| full_2025_01 | parquet | 539,747 | 7,777,803 | 0.157881 | 320.31 |

Todos los resultados de la operación coincidieron entre formatos y repeticiones. En el mes completo Parquet ocupó menos disco y tardó menos en esta ejecución. En la muestra CSV fue más rápido. El pico del proceso fue mayor con Parquet en ambos tamaños; no se afirma que Parquet reduzca siempre RAM. Esta comparación incluye motores y asignaciones internas, sin aislar su efecto individual.

Memoria: `PeakWorkingSetSize` en Windows o `ru_maxrss` en Unix, máximo del proceso desde su inicio, incluidos Python, bibliotecas y operación. Se registra también el tamaño profundo del DataFrame. Son medidas distintas; ninguna equivale a memoria de ejecutores Spark.

Evidencias: `reports/tables/benchmark_scale_runs.csv`, `benchmark_scale_summary.csv` y `benchmark_scale_environment.json`, con versiones, hashes de entradas, repeticiones y límites. El benchmark anterior de la base se conserva en `benchmark_runs.csv`, `benchmark_summary.csv` y `benchmark_environment.json`; usaba el mismo proceso y medía memoria del DataFrame. Sus tiempos no son directamente comparables con el método nuevo.

Este benchmark demuestra el comportamiento local de dos tamaños reales. No mide Databricks ni permite extrapolar el tiempo a los 24 meses. La ejecución integrada de Bronze, Silver y Gold sigue pendiente de sus respectivos módulos y reportes reales.
