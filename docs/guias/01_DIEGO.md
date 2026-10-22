# Diego García — diegogargo

Lee primero `00_EMPEZAR_AQUI.md`. Tus revisiones las hace Jose Miguel (`GUEVARA21`). Tú revisas los PR de Santiago (`Skraeder`).

## 1. Qué ya está hecho

- P1-01, issue #1: verificador CSV/Parquet/manifiesto, pruebas y [PR #13](https://github.com/diegogargo/datosmasivos_vuelos/pull/13).
- P2-01, issue #4: ingesta por rango y [PR #14](https://github.com/diegogargo/datosmasivos_vuelos/pull/14). Descarga de 24 meses completa: 14,080,680 filas; 709,735,704 bytes ZIP y 6,370,981,019 bytes CSV, fuera de Git.
- P2-04, issue #7: Bronze y ejecutor en [PR #15](https://github.com/diegogargo/datosmasivos_vuelos/pull/15). Ejecución completa de los 24 meses: 14,080,680 filas, Spark 4.2.0. Enero 2025 se reemplazó después del piloto y conservó 539,747 filas, sin duplicarse. Reportes reales en `reports/tables/databricks_bronze_result.json` y `databricks_bronze_validation.json`.
- P2-07, issue #10: benchmark real de muestra y mes completo, verificación de cobertura e inicio del recorrido de integración. La integración depende de Silver y Gold.

No vuelvas a empezar estos módulos ni regeneres el notebook original. Tus datos ya están en la copia de trabajo existente de Codex.

## 2. Prompt para continuar tu Codex

Copia todo este bloque en el chat de Codex que tiene abierto el repositorio:

```text
Soy Diego García, usuario GitHub diegogargo. Continúa mi parte del repositorio https://github.com/diegogargo/datosmasivos_vuelos. Trabaja en mi copia existente, preserva los datos y los cambios de los demás y comprueba la identidad antes de publicar. No reinicies el proyecto ni fabriques aportes de Jose Miguel o Santiago.

Lee README.md, config/project.yaml, docs/guias/00_EMPEZAR_AQUI.md, docs/team/diego.md, docs/bronze_contract.md y mis issues #1, #4, #7 y #10. Alcance definitivo: enero 2024 a diciembre 2025, 24 meses completos. El EDA y la muestra son una parte distinta del volumen completo.

Comprueba los PR #13, #14, #15 y #16. No dupliques ramas o PR. Se prepararon cambios con Codex y la asistencia debe seguir declarada. Verifica revisión de GUEVARA21, CI y los reportes reales antes de marcar algo completo.

Verifica reports/tables/acquisition_full.json y acquisition_validation.json: 24 meses y 14,080,680 filas. Confirma hashes de los archivos locales si hace falta, sin descargarlos de nuevo cuando la caché sea válida. No subas data/raw, data/interim, data/processed ni credenciales a GitHub.

Comprueba el reporte actual de Databricks, sus campos start/end/months/rows/complete y la evidencia privada local sin publicar el host o datos de la cuenta. Ya terminó Bronze 2024-01 a 2025-12 con 14,080,680 filas; verifica la evidencia y no repitas la carga completa sin necesidad. Un piloto aislado no probaría los 24 meses. Existe scripts/run_databricks.py, usa el perfil seguro vuelos. Si Windows impide usar el almacén seguro desde el sandbox, prepara un único comando para mi PowerShell; no cambies a tokens en texto plano. Ante un fallo recupera el diagnóstico real y corrige la causa. El ejecutor ya tiene --diagnose-run y --resume.

Conserva Bronze con todos los campos originales y metadatos. Su tabla es workspace.bronze.vuelos_raw. Usa CREATE TABLE mediante SQL: el alias errorifexists falló en Spark Connect y ya se corrigió. Conserva reemplazo mensual e idempotencia.

Después de las revisiones, integra los módulos reales de Jose Miguel y Santiago. Sus contratos están en sus guías: run_silver, run_historical_features y run_gold. Añade su ejecución al orquestador solo cuando existan, conserva sus autores y prueba la integración. No escribas sus aportaciones bajo otra identidad. Incorpora todos los notebooks de notebooks/databricks al cargador cuando lleguen esos módulos.

Ejecuta pruebas y el recorrido local desde copia limpia; conserva benchmark de 5,000 y 539,747 vuelos, repeticiones, equivalencia y definición de memoria. No compares esos tiempos como si fueran Spark. Actualiza checklist, arquitectura, decisiones y colaboración con enlaces reales. Resuelve conflictos solo si ocurren.

Revisa el PR de Santiago para #3 cuando exista. Analiza código y pruebas antes de redactar una review; no apruebes por compromiso. Si hay hallazgos, publícalos con ubicación y forma de reproducirlos. No registres revisiones inexistentes.

Completa lo que puedas ejecutar y publicar en mi cuenta; deja claramente identificados los puntos bloqueados por módulos faltantes, cuota o acceso. No prepares informe o presentación final y no prometas una calificación.
```

