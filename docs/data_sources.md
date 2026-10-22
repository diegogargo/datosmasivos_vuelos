# Fuente, adquisici�n y procedencia

## Fuente principal
Instituci�n: U.S. Department of Transportation, Bureau of Transportation Statistics (BTS). Tabla: **Reporting Carrier On-Time Performance (1987-present)**. Acceso p�blico mediante [TranStats](https://transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ) y [ZIP mensuales](https://transtats.bts.gov/PREZIP/). [Campos oficiales](https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ).

Formato de origen: ZIP con un CSV. El mes regenerado de enero 2025 tiene 539,747 filas y 110 columnas en el archivo descargado. La muestra elige 5,000 filas con `pandas.DataFrame.sample(random_state=42)` antes de proyectar los 21 campos del original. Se incluyen CSV y Parquet de la misma muestra y un manifiesto `.provenance.json`.

Frecuencia: publicaci�n hist�rica mensual, susceptible a revisiones. La fecha del vuelo no es su fecha de disponibilidad p�blica. Uso: datos p�blicos para an�lisis acad�mico; citar BTS, revisar avisos de uso de la fuente y no presentar el an�lisis como producto oficial del organismo. No se incluye una licencia de terceros ni se atribuye una licencia inventada a los datos.

## Periodo y volumen
Alcance aprobado para el pipeline: **2022�2025, 48 meses completos, sin muestreo**. El EDA original conserva 2024�2025, 24 meses. Los conteos originales conservados en la celda 17 del notebook suman **14,080,680 filas**: 7,079,061 en 2024 y 7,001,619 en 2025. Son conteos de una ejecuci�n hist�rica guardada de dos a�os, no el total del nuevo alcance de cuatro a�os.

El notebook guarda una muestra de 5,000 filas por mes, 120,000 en total. Su Parquet hist�rico no fue entregado. Esta base conserva esas salidas y solo volvi� a descargar enero 2025 para producir una muestra evaluable. Las 120,000 filas no equivalen a los 14.08 millones de vuelos originales.

## Comando de adquisici�n
Desde la ra�z, con dependencias instaladas:
```powershell
python -m src.ingestion.bts --year 2025 --month 1
```
A�adir `--sample` para regenerar los 5,000 registros. El comando acepta un mes expl�cito y no ejecuta descargas al importarse. Para varios meses, repetir de forma controlada; el issue P2-01 contempla selector de rango y memoria controlada.

El ZIP se conserva sin modificar en `data/raw/bts/`. El manifiesto registra URL, periodo, bytes, SHA256, momento de descarga y cabeceras disponibles. Se escribe primero `.part`, se verifica CRC y columnas y luego se renombra. Reintentos limitados y errores registrados. Un original existente sin manifiesto v�lido se rechaza; no se sobrescribe silenciosamente. La cach� valida integridad local; no comprueba autom�ticamente si BTS public� una revisi�n remota.

## Muestra incluida
`data/sample/flights_2025_01.csv`, su equivalente Parquet y su procedencia. Es una regeneraci�n del procedimiento original, no el archivo hist�rico recuperado. Con pandas 3.0.6 los conteos principales coinciden con las salidas guardadas. El muestreo lee todo el mes en memoria; debe mejorarse antes de escalar.

## Problemas conocidos

## Verificaci�n de procedencia de la muestra
`python -m src.ingestion.validate_provenance` escribe `reports/tables/provenance_validation.json` y devuelve c�digo 1 ante cualquier fallo. Comprueba SHA256 de CSV y Parquet, 21 campos en el orden esperado, filas y columnas declaradas, todas las fechas del periodo solicitado, URL oficial y equivalencia ordenada de valores y nulos. Las diferencias num�ricas de serializaci�n aceptadas se limitan a rtol=1e-12 y atol=1e-9.

Quince pruebas con archivos temporales incluyen hashes falsos, conteos alterados, cambio de contenido con hash actualizado, orden distinto, fechas ajenas al mes y ausencia de archivos. No modifican los originales. La coherencia de dimensiones originales y un hash registrado no sustituyen una comprobaci�n independiente del ZIP original; este alcance est� declarado en el reporte.

## Problemas conocidos de los datos
Nulos por cancelaci�n/desv�o, causas posteriores con nulos estructurales, horas locales HHMM, extremos de retraso, cambios de c�digos, posible duplicaci�n de claves y sesgo de muestreo mensual uniforme. [Diccionario](data_dictionary.md) y [auditor�a del original](notebook_audit.md).

## Clima y otras fuentes
No se integr� clima en esta base. Un experimento anterior mencionado en el contexto usaba 24 h y no valida el corte actual a 3 h. Para incorporar pron�sticos se necesita fecha de emisi�n, hora v�lida, ubicaci�n y disponibilidad hist�rica verificable; `WeatherDelay` de BTS es una causa posterior, no una variable meteorol�gica anticipada. No se agregan precios ni econom�a.
