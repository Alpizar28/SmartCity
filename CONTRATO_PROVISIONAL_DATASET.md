# Contrato provisional del dataset — `madrid-draft-v1-frozen`

**Estado:** interfaz provisional congelada para desarrollo; no autoriza una carga definitiva ni cambios en PostgreSQL, MongoDB o el servidor.  
**Base revisada:** [`research/datasets/05_data_contract.md`](research/datasets/05_data_contract.md), diccionario de 75 entradas y manifiesto de Fase 5.
**Alcance:** lecturas reales de Madrid de enero de 2025: calidad del aire, meteorología y tráfico. Los originales y sus SHA-256 son los del manifiesto Fase 5. No incluye accidentes 2026 ni energía mensual en este contrato.

## Contrato que queda congelado

La interfaz se llama **`madrid-draft-v1-frozen`**. Se congelan nombres, tipos lógicos, nulabilidad indicada y reglas de procedencia de los siguientes campos de lectura:

`madrid-draft-v1` es el contrato histórico/preliminar usado en Fase 5. Sus scripts, resultados y `schema_version='madrid-draft-v1'` se conservan como evidencia y no se reescriben. `madrid-draft-v1-frozen` es el contrato provisional vigente para desarrollar ahora; no autoriza cargas, migraciones ni cambios a la evidencia histórica.

`source_id`, `source_version`, `station_id`, `channel_id`, `measurement_type`, `value`, `original_time`, `original_timezone`, `timestamp_role`, `timestamp_status`, `quality_flag`, `raw_reference`, `data_origin`, `schema_version`, `catalog_version` y `transformation_method`.

Campos opcionales ya definidos, sin promesa de valor: `zone_id`, `unit`, `unit_status`, `candidate_unit`, `interval_minutes`, `element_type`, `measurements`, `sensor_id` y `observed_at`.

Un consumidor puede depender de la **forma** de esos campos, pero debe consultar sus estados de evidencia y aceptar `NULL`. No debe requerir una tabla `sensors`, `organizations`, `users`, `events` o `alerts` poblada.

## IDs

### Estables desde ahora

| ID | Regla congelada | Límite |
|---|---|---|
| `source_id` | `MAD-AIR`, `MAD-METEO` o `MAD-TRAFFIC` | Identifica el dataset, no al operador del dispositivo. |
| `source_version` | SHA-256 completo del snapshot original | Una nueva descarga es otra versión, no una sustitución silenciosa. |
| `station_id` | `station:` + SHA-256 de la tupla JSON canónica `['sca-id-v1', source_id, source_key]` | Sitio de una red; no fusionar códigos entre redes. |
| `channel_id` | `channel:` + SHA-256 de la tupla JSON canónica de la clave lógica del canal | Aire: estación/magnitud/punto-técnica; meteo: estación/magnitud/punto `NULL`; tráfico: id/tipo. |
| `location_id` | Hash de `station_id` y snapshot de inventario | Identifica un *snapshot* de ubicación, no prueba su vigencia histórica. |

No concatenar partes para formar IDs ni sustituirlos por índices de fila. La serialización canónica es JSON con claves ordenadas, separadores compactos y SHA-256, según `phase5_contract.py` del commit revisado.

### No estables todavía

| ID | Motivo |
|---|---|
| `measurement_id` y `_id` Mongo | Dependen de `channel_id + observed_at UTC + timestamp_role`. El reloj de meteo y tráfico no está acreditado; al corregirlo se requiere migración y correspondencia con la clave original. |
| `sensor_id` | No hay identidad individual de dispositivo acreditada. Debe ser `NULL`; no equivale a estación ni canal. |
| `organization_id` y `user_id` | No existe aún fuente administrativa/dispositivo-organismo ni registro de aplicación consentido. |
| `zone_id` | Solo procede del distrito publicado de tráfico; aire y meteo son `NULL` y la vigencia histórica no está probada. |

## Separación explícita de estabilidad

### A. Campos e IDs congelados

`source_id`, `source_version`, `station_id`, `channel_id`, `location_id`, `measurement_type`, `value`, `original_time`, `timestamp_role`, `timestamp_status`, `quality_flag`, `raw_reference`, `data_origin`, `schema_version`, `catalog_version`, `transformation_method`, `source_key`, `payload_hash`, `stations.source_key`, `stations.inventory_present`, `channels.catalog_basis`, `sources.*`, `source_versions.original_path`, `zones.level` y la estructura de `measurements` de tráfico.

### B. Campos provisionales que pueden cambiar

