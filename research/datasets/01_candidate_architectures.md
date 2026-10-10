# Fase 1 — Tres arquitecturas candidatas, no implementadas

Son propuestas para auditar, no modelos aprobados ni afirmaciones de cobertura. Fuentes/URLs/evidencias: [catálogo](01_sources_catalog.csv) y [métodos](01_download_methods.md). No se ejecutó DDL/DML, importación, HDFS ni Spark.

## 1. Contrato común propuesto

- Separar `station/site`, `physical_device` cuando esté acreditado, `measurement_channel`, `campaign`, `road_segment`, `building/property`, `household`, `incident` y `notification`. No convertir todos en sensores físicos por conveniencia del modelo.
- Identidad con namespace de fuente. Claves naturales conservadas en `source_key`; `sensor_id` interno derivado y estable solo cuando la fuente sustente esa entidad. Una variable medida no demuestra un dispositivo individual.
- Observación: `source_id`, `source_key`, `channel_id`, `observed_at`, `original_time`, `original_timezone`, `variable`, `value`, `unit`, `quality_flag`, `data_origin`, `raw_reference`. `ingested_at` será hora real de ingestión futura, nunca fecha de observación copiada.
- `data_origin=observed` para registros medidos/reportados; `derived` para unidades convertidas/agregaciones/reglas, con inputs y método; `synthetic` reservado, **no autorizado ni generado**. Notificaciones oficiales son mensajes observados, pero no necesariamente eventos IoT medidos.
- UTC cuando zona original quede acreditada. `Europe/Madrid`, `America/New_York`, `Europe/London` son zonas candidatas para datos locales, no decisiones automáticamente aplicadas: Madrid H01–H24 y LCL DST necesitan documentación. LAQN marca GMT y NOAA ISD usa UTC. EPA conserva fecha/hora local y GMT: preferir esta última cuando válida.
- Conservar versión de inventario, `valid_from/to`, responsable institucional y fuente. `installation_date` y `administrative_status` nullable/TBD si faltan: no imputar con primera lectura. Si la rúbrica exige NOT NULL, existe bloqueo de diseño que resolver, no licencia para fabricar datos.
- Geografía con CRS explícito, coordenada original y transformada, fuente de geometría y vigencia. Distancia/proximidad debe llevar umbral justificado y cobertura del emparejamiento; no asignar automáticamente todas las lecturas a la estación más cercana sin límite.

**Flujo futuro propuesto:** fuentes oficiales → área raw inmutable/versionada → validación/normalización → MongoDB observaciones/incidentología y PostgreSQL maestros/hechos limpios → exportaciones históricas HDFS → Spark joins/ventanas/agregados → hechos analíticos PostgreSQL + dashboard. Es adaptable: no exige duplicar sin propósito toda la información en ambos motores.

PostgreSQL: PK/FK reales, unicidad compuesta por fuente/clave, tipos y unidades separados, maestros en 3FN. Índices propuestos `(channel_id, observed_at)`, `(zone_id, observed_at)` para hechos y claves naturales únicas; particionamiento temporal si lo justifica la auditoría. MongoDB: `_id` estable por clave completa, validación de `data_origin`, índice único de observación e índices canal/fecha y zona/fecha; incidentes y mensajes separados de lecturas. GeoJSON WGS84 solo tras CRS verificado. No hay FK automática entre motores: la ingestión deberá validar las referencias. Versionar raw/correcciones y conservar procedencia; no borrar históricos silenciosamente.

100 000 registros PostgreSQL requieren **hechos estructurados reales**, no únicamente maestros pequeños. No crear 100 000 sensores. 500 000 documentos y 1 000 000 registros Spark requieren conteos de observaciones únicas y granularidad aprobada; una fórmula de capacidad no acredita cumplimiento. Cada transformación debe distinguir filas raw, observaciones físicas, inválidos, duplicados, reportes y agregados.

## 2. A — Madrid municipal multidominio

### Fuentes y período

Núcleo descargable comprobado: MAD-AIR + MAD-METEO. Complementos: MAD-ENERGY + MAD-CRASH; tráfico MAD-TRAFFIC condicionado a resolver acceso, con MAD-TRAFFIC-META disponible. Ventana amplia **2020–2026** para energía junto al resto; auditoría propuesta 2024–2025 para interanualidad, con recursos exactos a escoger del catálogo, no asumir que el CSV 2025 también contiene 2024.

### Integración

