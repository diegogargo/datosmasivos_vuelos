# Jose Miguel Guevara — GUEVARA21

Lee primero `00_EMPEZAR_AQUI.md`. Tus PR los revisa Santiago (`Skraeder`). Tú revisas los PR de Diego (`diegogargo`). Puedes empezar P1 sin Databricks y sin descargar millones de vuelos.

## 1. Preparar tu copia e identidad

Abre Codex con tu cuenta de ChatGPT, conecta GitHub como GUEVARA21 y pega:

```text
Soy Jose Miguel Guevara, mi cuenta GitHub es GUEVARA21. Prepara mi copia local de https://github.com/diegogargo/datosmasivos_vuelos en una carpeta propia de Documentos llamada datosmasivos_vuelos_GUEVARA21. Si ya existe, inspecciónala y reutilízala sin borrar cambios. Prefiero Codex local en este equipo.

Verifica la conexión GitHub y que GUEVARA21 tenga escritura en ese repositorio. Si hace falta conectar el plugin GitHub, guíame por el inicio de sesión del navegador; no pidas tokens. Si necesitas Git/GitHub CLI/Python y no existen, prepara su instalación oficial y comprueba las versiones. Usa Python 3.13 para las dependencias locales del repo. No sustituyas PySpark del runtime Databricks.

Antes de cualquier publicación, confirma que la cuenta autenticada es GUEVARA21. Configura el autor de Git solo en esta copia como Jose Miguel Guevara, usando el correo noreply de mi cuenta obtenido con su ID real. No uses la cuenta ni las credenciales de Diego o Santiago.

Lee README, CONTRIBUTING, config/github_tasks.json y docs/team/jose_miguel.md. Conserva main sin cambios directos. Usa la rama existente jose_miguel/p1-02 para mi primera tarea; si contiene avances, consérvalos. Incorpora main mediante un flujo seguro si hace falta. Crea .venv, instala requirements.txt y verifica la base antes de modificarla.

Mi primer issue es #2. Prepara todo para trabajar ahí y después continúa con el siguiente prompt. No crees otro repositorio ni copies al PR cambios de las ramas de Diego como si fueran míos.
```

Cuando Codex confirme carpeta, cuenta y rama, pega el siguiente bloque completo.

## 2. Primer parcial: calidad y contrato, issue #2

```text
Implementa mi P1-02 del issue #2 en jose_miguel/p1-02. Soy GUEVARA21. Usa el notebook original del equipo como antecedente sin modificarlo; trabaja con data/sample/flights_2025_01.csv y su Parquet. No vuelvas a construir el proyecto ni descargues todo el histórico para esta tarea.

Revisa src/validation/audit_sample.py y src/processing/contracts.py. Añade reglas que la base no cubre: CRSArrTime HHMM válido, incluidos 0000 y 2400, rechazo de minutos como 1260, números fraccionarios y no finitos; número de vuelo entero positivo según el contrato actual; valores numéricos finitos cuando estén observados; nulos permitidos documentados por campo. No rellenes causas de retraso faltantes con cero. Conserva DepDelay negativo, cancelados sin etiqueta aunque tengan DepDelay y el umbral >=15.

Corrige el caso sin vuelos elegibles: la tasa debe ser null/None, no error ni cero. Define denominadores explícitos. Mantén las reglas en funciones reutilizables y reportes con fallos legibles. No inventes problemas que los datos no muestran.

Escribe pruebas con archivos/casos temporales para cada regla nueva, demostrando detección de errores y conservación de casos válidos. Ejecuta las pruebas existentes y nuevas, auditoría, procesamiento, validación y revisión de estructura. Si un resultado cambia, explica por qué.

Actualiza docs/data_dictionary.md y docs/validation.md y guarda un reporte pequeño real. Haz al menos dos commits sustantivos: implementación/pruebas y documentación/evidencia. Declara asistencia de Codex.

Publica mi rama y abre un único PR hacia main con Closes #2 cuando cumpla los criterios; solicita revisión a Skraeder. Participa en el issue con un resumen concreto y el enlace. No mezcles otro issue en este PR ni apruebes tu propio trabajo. No marques revisiones pendientes como hechas. Si no puedes publicar, deja preparados los cambios y explica el acceso exacto que falta.
```

