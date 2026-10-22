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
| Arquitectura | docs/architecture.md, muestra local y Bronze completo de Databricks distinguidos | Revisar con Silver/Gold reales |
| Colaboración por persona | Issues y guía de trabajo | Dos commits, un PR, una review y participación en issue, con enlaces reales |

## Segundo parcial
| Entregable | Evidencia actual | Pendiente |
|---|---|---|
| Ingesta automatizada | src/ingestion/acquire_range.py, 24 meses adquiridos, hashes y conteos verificados; PR #14 | Revisión e integración del PR |
| Datos crudos | acquisition_full.json y acquisition_validation.json: 14,080,680 filas; ZIP/CSV fuera de Git y transferidos al Volume | Revisión de trazabilidad del equipo |
| Transformación | src/processing/build_dataset.py, tipos, nulos, clave, tiempo, etiqueta y agregado | PySpark/Delta del alcance acordado |
| Tres capas | Muestra local y Bronze Delta completo: 24 meses y 14,080,680 filas; databricks_bronze_result.json y validación de reejecución de enero 2025 | Silver/Gold e integración completa |
| Validaciones | Muestra y 19 comprobaciones procesadas | Ampliar a histórico y reglas temporales/entre tablas Spark |
| Desempeño | benchmark_scale: 5,000 y 539,747 vuelos, cinco repeticiones, operación equivalente y pico de proceso; PR #16 | Medir ejecución Spark si se hacen afirmaciones de desempeño distribuido |
| Decisiones | docs/decisions.md | Agregar decisiones reales de integración |
| Pruebas | 82 casos correctos, repetidos desde copia limpia; clean_reproduction.json. CI remota correcta en el commit 860f213 | Confirmar CI del último commit y pruebas de Silver/Gold reales |
| Arquitectura actualizada | Flujo local y Bronze ejecutado, Spark 4.2.0, catálogo y Volume documentados | Incorporar Silver/Gold cuando existan |
| Colaboración | Reparto transversal y issues principales | Contribución técnica y documental/validación por persona; PR revisados e integración |

## Solicitud adicional y fase posterior
El contexto menciona modelo preliminar solicitado por el profesor: confirmar forma y evaluar temporalmente. No hay modelo a 3 h ejecutado en esta base. La presentación, informe final y reflexiones finales se dejan para la entrega correspondiente.

## Orden de cierre
Los colaboradores ya tienen acceso; adquisición, Bronze completo y benchmark de muestra/mes completo ya tienen evidencia. Cerrar las tres tareas P1 y reviews → Silver e históricos → Gold → validación e integración de los 24 meses → modelo preliminar del alcance confirmado → revisión final de P1/P2. No marcar las tareas como hechas sin enlaces o resultados verificables.