1. Aire/meteo: preservar IDs de estación separados; normalizar H/V a observaciones por hora/canal. **Prueba preliminar:** ambas muestras tienen fecha y estructura horaria reales, misma ciudad y cobertura temporal común documentada. Integración municipal por hora es defendible aunque todavía no sea zonal.
2. Tráfico: histórico `id` → inventario `id`, por versión vigente. Hora agregada desde intervalos y `periodo_integracion`; intensidad veh/h no se suma como si fuese conteo veh/intervalo sin conversión justificada. `vmed`, carga y ocupación se tratan por definición del proveedor, no entre todos los tipos indiscriminadamente.
3. Energía: `(SENSOR, ID_edificio, año, mes, clase, grupo, unidad)` como clave candidata, unicidad pendiente. Join por código de distrito/barrio y **mes**, nunca replicar el consumo mensual en 720 horas. Seleccionar un nivel de medición para evitar general+submedidores.
4. Accidentes: deduplicar expediente a incidente; personas/vehículos como detalles aparte. Código de distrito/fecha ofrece puente real hacia energía y tráfico; CRS UTM debe acreditarse antes de mapa/proximidad.

### Roles por motor y capacidad

- PostgreSQL: inventario de estaciones/puntos/medidores, ubicaciones y organismos acreditados, hechos horarios aire/meteo/actividad y hechos mensuales energía, incidentes únicos. PG03/PG06 siguen bloqueadas por estado/instalación; `actividad_en_ventana` no se renombra como estado administrativo.
- MongoDB: documento por observación horaria o registro de intervalo real, con flag de validación; incidentes por expediente. Documento raw diario puede coexistir con representación horaria solo si no se contabilizan ambos como nuevas mediciones físicas. Alertas oficiales no comprobadas; reglas de evento crítico son derivaciones futuras sujetas a aceptación.
- HDFS: raw anuales/mensuales por fuente y fecha, manifest con hash; Spark normaliza, une ventanas compatibles y produce tendencias y rankings. Dashboard mensual para energía, horario para ambiente/tráfico; señalar datos no disponibles, no interpolar consumo para llenar KPI horario.

**E capacidad:** para observaciones horarias, `n_canales_validos × n_días × 24`. Durante dos años de 365 días, 30 canales continuos producirían 525 600 observaciones y 60 canales 1 051 200; son umbrales de planificación, **no prueba de que existan/cubran esos canales**. Auditar conteos reales; conservar inválidos aparte. Tráfico no aporta volumen acreditado mientras los ZIP estén bloqueados.

### Condiciones de rechazo

No inventario espacial aire/meteo o resolución administrativa de instalación/estado; volumen útil insuficiente; persistencia del 403 si movilidad obligatoria no admite alternativa; energía por hora/CO₂/alertas exigidas sin tratamiento aprobado. No elegir Madrid solo porque cuatro recursos sean accesibles.

## 3. B — NYC campañas de tráfico + ambiente regulatorio + servicios urbanos

### Fuentes y período

NYC-COUNTS + NYC-AIR (EPA filtro local), NYC-WEATHER (NOAA), NYC-311 y NYC-ENERGY. NYC-ALERT es complemento de mensajes emitidos condicionado al 503; NYC-CRASH pendiente de prueba. **2022–2024**, ancla **2023**. Los 1 875 154 conteos globales no garantizan 1 millón en esta ventana; 2023 tiene 85 106 filas comprobadas.

### Integración

1. Convertir fecha de conteo desde componentes después de acreditar timezone; clave candidata campaña + segmento + dirección + fecha + intervalo, no `requestid` solo. El mismo segmento puede medirse en diferentes campañas/contadores.
2. AQS: filtrar estado 36/condados NYC, usar `(state, county, site, parameter, POC, method, datetime_GMT)` según diccionario y depurar duplicados. Condado → borough mediante tabla oficial/administrativa trazable; no usar todo New York State como NYC. **Prueba preliminar:** ambos proveedores publican marcas temporales y geografía, y EPA publica año 2023; localidad de filas AQS queda condicionada a filtro real.
3. Tráfico → aire: primero borough/hora para análisis ecológico agregado con número de sitios/campañas disponibles; si hay geometrías y precisión acreditadas, proximidad con radio/ventana evaluados. No emparejar con sensor más cercano en otro borough sin criterio ni asumir causalidad.
4. NOAA LaGuardia por UTC como contexto meteorológico de ciudad; máximo un valor agregado por variable/hora según prioridad de informes documentada, no join de varios reportes que multiplique conteos.
5. Energía por propiedad/BBL/año y borough; enlazar agregados anuales ambientales, no series horarias artificiales. Separar propiedades padre/hijo y energía kWh de emisiones toneladas CO₂e.
6. 311 por solicitud/categoría/borough y fecha de creación; estado del trámite independiente de sensores. NYCEM por envío/tipo, zona solo si texto/mapeo oficial validado; no etiquetar como alerta ambiental ni sensor automático sin evidencia.

