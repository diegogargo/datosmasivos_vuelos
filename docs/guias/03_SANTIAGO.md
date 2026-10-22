# Santiago Roldán — Skraeder

Lee primero `00_EMPEZAR_AQUI.md`. Tus PR los revisa Diego (`diegogargo`). Tú revisas los PR de Jose Miguel (`GUEVARA21`). Puedes empezar P1 con la muestra incluida.

## 1. Preparar tu copia e identidad

Abre Codex con tu propia cuenta de ChatGPT, conecta GitHub como Skraeder y pega:

```text
Soy Santiago Roldán, usuario GitHub Skraeder. Prepara mi copia de https://github.com/diegogargo/datosmasivos_vuelos en Documentos/datosmasivos_vuelos_Skraeder. Reutiliza una copia existente si ya tiene avances; no borres cambios. Trabaja localmente en este equipo.

Comprueba conexión GitHub, identidad Skraeder y escritura en ese repositorio antes de publicar. Si falta la conexión o herramientas oficiales Git/GitHub CLI/Python, prepara el acceso e instalación; el inicio de sesión del navegador lo haré yo. No solicites tokens. Prepara Python 3.13 y un .venv con requirements.txt para el trabajo local.

Configura mi autor de Git solo en esta copia como Santiago Roldán y mi noreply obtenido del ID real de Skraeder. No uses las cuentas de Diego ni de Jose Miguel. Lee README, CONTRIBUTING, config/github_tasks.json y docs/team/santiago.md.

Mi primera tarea es issue #3 y la rama existente santiago/p1-03. Verifica la rama y conserva cualquier avance. No publiques directamente en main ni dupliques PR o repositorio. Incorpora main de forma segura si la rama lo necesita. Revisa la base y continúa con mi siguiente prompt.
```

## 2. Primer parcial: EDA reutilizable, issue #3

Copia el bloque completo:

```text
Implementa mi P1-03 del issue #3 en santiago/p1-03. Soy Skraeder. Conserva el notebook original notebooks/antecedentes/Proyecto_Notebook_original.ipynb sin cambios. Separa muestra actual y salidas históricas del notebook. No uses un proyecto alternativo ni inventes datos recuperados.

Crea src/analysis/eda.py y tests/test_analysis.py. Extrae funciones reutilizables y una CLI que calcule métricas por hora programada local, aerolínea y aeropuerto: total de filas, elegibles, retrasados >=15 y tasa. Elegibles son Cancelled==0 con DepDelay finito observado. Cancelados con DepDelay siguen excluidos. DepDelay negativo es válido. Horario 2400 se normaliza a hora 0 del día siguiente. Denominador cero implica tasa nula. Identifica grupos pequeños sin borrar ni esconderlos, con --min-group-size 30 configurable.

La CLI requerida es python -m src.analysis.eda --input data/sample/flights_2025_01.csv --output-dir reports/tables/eda_sample --min-group-size 30. Debe funcionar desde la raíz y sin rutas de Colab. Admite CSV y Parquet, valida el esquema y evita descargas al importar.

Prueba cancelados con resultado, nulos, infinitos, grupos sin elegibles, grupos pequeños, límite 2400 y consistencia de sumas/denominadores. En la muestra real deben aparecer 5000 totales, 164 cancelados, 4836 elegibles y 896 retrasos >=15; explica cualquier divergencia real.

Actualiza notebooks/01_exploration.ipynb para consumir el módulo sin duplicar reglas. Escribe docs/eda_findings.md con al menos tres hallazgos y dos limitaciones respaldados por tablas y gráficos reales. No generalices la muestra de enero a todos los vuelos ni presentes los 120000 registros históricos como un Parquet recuperado.

Haz dos commits sustantivos: código/pruebas y análisis/documentación. Ejecuta toda la suite y comprobaciones del repositorio. Publica mi rama y un único PR hacia main con Closes #3 y solicitud de review a diegogargo. Participa en el issue con resultados y enlace. Declara asistencia de Codex. No apruebes mi propio PR ni registres reviews ficticias.
```

Comprobaciones que Codex debe ejecutar después de crear el módulo:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m src.analysis.eda --input data/sample/flights_2025_01.csv --output-dir reports/tables/eda_sample --min-group-size 30
.venv\Scripts\python.exe scripts/check_repository.py
```

## 3. Revisar a Jose Miguel

Usa `04_REVISIONES.md` para revisar su PR del issue #2. Después revisarás sus PR de Silver, históricos y validación. El comentario debe explicar qué comprobaste, no solo decir “se ve bien”.

## 4. Segundo parcial: Gold, issue #6

Después del P1 y de Silver disponible, usa santiago/p2-03 y pega:

```text
Implementa mi P2-03 del issue #6. Soy Skraeder y el periodo definitivo es 2024-01 a 2025-12. Lee la guía de Jose Miguel y sus contratos reales antes de implementar Gold. No dupliques Silver, históricos o el trabajo de Diego.

Crea src/processing/gold.py, pruebas y notebooks/databricks/04_gold.py. La función pública exacta es run_gold(spark, silver_table, history_table, features_table, monthly_table, distribution_table, start, end, training_end, output_root).

Entradas: workspace.silver.vuelos_clean y workspace.silver.vuelos_history. Salidas: workspace.gold.flight_features, workspace.gold.delay_monthly y workspace.gold.delay_distribution. El esquema mantiene metadatos, elegibilidad, delay15 y las tres variables propuestas: is_peak_delay_season, origin_hour_delay_rate_28d y airline_delay_rate_28d. Los auxiliares de fechas/particiones no se cuentan como decenas de features nuevas.

