# Transferencia verificada — Proyecto de retrasos aéreos (Datos Masivos)

**Fecha:** 21 de octubre de 2026. **Origen:** esta conversación y sus capturas.  
**IMPORTANTE:** este archivo es una síntesis de transferencia, no una auditoría del código fuente, y no contiene datos BTS descargados ni tablas de Databricks.

## Equipo
El texto compartido al final identifica a Diego García, Jose Miguel Guevara y Santiago Roldán como integrantes. **No hay commits ni autorías individuales verificables en este chat.**

## Enfoque vigente
- Proyecto para los primeros dos parciales, más modelo preliminar solicitado por el profesor.
- Fuente: BTS Reporting Carrier On-Time Performance de Estados Unidos; vuelos programados y retrasos de *salida de puerta*, no despegue.
- Etiqueta predictiva: `DepDelay >= 15` minutos en vuelos operados con salida reportada. Mantener cancelaciones en Silver, sin imputarles retraso 0.
- Horizonte predictivo deseado: **3 horas antes de la salida programada**. **Aún no se verificó** una fuente histórica de pronósticos exactos de tres horas.
- Descartados: boletos, precios e impacto económico.
- Modelos: XGBoost sin clima vs con clima (principal); distribución exponencial vs gamma/lognormal (estadístico preliminar); GARCH, Monte Carlo y propagación de retrasos vía redes/SIR (extensiones sujetas a verificación).

## ¿Qué se ejecutó según capturas/mensajes?
- Una muestra de 5,000 vuelos de enero de 2025: 110 columnas, 0 duplicados completos; 164 cancelados y 4,836 operados con `DepDelay` conocido; 896 con retraso >=15 min (18.53%). Estas cifras son de la ejecución compartida, no recalculadas aquí.
- Descarga BTS: al menos 2024-01, 2024-02 y 2024-03 con 5,000 filas de muestra por mes; posteriormente se configuraron 24 meses 2024–2025 x 5,000 = 120,000 registros objetivo. El usuario informó que terminó.
- EDA sobre archivo temporal `/content/proyecto_retrasos/raw/muestra_historica_bts.parquet`: se reportaron 118,273 vuelos operados válidos, 44,413 retrasos positivos, media `DepDelay` 13.24 min, mediana -2 min, P50 positivo 18, P75 48, P90 105, P95 161, P99 365.88 minutos. **Solo evidencia histórica conversacional; falta recuperar archivo original.**
- EDA de tasas mensuales, aeropuerto, aerolínea, horario y día de semana, con indicios preliminares de estacionalidad. Resultados de **muestras**, no Gold.
- Experimento anterior XGBoost con **24 horas** de anticipación (NO el modelo vigente a 3 h), aproximadamente 107,716 train, 39,264 validación y 39,532 test. Métricas reportadas: ROC-AUC sin/con clima 0.676/0.687; PR-AUC 0.427/0.450. Fue creado un notebook `.ipynb` en un turno anterior, pero su archivo original no está disponible actualmente en este entorno.

## Qué se diseñó, pero NO está demostrado como implementado
- Databricks con Delta Bronze / Silver / Gold, PySpark y pruebas automáticas; no contamos con tabla, esquema, ID o job verificable.
- Tablas: `bronze.flights_raw`, `bronze.weather_raw`, `silver.flights_clean`, `silver.weather_clean`, `gold.flight_features`, `gold.delay_distribution`, `gold.delay_daily`, `gold.delay_monthly`, `gold.aircraft_sequences`.
- Tres variables nuevas a crear en Gold: `is_peak_delay_season` (mayo–julio como hipótesis entrenada SOLO con train), `origin_hour_delay_rate_28d`, `airline_delay_rate_28d`. Ventanas estrictamente anteriores al corte de predicción, sin leakage.
- Reparto transversal entre los tres integrantes en Bronze, Silver, Gold, EDA, modelado, documentación y revisiones de GitHub; la distribución es **plan**, no historial de commits.
- Repositorio GitHub del equipo y enlace real **NO entregados** en esta conversación.

## Rúbrica
El PDF adjunto de la conversación se llama `Proyecto Semestral de Datos Masivos(3).pdf`. En esta ejecución no se pudo recuperar el archivo original para copiarlo al paquete, por una restricción de acceso. **Descargarlo directamente desde el adjunto original y subirlo al otro chat.**

Según lo descrito anteriormente en el chat, el parcial 1 solicita definición, fuentes, muestra, diccionario, EDA, arquitectura, repositorio y colaboración; el parcial 2: adquisición automatizada, capas raw/interim/processed, transformaciones, validaciones, tests, benchmarking, documentación y colaboración; el reporte final/presentación quedan después. Verificar texto exacto en PDF.

## Lugares históricos de trabajo (no equivalen a enlaces compartidos)
- Colab temporal `/content/proyecto_retrasos/raw/` y archivo `muestra_historica_bts.parquet`.
- Colab temporal `/content/vuelos_clima/raw/weather/` y `/content/vuelos_clima/processed/pronosticos_rapido.parquet`.
- No se conoce ID ni URL de Google Colab perteneciente al equipo.
- El proyecto externo de Antonio-B85 sobre Alura es una **REFERENCIA**, no repositorio del equipo.

## Qué recuperar antes de programar
1. **Link real de Colab:** abrir desde la cuenta que ejecutó el EDA → Google Drive / Colab → compartir URL; alternativamente Descargar `.ipynb` desde Archivo.
2. **Link real de GitHub:** pedir URL al integrante que lo creó, o confirmar si aún no existe.
3. PDF de rúbrica original desde el adjunto del chat.
4. ZIP BTS originales o Parquet muestreado desde Drive/Colab, si persistieron. Evitar descargar de nuevo antes de comprobar.
5. Acceso/evidencias del workspace Databricks y sus tablas reales.
6. Logs, resultados de tests y tiempos de benchmark cuando existan.

## Reparto propuesto
Todos participan en cada etapa, con roles técnicos de dominio. Integrante 1: características operativas e ingesta BTS; integrante 2: clima y variables históricas; integrante 3: series/distribuciones, pruebas y propagación. Pueden redefinir para repartir carga; no atribuir commits sin evidencia.

## Primer paso al continuar
No volver a empezar. Inspeccionar Colab real, archivos originales y repositorio GitHub del equipo; luego acordar contrato de tablas y construir Bronze/Silver/Gold en Databricks, con EDA formal sobre Gold. El modelo a 3 horas se entrena solo después de verificar procedencia meteorológica válida.
