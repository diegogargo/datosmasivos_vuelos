# Evidencia de Diego García con asistencia de Codex

Alcance final: enero 2024–diciembre 2025 completos. El EDA original y la muestra pública se conservan.

| Tarea | Avance comprobado | Pendiente |
|---|---|---|
| P1-01 / #1 | Verificador de procedencia ejecutado; 15 casos nuevos; PR #13 con revisión solicitada | Revisión de Jose Miguel y merge |
| P2-01 / #4 | Rango completo adquirido: 24 meses, 14,080,680 vuelos; ZIP/CSV, hashes, fechas, reanudación, bloqueo y pruebas verificados | Revisión del PR pendiente |
| P2-04 / #7 | Bronze Delta completo: 24 meses, 14,080,680 filas, Spark 4.2.0; enero 2025 reemplazado sin duplicar sus 539,747 filas | Revisión del PR e integración del equipo |
| P2-07 / #10 | Benchmark de 5,000 y 539,747 vuelos, cinco repeticiones y pico del proceso; guías publicadas en PR #16 | Silver/Gold del equipo, integración y reviews |

La última suite propia completó 82 pruebas en 3.73 segundos. También pasó `scripts/check_delivery.py --full-acquisition`: procedencia, muestra, procesamiento, estructura y hashes de todos los originales del periodo. Los reportes actualizados conservan `team_integration_complete=false` porque faltan Silver/Gold. Las pruebas locales no sustituyen los reportes de Spark ni revisiones humanas. Los enlaces privados del workspace quedan fuera de Git.

La repetición desde un `git archive` del commit público c5bc983, extraído en una carpeta nueva, pasó las 82 pruebas, el recorrido de muestra y la validación de metadatos de adquisición. Usó el entorno de dependencias existente, sin datos raw; sus límites y el hash intacto del notebook original están en `reports/tables/clean_reproduction.json`.

Los issues [#1](https://github.com/diegogargo/datosmasivos_vuelos/issues/1), [#4](https://github.com/diegogargo/datosmasivos_vuelos/issues/4), [#7](https://github.com/diegogargo/datosmasivos_vuelos/issues/7) y [#10](https://github.com/diegogargo/datosmasivos_vuelos/issues/10) ya reflejan estos avances y sus pendientes. Se mantienen abiertos; los PR #13, #14 y #15 están listos para revisión de Jose Miguel, y #16 permanece draft hasta la integración completa. Al comprobar los cuatro PR no había reviews publicadas.

Diego todavía debe revisar un PR de Santiago cuando exista; no se registró una review ficticia. El usuario pidió cerrar primero el trabajo de Diego: el borrador asistido de los demás queda guardado localmente en `equipo/pipeline-completo`, sin publicar ni atribuir aportaciones a sus cuentas. La asistencia de IA se declara en los PR.
