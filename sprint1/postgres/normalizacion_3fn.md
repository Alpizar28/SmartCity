# Auditoría formal del modelo `smartcity` (v1 + extensión v2)

## Dictamen y alcance

Base: `main`, `b77e5497fa28f8c2b483b06e2e593d96b7bd0a5d`.
Autoridad: [`phase5_postgresql.sql`](../../research/datasets/scripts/phase5_postgresql.sql)
y [`contract_v2.sql`](contract_v2.sql). No se modificó ninguno de esos DDL.
El catálogo efectivo de restricciones/NOT NULL/índices se conserva en
[`evidencias/cierre_subconjunto_v2.json`](evidencias/cierre_subconjunto_v2.json).

**No se certifican doce relaciones en 3FN estricta.** Diez satisfacen 3FN respecto
de las DF justificadas abajo; `channels` y `observations` presentan violaciones,
incluso de 2FN respecto de sus claves candidatas compuestas. Las FK compuestas
aseguran coherencia, pero **no eliminan** las DF redundantes. La auditoría queda
cerrada; una descomposición contractual requiere decisión del equipo.

### Método formal (no inferencia estadística)

Una DF `X → A` significa que dos tuplas legales con igual X tienen igual A.
3FN exige, para **cada** DF no trivial, X superclave o A atributo primo
(miembro de alguna clave candidata). 2FN excluye dependencia de un atributo no
primo respecto de parte propia de **cualquier** clave candidata, no solo de la PK.
Las DF por claves se expanden atributo por atributo; `K → resto` es abreviatura.

* **G (garantizada):** PK/UNIQUE NOT NULL y CHECK del DDL; los supersets de una
  PK son superclaves, **no** nuevas claves candidatas mínimas.
* **J (garantizada mediante joins):** la clave del padre, FK NOT NULL y FK
  compuesta implican una DF entre atributos que también están en la hija.
* **S (semántica):** grano/contrato y trigger; se identifica su alcance.
* **O (observada):** coincidencia en este lote. No se incorpora al conjunto de DF.

SQL admite NULL, no contemplado por el modelo relacional clásico. Se interpretan
los opcionales como un valor ausente tipado; no se convierten UNIQUE nullable en
claves. En este DDL todas las UNIQUE declaradas tienen columnas NOT NULL; ninguna
clave candidata de la lista depende de la semántica de NULL de PostgreSQL.
Las DF condicionadas a `sensor_id IS NOT NULL` se separan explícitamente.

**1FN:** sí bajo dominios SQL tipados: cada celda JSONB es un documento, no una
relación SQL anidada. Esto no certifica una representación escalar recursiva:
`measurements`, `source_key` y `provenance` contienen objetos/listas. Si el curso
prohíbe dominios estructurados, debe aceptarse esta excepción o descomponerlos;
no afirmar entonces 1FN clásica de todos sus componentes. Los resultados de 2/3FN
son respecto de atributos SQL completos; se examina aparte el contenido JSON.

## Resumen formal

`K → R` indica que cada clave candidata determina todos los atributos de la relación.

