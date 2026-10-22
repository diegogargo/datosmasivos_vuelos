# Checklist de los primeros dos parciales

Referencia: PDF de proyecto aportado por Diego, páginas 2–13 y distribución de evaluación de página 19. Informe y presentación se solicitan en la fase final. Ninguna marca equivale a una garantía de calificación.

## Primer parcial
| Entregable | Evidencia actual | Pendiente |
|---|---|---|
| README inicial | README.md con integrantes, problema, pregunta, objetivo, fuente, estructura, ejecución y estado | Revisión del equipo |
| Alcance | docs/project_scope.md, unidad de análisis y limitaciones | Validar decisiones |
| Fuente | docs/data_sources.md, URL y procedencia de muestra | Verificar disponibilidad temporal para modelado |
| Muestra pequeña | data/sample/ CSV, Parquet y manifiesto | Aprobación del equipo |
| Diccionario | docs/data_dictionary.md, 21 variables y nulos reales | Revisión individual |
| EDA inicial | notebooks/01_exploration.ipynb y original preservado | Interpretación propia y PR de Santiago |
| Arquitectura | docs/architecture.md, actual y objetivo | Actualizar cuando exista Databricks |
| Colaboración por persona | Issues y guía de trabajo | Dos commits, un PR, una review y participación en issue, con enlaces reales |

## Segundo parcial
| Entregable | Evidencia actual | Pendiente |
|---|---|---|
| Ingesta automatizada | src/ingestion/bts.py, ZIP, trazabilidad, reintentos y caché verificada | Rango de 24 meses y escala |
| Datos crudos | Descarga real enero 2025 local; instrucciones reproducibles; ZIP excluido de Git | Recuperar o descargar histórico completo |
| Transformación | src/processing/build_dataset.py, tipos, nulos, clave, tiempo, etiqueta y agregado | PySpark/Delta del alcance acordado |
| Tres capas | raw, interim y processed de muestra local | Bronze/Silver/Gold completos en Databricks |
| Validaciones | Muestra y 19 comprobaciones procesadas | Ampliar a histórico y reglas temporales/entre tablas Spark |
| Desempeño | CSV vs Parquet, cinco repeticiones y memoria definida | Volumen mayor, sin extrapolar muestra |
| Decisiones | docs/decisions.md | Agregar decisiones reales de integración |
| Pruebas | 27 casos locales, CI configurada | Confirmar CI remota y pruebas de las capas reales |
| Arquitectura actualizada | Flujo local y objetivo distinguidos | Sustituir objetivo por arquitectura verificada al ejecutar |
| Colaboración | Reparto transversal y issues principales | Contribución técnica y documental/validación por persona; PR revisados e integración |

## Solicitud adicional y fase posterior
El contexto menciona modelo preliminar solicitado por el profesor: confirmar forma y evaluar temporalmente. No hay modelo a 3 h ejecutado en esta base. La presentación, informe final y reflexiones finales se dejan para la entrega correspondiente.

## Orden de cierre
Acceso de colaboradores → tres tareas P1 → workspace y primer mes Bronze → Silver/Gold → 24 meses y benchmark → variables/modelo preliminar si corresponde → evidencias y revisión final de P1/P2. No marcar las tareas como hechas sin enlaces o resultados verificables.
