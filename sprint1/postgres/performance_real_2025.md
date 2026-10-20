# Rendimiento local de PostgreSQL con Madrid 2025

Medición realizada el 16 de octubre de 2026 en `feature/postgresql-unified`.
El objetivo fue observar los planes de nuestras consultas antes de proponer índices nuevos.

## Datos y entorno

- Generación privada `expanded-2025`, contrato `madrid-draft-v1`.
- **1.076.813 observaciones reales aceptadas**, todas de `MAD-AIR` en 2025.
- PostgreSQL **16.15** en un contenedor temporal `postgres:16-alpine`.
- Contenedor con 3 GiB de límite de memoria, 2 CPU, red deshabilitada y sin puertos publicados.
- Dataset montado en solo lectura. El contenedor y su volumen propio se eliminaron al terminar.
- Pasaron los 9 controles del esquema, 14 casos controlados con `ROLLBACK` y 11 verificaciones sobre datos reales.
- PG01–PG08 devolvieron **0 filas**: no hay sensores físicos acreditados. No son tiempos representativos de esas consultas.
- PG09 devolvió **126 canales** y PG10 devolvió **5.133 estaciones**. PG10 cuenta canales, no sensores.

La copia a staging tardó **61,81 s** y la inserción de observaciones **2.233,54 s**.
Esos tiempos son de carga y no forman parte de las mediciones de consultas.

## Cómo se midió

Ejecuté `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` únicamente sobre `SELECT` y `WITH`,
en transacciones `READ ONLY` y después de `ANALYZE smartcity.observations`.
Cada consulta tuvo una primera ejecución de calentamiento y luego tres mediciones.
La tabla presenta la mediana de esas tres, seguida de su mínimo y máximo.
No se desactivó `Seq Scan` ni se modificaron los índices de JP.

Se usó el canal real `channel:22b22793147c07679ab9c6519ef25e4878314823835845b139091c1aa9033415`.
La ventana temporal fue el **1 de junio de 2025 en UTC**; para canal+tiempo se usó la
primera semana de enero en UTC. El resumen de aire utiliza el reloj original y agrupa
por tipo y unidad acreditada. Todas son ventanas de ejemplo, no conteos de meses completos.

| Consulta | Filas SQL | Ejecución, mediana ms (mín–máx) | Plan principal; estimadas/reales | Índices del plan |
|---|---:|---:|---|---|
| PG09, vista `channel_activity` | 126 | **711,360** (691,683–761,451) | Sort y Aggregate; 126/126 | Ninguno para recorrer observaciones |
| PG10, función por estación | 5.133 | **139,113** (134,904–142,150) | Index Only Scan; 5.133/5.133 | `stations_pkey` en el plan exterior |
| Canal, últimas 20 lecturas | 20 | **0,139** (0,134–0,140) | Limit e Index Scan; 20/20 | `observations_channel_id_observed_at_timestamp_role_key` |
| Fecha UTC, `COUNT(*)` | 1 | **0,839** (0,798–0,844) | Aggregate e Index Only Scan; 1/1 | `observations_time` |
| Canal y semana UTC, `COUNT(*)` | 1 | **0,223** (0,215–0,234) | Aggregate e Index Only Scan; 1/1 | `observations_channel_id_observed_at_timestamp_role_key` |
| Diez canales con más lecturas | 10 | **665,605** (642,231–713,067) | Limit, Aggregate y Seq Scan; 10/10 | Ninguno para recorrer todas las observaciones |
| Resumen de aire, día original | 11 grupos | **1.283,589** (1.275,492–1.423,934) | Aggregate, joins y Bitmap Heap Scan; 19/11 | Índice único canal/fecha, `stations_pkey` |

Los `COUNT(*)` devuelven **una fila SQL** aunque cuenten más registros: la ventana UTC
incluyó **3.013 lecturas** y el canal durante la semana **168**. Conté esos resultados
también directamente en el JSONL original. El canal usado en PG09 tiene **8.635 lecturas**;
el mismo conteo aparece en la vista, en `observations` y en el JSONL.

Las medianas de *Planning Time* fueron, en el mismo orden de la tabla:
**2,257; 1,982; 1,690; 1,486; 1,572; 2,175 y 6,010 ms**.
El calentamiento no está incluido en las medianas: por ejemplo, el filtro por fecha
tomó **12,328 ms** la primera vez y entre **0,798 y 0,844 ms** en las tres siguientes.
No interpreto diferencias pequeñas como una mejora garantizada.

## Planes e índices

El DDL de JP define cinco índices explícitos: `sensor_station`, `sensor_category`,
`sensor_org`, `channel_station` y `observations_time`. PostgreSQL crea además índices
para las PK y `UNIQUE`. El esquema genera **27 índices distintos**: 22 respaldan PK/UNIQUE
y cinco son explícitos. Una primera lectura del catálogo repetía algunas filas porque
contaba también FK que usan un mismo índice; corregí la consulta del verificador.
El conteo de 27 se comprobó contra el mismo DDL en una base vacía, sin repetir la carga.

Estos son los **27 índices distintos** que tenía el esquema cargado. Todos eran B-tree;
los tamaños son los registrados en la base temporal durante la línea base. `PK` y
`UNIQUE` indican índices creados por restricciones, no índices extras que agregué.