| Relación | PK | Otras candidatas mínimas | DF adicionales relevantes | 1FN SQL | 2FN | 3FN | Observación |
|---|---|---|---|---|---|---|---|
| sources | source_id | ninguna justificada | K → R | Sí | Sí | Sí* | No nombre/publicador como clave |
| source_versions | source_version | ninguna | K → R | Sí | Sí | Sí* | UNIQUE versión/fuente no mínima |
| zones | zone_id | ninguna | K → R | Sí | Sí | Sí* | Nombre no único |
| locations | location_id | ninguna | K → R | Sí† | Sí | Sí* | Coordenadas/CRS no identifican sitio |
| stations | station_id | (source_id, source_key) | K → R | Sí | Sí | Sí* | Código solo dentro de fuente |
| sensor_categories | category_id | ninguna | K → R | Sí | Sí | Sí* | No equivalencia universal categoría/tipo |
| measurement_types | measurement_type | (source_id, code) | K → R | Sí | Sí | Sí* | Unidad/estado no son claves |
| organizations | organization_id | ninguna | K → R | Sí† | Sí | Sí* | Procedencia JSONB |
| users | user_id | email | K → R | Sí | Sí | Sí* | email NOT NULL UNIQUE |
| sensors | sensor_id | ninguna | K → R | Sí† | Sí | Sí* | No station_id → sensor_id |
| channels | channel_id | (station_id, source_key) | station_id → source_id; measurement_type → source_id | Sí† | **No** | **No** | source_id no primo |
| observations | measurement_id | (channel_id, observed_at, timestamp_role); ver reloj | channel_id → source_id; source_version → source_id; observed_at → original_time | Sí† | **No** | **No** | Incluye atributos v2 y constantes |

\* Respecto de las DF declaradas y semánticas justificadas, no de toda regla de
negocio imaginable. † Dominio estructurado/ausente según la convención anterior.

## Evaluación por relación

### 1. `sources`

Propósito: dataset/publicador, no operador físico del sensor.
Atributos: `source_id`, `name`, `publisher`, todos NOT NULL. PK/candidata:
`{source_id}`. No otras UNIQUE ni FK. G: `source_id → name,publisher`.
No se justifica `publisher → name` ni `name → source_id`.
1FN: texto escalar. 2FN: clave simple, sin DF parcial; 3FN: todo determinante
justificado es superclave. No transitividad interna problemática. Sin corrección.

### 2. `source_versions`

Propósito: snapshot de origen identificado por SHA-256.
Atributos: `source_version`, `source_id`, `original_path`, `acquired_at` (opcional).
PK/candidata: `{source_version}`. UNIQUE `(source_version,source_id)` es superclave
no mínima. FK NOT NULL `source_id → sources`. G: `source_version → resto`.
El diseño presupone un solo origen por contenido: dos fuentes con bytes idénticos
compartirían hash y no pueden coexistir como versiones separadas. Es limitación
de identidad, no prueba de una segunda candidata. Ruta/fecha no son únicas.
1/2/3FN: sí; no DF parcial o transitiva interna no clave. El nombre/publicador
se obtiene por join, no se repite aquí. No hace falta descomposición por 3FN;
si se revisa identidad, considerar `(source_id,hash)` con contrato nuevo.

### 3. `zones`

Propósito: zona territorial. Atributos: `zone_id`, `name`, `level` NOT NULL.
PK/única candidata: `{zone_id}`. Sin otras UNIQUE o FK. CHECK level city/district
no determina nombre ni identidad. G: `zone_id → name,level`.
1/2/3FN: sí; sin DF parcial/transitiva problemática. No inferir
`level → zone_id` porque un lote tuviera una sola ciudad. Sin corrección.

### 4. `locations`

Propósito: ubicación del inventario disponible, no historial probado.
Atributos: `location_id`, `zone_id?`, `name?`, `latitude?`, `longitude?`,
`coordinate_crs`, `historical_location_verified`, `inventory_version?`.
PK/candidata única: `{location_id}`. Sin otras UNIQUE. FK opcionales: zona a
`zones`, versión de inventario a `source_versions`. G: `location_id → resto`.
CHECK de rangos y presencia conjunta de latitud/longitud no implica una DF entre
sus valores. Coordenadas iguales no obligan misma ubicación, nombre o zona.
1FN tipada; 2/3FN sí, sin DF parcial/transitiva interna demostrada. La DF
`inventory_version → source_id` está en el padre; source_id no está en esta tabla.
Limitación: no hay vigencias de ubicación; corregir historia es otra decisión.

### 5. `stations`