`measurement_id`/`_id` y `observed_at` para meteo/tráfico (reloj); `original_timezone` para meteo/tráfico (acreditación); `unit` y `candidate_unit` meteorológicos (diccionario); `zone_id`, `zones.name` y geografía histórica (cobertura/vigencia); `latitude`, `longitude`, `coordinate_crs` e `historical_location_verified` (CRS/vigencia); `measurements.*.value/applicability` (QA por tipo); `activity.*` (depende de reloj); `sensor_categories.*` (granularidad lógica); y `source_versions.acquired_at` (aún no cargado).

### C. Metadatos faltantes

Identidad, nombre, instalación, estado, fecha de estado y organismo de sensores; organizaciones y responsables acreditados; usuarios y consentimiento; inventario físico, relación dispositivo–organismo, unidades técnicas de meteo, documentación de reloj para meteo/tráfico, CRS/transformación y vigencia histórica de inventarios. Mientras falten, se mantienen `NULL`, vacíos o fuera del núcleo; no se infieren.

## Reglas obligatorias

### Normalización y trazabilidad

- Conservar `source_key` y `raw_reference` (ruta, SHA-256, fila, columna y, para ZIP, miembro). No usar `value` ni número de fila en una identidad.
- `data_origin='observed'` para las mediciones. IDs, conversiones temporales y catálogos son derivados por atributo; no generan una medición nueva.
- Una discrepancia de `payload_hash` para la misma clave se cuarentena; no se sobrescribe ni se crea otra observación.
- Las coordenadas se conservan como fueron publicadas. `coordinate_crs='unverified_decimal_geographic'`; no producir GeoJSON, `EPSG:4326`, 2dsphere ni asignaciones por proximidad.

### Tiempo

- Conservar `original_time` como reloj local sin zona y `original_timezone='Europe/Madrid'`; nunca usar la zona del host.
- Aire tiene `timestamp_role='hour_end'` documentado. H24 representa el extremo de 23:00–24:00 y pasa al día local siguiente.
- Meteo usa formato H/V, pero su zona/reloj es una hipótesis explícita; tráfico usa `timestamp_role='publisher_label'`, sin afirmar inicio o fin del intervalo.
- `observed_at` es `TIMESTAMPTZ`/BSON Date UTC cuando se calculó. Rechazar horas inexistentes o ambiguas de DST si el publicador no aporta el `fold`; no inventar la hora ausente de otoño.
- Para meteo y tráfico conservar `timestamp_status` de pendiente/hipotético. No hacer joins o conclusiones científicas de simultaneidad hasta acreditar el reloj.

## Campos abiertos y metadatos faltantes

| Pendiente | Clasificación | Estado verificable |
|---|---|---|
| Sensores físicos reales | Requiere consulta al profesor para aceptar el alcance alternativo; la evidencia requiere otra fuente | `sensor_id=NULL`; no existe inventario individual. |
| Fecha de instalación | Requiere consulta al profesor para aceptar `NULL`/consulta alternativa | No publicada; primera lectura o alta de sitio no la sustituyen. |
| Estado administrativo | Requiere consulta al profesor para aceptar `NULL`/consulta alternativa | No publicado; QA, actividad y ausencia de lecturas no son estado. |
| Organismos responsables | Requiere consulta al profesor para validar qué evidencia satisface el requisito; además fuente administrativa | El Ayuntamiento es publicador, no operador/responsable individual acreditado. |
| Usuarios | Requiere decisión de diseño (cuentas reales consentidas o ninguna); consulta docente solo si la rúbrica exige datos demo | No hay usuarios ni consentimientos en el dataset. |
| Unidades meteorológicas | Resoluble con documentación técnica oficial | `unit=NULL`; las candidatas 81–89 no son unidades científicas confirmadas. |
| Reloj/zona meteo | Resoluble con documentación del publicador | UTC actual es conversión provisional etiquetada. |
| Reloj/zona tráfico | Resoluble con documentación del publicador | No afirmar inicio/fin; duración publicada es independiente. |
| Normalización geográfica | Resoluble con documentación CRS y control de puntos | CRS decimal/UTM y vigencia histórica no acreditados; no transformar aún. |
| Equivalencias canal/variable | Resoluble mediante inferencia segura solo para la clave publicada; requiere documentación para equivalencias físicas | Canal lógico no es sensor físico; no equiparar variables entre fuentes. |

## Inventario de campos actual

Leyenda de fuente original: **A**=CSV aire (`MAD-AIR`), **M**=CSV meteorología (`MAD-METEO`), **T**=CSV tráfico (`MAD-TRAFFIC`), **I**=inventario auxiliar, **Man.**=manifiesto/snapshot, **Pend.**=no publicado. Tipos: primero PostgreSQL / segundo BSON. Estado `F` = estructura congelada; `A` = campo abierto o valor condicionado; `N` = no poblar. El texto entre paréntesis indica por qué podría cambiar.