## 3. Comandos de tu copia actual

Abre en el terminal la raíz del repositorio: la carpeta que contiene README.md, config, src y tests. En la copia original de esta sesión, el entorno y la CLI están dos carpetas arriba, en `work`. Estos comandos se ejecutan desde esa raíz:

```powershell
git status --short --branch
..\..\work\env\Scripts\python.exe scripts/check_delivery.py --full-acquisition
```

Si estás usando otra copia, pide a Codex localizar o crear su entorno; no ejecutes rutas relativas de una copia diferente.

### Piloto, solo si necesitas repetirlo

```powershell
..\..\work\env\Scripts\python.exe scripts/run_databricks.py --cli ..\..\work\tools\databricks.exe --profile vuelos --execute
```

Si ya se preparó el entorno y se transfirió exactamente ese mes, para reintentar después de una corrección:

```powershell
..\..\work\env\Scripts\python.exe scripts/run_databricks.py --cli ..\..\work\tools\databricks.exe --profile vuelos --execute --resume
```

### Los 24 meses completos

La carga completa ya terminó. Este comando queda como referencia para reproducirla si se necesita; no ejecutarlo otra vez solo para continuar con las guías. Consultar el reporte y el progreso local primero.

```powershell
..\..\work\env\Scripts\python.exe scripts/run_databricks.py --cli ..\..\work\tools\databricks.exe --profile vuelos --start 2024-01 --end 2025-12 --execute
```

`--resume` omite transferencia de datos y preparación; por eso no sirve para saltar de un mes transferido a 24 meses que aún no están en el Volume.

## 4. Comprobar Bronze en Databricks

1. Abrir el workspace propio de Diego.
2. Entrar a Workspace → carpeta del usuario → `datosmasivos_vuelos_diego` → `notebooks/databricks`.
3. Abrir el notebook del proyecto o crear un notebook Python de comprobación en esa carpeta.
4. Pegar y ejecutar este bloque:

```python
spark.sql('SELECT _source_period, COUNT(*) AS vuelos FROM workspace.bronze.vuelos_raw GROUP BY _source_period ORDER BY _source_period').show(30, truncate=False)
print('Total Bronze:', spark.table('workspace.bronze.vuelos_raw').count())
print('Spark:', spark.version)
```

Para los 24 meses, el total esperado es 14,080,680 y deben aparecer todos los meses de 2024-01 a 2025-12. Repetir enero 2025 debe conservar 539,747 filas en ese mes, sin duplicarlas.

## 5. Incorporar los módulos de tus compañeros

1. Espera el PR de Jose Miguel para Silver y revisa que Santiago lo haya evaluado.
2. Espera el PR de Santiago para Gold y revísalo tú con pruebas.
3. Después de integrar los PR, pedir a tu Codex actualizar el cargador para transferir los nuevos archivos y notebooks.
4. Ejecutar primero un mes de Bronze → Silver → históricos → Gold. Las guías de ellos tienen los bloques y firmas exactas.
5. Conciliar: Bronze = Silver aceptados + cuarentena + exclusiones explicadas; Gold debe conciliar con Silver y sus denominadores.
6. Escalar al periodo completo y descargar al repositorio los reportes pequeños reales. No copiar resultados históricos como si fueran una ejecución nueva.

## 6. Qué debes poder mostrar

- PR #13 revisado por Jose Miguel y CI correcta.
- PR #14 con reporte de 24 meses, hashes y conteos nuevos.
- PR #15 con evidencia real de Bronze, versiones y reejecución.
- Benchmark muestra/mes completo con tiempo, memoria y equivalencia.
- Review tuya al PR de Santiago y respuestas a observaciones de tus PR.
- Integración real después de que Silver y Gold existan. Mientras falten, P2-07 permanece pendiente de esa parte.
