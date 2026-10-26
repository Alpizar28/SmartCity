# Matriz de evidencia de consultas — Sprint 1

Esta matriz separa resultado técnico, procedencia y alcance académico. Una consulta marcada como `synthetic_demo` se ejecuta contra entidades administrativas deterministas autorizadas; no acredita que esos sensores sean dispositivos físicos que produjeron lecturas públicas.

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

Los informes `postgresql_full.json` y `mongodb_full.json` contienen `query_evidence` con el estado, alcance, comprobaciones y conteo de entradas sintéticas por consulta. `unified_full_verify.py` rechaza evidencia incompleta, incoherente o que declare una consulta observada con insumos sintéticos.
