# Fase 5 — Contrato común de datos `madrid-draft-v1`

Estado: **borrador implementable localmente, pendiente de revisión y aceptación**. Diccionario exhaustivo del DTO y campos críticos administrativos/complementarios: `05_data_dictionary.csv` (75 entradas). CSV incluye significado, tipos SQL/BSON, columna original, origen, unidad, nulos, disponibilidad, restricciones, transformación, fuente/versión y evidencia. Un campo no disponible queda NULL: no recibe una falsa etiqueta observed.

## Entidades y granularidad

| Concepto | Definición / identidad propuesta | Límite |
|---|---|---|
| Estación física/sitio | station_id por fuente y código original; punto de tráfico es un sitio de medición | No fusionar redes por código; co-localización no identidad de dispositivo |
| Sensor físico | sensor_id de dispositivo con evidencia independiente | NULL en todas las observaciones exportadas; tabla sensors vacía |
| Canal lógico | channel_id aire:fuente,estación,magnitud,punto/técnica; meteo conserva punto vacío como NULL; tráfico:fuente,id,tipo_elem | Feed multivariable de tráfico, no número de analizadores físicos |
| Variable | measurement_type fuente:código; intensidad principal y variables opcionales dentro del mismo intervalo | Una variable o categoría no acredita un sensor |
| Ubicación | location_id derivado del sitio y snapshot de inventario; zona distrito solo si publicado | Geografía actual no demuestra posición históricaenero2025 |
| Observación | measurement_id por canal+UTC+papel temporal | Una hora ambiental o un intervalo completo de tráfico |

Todos los IDs largos son texto, con prefijo y SHA256 de tupla JSON canónica `['sca-id-v1', ...]`; no concatenación ambigua, no hash del valor ni índice de fila. `source_version` no entra en la identidad: una corrección sobre misma clave se detecta por payload_hash y se pone en cuarentena, no genera una nueva observación aceptada. Cambiar reglas de identidad exige migración/versionado revisado.

La clave incluye UTC: una futura corrección del reloj puede cambiar IDs. Debe recatalogarse mediante una migración que vincule la clave fuente original con la nueva identidad; no apilar versiones de reloj como si fueran mediciones nuevas.

Unicidad: `(channel_id, observed_at, timestamp_role)` y `_id=measurement_id`. Para tráfico el tipo forma parte del canal; duración y mediciones forman parte del contenido, no de la identidad. Si se descubre multiplicidad legítima de dispositivos, se necesita otra clave física sustentada, no un desempate arbitrario.

## Tiempo y DST

`observed_at`: TIMESTAMPTZ SQL / BSON Date real; JSON Extended `{"$date":"...Z"}`, **no string BSON**. Conservar original_time naive, original_timezone=Europe/Madrid, timestamp_role y timestamp_status. Los rangos son [desde,hasta); selección base por fecha del registro fuente. H24 es media23–24h con endpoint al día siguiente según diccionario aire p.7–8 (`results/phase3/madrid_air_dictionary.txt`). No asumir que el timestamp de tráfico es inicio o fin: publisher_label y periodo_integracion separado.

Conversión con `zoneinfo.ZoneInfo('Europe/Madrid')`, independiente del host. Enero usa UTC+1 y julio UTC+2. El algoritmo hace roundtrip para ambos folds: hora inexistente (30marzo2025 02:30) se rechaza; ambigua (26octubre2025 02:30) se rechaza sin fold acreditado. El publicador elimina una hora de otoño en el formato24 columnas: **no fabricar la hora faltante ni adivinar cuál fold conservó**. La ampliación anual de Spark requiere resolver esto en su propia validación.

Aire local está documentado. Meteo hereda provisionalmente formato H/V; tráfico usa hipótesis local de Madrid, claramente etiquetada `timestamp_status=assumed...pending...`. UTC calculado bajo esa hipótesis **no se declara reloj confirmado por el proveedor** ni sincronía científica verificada. Antes de congelar/cargar definitivamente, José debe acreditar ambos clocks y mantener o corregir mediante versión nueva. No son decisiones académicas que el agente pueda ratificar unilateralmente.

## Geografía

Inventarios aire/meteo conservan DMS etiquetado ETRS89, X/Y ETRS89 y LONGITUD/LATITUD decimales; tráfico utm_x/y y longitud/latitud. Los originales completos y `original_coordinates` se preservan junto a inventory_reference. EPSG25830 es candidato para UTM30, **no confirmado solo por los números**; el CRS de decimales no se renombra WGS84 por una caja plausible. No se hizo transformación ni GeoJSON/2dsphere. Para autorizar mapa futuro: acreditar datum/huso del grupo de campos, transformar con pyproj always_xy, guardar ambos CRS, método/versiones y prueba de puntos de control. Hasta entonces coordinate_crs=unverified_decimal_geographic.

zone_id es NULL en aire/meteo; tráfico usa distrito publicado en inventario, con vigencia histórica pendiente. No asignar barrio por estación próxima ni inventar equivalencias temporales/geográficas.

## Origen, actividad y eventos

Mediciones reales: data_origin=observed. IDs, UTC, conversión de unidades y agregados son derived por campo, con método y versiones; no cambia el valor medido por normalizar formato. Synthetic solo los tres documentos **no métricos** de CRUD en colección desechable, nunca volumen del núcleo. Provenance tiene NULL cuando falta origen y una clave de disponibilidad separada, no un cuarto valor del enum.

Estado administrativo (unknown/NULL), actividad en ventana (MIN/MAX/conteo derivados), ausencia de lecturas y fallo operativo demostrado son cuatro conceptos diferentes. No obtener instalación de primera lectura ni responsable de publicador. `ingested_at`/`received_at` sería tiempo real de la carga posterior, no original_time; no lo rellenamos como medición histórica.

Eventos/alertas: propuesta `rule_id/version`, threshold, unit, duration, QA, algorithm, input_measurement_ids, threshold_source, observed_at, derived_at, severity; alerta además event_id, zone_id, emitted_at real y delivery_evidence. Regla aún no aprobada: **no eventos/alertas generados**. Replay debe separar observed_at histórico de emisión actual; no acredita alertas oficiales de2025. No adoptar IQR como crítico por conveniencia.

## Coherencia entre motores

DTO compartido con station/channel/measurement/source_version y catálogo hash; SQL3FN deriva source/type/unit/zone mediante joins, Mongo denormaliza copias versionadas. FK SQL y trigger de coherencia; Mongo no tiene FK a PostgreSQL: validar membresía y relación canal→estación→fuente/tipo/zona antes de cada lote, y comparar payload/conteos después. La prueba local comprueba ambos catálogos, no coordinación remota ni transacción distribuida.