Comprobaciones que Codex debe ejecutar desde tu copia, con su entorno local:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m src.validation.audit_sample
.venv\Scripts\python.exe -m src.processing.build_dataset
.venv\Scripts\python.exe -m src.validation.validate_dataset
.venv\Scripts\python.exe scripts/check_repository.py
```

El PR de esta fase debe contener tu código de calidad, pruebas y documentación. No basta con renombrar archivos o subir la base preparada por Diego.

## 3. Tu revisión a Diego

Después de publicar P1, usa `04_REVISIONES.md`. Revisa primero el PR #13; luego #14 y #15 cuando corresponda. Que el PR sea de tu compañero no cambia la obligación de leer cambios y comprobar resultados.

## 4. Segundo parcial: Silver, issue #5

Empezar después de tu P1 y de disponer de Bronze verificable. Usa `jose_miguel/p2-02`. Pega:

```text
Implementa mi P2-02, issue #5, en una rama propia desde el main actualizado. Conserva mi autor GUEVARA21. Consulta docs/guias/00_EMPEZAR_AQUI.md, docs/bronze_contract.md, el issue #5 y el PR de Bronze de Diego. El alcance son 24 meses completos, enero 2024 a diciembre 2025.

Crea src/processing/silver.py y un notebook notebooks/databricks/02_silver.py. La entrada es workspace.bronze.vuelos_raw: todos los campos originales como cadenas más metadatos _source_*, _run_id y _ingested_at. La función pública exacta debe ser:
run_silver(spark, bronze_table, silver_table, quarantine_table, start, end, output_root)

Valores de integración: bronze_table=workspace.bronze.vuelos_raw, silver_table=workspace.silver.vuelos_clean, quarantine_table=workspace.silver.vuelos_quarantine, start=2024-01, end=2025-12. No supongas que estas tablas aparecen en mi workspace personal: podemos integrar con la identidad de Diego y registrar ese hecho.

Implementa tipos, nulos y estandarización; conserva IDs estables de aeropuerto y aerolínea del original para los cruces históricos. Aplica reglas de dominio, deduplicación exacta y política explícita de claves contradictorias. Registra exclusiones y cuarentena con motivo; no borres vuelos silenciosamente. Cancelados permanecen en Silver con delay15 nulo y DepDelay negativo válido.

Normaliza HHMM=2400 al día siguiente. Construye scheduled_local, scheduled_utc y prediction_cutoff_utc=scheduled_utc-3 horas con una dimensión de aeropuertos y zonas IANA verificable, fuente/versiones/hash registrados. Comprueba cobertura de aeropuertos. Documenta y prueba horas ambiguas o inexistentes por DST; no afirmes UTC correcto sin evidencia ni apliques una zona única a Estados Unidos. No inventes una dimensión de zonas.

Usa DataFrames y SQL compatibles con Spark Connect/serverless; evita sparkContext, RDD y dependencias de un cluster clásico. Escritura Delta idempotente por mes y conciliación Bronze = aceptados + cuarentena/exclusiones explicadas. Incluye etiqueta delay15 solo para operados con resultado finito.

Genera reporte con layer=silver, start/end, complete, rows y months (cada elemento con period, source_rows, silver_rows y quarantine_rows), además de versiones y reglas. El reporte del último resultado se guarda en output_root/reports/silver/latest.json. Nunca complete=true si falta un mes o falla una conciliación. Conserva procedencia hasta Gold.

Prueba errores de tipos, nulos, duplicados, fechas, DST y conteos con casos pequeños. Si no hay Spark local, prepara pruebas de funciones puras y deja la ejecución Spark explícitamente pendiente hasta probarla realmente en Databricks; no uses mocks para fingir un pipeline ejecutado.

Documenta el contrato y abre PR propio con código, pruebas, decisiones y evidencia; solicita revisión a Skraeder. Si falta ejecución real, mantenlo draft con Refs #5. Cuando se cumplan los criterios, adjunta evidencia y cambia a Closes #5. Conserva asistencia de IA declarada.
```

## 5. Bloque exacto del notebook Silver

Este bloque se ejecuta **cuando Codex haya implementado y transferido `silver.py`** y exista Bronze. Diego puede ejecutarlo en el workspace de integración. Crear el notebook dentro de la carpeta del proyecto y pegar:

```python
from pathlib import Path
import sys
import json
for candidate in [Path.cwd(), *Path.cwd().parents]:
    if (candidate / 'src/processing/silver.py').is_file():
        sys.path.insert(0, str(candidate))
        break
