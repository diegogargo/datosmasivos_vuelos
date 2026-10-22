# Definición del alcance

## Contexto del problema
Los vuelos pueden salir adelantados o con retraso. Cancelaciones y desvíos son eventos distintos. Antes de interpretar diferencias entre aerolíneas, aeropuertos y horarios se necesitan datos trazables, reglas de calidad y denominadores comparables.

## Pregunta principal
¿Qué patrones operativos y temporales se relacionan con retrasos de salida de puerta >=15 minutos en vuelos reportados a BTS durante 2024–2025, y qué capacidad predictiva tienen con información disponible tres horas antes del horario programado?

## Preguntas secundarias
- ¿Cómo varían las tasas por mes, aerolínea, origen y hora local?
- ¿Qué nulos, duplicados y extremos afectan el análisis?
- ¿Se conservan los patrones al separar entrenamiento, validación y prueba por tiempo?
- ¿Qué fuentes tienen disponibilidad histórica verificable al corte de predicción?

## ¿Qué representa una fila?
Un segmento de vuelo programado reportado por una aerolínea a BTS en una fecha, con origen, destino y horario programado. La clave candidata combina fecha, aerolínea informante, número de vuelo, origen, destino y hora programada; se comprueba su unicidad. No representa un pasajero, boleto o itinerario completo.

## Unidad de análisis
La etiqueta es `DepDelay >=15` cuando `Cancelled ==0` y `DepDelay` está observado. Se conservan retrasos negativos. Cancelados permanecen en la capa limpia con etiqueta nula, incluso si reportan `DepDelay`.

## Alcance temporal
Pipeline: enero 2024–diciembre 2025, 24 meses completos de Reporting Carrier de BTS. El equipo eligió dos años. El EDA inicial mantiene su periodo 2024–2025 y 5,000 filas por mes; no representa automáticamente el histórico ampliado. La muestra reproducible incluida tiene 5,000 filas de enero 2025. Los resultados históricos de 120,000 filas siguen identificados como antecedentes.

La adquisición nueva ya verificó los 24 meses completos: 14,080,680 filas, 7,079,061 de 2024 y 7,001,619 de 2025. Los hashes, tamaños y conteos están en `reports/tables/acquisition_full.json` y `acquisition_validation.json`. Coinciden con el total histórico guardado en el notebook, pero ahora cuentan con una comprobación nueva de los originales. Bronze Delta también concilia ese volumen completo por mes.

`python -m src.ingestion.validate_provenance` comprueba hashes, filas, columnas, periodo y equivalencia ordenada CSV/Parquet de la muestra, con nulos iguales y tolerancias numéricas rtol=1e-12 y atol=1e-9. El reporte distingue integridad de muestra de una nueva auditoría del ZIP original.

## Alcance de los parciales
P1: definición, fuente, muestra, diccionario, EDA, arquitectura y colaboración. P2: adquisición, raw/interim/processed, transformaciones, validación, pruebas, desempeño y decisiones. La variante local permite revisar componentes sobre la muestra. En Databricks ya se ejecutó Bronze completo; faltan Silver, Gold e integración, además de las revisiones cruzadas del equipo.

El modelo preliminar se menciona en el contexto del equipo como solicitud adicional del profesor. Confirmar su forma exacta; no se presenta como requisito textual de modelado de P1/P2 en el PDF.

Objetivo de plataforma: Databricks, PySpark y Delta con Bronze/Silver/Gold. Variables nuevas propuestas: `is_peak_delay_season`, `origin_hour_delay_rate_28d`, `airline_delay_rate_28d`. Fechas, particiones y etiqueta son auxiliares del contrato; estas tres variables aún no están implementadas.

## Limitaciones
- BTS es histórico y mensual; los resultados no equivalen a información disponible en vivo a tres horas.
- HHMM usa hora local; comparar aeropuertos requiere zonas horarias verificables.
- Muestreo fijo por mes cambia la ponderación de la población. Tasas de grupos pequeños son inestables.
- El EDA inicial de dos años no demuestra estacionalidad permanente ni describe por sí solo los dos años completos.
- No se verificó un archivo histórico de pronósticos meteorológicos emitidos al corte de tres horas.
- La ejecución local no prueba escalabilidad distribuida. Bronze completo está ejecutado en Databricks Free Edition, Spark 4.2.0, catálogo `workspace`; se comprobaron permisos de ejecución y escritura de Diego. Los permisos Databricks de los otros integrantes no se han comprobado. El benchmark CSV/Parquet local no mide rendimiento Spark.

## Fuera del alcance vigente
Precios, impacto económico, sistema en producción, informe y presentación final. GARCH, Monte Carlo y redes/SIR son extensiones sujetas a justificación.

## Posibles usuarios y valor esperado
Equipo, docente y personas que estudian operaciones aeroportuarias. Valor inmediato: conjunto analítico reproducible y comprensión verificable de calidad y patrones. Cualquier uso predictivo requiere evaluación temporal.

## Criterios de éxito
Muestra reproducible, reglas que detecten errores, concordancia entre capas, benchmark con resultados equivalentes y evidencia auténtica de aportes/revisiones de las tres personas. Fijar métricas predictivas antes de abrir la prueba temporal.