Calcula agregados por mes, aerolínea y origen con totales, elegibles, retrasados y tasas, reconciliados con Silver. No uses cancelados como vuelos puntuales ni rellenes tasas sin elegibles con cero. Documenta claves y granularidad. La distribución de retrasos debe identificar su población, incluidos negativos o solo positivos según la tabla, sin mezclar denominadores.

Estima is_peak_delay_season únicamente con el periodo de entrenamiento indicado por training_end; mayo-julio es hipótesis del equipo, no regla obtenida mirando prueba. Registra el procedimiento y la estabilidad limitada de dos años. Conserva los históricos de Jose Miguel y su modo de disponibilidad. No conviertas tasas desconocidas en valores inventados ni escondas el supuesto retrospectivo.

Implementa Spark Connect/Delta y escrituras idempotentes por mes. Prueba consistencia entre filas y agregados, grupos duplicados, nulos, ausencia de fuga de información y que modificar etiquetas posteriores a training_end no cambie la estacionalidad aprendida. El mapeo/encoders futuros también se ajustan solo con entrenamiento.

Genera un reporte real layer=gold, start/end, complete, rows y months con period y conteos conciliados; guárdalo en output_root/reports/gold/latest.json. Adjunta versiones y ejecución real. Si falta Silver, históricos o ejecución, registra la dependencia y deja el PR draft; no fabriques tablas. Solicita revisión a diegogargo y declara asistencia de Codex.
```

## 5. Bloque exacto para ejecutar Gold

Solo usar después de implementar y transferir gold.py y disponer de Silver e históricos. Diego puede ejecutarlo en el workspace de integración. Pegar en un notebook Python dentro de la carpeta del proyecto:

```python
from pathlib import Path
import sys
import json
for candidate in [Path.cwd(), *Path.cwd().parents]:
    if (candidate / 'src/processing/gold.py').is_file():
        sys.path.insert(0, str(candidate))
        break
from src.processing.gold import run_gold
from src.utils.common import write_json
root = '/Volumes/workspace/bronze/vuelos_raw/vuelos'
report = run_gold(
    spark=spark,
    silver_table='workspace.silver.vuelos_clean',
    history_table='workspace.silver.vuelos_history',
    features_table='workspace.gold.flight_features',
    monthly_table='workspace.gold.delay_monthly',
    distribution_table='workspace.gold.delay_distribution',
    start='2024-01', end='2025-12',
    training_end='2024-12-31', output_root=root,
)
write_json(Path(root) / 'reports/gold/latest.json', report)
print(json.dumps(report, indent=2, ensure_ascii=False))
```

`training_end` fija la regla de estacionalidad de este ejemplo. No declara automáticamente una prueba intacta: el EDA original ya exploró 2024–2025. Cualquier evaluación predictiva debe registrar esa exposición y su protocolo.

Comprobación posterior:

```python
spark.sql('SELECT _source_period, COUNT(*) AS vuelos FROM workspace.gold.flight_features GROUP BY _source_period ORDER BY _source_period').show(30, truncate=False)
spark.table('workspace.gold.delay_monthly').show(30, truncate=False)
```

## 6. Modelo y EDA completo, issues #9 y #12

Pegar después de Gold:

```text
Continúa mis issues #9 (santiago/p2-06) y #12 (santiago/p2-09), un PR por tarea. Para #9 registra primero la definición confirmada del modelo preliminar adicional solicitado por el profesor; el PDF no obliga por sí solo a inventar una familia de modelos para P1/P2. Esta aclaración no debe detener Gold ni el EDA completo.

Si corresponde clasificación, compara un baseline constante y un modelo sencillo con división cronológica documentada, tamaños, variables, semillas y métricas ROC-AUC, PR-AUC y matriz de confusión. Ajusta encoders, imputación, hiperparámetros y selección solo en entrenamiento/validación. Reconoce que los años ya se exploraron; no declares prueba nunca vista si no lo fue. Excluye DepDelay, ArrDelay, causas posteriores y toda información del mismo vuelo no disponible al cutoff de tres horas. Separa experimento retrospectivo ideal de disponibilidad operacional. No reutilices métricas del experimento a 24 h como si validaran 3 h.

Si se solicita distribución en lugar de clasificación, trabaja con la población de retrasos que corresponda y explica sus límites. No inventes resultados ni entrenamientos. Mantén clima, GARCH, Monte Carlo y redes fuera del alcance salvo una solicitud confirmada.

Para #12 aplica mi EDA reutilizable al Gold real de los 24 meses. Documenta tabla, hashes/versiones, fechas, elegibilidad y denominadores. Compara población con la muestra inicial y explica selección fija de 5000 por mes y ponderación. Redacta hallazgos reales, limitaciones y diferencias; no vuelvas a subir archivos masivos a GitHub.

Actualiza docs/rubric_checklist.md con enlaces reales a reportes, CI, PR y reviews. No prepares informe ni presentación final. Conserva asistencia de IA declarada y solicita revisión a diegogargo. Deja pendientes los puntos que realmente dependan de módulos, profesor o ejecución no disponible.
```

## 7. Evidencias que entregas

- P1: módulo EDA, pruebas, tablas, interpretación y PR revisado por Diego.
- Review tuya al PR de Jose Miguel.
- P2: Gold, estacionalidad de entrenamiento y agregados reconciliados con Silver.
- Modelo del alcance confirmado y protocolo temporal honesto, si corresponde.
- EDA del volumen completo y comparación con la muestra.
- Checklist con evidencias de los tres y tus commits/PR desde Skraeder.
