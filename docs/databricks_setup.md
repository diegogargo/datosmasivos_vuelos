# Databricks: preparación y ejecución de Diego

## Estado comprobado
Diego mostró un workspace de **Free Edition**. El perfil `vuelos` quedó autenticado mediante la CLI oficial. La captura y el perfil no demuestran aún una carga Delta: confirmar el resultado de la ejecución en `reports/tables/databricks_bronze_result.json`.

El entorno aislado de Codex no puede usar el almacén seguro de Windows. El ejecutor se lanza desde PowerShell del integrante y conserva ese mecanismo de autenticación. No solicita ni imprime tokens y no cambia su almacenamiento. Los enlaces privados quedan en `data/raw/databricks_runs_private.json`, excluido de Git. El repositorio público no contiene la dirección del workspace.

## Ejecución automatizada
1. Instalar la [CLI oficial](https://docs.databricks.com/aws/en/dev-tools/cli/install) y autenticar el perfil con `databricks auth login --profile vuelos --configure-serverless`. Completar personalmente el inicio de sesión.
2. Instalar las dependencias locales del repositorio. Adquirir un mes con `python -m src.ingestion.bts --year 2025 --month 1`, o el periodo configurado mediante `python -m src.ingestion.acquire_range --execute`.
3. Consultar `python scripts/run_databricks.py`. No modifica el workspace hasta añadir `--execute`.
4. Ejecutar `python scripts/run_databricks.py --profile vuelos --execute`. Si la CLI no está en PATH, añadir `--cli RUTA_DEL_EJECUTABLE`. El catálogo propuesto es `workspace`; el programa comprueba que esté disponible. Elegir otro con `--catalog NOMBRE_REAL` cuando corresponda.
5. El ejecutor carga el código en una carpeta propia del usuario, ejecuta `00_setup`, transfiere el ZIP de enero 2025 y su manifiesto, y ejecuta `01_bronze`. Crea los esquemas del proyecto y un Volume, conserva todos los campos y concilia los conteos. No modifica notebooks anteriores.
6. Esperar `BRONZE CORRECTO` y comprobar el reporte, Spark, periodo y conteos. Repetir el mismo mes para comprobar que el volumen no se duplica.
7. Para los dos años completos, con los 24 ZIP ya adquiridos: `python scripts/run_databricks.py --profile vuelos --start 2024-01 --end 2025-12 --execute`. Se transfieren ZIP y manifiesto; el CSV idéntico se reconstruye por bloques en el Volume y se coteja con el hash adquirido localmente.

La carga funciona por meses y `replaceWhere` sustituye únicamente el mes correspondiente. Una interrupción puede dejar meses anteriores completados; volver a ejecutar el rango es seguro para los conteos. Una revisión de BTS que cambie un original requiere decisión explícita y no se mezcla silenciosamente con el CSV anterior.

## Capacidad y colaboración
[Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition) usa cómputo serverless y tiene [cuotas y restricciones](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations). Validar un mes antes de ampliar; no se promete que los 24 meses quepan en una cuota diaria. El ejecutor no contrata planes ni amplía recursos de pago.

Cada integrante conserva su propia identidad. Verificar opciones de acceso y colaboración de la edición real; si trabajan en workspaces separados, GitHub transmite el código y cada cuenta ejecuta sus capas con sus archivos. No compartir credenciales. Silver pertenece a Jose Miguel y Gold a Santiago.

## Evidencia que aún debe verificarse
- Catálogo, permisos de Volume y primera ejecución real.
- Conteos originales y Bronze de cada mes, versión Spark y versión Delta.
- Reejecución de un mes sin duplicación y cobertura completa 2024–2025.
- Ejecución posterior de Silver/Gold e integración de sus PR revisados.

Referencia: [archivos en Volumes](https://docs.databricks.com/aws/en/volumes/volume-files) y [sobrescritura selectiva Delta](https://docs.databricks.com/aws/en/delta/selective-overwrite).
