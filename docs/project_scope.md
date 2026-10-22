# Definici�n del alcance

## Contexto del problema
Los vuelos pueden salir adelantados o con retraso. Cancelaciones y desv�os son eventos distintos. Antes de interpretar diferencias entre aerol�neas, aeropuertos y horarios se necesitan datos trazables, reglas de calidad y denominadores comparables.

## Pregunta principal
�Qu� patrones operativos y temporales se relacionan con retrasos de salida de puerta >=15 minutos en vuelos reportados a BTS durante 2022�2025, y qu� capacidad predictiva tienen con informaci�n disponible tres horas antes del horario programado?

## Preguntas secundarias
- �C�mo var�an las tasas por mes, aerol�nea, origen y hora local?
- �Qu� nulos, duplicados y extremos afectan el an�lisis?
- �Se conservan los patrones al separar entrenamiento, validaci�n y prueba por tiempo?
- �Qu� fuentes tienen disponibilidad hist�rica verificable al corte de predicci�n?

## �Qu� representa una fila?
Un segmento de vuelo programado reportado por una aerol�nea a BTS en una fecha, con origen, destino y horario programado. La clave candidata combina fecha, aerol�nea informante, n�mero de vuelo, origen, destino y hora programada; se comprueba su unicidad. No representa un pasajero, boleto o itinerario completo.

## Unidad de an�lisis
La etiqueta es `DepDelay >=15` cuando `Cancelled ==0` y `DepDelay` est� observado. Se conservan retrasos negativos. Cancelados permanecen en la capa limpia con etiqueta nula, incluso si reportan `DepDelay`.

## Alcance temporal
Pipeline: enero 2022�diciembre 2025, 48 meses completos de Reporting Carrier de BTS. El equipo eligi� cuatro a�os. El EDA inicial mantiene su periodo 2024�2025 y 5,000 filas por mes; no representa autom�ticamente el hist�rico ampliado. La muestra reproducible incluida tiene 5,000 filas de enero 2025. Los resultados hist�ricos de 120,000 filas siguen identificados como antecedentes.

La cantidad real descargada de los 48 meses se documentar� mediante manifiestos y conteos nuevos. Los 14,080,680 registros guardados en el notebook corresponden �nicamente a 2024�2025. No son el total de los cuatro a�os.

`python -m src.ingestion.validate_provenance` comprueba hashes, filas, columnas, periodo y equivalencia ordenada CSV/Parquet de la muestra, con nulos iguales y tolerancias num�ricas rtol=1e-12 y atol=1e-9. El reporte distingue integridad de muestra de una nueva auditor�a del ZIP original.

## Alcance de los parciales
P1: definici�n, fuente, muestra, diccionario, EDA, arquitectura y colaboraci�n. P2: adquisici�n, raw/interim/processed, transformaciones, validaci�n, pruebas, desempe�o y decisiones. La variante local permite revisar componentes sobre la muestra; Databricks y colaboraci�n aut�ntica quedan como tareas expl�citas.

El modelo preliminar se menciona en el contexto del equipo como solicitud adicional del profesor. Confirmar su forma exacta; no se presenta como requisito textual de modelado de P1/P2 en el PDF.

Objetivo de plataforma: Databricks, PySpark y Delta con Bronze/Silver/Gold. Variables nuevas propuestas: `is_peak_delay_season`, `origin_hour_delay_rate_28d`, `airline_delay_rate_28d`. Fechas, particiones y etiqueta son auxiliares del contrato; estas tres variables a�n no est�n implementadas.

## Limitaciones
- BTS es hist�rico y mensual; los resultados no equivalen a informaci�n disponible en vivo a tres horas.
- HHMM usa hora local; comparar aeropuertos requiere zonas horarias verificables.
- Muestreo fijo por mes cambia la ponderaci�n de la poblaci�n. Tasas de grupos peque�os son inestables.
- El EDA inicial de dos a�os no demuestra estacionalidad permanente ni describe por s� solo los cuatro a�os completos.
- No se verific� un archivo hist�rico de pron�sticos meteorol�gicos emitidos al corte de tres horas.
- La ejecuci�n local no prueba escalabilidad distribuida. Workspace Free Edition confirmado por captura; cat�logo, permisos y ejecuci�n pendientes de verificar.

## Fuera del alcance vigente
Precios, impacto econ�mico, sistema en producci�n, informe y presentaci�n final. GARCH, Monte Carlo y redes/SIR son extensiones sujetas a justificaci�n.

## Posibles usuarios y valor esperado
Equipo, docente y personas que estudian operaciones aeroportuarias. Valor inmediato: conjunto anal�tico reproducible y comprensi�n verificable de calidad y patrones. Cualquier uso predictivo requiere evaluaci�n temporal.

## Criterios de �xito
Muestra reproducible, reglas que detecten errores, concordancia entre capas, benchmark con resultados equivalentes y evidencia aut�ntica de aportes/revisiones de las tres personas. Fijar m�tricas predictivas antes de abrir la prueba temporal.