Propósito: estación/sitio lógico de una fuente.
Atributos: `station_id`, `source_id`, `source_key`, `name?`, `location_id?`,
`inventory_present`. Candidatas: `{station_id}`, `{source_id,source_key}`
(ambos NOT NULL). UNIQUE adicional `(station_id,source_id)` no mínima.
FK: fuente obligatoria, ubicación opcional. G: ambas candidatas → resto.
Ni source_id ni source_key por separado determina el resto; el código se acota
a la fuente. Por ello no hay parcial sobre la candidata compuesta. Tampoco
`location_id → station_id/name/source_key`: varios sitios pueden compartir lugar.
1/2/3FN sí. Los IDs derivados usan fuente/código (S del ETL); el DDL no impone
la fórmula SHA. No proponer una UNIQUE geográfica por una coincidencia del lote.

### 6. `sensor_categories`

Propósito: clasificación. Atributos: `category_id`, `name`, NOT NULL.
PK/única candidata `{category_id}`. Sin otras UNIQUE ni FK.
G: `category_id → name`. No `name → category_id`.
1/2/3FN sí; sin parciales o transitivas problemáticas. El generador usa categorías
con nombres de tipos, pero eso no impone relación uno-a-uno en el modelo.

### 7. `measurement_types`

Propósito: magnitud lógica, unidad y grado de acreditación por fuente.
Atributos: `measurement_type`, `source_id`, `code`, `category_id`, `unit?`,
`candidate_unit?`, `unit_status`. Candidatas: `{measurement_type}` y
`{source_id,code}`; UNIQUE `(measurement_type,source_id)` no mínima.
FK obligatorias: fuente y categoría. G: ambas candidatas → resto.
No source_id → unidad/categoría ni code → unidad entre fuentes. El CHECK
`(unit IS NULL)=(unit_status='pending_dictionary')` controla nulidad; **no**
impone `unit → unit_status` para unidades no nulas, ni unidad candidata → unidad.
1/2/3FN sí respecto de estas DF. No parciales en clave compuesta ni transitiva
interna por categoría: el nombre de categoría está en otra tabla. Si se impone
en el futuro una regla adicional categoría → unidad, habrá que reevaluar.

### 8. `organizations`

Propósito: organismo administrativo y evidencia de su responsabilidad.
Atributos: `organization_id`, `name`, `responsible_person_or_role?`,
`evidence_reference?`, `data_origin`, `provenance` JSONB.
PK/única candidata `{organization_id}`; sin otras UNIQUE ni FK.
G: PK → resto. Nombre, rol y referencia no son únicos. Origen observado/sintético
no determina organismo ni evidencia. 1FN de dominio JSONB; 2/3FN sí, sin
parcial/transitiva no clave justificada. El JSON puede repetir una etiqueta de
origen por auditoría, pero no hay DF general data_origin → documento provenance.
No identifica al publicador con el responsable físico. Sin corrección por 3FN.

### 9. `users`

Propósito: usuario administrativo, independiente del inventario de sensores.
Atributos: `user_id`, `name`, `email`, `consent_reference`, `demo_only`, `data_origin`.
Candidatas `{user_id}` y `{email}`: email **NOT NULL UNIQUE**; igualdad según tipo
text/collation de PostgreSQL, no unicidad de correo insensible a mayúsculas.
Sin FK ni otras UNIQUE. G: cada candidata → resto.
No `demo_only → data_origin` en DDL (aunque sería una política razonable).
1/2/3FN sí, claves simples y ningún determinante no clave justificado. Consentir
no se acredita para personas reales con una referencia `synthetic://`.

### 10. `sensors`

Propósito: dispositivo/entidad administrativa, con origen explícito.
Atributos: `sensor_id`, `name`, `category_id`, `station_id`, `installation_date?`,
`administrative_status?`, `status_effective_at?`, `organization_id?`,
`identity_evidence_reference`, `data_origin`, `provenance` JSONB.
PK/única candidata `{sensor_id}`. UNIQUE `(sensor_id,station_id)` no mínima.
FK obligatorias categoría/estación; organismo opcional. G: sensor_id → resto.
No station_id → sensor_id/categoría/organismo; un sensor demo por estación es O,
no restricción. Tampoco estado → actividad o fecha → estado.
1FN tipada; 2/3FN sí en este modelo de estado actual. No parcial ni transitiva
interna no clave demostrada. No hay historial ni CHECK que ordene instalación y
estado efectivo; una referencia NOT NULL no acredita que su contenido sea real.

