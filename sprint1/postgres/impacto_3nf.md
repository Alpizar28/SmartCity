# Normalización relacional de Madrid v2

## Dependencias e intervención

El modelo anterior se conserva en `phase5_postgresql.sql` y `contract_v2.sql`
para reproducir sus ejecuciones verificadas. El modelo de entrega normalizado
se define en `schema_v2_3nf.sql`. No constituye una migración sobre bases pobladas.

| Dependencia anterior | Problema | Resolución |
|---|---|---|
| estación → fuente, magnitud → fuente dentro de canales | Determinantes no superclave; dependencia parcial respecto de estación/clave | `channels.source_id` se elimina; fuente se obtiene desde estaciones. Trigger de join comprueba estación/magnitud, con bloqueo de lectura de padres. |
| sensor → estación dentro de un canal asignado | Redundancia condicionada a sensor no nulo | Asignación en `channel_sensors(channel_id PK, sensor_id FK)`; estación permanece en sensores y canales. Trigger comprueba igualdad. |
| canal → fuente y versión → fuente dentro de observaciones | Dependencias parciales y transitivas | `observations.source_id` se elimina. Trigger compara las fuentes reconstruidas. |
| instante UTC → hora local de Madrid | Representación duplicada del reloj | Hora local calculada en `observation_contract`; se rechazan horas locales ambiguas. |
| ∅ → zona horaria, origen observado, versión de esquema y catálogo | Constantes no primas almacenadas en cada hecho | Literales de la vista del contrato, sin columnas repetidas en la relación base. |
| fuente → calidad, estado temporal, rol e intervalo aceptados en v2 | Política repetida por observación | Vista `accepted_source_policy`, calculada a partir de la fuente. No se crea una tabla de constantes repetidas. |
| referencia JSON completa → SHA de versión | Duplicación del identificador de snapshot | `raw_locator` almacena el objeto sin `sha256`; la vista repone exactamente esa propiedad desde `source_version`. |
| tipo de dispositivo → categoría | Posible transitividad en sensores | `sensor_types` contiene categoría; sensores almacena únicamente el tipo. Magnitudes medidas no referencian categorías de dispositivo. |
| zona → distrito | Duplicación territorial si ambos se repiten en ubicación | Ubicación referencia zona; una zona local referencia un distrito, que también es una zona administrativa. `location_geography` reconstruye ambos nombres. |

Las doce tablas anteriores se conservan como conceptos del núcleo. Dos relaciones
auxiliares, `sensor_types` y `channel_sensors`, elevan el esquema a **catorce tablas**.
Un diagrama limitado a doce ocultaría parte del modelo normalizado. No se añaden
tablas de hechos para fabricar volumen ni se modifican mediciones.

## Impacto por componente

| Componente | Efecto y compatibilidad |
|---|---|
| Identidad | Se conservan measurement_id, channel_id, station_id, source_version y payload_hash. Los únicos identificadores nuevos son tipos administrativos ficticios con prefijo `demo-type:`. |
| Contrato compartido | `observation_contract` reconstruye las mismas claves, valores, fechas, referencias y metadatos de `madrid-draft-v2`. `_id` sigue siendo measurement_id. |
| MongoDB | No cambian validadores, índices, documentos, preparador, reglas, códigos de magnitud ni carga MongoDB. La reconciliación se contrasta con el informe nativo ya sellado. |
| PG01 | Agrupa por tipo de dispositivo explícito. Ya no usa categorías de magnitudes como sustituto del tipo físico. Los doce grupos son administrativos sintéticos. |
| PG02–PG06, PG09–PG10 | Mantienen propósito y resultados. PG09 utiliza el mismo conteo y reloj UTC; PG10 cuenta canales. |
| PG07 | Lee asignaciones a través de `channel_contract`. Sin asignación acreditada, no atribuye lecturas a sensores demo. |
| PG08 | Conserva IDs, cantidades y ranking; sustituye etiquetas técnicas de distrito por nombres publicados. |
| Índices | Se retiran índices de superclaves que solo respaldaban FK compuestas redundantes. La clave natural de observación queda canal/UTC porque v2 fija un rol por fuente/canal. Se indexan tipo de dispositivo y asignaciones. |
| Cargador | Adaptador independiente: catálogos → modelo normalizado, JSON → proyección del hecho. Comparación completa contra la vista después de cargar; cualquier pérdida de metadatos produce FAIL. |
| Pruebas | Instancia PostgreSQL 16 propia, socket Unix privado sin TCP; muestra y lote completo separados; PG01–PG10 cotejadas con Python, replay, restricciones, cierres de DF y huella histórica. |
| Evidencias | Informes nuevos con nombre único y SHA-256. DDL, consultas y reportes históricos permanecen disponibles e inalterados. |

