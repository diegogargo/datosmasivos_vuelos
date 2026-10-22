# Contrato de comprobación entre capas

Código de validación de José Miguel Guevara, asistido por Codex. La publicación
de este contrato no acredita Gold implementado por Santiago ni una integración
ejecutada. Su PR permanece dependiente de esas salidas reales.

`run_layer_validation` lee una versión Delta fija de cada tabla existente y
registra sus versiones. Las tres primeras tablas (Bronze, Silver, cuarentena)
son obligatorias. Históricos, features, agregado mensual y distribución ausentes
quedan en `pending`; `complete=false`. Con `require_gold=True` el informe falla
si falta cualquier dependencia. Con `False` puede aprobar las capas disponibles,
manteniendo `complete=false`; no se presenta como validación total.

## Comprobaciones

- Tipos de Silver, claves obligatorias y únicas, números finitos, horarios,
  banderas, fecha mensual, hashes, IDs positivos, etiqueta y elegibilidad.
- Cutoff exactamente tres horas antes; cancelados sin etiqueta y negativos
  válidos. Estas reglas no convierten BTS mensual en una fuente en vivo.
- Cuarentena con motivos y hash coincidente con el payload original.
- Hash del registro calculado desde todos los campos originales Bronze,
  cobertura por anti-joins distribuidos, sin registros extra ni repetidos.
- Conciliación mensual con exclusiones de duplicados exactos explícitas.
- Históricos uno a uno, linaje/cutoff iguales a Silver, modo declarado, ausencia
  de afirmación operacional, mínimo, límites de ventana y política de nulos.
- Gold uno a uno con Silver, sin cambiar etiquetas, elegibilidad ni linaje;
  históricos conservados con su modo. La selección de estacionalidad solo con
  entrenamiento necesita además pruebas del módulo Gold de Santiago.

## Interfaz para integrar Gold

El validador usa las siguientes columnas. Santiago debe implementar este
contrato o acordar un adaptador explícito antes de certificar la integración.

| Tabla | Clave | Valores |
| --- | --- | --- |
| `flight_features` | `flight_id` | linaje, elegibilidad, etiqueta, UTC/cutoff, tasas y conteos históricos, modo y validez operacional |
| `delay_monthly` | `_source_period`, `Reporting_Airline`, `Origin` | `total_rows`, `eligible_departures`, `delayed_departures`, `delay_rate` |
| `delay_distribution` | `_source_period`, `delay_bin` | `eligible_departures` |

El mensual se compara con un agregado independiente de Silver. Tasa nula con
cero elegibles; tolerancia absoluta 1e-12; claves únicas. La distribución usa
**solo elegibles con resultado finito**, incluidos negativos. Bins:
`negative` (<0), `0_14` ([0,15)), `15_59` ([15,60)), `60_179` ([60,180)),
`180_plus` (>=180). Se admiten solo grupos presentes; no se inventan filas sin
observaciones. Se comparan grupo y conteo con Silver.

## Evidencia

Las pruebas con registros sintéticos inyectan etiqueta en cancelados, cutoff
incorrecto, hash de procedencia distinto, tasa errónea, grupos repetidos,
distribución mal contada y falsa validez operacional. Una prueba específica
verifica que la ausencia de Gold impide declarar integración completa.
Estas pruebas no se presentan como una carga real Gold. El reporte remoto se
guarda en `output_root/reports/validation/latest.json`.