### 11. `channels` — **excepción real**

Propósito: serie lógica de una magnitud en una estación; sensor opcional.
Atributos: `channel_id`, `station_id`, `source_id`, `sensor_id?`, `source_key` JSONB,
`measurement_type`, `catalog_basis`. Candidatas garantizadas: `{channel_id}` y
`{station_id,source_key}`. UNIQUE `(channel_id,source_id)` no mínima.
FK simples obligatorias estación/fuente/tipo, sensor opcional; compuestas:
`(station_id,source_id) → stations`, `(measurement_type,source_id) → measurement_types`,
`(sensor_id,station_id) → sensors`, MATCH SIMPLE (sensor NULL omite esa comprobación).

G: cada candidata → resto. **J: station_id → source_id** porque el padre tiene PK
station_id, y la FK compuesta obliga al mismo source_id. **J: measurement_type →
source_id**, por el mismo argumento con tipos. Ninguno de esos determinantes es
superclave de channels; source_id **no es primo**. Luego viola formalmente 3FN.
Además station_id es parte propia de `(station_id,source_key)`: viola **2FN**.
Camino transitivo: channel_id → station_id → source_id (y vía measurement_type).
1FN: sí bajo JSONB atómico, con salvedad de estructura.

Si sensor_id no es NULL, sensor_id → station_id por la FK compuesta; es DF
**condicionada**, no candidata global ni DF clásica de todas las filas con NULL.
La categoría del sensor y del tipo no se compara: el DDL permite diferencias.
No inventar `(station_id,measurement_type)` como candidata: pueden existir varios
puntos/técnicas/elementos con la misma estación y magnitud.

### 12. `observations` — **excepción real, también en v2**

Propósito: un hecho horario de aire o un intervalo de tráfico (no una fila por
muestra de integración). Atributos completos:
`measurement_id`, `channel_id`, `source_id`, `observed_at`, `original_time`,
`original_timezone`, `timestamp_role`, `timestamp_status`, `value`, `quality_flag`,
`source_version`, `data_origin`, `payload_hash`, `transformation_method`,
`transformation_version`, `catalog_version`, `raw_reference` JSONB,
`interval_minutes?`, `source_key` JSONB, `provenance` JSONB, `element_type?`,
`measurements?` JSONB, `schema_version`; v2 añade `integration_sample_count?` y
`zone_scope` NOT NULL.

Candidatas declaradas: `{measurement_id}` y
`{channel_id,observed_at,timestamp_role}` (UNIQUE y todas NOT NULL).
Con la semántica temporal del trigger —Madrid fijo y rechazo de horas ambiguas—
se deduce también `{channel_id,original_time,timestamp_role}` (S); no es otra
UNIQUE explícita. No son candidatas source_key, raw_reference o payload_hash:
ninguno es UNIQUE y el hash se comprueba solo por formato dentro de SQL.
FK simples a canales/fuentes/versiones y compuestas canal/fuente y versión/fuente.

DF relevantes:

* G: cada candidata → resto.
* **J: channel_id → source_id** y **source_version → source_id**. No son
  superclaves de observations, source_id no primo: dos demostraciones de no 3FN.
  La primera es también parcial sobre la candidata compuesta: **no 2FN**.
* **S/trigger: observed_at → original_time** con Europe/Madrid fijo. El tiempo
  no determina canal, rol, valor ni medición: no es superclave. original_time es
  primo si se consideran las claves temporales implícitas; por ello no se usa
  esa DF aislada como prueba universal de no 3FN. Bajo solo claves declaradas
  constituye otra redundancia parcial; el dictamen no depende de esa convención.
