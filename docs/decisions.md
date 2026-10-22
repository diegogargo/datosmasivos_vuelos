# Decisiones técnicas

## 1. Preservar el trabajo del equipo
**Decisión:** mantener el notebook original byte a byte y separar complementos reproducibles. **Razón:** conservar resultados y autoría histórica sin inventar ejecuciones nuevas. **Alternativa:** editar directamente el original. **Consecuencia:** hay antecedentes con rutas Colab; el README indica qué notebook se puede ejecutar ahora.

## 2. Periodo inicial de dos años (sustituido para el pipeline)
**Decisión inicial:** 2024–2025, alcance del notebook del equipo. **Actualización:** el usuario eligió enero 2024–diciembre 2025 para el pipeline completo. El EDA inicial conserva dos años. Se documentan ambos periodos para no mezclar muestras, antecedentes y nuevos conteos de población.

## 3. Etiqueta y cancelaciones
**Decisión:** `DepDelay >=15` solo para operados con resultado; cancelados conservados con etiqueta nula. **Razón:** no confundir cancelación con puntualidad. **Alternativa:** rellenar retraso nulo con cero. **Consecuencia:** denominador elegible explícito; se conservan retrasos negativos reales.

## 4. Capas y formatos
**Decisión:** local raw ZIP intacto, interim Parquet limpio, processed particionado y agregado. Objetivo posterior Bronze/Silver/Gold Delta en Databricks. **Razón:** trazabilidad y separación de transformaciones. **Alternativas:** solo notebook o solo CSV. **Consecuencia:** dependencias Arrow y comprobaciones entre tablas; esta implementación pandas no se presenta como Spark.

## 5. Alcance del muestreo
**Decisión:** regenerar solo enero 2025 con el procedimiento original; preservar resultados guardados de los otros meses. **Razón:** disponer de una muestra evaluable sin inventar recuperación del histórico. **Alternativas:** descargar de nuevo 24 meses o reutilizar cifras sin procedencia. **Consecuencia:** el EDA actual no representa toda la población. La muestra histórica uniforme por mes requerirá ponderación o datos completos para tasas poblacionales.

## 6. Disponibilidad a tres horas
**Decisión:** no declarar válidas tasas históricas ni clima hasta verificar `available_at` y corte de predicción. **Razón:** una ventana anterior al vuelo puede contener información publicada después. **Alternativa:** asumir disponibilidad inmediata de resultados BTS. **Consecuencia:** si no se puede verificar publicación, documentar explícitamente un análisis retrospectivo con disponibilidad ideal, sin prometer operación real.

## 7. Variables nuevas y evaluación
**Decisión:** mantener las tres variables propuestas del equipo sin darlas por implementadas. Estacionalidad se estima solo con entrenamiento. **Razón:** evitar selección con prueba temporal. **Alternativas:** escoger mayo-julio con los dos años completos o usar resultados del mismo vuelo como predictores. **Consecuencia:** los issues exigen pruebas temporales y separación de datos. La definición del modelo preliminar adicional se confirma con el profesor.

## 8. Colaboración verificable
**Decisión:** cuatro tareas por persona y revisión cruzada, con PR y evidencia propios. **Razón:** acreditar aportes auténticos. **Alternativa:** simular commits/reviews con identidades ajenas. **Consecuencia:** la creación asistida inicial no completa el requisito individual; cada integrante debe trabajar, revisar y responder.

## Alcance final y separación entre muestra y población
El equipo decidió usar 2024–2025 completos para el pipeline, 24 meses. Se conserva sin alterar el EDA original de 2024–2025 y la muestra pública de enero 2025. El objetivo es medir procesamiento con vuelos completos y comparar años, no aumentar artificialmente el número de filas repitiendo la muestra.

Bronze conservará todos los campos originales y sus metadatos. Los 21 campos del EDA seguirán como contrato analítico mínimo. La política temporal del futuro modelo debe tener en cuenta qué periodos ya se exploraron; el conjunto de prueba no se declara intacto retrospectivamente.
