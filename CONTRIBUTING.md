# Guía para trabajar los tres en GitHub

## Acceso
Diego invita a `GUEVARA21` y `Skraeder` desde Settings → Collaborators → Add people. Cada uno acepta con su cuenta. Mientras no tengan permiso de escritura pueden abrir un PR desde un fork. Nunca compartir contraseñas o tokens.

## Una tarea y una rama por persona
1. Abrir el issue propio y comentar el plan y cómo se comprobará.
2. Actualizar la copia local y crear la rama indicada. Ejemplo de Diego:
```powershell
git switch main
git pull --ff-only
git switch -c diego/p1-01
```
3. Hacer cambios propios y usar el nombre/correo de la cuenta propia. El correo privado `noreply` se consulta en GitHub → Settings → Emails.
4. Guardar dos avances sustantivos; por ejemplo, decisión de alcance y actualización del diagrama:
```powershell
git add docs/project_scope.md
git commit -m "docs: precisar pregunta y límites temporales"
git add docs/architecture.md
git commit -m "docs: actualizar arquitectura del equipo"
git push -u origin diego/p1-01
```
5. GitHub → Pull requests → New pull request. Base `main`, compare la rama propia. Completar la plantilla y escribir `Closes #N` con el número real del issue.
6. Pedir revisión según el reparto: Jose Miguel revisa a Diego, Santiago a Jose Miguel y Diego a Santiago.

## Revisión real
Abrir el PR de la otra persona → Files changed → Start a review → Finish your review. Explicar hallazgos, pedir cambios cuando falte evidencia y aprobar después de comprobarlos. El autor no aprueba su propio PR.

Responder comentarios, actualizar la misma rama y combinar con CI correcto. Usar `Create a merge commit` si se desea conservar los commits individuales de trabajo. Registrar enlaces de issue, commits, PR y review en `docs/collaboration_log.md`.

## Integración
Cada PR necesita revisión de otra persona y CI correcto. Si el plan lo permite, proteger `main` con una aprobación y el check de CI; en otro caso aplicar la regla manualmente. Antes de activar un check obligatorio, confirmar su nombre en una ejecución real.

Si hay conflictos, incorporar `main` a la rama propia, resolverlos, volver a probar y explicar las decisiones en el PR. No provocar conflictos artificiales: documentar una integración real también aporta evidencia.

## Comprobaciones desde la raíz
```powershell
python -m pytest -q
python -m src.validation.audit_sample
python -m src.processing.build_dataset
python -m src.validation.validate_dataset
python scripts/check_repository.py
```
No subir ZIP BTS grandes, tablas completas, entornos virtuales ni claves. Subir muestra pequeña, código, documentación y salidas identificadas.

La base asistida no sustituye los requisitos individuales: P1, dos commits, un PR, una review y participación en un issue por integrante; P2, aporte técnico y otro documental o de validación, issues principales y PR revisados. No usar nombres prestados ni fraccionar cambios sin propósito para inflar el historial.
