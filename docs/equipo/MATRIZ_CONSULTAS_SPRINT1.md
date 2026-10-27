# Matriz de evidencia de consultas — Sprint 1

**Alcance:** evidencia registrada de la carga anual `smartcity`, no del núcleo
local `sprint1`. «Ejecutada» es el estado del manifiesto, no aprobación académica
ni confirmación de que la consulta actual siga siendo reproducible.
`synthetic_demo` usa entidades administrativas autorizadas, no sensores físicos observados.

| Consulta | Motor | Estado | Alcance de datos | Evidencia |
|---|---|---|---|---|
| PG01 | PostgreSQL | ejecutada | `synthetic_demo` | Sensores demo por categoría; semilla y procedencia registradas. |
| PG02 | PostgreSQL | ejecutada | `synthetic_demo` | Sensores demo con ubicación de estación de catálogo. |
| PG03 | PostgreSQL | ejecutada | `synthetic_demo` | Estados administrativos demo, no estado observado. |
| PG04 | PostgreSQL | ejecutada | `synthetic_demo` | Organización demo asignada a sensores demo. |
| PG05 | PostgreSQL | ejecutada | `synthetic_demo` | Ranking de ubicaciones de sensores demo. |
| PG06 | PostgreSQL | ejecutada | `synthetic_demo` | Fechas de instalación demo. |
| PG07 | PostgreSQL | bloqueada | `synthetic_demo` | No existe relación observada sensor–canal; no se inventa. |
| PG08 | PostgreSQL | ejecutada | `synthetic_demo` | Cobertura por zona de sensores demo. |
| PG09 | PostgreSQL | ejecutada | `observed` | Vista `channel_activity` sobre lecturas reales. |
| PG10 | PostgreSQL | ejecutada | `observed` | Función `channels_at_station()` sobre canales reales. |
| MG01 | MongoDB | ejecutada | `observed` | Búsqueda por canal lógico con lecturas reales. |
| MG02 | MongoDB | ejecutada | `observed` | Rango BSON Date sobre lecturas reales. |
| MG03 | MongoDB | ejecutada | `observed` | Extremos por fuente/tipo/unidad. |
| MG04 | MongoDB | bloqueada | `derived_demo` | Falta regla/umbral/severidad aprobados. |
| MG05 | MongoDB | bloqueada | `derived_demo` | Falta fuente histórica de emisiones autorizada. |
| MG06 | MongoDB | ejecutada | `observed` | Agregación por zona/tipo cuando existe zona publicada. |
| MG07 | MongoDB | ejecutada | `observed` | Agregación por variable/unidad; no por dispositivo físico. |
| MG08 | MongoDB | bloqueada | `derived_demo` | No hay fuente de accidentes cargada. |
| MG09 | MongoDB | ejecutada | `observed` | Pipeline nativo de agregación. |
| MG10 | MongoDB | ejecutada | `observed` | Filtros múltiples e índice natural. |

## Qué falta para cerrar esta lista

- Las diez consultas canónicas están restauradas en `sprint1/postgres/queries.sql`
  para `smartcity`. Ejecutar `bash scripts/validate_sprint1.sh --engines` prueba
  sus resultados sobre fixtures controladas, no sobre el lote anual.
- PG07 ya tiene prueba funcional de ventana semiabierta y exclusión de sensores
  sin relación conocida; su bloqueo de datos observados continúa en el manifiesto histórico.
- Guardar parámetros y resultados de cada consulta Mongo: varias banderas de
  `query_evidence` son constantes y no prueban que se ejecutara el pipeline.
- Resolver PG07, MG04, MG05 y MG08; confirmar alcance de canal/sensor y zona.
  No presentar agrupaciones de zonas nulas como análisis geográfico.

Los manifiestos están en `research/datasets/results/expanded-2025/`.
Su verificador controla estructura y procedencia declarada, no sustituye la
ejecución ni la revisión del resultado de las 20 consultas.
