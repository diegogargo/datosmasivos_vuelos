# Jose Miguel: módulo de calidad y Silver

Cuenta: `GUEVARA21`. Santiago revisa tus PR. A ti te corresponde revisar los PR de Diego. Tu primera tarea es [#2](https://github.com/diegogargo/datosmasivos_vuelos/issues/2).

## Primer parcial: trabajo propio concreto
La auditoría de muestra ya existe, pero tiene reglas pendientes. Ampliar `src/validation/audit_sample.py`, reutilizar las funciones de `src/processing/contracts.py` y agregar pruebas en `tests/test_validation.py`.

Cambios concretos:
- Validar `CRSArrTime` como HHMM. Debe aceptar 2400 según el contrato y detectar valores como 1260.
- Comprobar que el número de vuelo sea entero y positivo; documentar qué campos permiten nulos.
- Detectar `DepDelay` infinito en vuelos operados y definir reglas de valores finitos en otros campos numéricos.
- Conservar nulos estructurales, cancelados sin etiqueta y retrasos negativos válidos.

Construir casos pequeños con errores conocidos. Mostrar qué no detectaba la versión inicial y qué detecta tu cambio; también probar que la muestra válida sigue pasando. Actualizar diccionario y validaciones con explicación propia de las reglas.

## Rama, commits y PR
La invitación ya fue aceptada y se verificó tu permiso de escritura. Desde tu copia del repositorio:
```powershell
git fetch origin
git switch --track origin/jose_miguel/p1-02
```
Si ya existe localmente, usar `git switch jose_miguel/p1-02`.

Guardar un avance con reglas y pruebas, y otro con documentación y resultados. Ejecutar desde la raíz:
```powershell
python -m pytest -q
python -m src.validation.audit_sample
python -m src.processing.build_dataset
python -m src.validation.validate_dataset
```
Si agregas comprobaciones, actualizar los conteos descritos en la documentación. Abrir PR hacia `main` con `Closes #2`, casos probados y resultados. Solicitar revisión de Santiago y responder sus comentarios. Revisar también el PR de Diego desde Files changed y enviar una review real.

## Segundo parcial
- [#5](https://github.com/diegogargo/datosmasivos_vuelos/issues/5): Silver en PySpark, reglas de dominio, zonas horarias, duplicados y evidencia Delta.
- [#8](https://github.com/diegogargo/datosmasivos_vuelos/issues/8): dos tasas históricas de 28 días con pruebas de disponibilidad al corte de tres horas. BTS mensual no equivale a resultados disponibles en vivo.
- [#11](https://github.com/diegogargo/datosmasivos_vuelos/issues/11): conciliar calidad y conteos entre Bronze, Silver y Gold.

Tu módulo incluye transformación técnica, pruebas de errores y documentación. No basta con ejecutar la auditoría preparada: la tarea exige implementar las reglas pendientes y demostrar su efecto con evidencia propia.
