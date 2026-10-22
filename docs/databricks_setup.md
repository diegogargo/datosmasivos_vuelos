# Preparación de Databricks

## Estado
El equipo confirmó que todavía no tiene workspace. No hay catálogo, Volume, tablas Delta, runtime o job real verificado. La base local no se presenta como ejecución en Databricks. Responsable inicial: Diego, issue P2-04; Jose Miguel revisa. Silver: Jose Miguel; Gold/EDA: Santiago.

## Ruta de inicio
1. Revisar [Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition) y sus [limitaciones](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations). Es una opción educativa con cómputo serverless y cuotas; verificar colaboración/permisos antes de elegir una cuenta compartida. Cada persona mantiene su identidad y credenciales.
2. El integrante crea su cuenta/workspace y completa por sí mismo las condiciones de registro. Registrar abajo los nombres reales, sin tokens.
3. Confirmar catálogo disponible y permisos. Crear los esquemas `bronze`, `silver`, `gold` dentro del catálogo autorizado y un Volume para archivos de origen si se cuenta con permisos.
4. [Cargar archivos a un Volume](https://docs.databricks.com/aws/en/volumes/volume-files). Ruta de ejemplo, no existente: `/Volumes/CATALOGO/ESQUEMA/VOLUME/`. Conservar ZIP y manifiesto; descomprimir el CSV antes de leerlo con Spark. No usar una ruta DBFS inventada.
5. Comenzar con enero 2025 completo. Declarar esquema, conservar procedencia y escribir Bronze en Delta. Registrar conteos, versión y evidencia del job.
6. Implementar Silver con el contrato validado localmente, más zonas horarias y reglas históricas. Construir Gold y conciliar agregados; después escalar a los 24 meses.
7. Conservar logs/reportes pequeños y enlaces del workspace permitidos por el equipo; datos completos y secretos quedan fuera de GitHub.

La edición gratuita puede restringir salidas a internet y detener cómputo por cuotas. Si no permite descargar BTS desde el workspace, usar el downloader local y subir los CSV/manifiestos al Volume. Confirmar capacidades reales antes de planear tareas simultáneas.

## Registro a completar durante ejecución
| Campo | Valor |
|---|---|
| Edición y workspace | Pendiente |
| Catálogo / esquemas | Pendiente |
| Volume y ruta | Pendiente |
| Runtime / versión Spark | Pendiente |
| Mes inicial y conteos Bronze/Silver/Gold | Pendiente |
| Enlace de notebook/job y fecha | Pendiente |
| Restricciones verificadas | Pendiente |

No incluir URL con tokens, correos privados, contraseñas, claves o cadenas de conexión.
