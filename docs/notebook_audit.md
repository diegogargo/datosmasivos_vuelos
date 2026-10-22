# Auditoría de los archivos del equipo

## Notebook original preservado
Origen: `Proyecto Notebook.ipynb` aportado por Diego. Copia idéntica: `notebooks/antecedentes/Proyecto_Notebook_original.ipynb`.

SHA256: `242eb31ac2994ba10a9ccb3f3a4d6390e661728c87e7774d4f0d7e1fbb8ff358`.

Tiene 22 celdas y salidas guardadas. Algunos contadores de ejecución son nulos aunque exista salida; esto impide certificar que todo se ejecutó en orden en un entorno limpio. No se alteró el original.

## Qué demuestra la evidencia guardada
- Enero 2025: 539,747 filas originales, 110 columnas, muestra de 5,000; 164 cancelados, 4,836 elegibles y 896 retrasos >=15 min.
- Celda 17: log de los 24 meses de 2024–2025, 5,000 seleccionados por mes y 120,000 finales. Los conteos originales guardados suman 14,080,680.
- Celda 18: tabla mensual completa, 118,273 elegibles y 1,727 cancelados excluidos.
- Celda 19: correlación mensual entre años 0.711 y diferencia absoluta media 2.89 puntos porcentuales.
- Celda 20: 44,413 retrasos positivos, media general 13.24 min y mediana -2 min.

Estas cifras proceden de salidas guardadas. No se recuperó el Parquet histórico. En esta preparación solo se regeneró enero 2025 y se confirmaron sus conteos; no se recalculó el EDA de los 24 meses.

## Hallazgos para mejorar
Rutas `/content/` de Colab, lectura completa de cada CSV, caché original basada solo en existencia, lógica de hora mediante división HHMM que necesita tratar 2400, y falta de pipeline PySpark/Delta. No contiene entrenamiento del modelo a tres horas ni implementación meteorológica.

## Qué agrega la organización actual
Un notebook portable de muestra (`01_exploration.ipynb`), procedencia de archivos, componentes locales de ingesta/procesamiento/validación, pruebas y documentación. Son complementos del trabajo del equipo, no recuperación ficticia del Parquet ni sustitución del notebook original.

`EDA_BTS_RECONSTRUIDO_DESDE_CHAT.ipynb` es una reconstrucción anterior sin resultados, identificada como tal. Los Markdown de `docs/antecedentes` son transferencias históricas: sus frases sobre archivos faltantes o enlaces desconocidos ya no describen todo el estado actual. No se usan como instrucciones vigentes.

## Índice de evidencia
`reports/tables/antecedentes/` conserva texto extraído de las celdas, tabla mensual y manifiesto de procedencia. Las imágenes en `reports/figures/antecedentes/` son salidas extraídas sin recalcular. Las figuras `sample_*` proceden del notebook portable ejecutado ahora.
