# Avance preparado para Jose Miguel Guevara con Codex

## Primer parcial — issue #2
Se implementaron reglas nuevas de HHMM de llegada programada y horarios reales observados, número de vuelo entero positivo y valores finitos en todos los campos numéricos observados. El reporte devuelve tasa nula cuando no hay elegibles. Se conserva el notebook original y los cancelados sin etiqueta, incluso cuando tienen retraso reportado.

La suite de esta rama comprende 27 casos de la base y 12 nuevos: **39 pruebas correctas**, incluida inyección de errores y conservación de casos válidos. Auditoría, procesamiento, validación entre tablas y estructura también pasaron. Evidencia pequeña en `reports/tables/jose_p1_evidence.json`; los datos masivos no forman parte de esta tarea.

Implementación, pruebas y documentación asistidas por Codex. La publicación debe verificarse como `GUEVARA21`. El PR solicita revisión de `Skraeder`; este archivo no acredita revisiones que aún no se han realizado.

## Segundo parcial
Silver (#5), históricos (#8) y validación entre las tres capas (#11) se trabajan después, sobre la base de Bronze revisada. El código del primer parcial no certifica una ejecución Spark de Silver. La validación completa depende también del Gold de Santiago.