| Campo | Fuente original | Tipo | Significado; origen | Estado / posible cambio |
|---|---|---|---|---|
| observation.`sensor_id` | Pend. dispositivo | text FK / string-null | dispositivo; — | N (sin inventario físico) |
| observation.`station_id` | A/M `ESTACION`; T `id` | text FK / string | sitio de red; derivado | F |
| observation.`zone_id` | I tráfico `distrito` | text FK / string-null | distrito; derivado | A (cobertura/vigencia) |
| observation.`channel_id` | A/M estación+magnitud+punto; T id+tipo | text FK / string | serie lógica; derivado | F |
| observation.`measurement_id` | canal+UTC+rol | text PK / string | lectura única; derivado | A (reloj M/T) |
| observation.`_id` | `measurement_id` | proyección / string | ID Mongo; derivado | A (igual a `measurement_id`) |
| observation.`observed_at` | A/M Hxx; T `fecha` | timestamptz / date | UTC normalizado; derivado | A (reloj M/T) |
| observation.`measurement_type` | A/M `MAGNITUD`; T intensidad | FK / string | variable principal; derivado | F |
| observation.`value` | A/M Hxx; T `intensidad` | double / double-int | valor elegible; observado | F |
| observation.`unit` | diccionarios A/T; M Pend. | catálogo text / string-null | unidad física; derivado | A (M sin diccionario) |
| observation.`source_id` | Man. | FK / string | dataset origen; derivado | F |
| observation.`source_version` | Man. SHA-256 | text FK / string | snapshot inmutable; derivado | F |
| observation.`data_origin` | medición/método | text enum / enum | naturaleza del dato; derivado | F |
| observation.`original_time` | A/M día+Hxx; T fecha | timestamp / ISO string | reloj fuente; derivado | F |
| observation.`original_timezone` | diccionario A; hipótesis M/T | text / string | zona IANA propuesta | A (M/T por acreditar) |
| observation.`timestamp_role` | A/M Hxx; T fecha | text / string | papel del tiempo; derivado | F (T sigue `publisher_label`) |
| observation.`timestamp_status` | diccionario/formato | text / string | evidencia del reloj; derivado | F |
| observation.`quality_flag` | A/M Vxx; T `error` | text / string | bandera fuente; observado | F |
| observation.`unit_status` | evidencia/diccionario | catálogo text / string | acreditación de unidad; derivado | F |
| observation.`candidate_unit` | mapa M provisional | catálogo text / string-null | hipótesis de unidad; derivado | A (no confirmada) |
| observation.`interval_minutes` | T `periodo_integracion` | integer / number-null | duración de tráfico; observado | F |
| observation.`element_type` | T `tipo_elem` | derivado / string | clase del punto; observado | F |
| observation.`measurements` | T ocupación/carga/vmed | jsonb / object | payload multivariable; observado | F |
| observation.`measurements.*.value` | T ocupación/carga/vmed | jsonb number / number-null | valor opcional; observado | A (QA por tipo) |
| observation.`measurements.*.raw_value` | T CSV literal | jsonb string / string | literal original; observado | F |
| observation.`measurements.*.applicability` | QA por `tipo_elem` | jsonb text / string | límite de uso; derivado | A (QA específica) |
| observation.`source_key` | claves A/M/T | JSONB / array | clave fuente; observado | F |
| observation.`raw_reference` | Man.+fila/columna/miembro | JSONB / object | procedencia verificable; derivado | F |
| observation.`provenance` | método phase5 | derivable / object | origen por atributo; derivado | F |
| observation.`payload_hash` | documento canónico | ledger / string | huella de contenido; derivado | F |
| observation.`schema_version` | código contrato | text / string | versión de formato; derivado | F (`madrid-draft-v1-frozen`) |
| observation.`catalog_version` | manifiesto catálogos | text / string | versión catálogo; derivado | F |
| observation.`transformation_method` | scripts Fase 5 | text / string | algoritmo; derivado | F |
| stations.`name` | I nombre/`ESTACION` | text / string-null | nombre de sitio; observado | A (parcial) |
| stations.`source_key` | I `CODIGO_CORTO`/id | text / string | código de red; observado | F |
| stations.`inventory_present` | I auditado | boolean / bool | aparece en inventario; derivado | F |
| locations.`latitude` | I `LATITUD`/latitud | double / double-null | latitud publicada; observado | A (CRS/vigencia) |
| locations.`longitude` | I `LONGITUD`/longitud | double / double-null | longitud publicada; observado | A (CRS/vigencia) |
| locations.`original_coordinates` | I ETRS89/X-Y/UTM | JSON catálogo / object-null | coordenada sin transformar; observado | F |
| locations.`coordinate_crs` | I/metadatos | text / string | CRS/estado; derivado | A (sin confirmar) |
| locations.`historical_location_verified` | vigencia I | boolean / bool | ubicación válida en fecha; derivado | N (pendiente) |
| locations.`inventory_reference` | Man. snapshot I | FK+ref / object-null | referencia inventario; derivado | F |
| sensors.`installation_date` | Pend. | date / date-null | instalación física; — | N |
| sensors.`administrative_status` | Pend. | text / string-null | activo/inactivo; — | N |
| sensors.`status_effective_at` | Pend. | timestamptz / date-null | validez del estado; — | N |
| sensors.`identity_evidence_reference` | Pend. | text / string | prueba identidad; — | N |
| sensors.`organization_id` | Pend. relación | text FK / string-null | vínculo organismo; — | N |
| sensors.`name` | Pend. inventario | text / string | nombre dispositivo; — | N |
| organizations.`organization_id` | Pend. admin. | text / string | ID organismo; — | N |
| organizations.`name` | Pend. admin. | text / string | denominación; — | N |
| organizations.`evidence_reference` | Pend. documento | text / string-null | prueba relación; — | N |
| organizations.`responsible_person_or_role` | Pend. persona/cargo | text / string-null | responsable; — | N |
| users.`user_id/name/email` | registro consentido futuro | text / string | identidad aplicación; — | N |
| users.`consent_reference` | consentimiento futuro | text / string | autorización; — | N |
| users.`user_id` | registro consentido futuro | text / string | ID aplicación; — | N |
| users.`name` | registro consentido futuro | text / string | nombre; — | N |
| users.`email` | registro consentido futuro | text / string | correo; — | N |
| users.`demo_only` | decisión futura | boolean / bool | marca demo; derivado | N |
| activity.`first_observed_at/last_observed_at` | MIN/MAX `observed_at` | vista timestamptz / date | actividad canal; derivado | A (depende reloj M/T) |
| events.`rule_id/rule_version/threshold/unit/algorithm` | regla futura | diseño / object | evento derivado; — | N |
| alerts.`emitted_at` | emisión real futura | timestamptz / date | emisión alerta; — | N |
| incidents.`incident_id/category/occurred_at` | accidentes 2026 | separado / string/date | expediente 2026; observado | N (fuera alcance) |
| energy_reports.`period/value/unit` | energía mensual | separado / date/number/string | consumo mensual; observado | N (fuera alcance) |
| locations.`location_id` | estación+snapshot I | text / string | ID ubicación; derivado | F |
| sensor_categories.`category_id` | fuente+magnitud/intensidad | text / string | categoría lógica; derivado | A (granularidad) |
| sensor_categories.`name` | etiqueta código fuente | text / string | nombre categoría; derivado | A (granularidad) |
| channels.`catalog_basis` | lecturas fuente | text / string | base catálogo; derivado | F |
| sources.`name` | Man. | text / string | etiqueta fuente; derivado | F |
| sources.`publisher` | portal municipal | text / string | publicador; observado | F |
| source_versions.`original_path` | Man. ruta | text / string | archivo snapshot; observado | F |
| source_versions.`acquired_at` | Man. fecha descarga | timestamptz / date-null | adquisición real; observado | A (disponible, no cargado) |
| zones.`name` | I tráfico distrito | text / string | etiqueta distrito; derivado | A (vigencia) |
| zones.`level` | I tráfico distrito | text / string | granularidad; derivado | F (`district`) |
| raw_reference.`path/sha256/row/column/member` | Man.+fila/columna/ZIP | JSONB / object | localizador original; derivado | F |
| measurements.`*.unit/*.data_origin` | diccionario T/valor raw | JSONB / object | unidad/origen opcional; derivado | F |

## Qué no debe asumir otro desarrollador

- Un canal, variable, categoría o punto de tráfico **no es** un sensor físico.
- `NULL` no significa cero, inactivo, averiado, fuera de Madrid ni dato sintético.
- Publicador no significa propietario, operador ni responsable individual.
- Meteo no tiene unidad científica confirmada; no promediarla ni etiquetarla como °C, %, hPa, etc.
- Tráfico es un intervalo con intensidad en veh/h; no convertirlo en conteo ni afirmar que `fecha` sea inicio o fin.
- Las coordenadas no están certificadas como WGS84 ni demuestran ubicación en enero de 2025.
- Accidentes 2026 y energía mensual no se pueden unir causal o temporalmente al núcleo de enero de 2025.

## Preguntas docentes pendientes

Ver [`PREGUNTAS_PROFESOR.md`](PREGUNTAS_PROFESOR.md). La evidencia técnica pendiente (unidades, clocks, CRS y fuentes administrativas) se resuelve con documentación del publicador, no con una respuesta docente.
