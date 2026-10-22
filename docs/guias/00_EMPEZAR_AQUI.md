# Empiecen aquí: proyecto de vuelos, primer y segundo parcial

Esta guía se lee primero. Después cada integrante abre únicamente su guía personal. El objetivo es que Codex haga el trabajo técnico y ustedes intervengan para iniciar sesión, revisar resultados y explicar su parte.

## 1. Las tres cuentas y el proyecto correcto

| Persona | Cuenta GitHub | Guía |
|---|---|---|
| Diego García | diegogargo | 01_DIEGO.md |
| Jose Miguel Guevara | GUEVARA21 | 02_JOSE_MIGUEL.md |
| Santiago Roldán | Skraeder | 03_SANTIAGO.md |

Repositorio único: https://github.com/diegogargo/datosmasivos_vuelos

Las guías nuevas están publicadas en [docs/guias de la rama diego/p2-07](https://github.com/diegogargo/datosmasivos_vuelos/tree/diego/p2-07/docs/guias), dentro del [PR #16](https://github.com/diegogargo/datosmasivos_vuelos/pull/16). Hasta que ese PR se integre, pueden no aparecer en main. Abran esa ruta en GitHub o usen las copias del ZIP para copiar los prompts. Sus primeras ramas P1 parten de main: no copien a sus PR los cambios de Diego para conseguir las guías. En P2, incorporar la base del pipeline después de su revisión e integración.

No creen otro repositorio ni otro proyecto de vuelos. El notebook de partida es `notebooks/antecedentes/Proyecto_Notebook_original.ipynb`, que permanece intacto. El EDA usa una muestra; el pipeline usa los **24 meses completos de enero 2024 a diciembre 2025**. La adquisición nueva tiene **14,080,680 vuelos**. La muestra pública de enero 2025 tiene 5,000 filas. Las salidas históricas de 120,000 filas no son un archivo recuperado ni el total de vuelos.

## 2. Conectar ChatGPT y Codex a GitHub

1. Cada integrante inicia sesión en su propia cuenta de ChatGPT.
2. Abrir **Plugins**, buscar **GitHub**, abrir su ficha e instalarlo con el botón de añadir. Si solicita conexión, elegir conectar e iniciar sesión en la cuenta GitHub de la tabla.
3. Revisar la cuenta que aparece antes de autorizar. Cuando permita seleccionar repositorios, conceder acceso a `diegogargo/datosmasivos_vuelos`. Ustedes ya aceptaron las invitaciones de colaboradores.
4. Abrir un chat nuevo después de instalar y pedir usar GitHub. Comprobar identidad y acceso al repositorio antes de escribir.
5. La documentación de OpenAI describe un directorio compartido de plugins para ChatGPT y Codex; la disponibilidad y las acciones dependen de permisos. [Instalación oficial](https://learn.chatgpt.com/docs/plugins).

Mensaje para comprobar la conexión, sin escribir nada aún:

```text
Usa GitHub para comprobar qué usuario está conectado y si tengo acceso de escritura a diegogargo/datosmasivos_vuelos. Muéstrame el usuario, el repositorio y mis issues asignados. No cambies archivos todavía y no solicites ni muestres tokens.
```

Resultado correcto: la cuenta propia de la tabla, el repositorio correcto y acceso de escritura. Si aparece la cuenta de otra persona, desconectar esa conexión y entrar con la propia. Cambiar el nombre de Git no cambia la cuenta conectada.

## 3. Abrir Codex en una carpeta local

Usen la aplicación de escritorio, abran Codex y seleccionen trabajo en **este equipo / Local**. Abran la carpeta del repositorio como proyecto local. Un proyecto local concede acceso a sus archivos; adjuntar un enlace en un chat no clona automáticamente el repositorio. [Proyectos oficiales](https://learn.chatgpt.com/docs/projects), [entornos locales](https://learn.chatgpt.com/docs/environments/local-environment).

Si todavía no tienen una copia, peguen en Codex el primer prompt de su guía. Le pide clonar en una carpeta propia dentro de Documentos, comprobar herramientas y preparar el entorno. Puede pedirles completar un inicio de sesión en el navegador; hagan personalmente ese paso. No necesitan una API key para estas instrucciones.

Si los tres usan una laptop, trabajen uno por uno y preferentemente con perfiles separados de Windows y navegador. Cada persona usa su sesión de ChatGPT, GitHub y una carpeta propia. No cambien la sesión de un compañero mientras su Codex trabaja. El trabajo simultáneo es más sencillo en sus equipos personales.

## 4. Si Codex pide autenticar Git desde PowerShell

La conexión del plugin y las credenciales del Git local son mecanismos distintos. Si Codex puede publicar con su herramienta GitHub, puede usarla. Si va a usar GitHub CLI y necesita conexión local, estos son los comandos:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth status
gh api user --jq .login
gh auth setup-git
```

Si `gh` o `git` no se reconoce, pedir a Codex que instale las herramientas oficiales y vuelva a comprobarlas. No copiar tokens, no ejecutar `gh auth token` para compartirlo y no configurar almacenamiento de credenciales en texto plano. La cuenta que imprime el tercer comando debe ser la de la tabla. En un equipo compartido, Codex debe comprobar de nuevo la identidad antes de publicar.

## 5. Qué hacen ustedes y qué hace Codex

Ustedes: iniciar sesión, autorizar el acceso del repositorio, pegar el prompt correspondiente, leer los resultados y revisar el trabajo del compañero. Si el entorno aislado no puede usar una sesión segura de Windows, pueden ejecutar desde su PowerShell el comando concreto preparado por Codex.

Codex: inspeccionar archivos, implementar el módulo, escribir y ejecutar pruebas, corregir fallos, documentar resultados, preparar commits y PR y analizar revisiones. Los PR deben declarar la asistencia de IA. No debe inventar ejecuciones, reviews, contribuciones, conflictos o resultados.

## 6. Databricks: una ruta sencilla para el equipo

La ejecución integrada se centraliza inicialmente en el workspace de Diego. Ya se ejecutó un piloto Bronze de enero 2025 con 539,747 vuelos. La carga completa de 24 meses tiene una ejecución separada; comprobar su reporte antes de declararla terminada.

Jose Miguel y Santiago pueden comenzar su primer parcial sin Databricks y preparar los módulos del segundo parcial en sus ramas. Después Diego ejecuta los módulos revisados en el workspace de integración. Esto permite tres autores reales en GitHub y una ejecución común documentada; no exige compartir la contraseña de Databricks.

Si les conceden acceso con su propia identidad al mismo workspace, podrán ejecutar allí. No asumimos que Free Edition permita ese acceso. Si usan workspaces personales distintos, las tablas de Diego no aparecen automáticamente en ellos: deben reproducir la ingesta o usar la integración de Diego. [Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition), [límites](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

Tablas y rutas acordadas para el workspace de integración:

| Uso | Nombre |
|---|---|
| Bronze real de Diego | workspace.bronze.vuelos_raw |
| Silver que implementa Jose Miguel | workspace.silver.vuelos_clean |
| Cuarentena que implementa Jose Miguel | workspace.silver.vuelos_quarantine |
| Históricos que implementa Jose Miguel | workspace.silver.vuelos_history |
| Gold que implementa Santiago | workspace.gold.flight_features |
| Agregado mensual que implementa Santiago | workspace.gold.delay_monthly |
| Distribución que implementa Santiago | workspace.gold.delay_distribution |
| Raíz del Volume del proyecto | /Volumes/workspace/bronze/vuelos_raw/vuelos |

**Solo Bronze está implementado en la base de Diego. Las otras funciones y tablas son contratos que deben construir sus respectivos Codex.** No ejecutar un bloque que importe Silver o Gold antes de tener ese módulo. Las guías indican cuándo usarlo.

Dentro de Databricks se usan Spark y las bibliotecas compatibles con su runtime. No instalar allí a ciegas el `requirements.txt` del entorno local ni sustituir la versión de PySpark del servicio.

## 7. Orden de trabajo y revisión

1. Los tres pueden comenzar sus tareas P1 al mismo tiempo.
2. Jose Miguel revisa los PR de Diego; Santiago revisa los de Jose Miguel; Diego revisa los de Santiago.
3. Cada PR se revisa antes de integrarlo. Los PR apilados de Diego se integran en orden y se cambia la base al integrar el anterior; Codex debe resolverlo sin borrar avances.
4. Después: Bronze completo → Silver → históricos/Gold → validación y benchmark de integración.
5. Modelo preliminar: registrar qué pidió exactamente el profesor antes de ampliar ese trabajo. No se inventa un requisito del PDF.
6. No son parte de esta entrega el informe ni la presentación final. No ampliar a clima, precios o modelos avanzados para llenar tareas.

La rúbrica exige trabajo reproducible y colaboración verificable. Una etiqueta “aprobado” de un bot no sustituye la revisión que cada integrante debe comprender y poder explicar.

## 8. Cómo comprobar que terminaron

Cada guía termina con una lista de evidencias. En GitHub deben verse: cambios propios, pruebas, documentación, PR y revisión cruzada. En Databricks: reportes reales con periodos, conteos y versiones. Un mensaje de “código listo” no acredita una ejecución completa.