### Roles por motor y capacidad

- PostgreSQL: sitios AQS/NOAA acreditados, segmentos/campañas como entidades propias, boroughs/organismos, hechos limpios de conteos y ambiente y reportes anuales energía. Los 103 259 reportes LL84 globales incluyen tres años/revisiones y no garantizan 100 000 filas útiles de un subconjunto. Usuarios/responsable personal pendientes.
- MongoDB: conteos raw flexibles, lecturas AQS/NOAA, solicitudes 311, notificaciones en colecciones separadas y con origen. MG01 debe apoyarse en sitio/canal ambiental real, no campaña DOT presentada como sensor permanente.
- HDFS/Spark: exportaciones JSON/CSV por fuente/año, ventanas, ranking por exposición al muestreo, comparación interanual con cobertura comparable. Dashboard distingue conteo de volumen, energía anual, emisiones CO₂e y PM2.5; no convertir estas últimas en concentración de CO₂.

**C capacidad:** 1 875 154 filas DOT en endpoint global al verificar; basta como capacidad del origen para Spark y 500k documentos si se autorizase una selección multi-anual amplia y la unicidad/calidad lo permiten. **P:** conteos válidos en período común, capacidad PostgreSQL después de depuración y cobertura EPA local. Los 85 106 conteos 2023 muestran por qué no prometer mínimos con un solo año.

### Condiciones de rechazo

No cobertura EPA NYC suficiente/período común; CRS no resoluble; campos de sensor físico usados en conteos sin sustento; requisitos de energía horaria o velocidad/recorrido sin complemento aprobado; dependencia de NYCEM sin acceso ni zonas. La variedad de APIs no reemplaza identidad/calidad.

## 4. C — Londres aire + smartmeter + movilidad/incidentología

### Fuentes y período

LON-AIR + LON-AIR-META, LON-ENERGY UKPN, LON-COUNTS DfT, LON-WEATHER NOAA Heathrow y LON-CRASH TfL. **2012–2013**, ancla **2013**; seleccionar hogares con cobertura suficiente y sitios LAQN abiertos en esa ventana. No tratar toda la historia LAQN como simultánea al proyecto LCL.

### Integración

1. LAQN lecturas → sitio mediante `SiteCode`, canal mediante especie. La muestra MY1/NO2 2013 y el inventario con apertura 1997 demuestran plausibilidad histórica. Apertura/cierre del sitio puede definir `site_operational_at(t)` derivado con regla, no `sensor_installed_at` ni estado administrativo individual.
2. LCL por `LCLid` + fecha/intervalo, tratamiento de tarifas y valores nulos. Sumar dos intervalos completos a kWh/hora; marcar horas parciales; acreditar timezone y DST. **Prueba preliminar:** energía semihoraria real en Londres 2012–2014 y aire GMT 2013; ciudad–hora como unidad común, no hogares por barrio.
3. DfT Londres región 6, punto/fecha/hora/dirección. Seleccionar los días medidos, no rellenar 16 956 filas de 2013 hasta todo el año. Contraste con LAQN en misma fecha y proximidad/autoridad si cobertura lo permite.
4. NOAA Heathrow como contexto meteo de ciudad. TfL por AREFNO y borough/fecha; transformar BNG si se acredita CRS. No multiplicar incidente al unir casualty/vehicle.
5. Energía **solo a nivel ciudad o cohortes de hogares/tarifa**, pues no hay geografía de hogar probada. Cohorte/tarifa no es «zona geográfica». El mapa presenta sitios ambientales, puntos DfT y accidentes, no viviendas ficticias.

### Roles por motor y capacidad

- PostgreSQL: sitio/autoridad/data owner, variables y referencias de medidores/hogares sin inventar dispositivo, hechos horarios energía/ambiente y actividad. Usuarios no vienen en LCL. DateOpened no soluciona PG06 estricta sin decisión docente.
- MongoDB: observaciones semihorarias de energía, hora–sitio–especie LAQN e incidentes con distinta estructura. Eventos críticos derivables de mediciones con método, no alertas históricas emitidas acreditadas.
- HDFS/Spark: subconjuntos raw inmutables y lotes por fuente/año; joins hora–ciudad y hora–sitio donde proceda, comparación 2012–2013 condicionada a exposición y continuidad. Evitar descargar 10 GB sin presupuesto aprobado.

