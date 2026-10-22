# Santiago: módulo de análisis y Gold

Cuenta: `Skraeder`. Diego revisa tus PR. A ti te corresponde revisar los PR de Jose Miguel. Tu primera tarea es [#3](https://github.com/diegogargo/datosmasivos_vuelos/issues/3).

## Primer parcial: trabajo propio concreto
El notebook original del equipo conserva el EDA, pero falta un módulo de análisis reutilizable. Crear `src/analysis/eda.py` y `tests/test_analysis.py` a partir de esas reglas; el original se mantiene intacto.

El nuevo módulo debe producir tablas con volumen, vuelos elegibles y tasa de retraso por hora programada, aerolínea y aeropuerto. Siempre mostrar el denominador y señalar grupos pequeños según una regla documentada. Incluir un comando que lea la muestra y exporte tablas pequeñas con procedencia.

Probar cancelados con retraso reportado, grupos sin vuelos elegibles, grupos pequeños y HHMM=2400. Contrastar enero con 5,000 totales, 4,836 elegibles y 896 retrasos. Actualizar el notebook portable para llamar a las funciones y reducir lógica duplicada.

Redactar `docs/eda_findings.md` con al menos tres hallazgos y dos limitaciones propios. Separar resultados de la muestra nueva y salidas históricas guardadas; la correlación 0.711 del original no representa una nueva ejecución. Los resultados de dos años no justifican elegir meses de estacionalidad usando el conjunto de prueba.

## Rama, commits y PR
La invitación ya fue aceptada y se verificó tu permiso de escritura. Desde tu copia del repositorio:
```powershell
git fetch origin
git switch --track origin/santiago/p1-03
```
Si ya existe localmente, usar `git switch santiago/p1-03`.

Guardar un avance con funciones y pruebas y otro con interpretación, tablas o integración del notebook. Ejecutar:
```powershell
python -m pytest -q
python -m src.validation.audit_sample
python scripts/check_repository.py
```
Ejecutar además el comando nuevo de EDA y el notebook portable. Abrir PR hacia `main` con `Closes #3`, resultados e interpretación. Solicitar revisión de Diego y responder comentarios. Revisar el PR de Jose Miguel y enviar una review desde tu cuenta.

## Segundo parcial
- [#6](https://github.com/diegogargo/datosmasivos_vuelos/issues/6): Gold, agregados conciliados y estacionalidad estimada exclusivamente con entrenamiento.
- [#9](https://github.com/diegogargo/datosmasivos_vuelos/issues/9): modelo preliminar del alcance confirmado con el profesor. Jose Miguel apoya la verificación temporal de datos y Diego la reproducción; las extensiones avanzadas no se agregan automáticamente al parcial.
- [#12](https://github.com/diegogargo/datosmasivos_vuelos/issues/12): ejecutar EDA sobre Gold real e integrar evidencias de los tres.

Tu entrega incluye código de análisis, pruebas, datos preparados, interpretación y revisión de otro integrante. Informe y presentación se reservan para la entrega final.
