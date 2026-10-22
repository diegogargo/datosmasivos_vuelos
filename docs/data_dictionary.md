# Diccionario de datos

Muestra regenerada: enero de 2025, 5,000 filas. Los porcentajes son calculados sobre esa muestra, no sobre todos los vuelos de 2024–2025. Selección de 21 campos del notebook original. [Definiciones oficiales de BTS](https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ).

| Variable | Tipo lógico | Descripción | Unidad | Faltantes | Observaciones |
|---|---|---|---|---|---|
| `FlightDate` | date | Fecha del segmento | fecha | 0.00% (0) | Base del calendario; no incluye zona horaria |
| `Reporting_Airline` | string | Código de aerolínea informante | código | 0.00% (0) | Usar definición de BTS; no representa toda la marca comercial |
| `Flight_Number_Reporting_Airline` | integer | Número de vuelo informado | identificador | 0.00% (0) | No es único por sí solo |
| `Tail_Number` | string | Matrícula de aeronave | identificador | 0.52% (26) | Puede faltar; asignación efectiva no garantizada a 3 h |
| `Origin` | string | Aeropuerto de origen | código IATA | 0.00% (0) | Tres letras; verificar dimensión histórica al ampliar periodo |
| `Dest` | string | Aeropuerto de destino | código IATA | 0.00% (0) | Tres letras; horario de llegada usa zona del destino |
| `Distance` | float | Distancia entre aeropuertos | millas | 0.00% (0) | Positiva; no convertir a km sin indicarlo |
| `CRSDepTime` | integer HHMM | Salida programada local | HHMM | 0.00% (0) | 2400 equivale a medianoche del día siguiente |
| `CRSArrTime` | integer HHMM | Llegada programada local | HHMM | 0.00% (0) | No comparar directamente con salida entre zonas |
| `CRSElapsedTime` | float | Duración programada | minutos | 0.00% (0) | Atributo programado; verificar versión disponible al corte |
| `DepTime` | integer HHMM nullable | Salida efectiva local | HHMM | 3.22% (161) | Resultado posterior; prohibido como predictor del mismo vuelo |
| `ArrTime` | integer HHMM nullable | Llegada efectiva local | HHMM | 3.36% (168) | Resultado posterior; prohibido como predictor del mismo vuelo |
| `DepDelay` | float nullable | Diferencia de salida efectiva respecto a programada | minutos | 3.22% (161) | Negativos válidos; objetivo, no predictor |
| `ArrDelay` | float nullable | Diferencia de llegada efectiva respecto a programada | minutos | 3.56% (178) | Puede faltar por cancelación/desvío; no predictor |
| `Cancelled` | binary | Indicador de cancelación | 0/1 | 0.00% (0) | Conservar fila en Silver; etiqueta nula si 1 |
| `Diverted` | binary | Indicador de desvío | 0/1 | 0.00% (0) | Resultado posterior; no predictor del mismo vuelo |
| `CarrierDelay` | float nullable | Retraso atribuido al transportista | minutos | 81.74% (4087) | Causa conocida después; nulos estructurales |
| `WeatherDelay` | float nullable | Retraso atribuido a clima | minutos | 81.74% (4087) | No es un pronóstico; nulos estructurales |
| `NASDelay` | float nullable | Retraso atribuido al sistema aéreo | minutos | 81.74% (4087) | Causa posterior; nulos estructurales |
| `SecurityDelay` | float nullable | Retraso atribuido a seguridad | minutos | 81.74% (4087) | Causa posterior; nulos estructurales |
| `LateAircraftDelay` | float nullable | Retraso atribuido a aeronave tardía | minutos | 81.74% (4087) | Causa posterior del vuelo, no tasa histórica disponible |

## Campos auxiliares del procesamiento local
- `scheduled_departure_local`: fecha/hora programada de salida, sin zona; normaliza 2400 al día siguiente.
- `prediction_cutoff_local`: salida programada menos tres horas; no se afirma que represente UTC.
- `delay15`: entero nullable 0/1, solo para operados con `DepDelay` conocido.
- `eligible_departure`: etiqueta observada; indicador analítico, no predictor.
- `year`, `month`: calendario de `FlightDate` para particionar.

Clave candidata: `FlightDate`, `Reporting_Airline`, `Flight_Number_Reporting_Airline`, `Origin`, `Dest`, `CRSDepTime`. Las repeticiones exactas se eliminan con conteo; una clave repetida con datos distintos bloquea el procesamiento.

## Contrato de calidad P1-02, preparado con Codex

| Campos | Política de nulos y dominio |
|---|---|
| `FlightDate`, aerolínea, número de vuelo, `Origin`, `Dest`, `CRSDepTime` | Clave requerida; fecha válida, aeropuertos de tres letras, número de vuelo entero positivo |
| `CRSDepTime`, `CRSArrTime` | Horario programado requerido; HHMM entero válido, incluidos `0000` y `2400`; `1260`, fracciones e infinitos se rechazan |
| `Distance`, `Cancelled`, `Diverted` | Distancia finita positiva e indicadores binarios requeridos |
| `Tail_Number` | Nulo permitido; no se inventa una matrícula |
| `DepTime`, `ArrTime` | Nulo permitido; si está observado debe cumplir HHMM válido |
| `CRSElapsedTime`, `ArrDelay` | Nulo permitido; si está observado debe ser numérico finito |
| `DepDelay` | Finito y observado para elegibilidad de un operado; negativo válido. Puede faltar en cancelados y no genera una etiqueta de puntualidad |
| `CarrierDelay`, `WeatherDelay`, `NASDelay`, `SecurityDelay`, `LateAircraftDelay` | Nulos permitidos, sin rellenarlos con cero. Si están observados deben ser numéricos finitos. Son causas posteriores, no predictores conocidos tres horas antes |

La tasa es retrasados `>=15` divididos entre operados con `DepDelay` finito observado. Si el denominador es cero, la tasa se publica como `null`, nunca como cero. Un cancelado con `DepDelay` reportado conserva etiqueta nula.

## Variables nuevas propuestas, todavía pendientes
| Variable | Definición propuesta | Condición |
|---|---|---|
| `is_peak_delay_season` | Indicador de meses con mayor tasa estimada en entrenamiento | Mayo-julio es hipótesis; no escoger meses con el conjunto de prueba |
| `origin_hour_delay_rate_28d` | Tasa previa por aeropuerto y hora programada | Eventos y publicación disponibles antes del cutoff; definir tratamiento de grupos sin historia |
| `airline_delay_rate_28d` | Tasa previa por aerolínea | Misma condición de disponibilidad y ventana |

En un modelo a tres horas solo se admiten atributos programados cuya versión esté disponible al corte y características históricas verificables. BTS no aporta por sí solo el historial de versiones de horarios ni resultados en vivo.