* En filas con raw_reference objeto válido, `raw_reference → source_version`
  por extracción de sha256 y CHECK. No confundir la proyección de un componente
  JSON con una FK nueva. La forma JSON no está exhaustivamente restringida;
  por eso se explicita esta condición y no se usa como prueba incondicional.
* Constantes G: `∅ → original_timezone,data_origin,schema_version,catalog_version`
  por CHECK + NOT NULL (v1/v2 según base). En la definición literal con
  determinante vacío también violan 3FN al no ser primos; las convenciones que
  excluyen atributos constantes deben declararlo. No salvan source_id.
* En v2, CHECK + NOT NULL de quality_flag/timestamp_status/source_id implica
  `source_id → quality_flag,timestamp_status` (aire V/documented_local; tráfico
  N/publisher_confirmed_local; no meteo). source_id no es superclave y ambos
  dependientes son no primos. Es otra DF que debe revisarse, no ignorar por venir
  después de v1. Las reglas de tráfico acotan muestras positivas y 15 minutos
  **cuando no son NULL**; ver advertencia de CHECK abajo.

No source_version → valor/fecha/transformación, ni canal → valor, ni
integration_sample_count → interval_minutes como regla general acreditada.
Tampoco se garantiza transformation_version → transformation_method: son
cadenas no vacías sin catálogo versionado de transformaciones. El par concreto
usado por el ETL no autoriza una DF universal; un futuro registro de versiones
de transformación exigiría reevaluar esa dependencia y su descomposición.
`zone_scope` depende del alcance de cada dato geográfico según ETL; SQL solo
restringe su dominio, no impone channel_id → zone_scope. Compartir una etiqueta
en este lote es O, no DF. JSON measurements conserva ocupación/carga/velocidad
del mismo intervalo, con unidades y estados propios; no debe promediarse junto
con value de intensidad. El payload hash no incluye raw_reference/time_error:
no es una clave criptográfica de toda la fila SQL ni prueba de unicidad.

## Propuesta de descomposición (NO aplicada)

### Fuente redundante

Para channels, proyectar `C'(channel_id,station_id,sensor_id,source_key,
measurement_type,catalog_basis)` y usar la proyección existente
`S(station_id,source_id)` de stations. La intersección es station_id, clave de S:
la reunión natural es **sin pérdida** para el estado legal original. Las claves
channel_id y (station_id,source_key) permanecen en C'. La DF station_id → source_id
se preserva en S. measurement_type → source_id se preserva en el catálogo T.
La obligación de que el tipo y la estación tengan la **misma** fuente ya no se
expresa con las FK compuestas originales: requiere trigger/assertion de join,
incluidas actualizaciones de padres. Esto es integridad interrelacional, no otra
DF interna de C'. Para tratar la relación condicional sensor/estación, separar
asignaciones acreditadas `(channel_id,sensor_id,valid_from,valid_to,evidence)` y
validar estación/periodo, sin inventar asignaciones actuales.

Para observations, proyectar O' sin source_id y reconstruirlo desde la
proyección `(channel_id,source_id)` del canal (no hacer NATURAL JOIN con todos
los atributos homónimos de channels, como source_key).
Intersección channel_id, clave del padre: reunión sin pérdida; se conservan PK
y UNIQUE natural. source_version → source_id queda en V. Asegurar por trigger de
join que fuente de versión y canal coincidan; el conflicto no puede resolverse
con dos FKs simples independientes. Esta corrección elimina la redundancia de
fuente, **no** certifica por sí sola la 3FN de todas las otras columnas.

### Reloj, contratos y procedencia