**D capacidad:** UKPN anuncia ~167 millones de filas. **E selección posible:** 100 hogares × 365 × 48 = 1 752 000 intervalos, suficiente potencial para 500k Mongo/1M Spark y hechos relacionales de 100k. **P:** que los hogares seleccionados tengan ese año completo y suficientes valores válidos. Contar hogares/intervalos reales, no copiar valores ni ampliar por combinaciones.

### Condiciones de rechazo

Licencia LAQN incompatible con redistribución prevista; exigencia estricta de energía por zona sin fuente adicional; instalación individual/estado no resueltos; falta de velocidad/recorrido/CO₂/alertas. No dibujar ubicación energética ficticia para obtener un mapa.

## 5. Cobertura de las 20 consultas del Sprint 1

**R:** atributo real documentado/comprobado; **P:** comprobación/implementación pendiente; **B:** falta atributo o semántica exigida. No significa consultas ejecutadas. La matriz de fase 0 se conserva como snapshot; esta tabla agrega hallazgos sin reescribir su evidencia histórica.

| Consulta | Madrid | NYC | Londres |
|---|---|---|---|
| PG01 tipo | R canales/magnitudes/puntos; P dispositivo | R AQS/NOAA; campaña no dispositivo | R sitio/especie; P analizador |
| PG02 ubicación | R tráfico/energía; P aire/meteo | R borough; P CRS/completitud sitios | R sitios/DfT; B ubicación hogar |
| PG03 activos/inactivos | B administrativo | B administrativo | R fechas sitio; B estado dispositivo |
| PG04 organismo | R direcciones proveedoras; P vínculo individual/responsable | R DOT/EPA/NOAA/NYCEM; P operador físico/persona | R DataOwner/DataManager sitio; P persona/dispositivo |
| PG05 ubicaciones con más sensores | P inventario completo/granularidad | P inventario/CRS | R sitios; P definición sensor |
| PG06 instalados por año | B instalación | B instalación | R apertura sitio; B instalación analizador |
| PG07 sin actividad | P inventario independiente+ventana | P inventario AQS/NOAA, no solo lecturas | R inventario sitio; P inventario canal+actividad |
| PG08 ranking zonas | P geografía aire/meteo e inventario | P borough/CRS y universo | R autoridad local; P canales y cobertura |
| PG09 vistas | P implementación sobre datos reales | P implementación | P implementación |
| PG10 funciones/procedimientos | P implementación | P implementación | P implementación |
| MG01 sensor específico | R punto/canal; P identidad física | R canal AQS/NOAA condicionado a sitio NYC | R sitio/especie; P sensor individual |
| MG02 fechas | R estructura temporal; P DST | R fechas; P zona de conteos/311 | R LAQN GMT; P LCL DST |
| MG03 máximos/mínimos | R valores/flags; P limpieza | R conteos/esquemas; P filtro AQS/QC | R valores; P limpieza |
| MG04 eventos críticos | B publicado; P regla derivada aprobada | R incidentes/avisos candidatos; P acceso/clasificación/derivados | B publicado; P regla derivada aprobada |
| MG05 alertas emitidas por zona | B emisión real | R NYCEM esquema de emisión; B zona explícita, P503 | B emisión real |
| MG06 promedio por zona | P ubicación aire/meteo; R energía distrito/mes | R borough; P cobertura/CRS | R ambiental autoridades; B hogares por zona |
| MG07 promedio por tipo | R magnitud/unidad; P limpieza | R tipo/unidad; P definición sensor | R especie/energía; P sin mezclar unidades |
| MG08 incidentes por categoría | R accidentes, deduplicar expediente | R 311 categoría, distinguir reporte de hecho | R TfL categoría/severidad |
| MG09 agregaciones | P pipeline sobre observaciones reales | P pipeline | P pipeline |
| MG10 filtros múltiples | R campos; P índices/pipeline | R campos; P índices/pipeline | R campos; P índices/pipeline |

Las diez consultas Spark tienen soporte potencial para series, categorías, rankings, anomalías y comparaciones en los tres paquetes, pero SP02 depende de eventos/incidentología bien definidos, SP04 de cobertura de joins y SP09 de años comparables. Energía/CO₂/movilidad del dashboard conservan los bloqueos descritos; **no hay 20/20 consultas verificadas por ejecución**.