El rol por canal de v2 permite reducir la UNIQUE de
`(channel_id,observed_at,timestamp_role)` a `(channel_id,observed_at)`. La vista
conserva timestamp_role; no se recalcula ningún identificador. La comparación
integral del DTO detecta cualquier fila que no pueda representarse así.

## Datos administrativos y geográficos

Se conservan las 5.133 identidades de sensores y usuarios demo y el organismo
demo. Sus fechas, estados y responsables son sintéticos. Las categorías reciben
nombres administrativos explícitos; los tipos de dispositivo se definen como
tipos ficticios, sin atribuir equipos reales a los puntos de medida. Los códigos
de magnitud permanecen exclusivamente en `measurement_types` y en el contrato.

Los 21 nombres de distrito proceden de las columnas públicas de código/nombre
del snapshot de accidentes de 2026. `distritos_madrid.json` registra SHA-256 y
alcance: es un diccionario administrativo, no una unión temporal entre accidentes
y mediciones ni evidencia de ubicación histórica en 2025. Las 55 ubicaciones
sin distrito permanecen sin asignación. Las 22 sin nombre permanecen NULL.

## Prueba formal de 3FN

`dependencias_3nf.json` enumera todos los atributos y la cobertura de DF de cada
relación. Para cada clave candidata K se declara K → resto. Las claves son:

| Relación | Claves candidatas |
|---|---|
| sources | source_id |
| source_versions | source_version |
| zones | zone_id |
| locations | location_id |
| stations | station_id; (source_id, source_key) |
| sensor_categories | category_id |
| measurement_types | measurement_type; (source_id, code) |
| organizations | organization_id |
| users | user_id; email |
| sensor_types | sensor_type |
| sensors | sensor_id |
| channels | channel_id; (station_id, source_key) |
| channel_sensors | channel_id |
| observations | measurement_id; (channel_id, observed_at) |

Los determinantes antes transitivos ya no aparecen junto a sus dependientes en
la misma relación. En particular, sensor_type no determina una categoría
almacenada en sensores y parent_zone_id no repite el nombre del distrito en
ubicaciones. Las reglas que relacionan fuentes se comprueban entre relaciones,
sin reintroducir columnas dependientes.

El verificador calcula exhaustivamente X+ para todos los subconjuntos de
atributos, deriva las claves mínimas y comprueba que cada DF no trivial tenga
determinante superclave o atributo dependiente primo. También compara el
inventario de atributos con el catálogo real de PostgreSQL. La prueba es formal
respecto de la cobertura declarada; no infiere DF de coincidencias estadísticas.
Con esa cobertura, las catorce relaciones satisfacen incluso BCNF.

La descomposición de fuente usa estación/canal como clave de las proyecciones
padre: la reunión es sin pérdida. La asignación sensor–canal conserva por
separado las filas opcionales, que se reconstruyen con LEFT JOIN. La separación
del tipo conserva su categoría en un catálogo con clave propia. Las propiedades
constantes y las conversiones deterministas se restituyen mediante la vista.
La comprobación del DTO completo verifica esa reconstrucción para cada lectura.

Se consideran dominios SQL tipados: JSONB es un valor documental indivisible
para esta prueba, no una normalización escalar recursiva de sus propiedades.
Los opcionales NULL representan información ausente y no forman claves
candidatas. No se deducen DF globales de una condición que solo rige cuando un
opcional es no nulo. Los CHECK de dominio y la jerarquía territorial no convierten
los nombres, coordenadas o etiquetas de estado en claves.

## Reproducción

Con PostgreSQL 16 instalado y el entorno Python de investigación:

```bash
python scripts/validar_postgresql_3nf.py --sample 1000
python scripts/validar_postgresql_3nf.py
```

El segundo comando es el que acredita el volumen completo. No se acepta un DSN
ni un host externo. Cada ejecución genera su propio informe; no sobrescribe
resultados anteriores. Una ejecución fallida conserva diagnósticos protegidos,
identificados por su ruta, y nunca se convierte en PASS por resultados previos.
