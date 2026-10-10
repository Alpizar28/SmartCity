# Modelos y pruebas técnicas — preliminares de Fase 5

Contrato histórico de los diagramas y DDL: [`madrid-draft-v1`](../../research/datasets/05_data_contract.md), pendiente de revisión conjunta. El contrato provisional vigente para desarrollo es [`madrid-draft-v1-frozen`](../../CONTRATO_PROVISIONAL_DATASET.md); no reinterpreta ni modifica la evidencia histórica. El [diccionario](../../research/datasets/05_data_dictionary.csv) define tipos SQL/BSON, origen, disponibilidad y nulos. Los [diagramas](diagramas.md) representan el DDL real de prueba y el flujo propuesto, no un despliegue definitivo.

## PostgreSQL: doce tablas en `draft5`

Autoridad: [phase5_postgresql.sql](../../research/datasets/scripts/phase5_postgresql.sql). Se ejecutó únicamente en una base local desechable; `postgres/init/` continúa sin inicializadores.

| Tabla | PK | FK y función |
|---|---|---|
| `sources` | `source_id` | Dataset y publicador; no operador físico inferido |
| `source_versions` | `source_version` (SHA-256) | `source_id → sources`; path y fecha de adquisición |
| `zones` | `zone_id` | Zona publicada, nivel city/district |
| `locations` | `location_id` | `zone_id → zones`, `inventory_version → source_versions`, ambas opcionales; coordenadas/CRS/vigencia |
| `stations` | `station_id` | `source_id → sources`, `location_id → locations` opcional; código y presencia en inventario |
| `sensor_categories` | `category_id` | Catálogo de categorías |
| `measurement_types` | `measurement_type` | `source_id → sources`, `category_id → sensor_categories`; código, unidad/candidata/estado |
| `organizations` | `organization_id` | Nombre y evidencia del responsable; sin miembros ficticios |
| `users` | `user_id` | Sin FK; correo único, consentimiento y etiqueta demo/origen |
| `sensors` | `sensor_id` | `category_id → sensor_categories`, `station_id → stations`; `organization_id → organizations` opcional; evidencia física obligatoria |
| `channels` | `channel_id` | `station_id → stations`, `measurement_type → measurement_types`; `sensor_id → sensors` opcional; base de catálogo y clave fuente |
| `observations` | `measurement_id` | `channel_id → channels`, `source_version → source_versions`; valor, QA, reloj, procedencia y payload opcional |

Una fuente puede tener cero o muchas versiones, sitios y tipos; cada hijo con FK NOT NULL referencia exactamente un padre. Las ubicaciones pueden compartirse por varios sitios, aunque la preparación actual derive una por sitio. Un sensor puede referenciarse desde cero o muchos canales y cada canal referencia cero o un sensor; **no existe UNIQUE que imponga uno a uno**. No hay FK entre usuarios y sensores ni entre SQL y MongoDB. Cardinalidades y nulos exactos en el [E-R](diagramas.md).

### Normalización, restricciones e índices

El diseño separa dependencias de fuente, estación, ubicación, categoría, tipo/unidad y dispositivo en catálogos para aproximar 3FN. `observations` no duplica fuente, sitio, zona, tipo ni unidad; `observation_contract` los reconstruye mediante joins. Reloj original, valor, QA, duración y localizador dependen del hecho. El JSONB `measurements` conserva variables opcionales del mismo intervalo de tráfico, no otro conjunto de filas ni un modelo puramente escalar de todos los campos.

No se declara certificada la 3FN ni resuelta la historia de metadatos: Daniel debe revisar dependencias funcionales, JSONB y vigencias. El DDL no tiene tablas de historial temporal de ubicación/organismo. `inventory_version` y `historical_location_verified=false` hacen visible la limitación.

- PK y UNIQUE: `(source_id,source_key)` en estaciones; `(source_id,code)` en tipos; `(station_id,source_key)` en canales; `(channel_id,observed_at,timestamp_role)` en observaciones. `source_versions` también declara UNIQUE de versión/fuente.
- CHECK: coordenadas en rango y lat/lon ambas presentes o ambas NULL; valor finito; duración 1–30; origen y enums; zona original y versión de contrato.
- Trigger `observation_source`: valida fuente de versión contra estación y tipo del canal, además de las FK. No acredita identidad física ni vigencia administrativa.
- Índices B-tree de PK/UNIQUE; `sensor_station`, `sensor_category`, `sensor_org`, `channel_station`, `observations_time`. El UNIQUE natural ya cubre canal/fecha; no duplicarlo sin evidencia de plan.
- Vistas: `channel_activity` (MIN/MAX/conteo) y `observation_contract`; función `channels_at_station(text)`. Actividad es derivada en ventana, no estado administrativo.
- Particiones, BRIN y vista materializada son propuestas posteriores sujetas a benchmark y revisión de unicidad global; **no implementadas**.

### Prueba local y consultas pendientes

[postgresql_sample.json](../../research/datasets/results/phase5/postgresql_sample.json) registra PostgreSQL **16.15**, **5.000 observaciones**, **462 canales**, **5.134 sitios**, **0 sensores** y **0 usuarios**. Los catálogos completos no equivalen a 462 canales con lecturas en la pequeña muestra. DDL, consultas, vistas, función, PK, referencias/trigger y valores contra referencia independiente se verificaron; contenedor y volúmenes fueron eliminados. Estos conteos no demuestran mínimo definitivo de 100.000.

Diseños: [phase5_postgresql_queries.sql](../../research/datasets/scripts/phase5_postgresql_queries.sql); estado por requisito: [05_postgresql_design.md](../../research/datasets/05_postgresql_design.md).