Propuesta adicional: relación de conversión aceptada
`T(observed_at PK, original_time UNIQUE)` para Madrid/no ambigüedad, relación de
política contractual por fuente para flags/estado/intervalo, y metadatos de lote
para constantes. Cada separación X → Y sin pérdida se justifica por X como clave
en la proyección X,Y. Preservar UNIQUE natural por UTC y mantener original_time
reconstruible. Si se normaliza raw_reference, separar localizador validado y su
versión, o quitar únicamente el sha redundante de su representación almacenada;
una vista debe reponer el objeto exacto exigido por el contrato.

No se entrega una migración pretendidamente final: la representación multivariable
JSON y las DF condicionadas requieren un diseño revisado. Una descomposición
escalar de measurements tendría PK `(measurement_id,variable)` y catálogo de
variable/unidad, pero necesita revisar estados opcionales y preservar una lectura
de tráfico por intervalo. La condición de reunión sin pérdida no prueba por sí
sola preservación de todas las restricciones de negocio ni aceptación del equipo.

**Impacto:** actualizar vistas/trigger/cargadores; conservar IDs canónicos, DTO
v2, payload_hash y _id de MongoDB mediante vista de compatibilidad. La mayoría
de PG01–PG10 no necesita source_id de observations, pero ETL y validación de
metadatos sí. Requiere contrato/migración explícitos, replay y regresión completa.
Mantener hoy la redundancia validada es una decisión de auditoría/integridad,
**no cumplimiento formal de 3FN**.

## Integridad efectiva y límites

* PK: doce; 10 UNIQUE adicionales: email, cuatro superclaves de respaldo de FK
  (versión/fuente, estación/fuente, tipo/fuente, sensor/estación), canal/fuente,
  y las claves naturales de estaciones, tipos, canales y observaciones.
* FK: las aristas del [E-R de doce tablas](../../docs/arquitectura/diagramas.md#3-e-r-postgresql--doce-tablas-preliminares)
  son las reales. Padre 0..N hijos; hijo exactamente 1 padre con FK NOT NULL y
  0..1 con FK nullable. users es independiente; demo.entities no integra el núcleo.
* CHECK: fuentes/enums, hashes por formato, coordenadas en rango/pares, valor
  finito, intervalos 1..30, origen observado, contrato/reloj y sha de referencia.
  v2 cambia versiones, añade campos y política específica aire/tráfico.
* **CHECK acepta UNKNOWN:** columnas opcionales como element_type e
  interval_minutes pueden dejar UNKNOWN en la rama tráfico; no se debe afirmar
  que el DDL solo por sí mismo exige todos los campos v2. El ETL verificado los
  completa. Se propone NOT NULL condicional o `CHECK ((regla) IS TRUE)` previa
  revisión, sin alterar el DDL común en esta sesión.
  La prueba `postgres_v2_limitations.sql`, registrada en el JSON del subconjunto,
  reproduce también la aceptación de raw_reference como array `["sha256"]`:
  el acceso por clave produce NULL y la regla termina en UNKNOWN. Exigir objeto,
  propiedades y `IS TRUE` es una propuesta explícita, no una garantía actual.
* `observation_source` valida fuente/estación/tipo/versión y reloj Madrid no
  ambiguo, y bloquea UPDATE si NEW difiere de OLD. Replay idéntico permitido.
  **No impide DELETE/TRUNCATE**, ni cambios administrativos en padres que no
  violen FK; no equivale a almacenamiento WORM ni a historial de asignaciones.
* No hay CHECK de instalación anterior a estado efectivo, expiración de
  inventario ni FK sensor.categoría = tipo.categoría. No se inventan tales reglas.
* SQL no recalcula los SHA de los IDs/payload; lo hace la validación de archivos.
  `_id = measurement_id` es interfaz entre motores, **no** FK distribuida.
* Índices: 27 B-tree (12 PK + 10 UNIQUE + 5 explícitos). No se añadieron índices,
  particiones, vistas materializadas ni migraciones. planes/mediciones v1 y
  prueba de subconjunto v2 están diferenciados en la entrega técnica.