| Tabla | Índice y columnas | Origen | Bytes |
|---|---|---|---:|
| `sources` | `sources_pkey` (`source_id`) | PK | 16.384 |
| `source_versions` | `source_versions_pkey` (`source_version`) | PK | 16.384 |
| `source_versions` | `source_versions_source_version_source_id_key` (`source_version`, `source_id`) | UNIQUE | 16.384 |
| `zones` | `zones_pkey` (`zone_id`) | PK | 16.384 |
| `locations` | `locations_pkey` (`location_id`) | PK | 679.936 |
| `stations` | `stations_pkey` (`station_id`) | PK | 688.128 |
| `stations` | `stations_source_id_source_key_key` (`source_id`, `source_key`) | UNIQUE | 319.488 |
| `stations` | `stations_station_id_source_id_key` (`station_id`, `source_id`) | UNIQUE | 802.816 |
| `sensor_categories` | `sensor_categories_pkey` (`category_id`) | PK | 16.384 |
| `measurement_types` | `measurement_types_pkey` (`measurement_type`) | PK | 16.384 |
| `measurement_types` | `measurement_types_source_id_code_key` (`source_id`, `code`) | UNIQUE | 16.384 |
| `measurement_types` | `measurement_types_measurement_type_source_id_key` (`measurement_type`, `source_id`) | UNIQUE | 16.384 |
| `organizations` | `organizations_pkey` (`organization_id`) | PK | 16.384 |
| `users` | `users_pkey` (`user_id`) | PK | 8.192 |
| `users` | `users_email_key` (`email`) | UNIQUE | 8.192 |
| `sensors` | `sensors_pkey` (`sensor_id`) | PK | 16.384 |
| `sensors` | `sensors_sensor_id_station_id_key` (`sensor_id`, `station_id`) | UNIQUE | 16.384 |
| `sensors` | `sensor_station` (`station_id`) | Explícito | 16.384 |
| `sensors` | `sensor_category` (`category_id`) | Explícito | 16.384 |
| `sensors` | `sensor_org` (`organization_id`) | Explícito | 16.384 |
| `channels` | `channels_pkey` (`channel_id`) | PK | 40.960 |
| `channels` | `channels_channel_id_source_id_key` (`channel_id`, `source_id`) | UNIQUE | 40.960 |
| `channels` | `channels_station_id_source_key_key` (`station_id`, `source_key`) | UNIQUE | 40.960 |
| `channels` | `channel_station` (`station_id`) | Explícito | 16.384 |
| `observations` | `observations_pkey` (`measurement_id`) | PK | 147.980.288 |
| `observations` | `observations_channel_id_observed_at_timestamp_role_key` (`channel_id`, `observed_at`, `timestamp_role`) | UNIQUE | 251.584.512 |
| `observations` | `observations_time` (`observed_at`) | Explícito | 10.240.000 |

`pg_stat_user_indexes` es acumulativo durante la sesión y también incluye carga,
FK y controles de integridad. Por ejemplo, el contador del índice único de
canal/fecha/rol pasó de **7 a 529** y el de `observations_time` de **2 a 11** durante
el benchmark. Esos contadores no permiten atribuir todas las búsquedas a una sola
consulta; para eso revisé los nombres de índice dentro de cada plan.
Los `UNIQUE` compuestos de fuente también respaldan FK compuestas: no los quitaría
por su parecido con una PK sin revisar antes esas relaciones.

El índice único `(channel_id, observed_at, timestamp_role)` ocupa **251.584.512 bytes**
en la carga real. Su prefijo sirve para filtrar por canal y por canal+tiempo: ambos planes
lo utilizaron. Crear otro índice igual no aportaría una clave de búsqueda distinta.
`observations_time` ocupa **10.240.000 bytes** y se utilizó para la ventana UTC.
`observations_pkey` ocupa **147.980.288 bytes** y protege `measurement_id`.

PG09 y el ranking de todos los canales hicieron `Seq Scan` de `observations`, porque
agregan una parte grande o la totalidad del lote. Eso puede ser razonable; el hecho de
ver un `Seq Scan` no prueba que falte un índice. El resumen de aire combinó un
`Bitmap Index Scan` y un `Bitmap Heap Scan` sobre el índice único, además de recorridos
secuenciales de catálogos pequeños. Fue la consulta más costosa de esta muestra.

Los planes medidos también registraron buffers de la última repetición. PG09 tuvo
**15.946** bloques compartidos en caché y **103.720** leídos; la agrupación por canal,
**16.022** y **103.644**; el resumen de aire, **568** y **150.046**. En cambio, los
filtros de canal, fecha y canal+fecha registraron **9**, **102** y **9** bloques en caché,
respectivamente, sin lecturas de disco en esa repetición. Son bloques del plan completo,
no cifras atribuibles a un índice individual.

PG10 mostró `stations_pkey` en el plan exterior. Ese plan no detalla necesariamente
los accesos internos de la función SQL, así que no afirmo que sea el único índice usado.
Los índices de `sensors` no pueden evaluarse con este dataset: esa tabla está vacía.
Tampoco declaro redundante un índice solo porque no apareció en estas mediciones.

## Conclusión y límites

Los índices existentes atendieron bien los filtros selectivos probados. **No añadí,
eliminé ni cambié índices o consultas**: no medí una alternativa antes y después que
justifique una optimización. Si el resumen diario se vuelve una consulta frecuente,
conviene probar en otra sesión un filtro UTC equivalente para aire y medirlo antes de
proponer cambios; este informe **no** afirma que vaya a ser más rápido.

PG01–PG08 solo tuvieron `EXPLAIN` **sin `ANALYZE`**. Sus planes no demuestran rendimiento
con sensores físicos. El conjunto contiene solo lecturas aceptadas de aire; faltan
inventario físico, datos administrativos acreditados y una segunda fuente aceptada.
Estas mediciones son locales, con caché y recursos concretos; no representan el
servidor compartido ni certifican el cumplimiento académico de consultas vacías.

Para repetir la carga y medición en un solo contenedor temporal:
`PYTHONDONTWRITEBYTECODE=1 python3 -B tests/sprint1/validate_real_postgres.py --benchmark`.
Sin `--benchmark`, el verificador conserva su comportamiento anterior.
