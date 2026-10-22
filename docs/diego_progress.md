# Evidencia de Diego García con asistencia de Codex

Alcance final: enero 2024–diciembre 2025 completos. El EDA original y la muestra pública se conservan.

| Tarea | Avance comprobado | Pendiente |
|---|---|---|
| P1-01 / #1 | Verificador de procedencia ejecutado; 15 casos nuevos; PR #13 con revisión solicitada | Revisión de Jose Miguel y merge |
| P2-01 / #4 | Rango completo adquirido: 24 meses, 14,080,680 vuelos; ZIP/CSV, hashes, fechas, reanudación, bloqueo y pruebas verificados | Revisión del PR pendiente |
| P2-04 / #7 | Bronze Delta, contratos y ejecutor de CLI segura preparados y probados localmente | Piloto real: 539,747 filas, Spark 4.2.0; cierre de cobertura completa e idempotencia pendientes |
| P2-07 / #10 | Benchmark de 5,000 y 539,747 vuelos, cinco repeticiones y pico del proceso; guías publicadas en PR #16 | Silver/Gold del equipo, integración y reviews |

La suite local completa tiene 82 pruebas aprobadas en esta revisión. Esto no certifica ejecución Spark ni revisiones humanas. Los enlaces del workspace y estado de acceso quedan fuera de Git.

La repetición desde un `git archive` del commit público c5bc983, extraído en una carpeta nueva, pasó las 82 pruebas, el recorrido de muestra y la validación de metadatos de adquisición. Usó el entorno de dependencias existente, sin datos raw; sus límites y el hash intacto del notebook original están en `reports/tables/clean_reproduction.json`.

Diego todavía debe revisar un PR de Santiago cuando exista; no se registró una review ficticia. Los trabajos de Jose Miguel y Santiago permanecen a su cargo, con apoyo de sus respectivas sesiones de Codex. La asistencia de IA se declara en los PR.
