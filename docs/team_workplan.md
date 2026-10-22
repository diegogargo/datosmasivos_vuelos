# Reparto y orden de trabajo

Las tareas están preparadas, no realizadas ni aprobadas por los integrantes. Cuatro tareas por persona: una del primer parcial y tres del segundo. Todos tendrán trabajo técnico, documentación y revisiones.

| Tarea | Responsable | Revisa | Resultado |
|---|---|---|---|
| [P1-01](https://github.com/diegogargo/datosmasivos_vuelos/issues/1) | @diegogargo | @GUEVARA21 | Validar alcance, arquitectura y organización |
| [P1-02](https://github.com/diegogargo/datosmasivos_vuelos/issues/2) | @GUEVARA21 | @Skraeder | Revisar fuente, diccionario y calidad de la muestra |
| [P1-03](https://github.com/diegogargo/datosmasivos_vuelos/issues/3) | @Skraeder | @diegogargo | Reproducir y comentar el EDA del equipo |
| [P2-01](https://github.com/diegogargo/datosmasivos_vuelos/issues/4) | @diegogargo | @GUEVARA21 | Extender ingesta reproducible a los 24 meses |
| [P2-02](https://github.com/diegogargo/datosmasivos_vuelos/issues/5) | @GUEVARA21 | @Skraeder | Implementar Silver en PySpark con contrato temporal |
| [P2-03](https://github.com/diegogargo/datosmasivos_vuelos/issues/6) | @Skraeder | @diegogargo | Implementar Gold y agregados trazables |
| [P2-04](https://github.com/diegogargo/datosmasivos_vuelos/issues/7) | @diegogargo | @GUEVARA21 | Crear workspace y ejecutar Bronze en Databricks |
| [P2-05](https://github.com/diegogargo/datosmasivos_vuelos/issues/8) | @GUEVARA21 | @Skraeder | Diseñar tasas históricas sin fuga de información |
| [P2-06](https://github.com/diegogargo/datosmasivos_vuelos/issues/9) | @Skraeder | @diegogargo | Validar el modelo preliminar solicitado por el profesor |
| [P2-07](https://github.com/diegogargo/datosmasivos_vuelos/issues/10) | @diegogargo | @GUEVARA21 | Integrar CI, benchmark y reproducción del segundo parcial |
| [P2-08](https://github.com/diegogargo/datosmasivos_vuelos/issues/11) | @GUEVARA21 | @Skraeder | Validar capas completas y ampliar pruebas de calidad |
| [P2-09](https://github.com/diegogargo/datosmasivos_vuelos/issues/12) | @Skraeder | @diegogargo | Actualizar EDA y evidencias desde Gold |

## Para comenzar
1. Diego invita a `Skraeder` y `GUEVARA21` en Settings → Collaborators. Ambos aceptan. Mientras tanto pueden usar un fork.
2. Cada persona toma su tarea P1, comenta su plan en el issue y crea la rama indicada.
3. Hace dos commits con cambios reales, abre PR y solicita revisión.
4. Jose Miguel revisa a Diego; Santiago revisa a Jose Miguel; Diego revisa a Santiago. Usar Files changed y enviar una review con observaciones reales.
5. Responder comentarios, combinar con CI correcto y registrar enlaces en collaboration_log.md.
6. Continuar P2 según dependencias: workspace, un mes de Bronze, Silver/Gold y después los 24 meses.

No usar nombres prestados ni aprobar desde la cuenta de otro. La preparación inicial asistida no acredita participación individual.

Los criterios y ramas están en [github_tasks.json](../config/github_tasks.json). Los enlaces publicados se guardan en [github_issues.json](../reports/tables/github_issues.json).

## Asignación publicada
Se crearon los 12 issues. Los cuatro de Diego están asignados en GitHub. Los de Jose Miguel y Santiago identifican responsable y revisor en el cuerpo, pero GitHub no permitió asignarlos porque todavía falta acceso de colaboradores. Tras aceptar las invitaciones, asignar los ocho issues restantes según el reparto.
