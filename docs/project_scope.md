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
Enero 2024–diciembre 2025, vuelos incluidos en Reporting Carrier de BTS. El original usó 5,000 filas por mes. Esta base regenera enero de 2025 y preserva salidas históricas sin afirmar una ejecución nueva de los 24 meses.

## Alcance de los parciales
P1: definición, fuente, muestra, diccionario, EDA, arquitectura y colaboración. P2: adquisición, raw/interim/processed, transformaciones, validación, pruebas, desempeño y decisiones. La variante local permite revisar componentes sobre la muestra; Databricks y colaboración auténtica quedan como tareas explícitas.

El modelo preliminar se menciona en el contexto del equipo como solicitud adicional del profesor. Confirmar su forma exacta; no se presenta como requisito textual de modelado de P1/P2 en el PDF.

Objetivo de plataforma: Databricks, PySpark y Delta con Bronze/Silver/Gold. Variables nuevas propuestas: `is_peak_delay_season`, `origin_hour_delay_rate_28d`, `airline_delay_rate_28d`. Fechas, particiones y etiqueta son auxiliares del contrato; estas tres variables aún no están implementadas.

## Limitaciones
- BTS es histórico y mensual; los resultados no equivalen a información disponible en vivo a tres horas.
- HHMM usa hora local; comparar aeropuertos requiere zonas horarias verificables.
- Muestreo fijo por mes cambia la ponderación de la población. Tasas de grupos pequeños son inestables.
- Dos años no demuestran estacionalidad permanente.
- No se verificó un archivo histórico de pronósticos meteorológicos emitidos al corte de tres horas.
- La ejecución local no prueba escalabilidad distribuida. Falta workspace.

## Fuera del alcance vigente
Precios, impacto económico, sistema en producción, informe y presentación final. GARCH, Monte Carlo y redes/SIR son extensiones sujetas a justificación.

## Posibles usuarios y valor esperado
Equipo, docente y personas que estudian operaciones aeroportuarias. Valor inmediato: conjunto analítico reproducible y comprensión verificable de calidad y patrones. Cualquier uso predictivo requiere evaluación temporal.

## Criterios de éxito
Muestra reproducible, reglas que detecten errores, concordancia entre capas, benchmark con resultados equivalentes y evidencia auténtica de aportes/revisiones de las tres personas. Fijar métricas predictivas antes de abrir la prueba temporal.
