# Silver: vuelos aceptados y cuarentena

Implementación de José Miguel Guevara, asistida por Codex. Integra Bronze de
Diego; no modifica el notebook original ni presenta la base de Diego como nueva
aportación de José. Periodo definitivo: enero de 2024 a diciembre de 2025.

## Entrada y salidas

`run_silver(spark, bronze_table, silver_table, quarantine_table, start, end, output_root)`.
Entrada `workspace.bronze.vuelos_raw`, campos BTS originales como cadenas y ocho
metadatos de procedencia. Salidas `workspace.silver.vuelos_clean` y
`workspace.silver.vuelos_quarantine`, Delta particionado por `_source_period`.
Se conserva el identificador BTS de ambos aeropuertos y de la aerolínea, además
del hash del registro original, los hashes ZIP/CSV y los metadatos de Bronze.

Tipos analíticos: fecha, identificadores y número de vuelo enteros de 64 bits,
horarios programados y banderas enteros, medidas y retrasos double. Se validan
valores observados finitos, enteros positivos, HHMM, banderas, distancia,
fecha del archivo mensual y códigos de aeropuerto. No se imputan causas de
retraso. `DepDelay < 0` es válido. Los cancelados se conservan con `delay15=NULL`.
Solo `Cancelled=0` con resultado finito es elegible; `delay15 = DepDelay >= 15`.

BTS serializa banderas como `0.00` y `1.00`: se convierten primero a número
y después a entero. Los IDs admiten representación decimal entera sin aceptar
fracciones. Se comprueban nulos después de convertir, además de las reglas
sobre el texto original. Cada mes registra cancelados, elegibles, etiquetados,
retrasados y violaciones en `quality_summary`; `quality_summary_passed=true`
exige que todos los meses pasen. La referencia independiente del CSV completo
de enero exige 16,312 cancelados, 523,435 elegibles y 95,432 retrasados.

## Duplicados y cuarentena

Los duplicados exactos se determinan sobre **todos** los campos originales,
excluyendo únicamente metadatos de ingestión; se registra el número eliminado.
Si dos registros distintos comparten la clave natural del contrato, ambos van
a cuarentena. No se elige arbitrariamente uno.

Cada rechazado mantiene `_raw_payload`, `_record_sha256` y `_quality_errors`.
Una fila puede tener varios motivos; su suma no representa filas distintas.
Para cada mes debe cumplirse:

`Bronze = Silver + cuarentena + exclusiones por duplicado exacto`.

## Horarios y dimensión

`2400` pasa a las 00:00 del día siguiente. `scheduled_local` es timestamp sin
zona; `scheduled_utc` se obtiene por aeropuerto; el cutoff es exactamente tres
horas antes. Se rechazan horas locales inexistentes o ambiguas por DST. La
comprobación distribuida de ambigüedad usa desplazamientos de una hora y se
limita a Estados Unidos y sus territorios en 2024–2025. Las pruebas puras usan
también roundtrip de ambos folds de ZoneInfo.

La dimensión comunitaria airportsdata está fijada a un commit y conserva fuente,
licencia MIT, hashes y transformación en `data/reference/`. Los IATA ambiguos se
excluyen y los desconocidos van a cuarentena. Esta dimensión actual **no**
certifica todos los cambios históricos IATA de 2024–2025; mantener IDs BTS no
elimina esa limitación. El CSV derivado usa UTF-8 y LF con hash estable en Git.

## Escritura y prueba

Solo se escriben tablas con propiedades `vuelos.layer` y `vuelos.source`
esperadas; un esquema incompatible conserva la tabla y provoca error. Una
tabla de staging propia evita recalcular el plan; cada mes se sustituye mediante
`replaceWhere`, conservando otros meses. Staging se elimina solo al completar
todo el rango y verificar la conciliación. Un fallo deja informe `complete=false`
y staging para diagnóstico. Spark Connect/serverless: sin RDD ni `sparkContext`.

El informe remoto se guarda en `output_root/reports/silver/latest.json`.
La CLI guarda un resultado público solo tras éxito; errores y URL/identidad
del workspace se mantienen bajo `data/raw/`, excluido de Git.

Se probaron nueve casos locales en Spark real: horarios y DST, dimensión
alterada/duplicada, tipos, cancelados, negativos, duplicación exacta y claves
contradictorias. El piloto Databricks inicial de enero de 2025 concilió volúmenes:
539,747 filas Bronze, 539,747 aceptadas, cero en cuarentena y cero exclusiones
por duplicado exacto. Spark 4.2.0, Bronze versión 25, Silver y cuarentena versión
1; staging eliminado. Evidencia en
`reports/tables/databricks_silver_pilot.json`. Ese piloto no comprobaba los
nulos generados por la conversión de banderas; no certifica su calidad tipificada.

La carga inicial completa 2024–2025 también concilió volúmenes; evidencia en
`reports/tables/databricks_silver_result.json`. Conciliación: 14,080,680 filas
Bronze = 14,080,669 aceptadas + 11 en cuarentena + 0 duplicados exactos excluidos.
Un número de vuelo no cumple entero positivo (agosto 2024); diez horas locales
son ambiguas por DST (seis en noviembre 2024 y cuatro en noviembre 2025).
Sus datos originales permanecen en Bronze y en el payload de cuarentena.
El reporte de aquella ejecución conserva versión de origen 25 y runtime Spark
4.2.0. Después se detectó el defecto de conversión de banderas y se regeneró el
código con controles de tipos y etiquetas. La ejecución corregida se acredita
solo con `quality_summary_passed=true` y `january_reference_passed=true` en el
reporte actual; un reporte anterior que solo cuadre volúmenes no basta.

Enero de 2025 se volvió a escribir dentro del rango completo: conserva 539,747
aceptados y cero rechazos; su versión Delta pasa de 1 a 14 sin duplicar filas.
El monitor perdió conexión, pero se recuperó el resultado del mismo job, sin
repetir la carga. Se declara la pérdida de hashes locales de transferencia en
`recovery`; los conteos, versiones y hashes de la dimensión proceden del job.
Los hashes del código en la evidencia local describen los archivos Git, sin
presentarse como hashes de transferencia recuperados.

La implementación no
demuestra disponibilidad en vivo de los resultados BTS a tres horas.
