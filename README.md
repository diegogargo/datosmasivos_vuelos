# Datos Masivos: retrasos de salida de vuelos

## Integrantes
| Integrante | GitHub |
|---|---|
| Diego García | [@diegogargo](https://github.com/diegogargo) |
| Jose Miguel Guevara | [@GUEVARA21](https://github.com/GUEVARA21) |
| Santiago Roldán | [@Skraeder](https://github.com/Skraeder) |

Repositorio público: [datosmasivos_vuelos](https://github.com/diegogargo/datosmasivos_vuelos).

**Notebook principal de partida:** [Proyecto Notebook original del equipo](notebooks/antecedentes/Proyecto_Notebook_original.ipynb), conservado sin modificar.

## Problema
Los retrasos de salida varían entre aeropuertos, aerolíneas, meses y horarios. Se necesita un proceso trazable que conserve los datos crudos, valide su calidad y prepare información para investigar esos patrones y su capacidad predictiva.

## Pregunta principal
¿Qué patrones operativos y temporales se relacionan con retrasos de salida de puerta de al menos 15 minutos en vuelos reportados a BTS durante 2024–2025, y qué capacidad predictiva tienen usando información disponible tres horas antes de la salida programada?

## Objetivo
Construir un flujo reproducible de adquisición, limpieza, validación y análisis; evolucionarlo a PySpark y Delta en Databricks y evaluar un modelo preliminar sin fuga de información. La disponibilidad a tres horas debe verificarse antes del modelado.

## Fuentes de datos
[BTS Reporting Carrier On-Time Performance](https://transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ), del U.S. Department of Transportation. ZIP mensuales con CSV. Periodo: enero 2024–diciembre 2025. La muestra incluida usa enero de 2025, 5,000 filas, 21 campos y semilla 42. Ver [procedencia y limitaciones](docs/data_sources.md).

## Estado actual
| Elemento | Evidencia y estado |
|---|---|
| Original del equipo | Notebook intacto con salidas guardadas de 24 meses |
| Muestra regenerada | 5,000 filas; 164 cancelados; 4,836 elegibles; 896 retrasos >=15 min (18.53%) |
| Ejecución local | Adquisición verificable, limpieza, raw/interim/processed, validaciones, pruebas y benchmark sobre muestra |
| EDA | Notebook portable ejecutado; antecedentes identificados por separado |
| Databricks/PySpark/Delta | Arquitectura objetivo; workspace y ejecución pendientes |
| Histórico de 24 meses | Salidas guardadas disponibles; Parquet original de 120,000 filas no entregado. Solo enero 2025 se regeneró aquí |
| Variables y modelo a 3 h | Propuestos; no entrenados ni validados en esta base |
| Colaboración | Tareas repartidas; los aportes y revisiones individuales deben realizarlos los integrantes |

Esta base se organizó con asistencia de IA a partir de los archivos del equipo. No acredita por sí sola colaboración ni ejecución distribuida. El [checklist de parciales](docs/rubric_checklist.md) identifica lo pendiente. Informe y presentación corresponden a la entrega final.

## Estructura del repositorio
```text
config/                  Configuración, equipo y tareas
notebooks/01_exploration.ipynb  EDA portable de la muestra
notebooks/antecedentes/   Notebook original y reconstrucción histórica
src/ingestion/           Descarga BTS, caché, ZIP y trazabilidad
src/processing/          Contrato y transformación local
src/validation/          Calidad y consistencia entre tablas
src/analysis/            Benchmark reproducible
src/utils/               Rutas, fechas, JSON y checksums
data/sample/             Muestra pequeña CSV/Parquet y procedencia
data/raw/                ZIP completos locales, excluidos de Git
data/interim/            Limpieza local, excluida de Git
data/processed/          Parquet y agregados locales, excluidos de Git
reports/figures/          Gráficas actuales y antecedentes identificados
reports/tables/           Validaciones, mediciones y evidencia
docs/                    Alcance, diccionario, arquitectura y guías
tests/                   Pruebas de ingesta, transformación y calidad
.github/                 CI y plantillas de issues/PR
```

## Instrucciones iniciales de ejecución
Python 3.13 recomendado (compatibilidad declarada >=3.12). En PowerShell:
```powershell
git clone https://github.com/diegogargo/datosmasivos_vuelos.git
cd datosmasivos_vuelos
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m src.validation.audit_sample
.venv\Scripts\python -m src.processing.build_dataset
.venv\Scripts\python -m src.validation.validate_dataset
.venv\Scripts\python -m src.analysis.benchmark
.venv\Scripts\python -m pytest -q
.venv\Scripts\python scripts/check_repository.py
```
En Linux/macOS sustituir `.venv\Scripts\python` por `.venv/bin/python`. La muestra está incluida; este recorrido funciona sin descargar los 24 meses ni tener Databricks.

### Obtención de datos crudos
```powershell
.venv\Scripts\python -m src.ingestion.bts --year 2025 --month 1
```
Conserva el ZIP completo en `data/raw/bts/` y un manifiesto con URL, fecha y SHA256 en `data/raw/manifest.json`. Al reutilizarlo verifica hash y ZIP. Para regenerar la muestra añadir `--sample`.

La regeneración lee el CSV mensual completo en memoria antes de muestrear. La ingesta acepta un mes explícito por ejecución. Extenderla a un rango completo con memoria controlada es una tarea del equipo.

### Notebook
Abrir `notebooks/01_exploration.ipynb` en VS Code o Jupyter con el entorno anterior. Para Jupyter instalar `jupyterlab` e `ipykernel` en ese entorno. Los antecedentes conservan rutas y dependencias originales de Colab; no se ejecutan en CI.

## Cómo participa cada integrante
Comenzar por el [reparto de tareas](docs/team_workplan.md), la [guía de contribución](CONTRIBUTING.md) y el [registro de evidencias](docs/collaboration_log.md). [Issues publicados](https://github.com/diegogargo/datosmasivos_vuelos/issues).

## Documentación
- [Alcance](docs/project_scope.md), [fuentes](docs/data_sources.md) y [diccionario](docs/data_dictionary.md).
- [Arquitectura](docs/architecture.md), [validaciones](docs/validation.md), [benchmark](docs/benchmark.md) y [decisiones](docs/decisions.md).
- [Auditoría de originales](docs/notebook_audit.md), [Databricks](docs/databricks_setup.md) y [rúbrica de parciales](docs/rubric_checklist.md).
