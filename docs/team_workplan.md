# Reparto del trabajo del equipo

## Qué representa la primera carga
El repositorio parte del notebook original del equipo y de una base organizada con asistencia. La cuenta que subió los archivos no demuestra quién desarrolló cada parte antes de GitHub. Esa primera carga y esta planificación no sustituyen los aportes individuales.

El notebook original permanece intacto. Los resultados históricos guardados se distinguen de las ejecuciones nuevas. Cada integrante debe entender, ejecutar, modificar y documentar su módulo desde su propia cuenta.

## Responsabilidad completa por integrante
| Integrante | Módulo técnico principal | Entrega de calidad | Quién revisa su PR | A quién le toca revisar |
|---|---|---|---|---|
| Diego / `diegogargo` | Procedencia, adquisición de 24 meses del pipeline (2024–2025) y Bronze | Pruebas de ingesta, manifiestos, benchmark e integración | Jose Miguel | Santiago |
| Jose Miguel / `GUEVARA21` | Calidad, Silver y dos variables históricas | Pruebas de reglas, tiempo y consistencia entre capas | Santiago | Diego |
| Santiago / `Skraeder` | EDA reutilizable, Gold y estacionalidad | Pruebas de agregados, interpretación y evaluación preliminar si corresponde | Diego | Jose Miguel |

Todos entregan código, pruebas, documentación y revisión. Tener cuatro issues por persona no garantiza igual esfuerzo: si un módulo crece, registrar el ajuste de alcance y apoyo en el issue. El modelo adicional lo lidera Santiago con apoyo de los otros dos en disponibilidad de datos y reproducción; primero se confirma qué pidió el profesor.

## Primer parcial: los tres pueden comenzar ahora
La muestra incluida permite trabajo técnico independiente sin esperar a Databricks.

| Persona | Tarea inicial | Cambio propio que todavía falta | Rama |
|---|---|---|---|
| Diego | [#1: procedencia](https://github.com/diegogargo/datosmasivos_vuelos/issues/1) | Verificar periodo, metadatos y equivalencia CSV/Parquet mediante un módulo y pruebas | `diego/p1-01` |
| Jose Miguel | [#2: calidad](https://github.com/diegogargo/datosmasivos_vuelos/issues/2) | Añadir reglas de HHMM de llegada, número de vuelo y valores no finitos, con errores inyectados | `jose_miguel/p1-02` |
| Santiago | [#3: EDA](https://github.com/diegogargo/datosmasivos_vuelos/issues/3) | Extraer métricas del notebook a funciones y un comando probado, con hallazgos propios | `santiago/p1-03` |

Las ramas iniciales se preparan desde la misma base. Crear la rama no cuenta como contribución. Dos commits deben representar avances sustantivos: por ejemplo, módulo con pruebas y documentación basada en resultados. Cada uno abre un PR propio, responde comentarios y realiza una review al PR que le corresponde. [Guía común](../CONTRIBUTING.md).

## Segundo parcial: módulos conectados
| Responsable | Issues | Resultado |
|---|---|---|
| Diego | [#4](https://github.com/diegogargo/datosmasivos_vuelos/issues/4), [#7](https://github.com/diegogargo/datosmasivos_vuelos/issues/7), [#10](https://github.com/diegogargo/datosmasivos_vuelos/issues/10) | Ingesta de volumen completo, workspace/Bronze e integración con mediciones de escala |
| Jose Miguel | [#5](https://github.com/diegogargo/datosmasivos_vuelos/issues/5), [#8](https://github.com/diegogargo/datosmasivos_vuelos/issues/8), [#11](https://github.com/diegogargo/datosmasivos_vuelos/issues/11) | Silver, dos tasas históricas con disponibilidad verificable y validación completa |
| Santiago | [#6](https://github.com/diegogargo/datosmasivos_vuelos/issues/6), [#9](https://github.com/diegogargo/datosmasivos_vuelos/issues/9), [#12](https://github.com/diegogargo/datosmasivos_vuelos/issues/12) | Gold/estacionalidad, modelo adicional del alcance confirmado y EDA de datos completos |

Orden de ejecución: ingesta y primer mes Bronze → Silver → Gold y variables históricas → validación, análisis e integración → expansión y mediciones de los 24 meses del pipeline (2024–2025). Las dependencias y criterios completos están en cada issue y en [la configuración de tareas](../config/github_tasks.json). Los contratos pueden acordarse mientras se prepara el workspace; la prueba final exige datos y tablas reales.

## Guía individual
- [Diego: por dónde empezar y qué entregar](team/diego.md).
- [Jose Miguel: por dónde empezar y qué entregar](team/jose_miguel.md).
- [Santiago: por dónde empezar y qué entregar](team/santiago.md).

## Acceso y cierre
Las invitaciones fueron aceptadas y se verificó permiso de escritura de `GUEVARA21` y `Skraeder`. Las 12 tareas se asignan a sus responsables en GitHub. Cada persona trabaja con su cuenta y su rama.

Al terminar, registrar enlaces reales en [collaboration_log.md](collaboration_log.md). No se cierran issues ni se marcan requisitos individuales solo porque la base ya tenga archivos similares. Informe y presentación siguen reservados para la entrega final.

El EDA inicial de 2024–2025 permanece como antecedente. El pipeline se amplía a enero 2024–diciembre 2025 por elección de Diego. La separación temporal de evaluación deberá acordarse antes de modelar y reconocer los periodos ya explorados; no llamar prueba intacta a datos revisados en el EDA.
