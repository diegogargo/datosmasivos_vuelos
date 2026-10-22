# Fuente, adquisición y procedencia

## Fuente principal
Institución: U.S. Department of Transportation, Bureau of Transportation Statistics (BTS). Tabla: **Reporting Carrier On-Time Performance (1987-present)**. Acceso público mediante [TranStats](https://transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ) y [ZIP mensuales](https://transtats.bts.gov/PREZIP/). [Campos oficiales](https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ).

Formato de origen: ZIP con un CSV. El mes regenerado de enero 2025 tiene 539,747 filas y 110 columnas en el archivo descargado. La muestra elige 5,000 filas con `pandas.DataFrame.sample(random_state=42)` antes de proyectar los 21 campos del original. Se incluyen CSV y Parquet de la misma muestra y un manifiesto `.provenance.json`.

Frecuencia: publicación histórica mensual, susceptible a revisiones. La fecha del vuelo no es su fecha de disponibilidad pública. Uso: datos públicos para análisis académico; citar BTS, revisar avisos de uso de la fuente y no presentar el análisis como producto oficial del organismo. No se incluye una licencia de terceros ni se atribuye una licencia inventada a los datos.

## Periodo y volumen
2024–2025, 24 meses. Los conteos originales conservados en la celda 17 del notebook suman **14,080,680 filas**: 7,079,061 en 2024 y 7,001,619 en 2025. Son conteos de una ejecución histórica guardada, no una descarga nueva auditada de todos los meses.

El notebook guarda una muestra de 5,000 filas por mes, 120,000 en total. Su Parquet histórico no fue entregado. Esta base conserva esas salidas y solo volvió a descargar enero 2025 para producir una muestra evaluable. Las 120,000 filas no equivalen a los 14.08 millones de vuelos originales.

## Comando de adquisición
Desde la raíz, con dependencias instaladas:
```powershell
python -m src.ingestion.bts --year 2025 --month 1
```
Añadir `--sample` para regenerar los 5,000 registros. El comando acepta un mes explícito y no ejecuta descargas al importarse. Para varios meses, repetir de forma controlada; el issue P2-01 contempla selector de rango y memoria controlada.

El ZIP se conserva sin modificar en `data/raw/bts/`. El manifiesto registra URL, periodo, bytes, SHA256, momento de descarga y cabeceras disponibles. Se escribe primero `.part`, se verifica CRC y columnas y luego se renombra. Reintentos limitados y errores registrados. Un original existente sin manifiesto válido se rechaza; no se sobrescribe silenciosamente. La caché valida integridad local; no comprueba automáticamente si BTS publicó una revisión remota.

## Muestra incluida
`data/sample/flights_2025_01.csv`, su equivalente Parquet y su procedencia. Es una regeneración del procedimiento original, no el archivo histórico recuperado. Con pandas 3.0.6 los conteos principales coinciden con las salidas guardadas. El muestreo lee todo el mes en memoria; debe mejorarse antes de escalar.

## Problemas conocidos
Nulos por cancelación/desvío, causas posteriores con nulos estructurales, horas locales HHMM, extremos de retraso, cambios de códigos, posible duplicación de claves y sesgo de muestreo mensual uniforme. [Diccionario](data_dictionary.md) y [auditoría del original](notebook_audit.md).

## Clima y otras fuentes
No se integró clima en esta base. Un experimento anterior mencionado en el contexto usaba 24 h y no valida el corte actual a 3 h. Para incorporar pronósticos se necesita fecha de emisión, hora válida, ubicación y disponibilidad histórica verificable; `WeatherDelay` de BTS es una causa posterior, no una variable meteorológica anticipada. No se agregan precios ni economía.
