# Históricos de 28 días y disponibilidad

Módulo de José Miguel Guevara, asistido por Codex. Firma pública:

```python
run_historical_features(spark, silver_table, target_table, start, end,
                        output_root, availability_mode='disabled')
```

Entrada `workspace.silver.vuelos_clean`; salida
`workspace.silver.vuelos_history`, una fila por `flight_id`, partición mensual,
linaje, cutoff y modo de disponibilidad. Las dos tasas son
`origin_hour_delay_rate_28d` y `airline_delay_rate_28d`; sus denominadores se
guardan como `origin_hour_history_count_28d` y `airline_history_count_28d`.

## Modos

- `disabled` es el valor predeterminado: tasas y conteos nulos. No implica cero
  retrasos y no acredita un predictor operativo.
- `retrospective_ideal` calcula las tasas exploratorias suponiendo que cada
  resultado aparece de inmediato al salir de puerta. **No** acredita
  disponibilidad histórica real. Debe seleccionarse explícitamente.
- `publication_aware` falla antes de escribir: falta `available_at` real,
  procedencia y una política de disponibilidad validada. La descarga del archivo
  o la fecha del vuelo no sustituyen esa evidencia.

`history_operational_validity` permanece `false` en los dos modos admitidos.
No se usan WeatherDelay ni otros resultados del vuelo actual como predictores.

## Definición exacta del experimento ideal

El instante estimado de salida de puerta de cada antecedente es
`scheduled_utc + DepDelay minutos`. BTS registra retraso de salida de puerta;
no se presenta esta aproximación como hora de despegue. La ventana es
`[prediction_cutoff_utc - 28 días, prediction_cutoff_utc)`: incluye el extremo
inferior y excluye cualquier resultado exactamente al corte o después.

Se agrupa por ID BTS de origen + hora local programada, y por ID BTS de
aerolínea. Se excluyen cancelados, resultados no finitos y siempre el vuelo
actual, incluso si un adelanto superior a tres horas sitúa su resultado antes
del cutoff. No se rellena historia faltante.

Con al menos 30 antecedentes, la tasa es `(retrasados + 1)/(antecedentes + 2)`.
El prior Beta(1,1) es fijo y no se estima mirando etiquetas futuras; el mínimo
de 30 es una decisión de diseño, sin búsqueda en prueba. Debajo del mínimo la
tasa es nula, con conteo observado disponible. Hora de consulta normalizada a
UTC; comparaciones a resolución de segundo; entradas BTS a resolución de minuto.

La ejecución usa eventos y dos consultas de prefijo por vuelo: conteo/suma
acumulados hasta `cutoff-1s`, menos los acumulados hasta `cutoff-28d-1s`, y
exclusión del propio resultado cuando corresponda. Todos los eventos del mismo
segundo comparten prefijo. Así se conserva exactamente la ventana indicada sin
reevaluar todos sus antecedentes en cada fila. Se usan ventanas acumuladas
Spark, sin joins cuadráticos ni `collect` de vuelos. La decisión se apoya en la
[implementación oficial de ventanas de Spark 4.2](https://github.com/apache/spark/blob/v4.2.0/sql/core/src/main/scala/org/apache/spark/sql/execution/window/WindowFunctionFrame.scala),
que permite actualizaciones incrementales en ventanas con inicio no acotado.
Esta elección no sustituye una medición del rendimiento del volumen completo.
Solo se recuperan límites temporales, conteos por mes y metadatos. Lee una versión Delta fija de Silver y escribe el
rango con un único reemplazo Delta, conservando particiones exteriores. Se
comprueba unicidad y conciliación por mes.

## Límites y evidencia

Solo contribuyen vuelos aceptados en Silver. Enero de 2024 carece del contexto
de diciembre de 2023 y los rechazos de cuarentena quedan fuera. El origen de
zonas IANA es una dimensión actual, con la limitación histórica de Silver.
Dos años no certifican estabilidad futura ni disponibilidad operacional.

Las pruebas locales sobre Spark real cubren nulos en disabled; frontera de
28 días; exclusión del cutoff/futuro/propio vuelo; grupos independientes;
historia insuficiente; prior; modificación de resultados futuros que no altera
una consulta anterior; validación de modo/esquema y comparación de todos los
resultados de 100 registros con un cálculo independiente, incluidos eventos
con el mismo segundo. El resultado y número de pruebas comprobados se guardan
en `reports/tables/jose_history_evidence.json`. Los datos son sintéticos y no
sustituyen un reporte Databricks del volumen completo.

La ejecución remota guarda `output_root/reports/history/latest.json`; la CLI
copia `reports/tables/databricks_history_result.json` únicamente tras éxito.
