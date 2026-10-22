# Diego: módulo de adquisición y Bronze

Cuenta: `diegogargo`. Jose Miguel revisa tus PR. A ti te corresponde revisar los PR de Santiago. Tu primera tarea es [#1](https://github.com/diegogargo/datosmasivos_vuelos/issues/1).

## Primer parcial: trabajo propio concreto
La auditoría actual comprueba el SHA256 del CSV, pero falta un verificador de procedencia que relacione CSV, Parquet, manifiesto y periodo esperado.

Crear `src/ingestion/validate_provenance.py` y `tests/test_provenance.py`. El módulo debe comprobar ambos hashes, conteos, columnas y fechas del periodo y verificar que los dos formatos contienen la misma información. Definir tolerancia para diferencias numéricas de serialización. Guardar un reporte pequeño y devolver error si la comprobación falla.

Probar un periodo incorrecto, un conteo alterado, contenido diferente entre formatos y un hash falso. No modificar el original para construir estas pruebas: usar copias temporales o casos de prueba.

Actualizar `docs/data_sources.md` y `docs/project_scope.md` con lo que verificaste. Diferenciar la muestra actual de 5,000 filas, los resultados históricos de 120,000 y los aproximadamente 14.08 millones de registros originales reportados en los logs guardados.

## Rama, commits y PR
Desde una copia del repositorio con dependencias instaladas:
```powershell
git fetch origin
git switch --track origin/diego/p1-01
```
Si la rama local ya existe, usar `git switch diego/p1-01`. El repositorio está en `outputs/vuelos-datos-masivos` en la copia de Diego; las instrucciones se ejecutan desde su raíz.

Guardar un avance funcional con pruebas y otro avance de documentación basada en resultados. Antes del PR ejecutar:
```powershell
python -m pytest -q
python -m src.validation.audit_sample
python scripts/check_repository.py
```
Añadir también el comando de tu nuevo verificador una vez implementado. Subir la rama y abrir PR hacia `main` con `Closes #1`, descripción del cambio y resultados. Solicitar revisión a Jose Miguel. No aprobar tu propio PR ni dar por cumplida su review antes de que él la envíe.

## Segundo parcial
- [#4](https://github.com/diegogargo/datosmasivos_vuelos/issues/4): ingesta explícita y reanudable de 24 meses, memoria controlada y trazabilidad.
- [#7](https://github.com/diegogargo/datosmasivos_vuelos/issues/7): workspace y Bronze, empezando con un mes completo. Cada persona usa su identidad; verificar permisos y opciones de colaboración antes de elegir la edición.
- [#10](https://github.com/diegogargo/datosmasivos_vuelos/issues/10): integrar los módulos de los tres y medir escala con resultados equivalentes.

Tu entrega incluye código de ingesta, pruebas, manifiestos, documentación y mediciones propias. La subida inicial y esta guía son preparación asistida; la evidencia de tu tarea comienza con los cambios, ejecución y revisiones que realmente realices.