from src.processing.silver import run_silver
from src.utils.common import write_json
root = '/Volumes/workspace/bronze/vuelos_raw/vuelos'
report = run_silver(
    spark=spark,
    bronze_table='workspace.bronze.vuelos_raw',
    silver_table='workspace.silver.vuelos_clean',
    quarantine_table='workspace.silver.vuelos_quarantine',
    start='2024-01', end='2025-12', output_root=root,
)
write_json(Path(root) / 'reports/silver/latest.json', report)
print(json.dumps(report, indent=2, ensure_ascii=False))
```

Comprobación adicional en otra celda:

```python
spark.sql('SELECT _source_period, COUNT(*) AS vuelos FROM workspace.silver.vuelos_clean GROUP BY _source_period ORDER BY _source_period').show(30, truncate=False)
spark.sql('SELECT COUNT(*) AS cancelados_con_etiqueta FROM workspace.silver.vuelos_clean WHERE Cancelled = 1 AND delay15 IS NOT NULL').show()
```

La segunda consulta debe devolver 0. Si falta el módulo, no “arregles” la celda inventando una función vacía: vuelve al prompt para que Codex termine la implementación.

## 6. Históricos y validación, issues #8 y #11

Después de Silver, pega en Codex:

```text
Continúa mis issues #8 (jose_miguel/p2-05) y #11 (jose_miguel/p2-08), un PR por tarea. En #8 crea src/processing/historical_features.py con run_historical_features(spark, silver_table, target_table, start, end, output_root, availability_mode='disabled'). Entrada workspace.silver.vuelos_clean y salida workspace.silver.vuelos_history.

Implementa origin_hour_delay_rate_28d y airline_delay_rate_28d con ventana anterior al cutoff, exclusión del vuelo actual, futuro y publicación posterior. Define mínimo de historia y suavizado usando solo antecedentes disponibles o entrenamiento, y política nula para historia insuficiente. Usa IDs estables y horas locales normalizadas. Escribe pruebas de frontera, ausencia de antecedentes y fugas temporales.

BTS publica por lotes mensuales: su fecha de vuelo no demuestra disponibilidad del resultado a tres horas. En modo disabled conserva las tasas nulas y documenta por qué. Si implementas retrospective_ideal, actívalo explícitamente y etiqueta la suposición; no lo presentes como modelo operacional validado. Un modo publication_aware exige available_at real; downloaded_at no se hace pasar por disponibilidad histórica del evento. Conserva scheduled_utc y prediction_cutoff_utc coherentes. No uses WeatherDelay ni resultados del mismo vuelo como predictores.

En #11 valida el flujo real Bronze/Silver/Gold por tipos, nulos, claves, rangos, fechas, disponibilidad y conciliación de volúmenes. Integra los contratos reales de Santiago cuando existan. Inyecta errores para demostrar detección y adjunta reportes de ejecuciones verdaderas. No declares terminada esa validación mientras falte Gold o ejecución. Solicita review de Skraeder en cada PR y actualiza solo evidencias reales.
```

Celda de históricos, después de implementar ese módulo:

```python
from src.processing.historical_features import run_historical_features
report_history = run_historical_features(
    spark=spark,
    silver_table='workspace.silver.vuelos_clean',
    target_table='workspace.silver.vuelos_history',
    start='2024-01', end='2025-12',
    output_root='/Volumes/workspace/bronze/vuelos_raw/vuelos',
    availability_mode='disabled',
)
print(report_history)
```

El modo disabled no acredita tasas temporales implementadas y validadas operacionalmente. El PR debe explicar el modo efectivamente ejecutado y sus límites.

## 7. Evidencias que entregas

- P1: código nuevo de calidad, casos con errores, documentación y PR revisado por Santiago.
- Review tuya de Diego con observaciones fundadas.
- P2: Silver y cuarentena con conteos conciliados y ejecución real.
- Dos históricos con pruebas temporales y disponibilidad declarada.
- Validación entre capas después de disponer de Gold.
- Tus ramas, commits, PR y reviews hechos desde GUEVARA21 y asistencia de Codex declarada.
