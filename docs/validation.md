# Validaciones y pruebas

## Evidencia local comprobada
La muestra tiene 5,000 filas, 21 columnas, 164 cancelados, 4,836 etiquetas observadas y 896 retrasos >=15 min. Tres cancelados conservan `DepDelay` reportado, pero su etiqueta permanece nula.

`python -m src.validation.audit_sample` verifica columnas, fechas, claves requeridas, duplicados por clave, indicadores binarios, HHMM de salida, distancia positiva, formato de origen/destino, cancelaciones sin etiqueta, resultados operados y SHA256 de la muestra cuando existe su manifiesto. Escribe `reports/tables/sample_validation.json` y termina con error si falla.

`python -m src.processing.build_dataset` escribe interim y processed de muestra. Con las nuevas reglas, `python -m src.validation.validate_dataset` verifica **39 comprobaciones**, incluidas volumen esperado, tipos procesados, corte de tres horas, etiqueta/eligibilidad, particiones y equivalencia del agregado mensual. Escribe `reports/tables/processed_validation.json`. Los nulos permitidos se reportan; no se rellenan todas las columnas indiscriminadamente.

## Reglas nuevas P1-02 de Jose Miguel, con asistencia de Codex
La auditoría también verifica HHMM de llegada programada, horarios reales cuando están observados, números de vuelo enteros positivos y valores finitos en todas las columnas numéricas observadas. Los valores numéricos mal formados no se confunden con nulos permitidos. El contrato por campo está en `data_dictionary.md`.

Cuando no hay vuelos elegibles, el reporte devuelve `delay_rate=null`; no divide entre cero ni interpreta cancelados como puntuales. Las pruebas inyectan errores de llegada, fracciones y números de vuelo no positivos, infinitos y texto en campos numéricos, además de conservar `0000`, `2400`, negativos válidos y nulos permitidos.

## Pruebas automáticas
La base tenía **27 casos**. P1-02 añade **12 casos** de calidad a esa base; el resultado de la suite y la ejecución nueva se registran en `reports/tables/jose_p1_evidence.json`. Comprueban umbral 14/15, adelantos, cancelados con retraso, resultados faltantes/no finitos, HHMM inválidos y 2400 al día siguiente, deduplicación exacta, rechazo de claves contradictorias, lectura/escritura, agregado alterado, corte incorrecto, reintentos, caché, alteración SHA256, HTML en lugar de ZIP y esquema incompleto.

CI ejecuta pruebas, auditoría, construcción, validación y verificación de estructura. El estado de GitHub Actions se debe consultar en la ejecución real; aprobar localmente no garantiza una ejecución remota.

## Lo que no certifica esta validación
Los campos temporales actuales son locales sin zona. Comprobar la resta de tres horas no demuestra conversión UTC, disponibilidad de publicaciones, ausencia de fuga en ventanas históricas ni acceso a pronósticos pasados. El módulo tampoco certifica tablas Delta o toda la población de 24 meses.

## Pendientes sobre volumen completo
Tipos y reglas en Spark, HHMM de llegada, zonas/DST, disponibilidad de fuentes, conteos por mes y entre capas Bronze/Silver/Gold, esquema histórico, duplicados fuera de la muestra y cuarentena. Los issues P2-02, P2-05 y P2-08 requieren pruebas con errores inyectados y evidencia del workspace real.