| Consultas | Estado semántico |
|---|---|
| PG01/PG02/PG05/PG08 | Alternativas por canal/sitio/zona parcial; necesitan aceptar alcance y geografía, no cuentan sensores físicos acreditados |
| PG03 | Sin estado administrativo: actividad no lo sustituye |
| PG04 | Sin relación completa dispositivo–organismo/responsable; publicador no basta |
| PG06 | Sin instalación individual; primera lectura/alta de sitio no equivalen |
| PG07 | `NOT EXISTS` diseñado, pero falta inventario físico y completo de canales independiente de lecturas |
| PG09/PG10 | Vista y función ejecutadas nativamente en prueba local; no certifican todo el contrato |

Fase 3 conservaba **2/10 estrictas y 6/10 funcionales condicionadas**, no 10/10; es evidencia histórica, no aprobación de alternativas por el profesor.

## MongoDB: documentos con referencias compartidas

Autoridad: [05_mongodb_design.md](../../research/datasets/05_mongodb_design.md) y [phase5_mongo_test.js](../../research/datasets/scripts/phase5_mongo_test.js).

| Colección | Granularidad y estado |
|---|---|
| `readings` | Hora ambiental o intervalo multivariable de tráfico; muestra real ejecutada |
| `derived_events` | Regla/version/inputs, `observed_at`, `derived_at`; propuesta, **sin eventos generados** |
| `alerts` | Evento/zona y `emitted_at` con evidencia de entrega; propuesta, **sin emisiones acreditadas** |
| `incidents_2026` | Expediente único de accidente y categoría NULL explícita; complemento fuera de muestra, sin prueba nativa propia |
| `energy_reports_monthly` | Medidor/nivel/unidad/mes; propuesta separada, no energía horaria |
| `dynamic_metadata` | Payload semiestructurado con versión y `raw_reference`; especificación pendiente |
| `crud_demo` | Tres fixtures synthetic no métricos, únicamente en DB desechable; no usuarios/sensores/lecturas |

`readings._id=measurement_id`. Campos comunes: canal, sitio, sensor NULL, fuente/versión, variable/unidad, zona opcional, QA, procedencia, reloj original y `observed_at` como **BSON Date**, no string. Copias desnormalizadas permiten filtrar sin joins repetidos; su coherencia se valida contra catálogos versionados antes de cada lote. Ejemplos reales pequeños: [examples.extjson](../../research/datasets/results/phase5/examples.extjson).

Índices de prueba: `_id` único, UNIQUE `(channel_id, observed_at, timestamp_role)`, `channel_time`, fuente/tipo/tiempo y zona/tipo/tiempo. El validator `$jsonSchema` controla campos, tipos y origen. No hay `2dsphere` sin CRS ni TTL que borre historia. Se eligió colección estándar; time-series queda como alternativa no probada, con deduplicación y restricciones de CRUD que requieren revisión por versión.

### Prueba nativa y cobertura académica

[mongodb_execution.json](../../research/datasets/results/phase5/mongodb_execution.json) y [05_native_mongodb_test.md](../../research/datasets/05_native_mongodb_test.md) registran MongoDB **7.0.43**, muestra de **5.000 documentos** (1.000 aire, 1.000 meteo y 3.000 tráfico), mismos catálogos e IDs que SQL. No se extrapolan mínimos ni rendimiento de producción.

- Ejecutados: MG01 canal, MG02 rango, MG03 extremos, MG06 zona publicada de tráfico, MG07 variable/unidad, MG09 Aggregation Framework y MG10 filtros múltiples.
- Agregaciones `$match → $group → $sort`; sumas/extremos/conteos cotejados con referencia independiente. Unidades y zonas NULL se excluyen según la operación, sin inventarlas.
- Índices y `explain('executionStats')` natural y con hint documentados; el plan natural eligió IXSCAN `channel_time`. Un hint no demuestra elección automática.
- Reimportación idéntica: cero documentos adicionales; total permanece 5.000. Rechazos de duplicado y string donde se exige BSON Date.
- CRUD `insertOne`, `insertMany`, `find`, `findOne`, `updateOne`, `updateMany`, `deleteOne` únicamente sobre `crud_demo` en la DB desechable; ninguna observación fuente mutada.
- MG04/MG05 bloqueadas por regla/emisión; MG08 requiere incidentes de 2026 y prueba separada. MG01/MG07 por canal/variable necesitan aceptación; MG06 tiene alcance geográfico parcial.

**Siete diseños técnicos no equivalen a siete requisitos académicos estrictos cumplidos.** La prueba no contiene 500.000 documentos, cluster, sharding ni prueba time-series. MongoDB 8.0 falló al arrancar por incompatibilidad declarada con kernel Linux 6.19+ (`SERVER-121912`); se preservó el diagnóstico y se usó 7.0, sin modificar kernel o Compose.

Los motores de prueba usaron socket Docker local explícito, red `none`, sin puertos publicados, inputs readonly y recursos desechables. Ambas evidencias acreditan cleanup. Las versiones de prueba son diferentes de los pins de infraestructura `16.6-alpine`/`7.0.16`; no se modificaron ni se certificó compatibilidad exacta de esos patches.

## Coherencia entre SQL y MongoDB

Los IDs y catálogos derivan del mismo DTO. PostgreSQL aplica FK/trigger; MongoDB replica referencias y depende del ETL, validator y reconciliación. No hay FK cruzada ni transacción distribuida. El [pipeline](pipeline.md) implementa controles de muestra; outbox/manifiestos de lote, recuperación de escrituras entre motores y backups son especificaciones futuras. Esta documentación no instruye conectar a las bases compartidas.
