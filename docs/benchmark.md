# Comparación de desempeño

## Operación y método
Lectura de los mismos 5,000 vuelos y 21 campos en CSV y Parquet, seguida de filtro de vuelos elegibles y conteo de retrasos >=15 min. Una lectura de calentamiento por formato, cinco repeticiones medidas y mediana de tiempo. La caché del sistema operativo no se vació. Resultados: 5,000 totales, 4,836 elegibles y 896 retrasados en ambos formatos.

| Formato | Filas | Bytes de archivo | Mediana (s) | Memoria DataFrame (bytes) | Resultado |
|---|---:|---:|---:|---:|---|
| CSV | 5,000 | 477547 | 0.022160 | 960507 | Equivalente |
| Parquet | 5,000 | 162501 | 0.007802 | 960507 | Equivalente |

La memoria es `DataFrame.memory_usage(deep=True)`, no pico RSS ni consumo total del proceso. Ambos DataFrames tienen el mismo contenido y tamaño lógico. Mediciones y versiones: [repeticiones](../reports/tables/benchmark_runs.csv), [resumen](../reports/tables/benchmark_summary.csv), [entorno](../reports/tables/benchmark_environment.json).

## Interpretación y límites
En esta ejecución Parquet ocupó menos espacio y se leyó más rápido. Su compresión/formato columnar son explicaciones compatibles con la medición; no se aisló su contribución individual. La muestra cabe en memoria y el overhead es importante. No demuestra una mejora de Spark ni permite extrapolar tiempos linealmente a 24 meses.

## Reproducción y siguiente escala
`python -m src.analysis.benchmark`. Ejecutar desde la raíz con las dependencias instaladas; cambiará las mediciones según equipo/carga/caché. No ejecutarlo a la vez que otro benchmark al comparar resultados. Para el segundo parcial medir además un mes completo y, en Databricks, operaciones equivalentes con igualdad de resultados, datos, versiones, tiempo y medida explícita de memoria. Issue P2-07.
