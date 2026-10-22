# Validaciones y pruebas

## Evidencia local comprobada
La muestra tiene 5,000 filas, 21 columnas, 164 cancelados, 4,836 etiquetas observadas y 896 retrasos >=15 min. Tres cancelados conservan `DepDelay` reportado, pero su etiqueta permanece nula.

`python -m src.validation.audit_sample` verifica columnas, fechas, claves requeridas, duplicados por clave, indicadores binarios, HHMM de salida, distancia positiva, formato de origen/destino, cancelaciones sin etiqueta, resultados operados y SHA256 de la muestra cuando existe su manifiesto. Escribe `reports/tables/sample_validation.json` y termina con error si falla.

`python -m src.processing.build_dataset` escribe interim y processed de muestra. `python -m src.validation.validate_dataset` verifica **19 comprobaciones**, incluidas volumen esperado, tipos procesados, corte de tres horas, etiqueta/eligibilidad, particiones y equivalencia del agregado mensual. Escribe `reports/tables/processed_validation.json`. Los nulos permitidos se reportan; no se rellenan todas las columnas indiscriminadamente.

## Pruebas automáticas
`python -m pytest -q`: **27 casos aprobados** en la verificación local inicial. Comprueban umbral 14/15, adelantos, cancelados con retraso, resultados faltantes/no finitos, HHMM inválidos y 2400 al día siguiente, deduplicación exacta, rechazo de claves contradictorias, lectura/escritura, agregado alterado, corte incorrecto, reintentos, caché, alteración SHA256, HTML en lugar de ZIP y esquema incompleto.

CI ejecuta pruebas, auditoría, construcción, validación y verificación de estructura. El estado de GitHub Actions se debe consultar en la ejecución real; aprobar localmente no garantiza una ejecución remota.

## Lo que no certifica esta validación
Los campos temporales actuales son locales sin zona. Comprobar la resta de tres horas no demuestra conversión UTC, disponibilidad de publicaciones, ausencia de fuga en ventanas históricas ni acceso a pronósticos pasados. El módulo tampoco certifica tablas Delta o toda la población de 24 meses.

## Pendientes sobre volumen completo
Tipos y reglas en Spark, HHMM de llegada, zonas/DST, disponibilidad de fuentes, conteos por mes y entre capas Bronze/Silver/Gold, esquema histórico, duplicados fuera de la muestra y cuarentena. Los issues P2-02, P2-05 y P2-08 requieren pruebas con errores inyectados y evidencia del workspace real.

## Silver implementado y piloto real

Las secciones anteriores describen la base inicial de muestra. El módulo
`src/processing/silver.py` aplica tipos, nulos, claves, HHMM, UTC/DST y cuarentena
con conciliación mensual; contrato y límites en [silver_contract.md](silver_contract.md).
Nueve pruebas locales reales de Spark pasaron. El piloto Databricks de enero
2025 terminó con 539,747 aceptados, cero en cuarentena y cero exclusiones;
evidencia en `reports/tables/databricks_silver_pilot.json`. La carga completa
2024–2025 tiene su propia evidencia en `reports/tables/databricks_silver_result.json`:
14,080,680 entradas, 14,080,669 aceptadas y 11 en cuarentena, con cero exclusiones
por duplicado exacto y 24 meses conciliados. Enero se reescribió con el mismo
conteo sin duplicación. Se detectó que convertir directamente texto `0.00/1.00`
a entero generaba nulos; esa conciliación inicial no certificaba tipos/etiquetas.
La corrección usa conversión numérica previa y controles posteriores por mes.
Solo se acredita el resultado corregido con `quality_summary_passed=true` y
coincidencia con el CSV completo de enero (16,312 cancelados, 523,435 elegibles y
95,432 retrasados). La suite conjunta de las tres tareas locales pasó 105 casos;
su evidencia se incluye en la tarea de validación que contiene los tres módulos.
Esto no demuestra disponibilidad operacional a tres horas.

## Validación entre capas

`src/validation/validate_layers.py` comprueba tipos, claves, nulos, rangos,
etiquetas, cutoff, hash del registro original, cobertura por anti-joins y
conciliación de volúmenes; compara históricos y salidas Gold cuando existan.
Seis pruebas reales de Spark con datos sintéticos detectaron errores inyectados
en etiquetas, cutoff, linaje, tasas, grupos, distribución y disponibilidad
declarada. No son una ejecución Gold real. Las reglas están en
[gold_validation_contract.md](gold_validation_contract.md).

Si falta una tabla, queda en `pending` y `complete=false`. `require_gold=False`
solo permite aprobar las capas presentes, conservando la integración pendiente;
no certifica todo el flujo. La selección de estacionalidad con entrenamiento
requiere además pruebas del módulo Gold. Implementación y documentación de
José Miguel asistidas por Codex; revisión independiente pendiente.
