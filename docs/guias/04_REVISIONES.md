# Cómo hacer las revisiones y cerrar los PR

Una rama contiene cambios; un commit guarda un avance; un PR propone integrarlos; una review evalúa el PR de otra persona; merge integra cambios. No necesitan programar manualmente para que el trabajo sea asistido por Codex, pero deben comprender lo que publican.

## 1. Quién revisa a quién

| Revisor | Autor que debe revisar | Primer trabajo |
|---|---|---|
| Jose Miguel / GUEVARA21 | Diego / diegogargo | PR #13, issue #1 |
| Santiago / Skraeder | Jose Miguel / GUEVARA21 | PR del issue #2 |
| Diego / diegogargo | Santiago / Skraeder | PR del issue #3 |

Cada persona inicia sesión con su cuenta. No usar otra cuenta para simular una revisión independiente.

## 2. Prompt de revisión para copiar a su Codex

```text
Revisa el PR que me corresponde según docs/guias/04_REVISIONES.md. Comprueba mi identidad GitHub antes de publicar. Busca el PR real del autor y del issue asignados; si no existe, dilo y deja la revisión pendiente. No inventes su número ni un comentario.

Lee el diff completo, los criterios del issue y CONTRIBUTING. Comprueba datos de entrada, denominadores, nulos, casos límite, ausencia de fugas temporales, preservación del original y límites declarados. Reproduce pruebas en una copia aislada o worktree sin modificar mi trabajo activo. Si propones crear un worktree, prepáralo solo dentro de la copia del proyecto y conserva cambios existentes.

Prepara una revisión con qué comprobaste, comandos/resultados, hallazgos con archivo/línea y una recomendación fundada. Publica observaciones concretas en mi cuenta si están respaldadas por la revisión. No apruebes automáticamente ni emitas una aprobación que yo no haya revisado. Muéstrame el resultado para que pueda confirmar mi evaluación. Declara que la revisión fue asistida por Codex.

Si hay problemas importantes, solicita cambios con una forma de reproducirlos. Si las comprobaciones pasan y no hay hallazgos, explica la evidencia y los límites; no inventes problemas ni garantías. Una revisión automática adicional de un bot no sustituye mi participación individual.
```

## 3. Qué hace la persona en GitHub

1. Abrir el enlace del PR.
2. Revisar **Files changed** y la explicación preparada por Codex.
3. Entrar a **Review changes** y publicar la evaluación que realmente corresponda: comentario, cambios solicitados o aprobación. Si Codex la publica con autorización, comprobar que aparece bajo la cuenta correcta.
4. El autor responde a las observaciones y hace nuevos commits si son necesarios.
5. Comprobar CI del último commit. Una CI anterior no demuestra que el último cambio pasó.
6. Integrar cuando la revisión y los criterios estén satisfechos. Conservar el historial requerido por la rúbrica; la guía del repo recomienda merge commit para no ocultar los avances.

## 4. PR apilados de Diego

El PR #14 parte de la rama del #13 y el #15 parte de la rama del #14. El PR de integración parte del #15. No integrar el último saltándose los anteriores. Después de integrar un PR, pedir a Codex cambiar la base del siguiente a main, resolver diferencias reales y volver a comprobar CI. No usar force push ni borrar trabajo de compañeros para resolver conflictos.

## 5. Cómo acreditar los parciales

P1: cada integrante debe tener al menos dos commits sustantivos, su PR, una revisión al compañero y participación en issues. P2: código técnico más documentación o validación, PR revisados e integración real. Registrar los enlaces en docs/collaboration_log.md. Si un punto sigue pendiente, debe seguir marcado como pendiente.
