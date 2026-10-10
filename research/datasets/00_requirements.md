# Fase 0 — Requisitos y preparación

Fecha: 2026-10-09. Referencias E/P/I y huellas documentales en [README.md](README.md).

## 1. Autoridad y alcance

1. **Oficial:** E define el proyecto completo, entrega 25 de noviembre de 2026, grupos de máximo cuatro personas (E p. 1). El contenido identifica el curso **CE-3191 Base de Datos**, aunque el nombre del archivo dice CE3101. Debe confirmarse la identificación administrativa, no cambiar el documento.
2. **Equipo:** P delimita primer avance a PostgreSQL/MongoDB el 28 de octubre, segunda entrega con los componentes restantes el 25 de noviembre. P reconoce que E no contiene rúbrica separada para el avance (P pp. 1–2, 5). El 28 de octubre figura como entrega oficial en P, pero **no está acreditado por E**: confirmar comunicación docente.
3. **Propuesta:** I evalúa candidatos sin importaciones, muestras ni mediciones de rendimiento (I p. 1). Sus puntuaciones y afirmaciones de volumen/calidad no se consideran verificadas en esta fase.
4. **Restricción de esta investigación:** infraestructura ya desplegada en Coolify con acceso privado Tailscale, según el usuario; no comprobarla conectando a bases remotas, no modificarla. No generar datos sintéticos, descargar datasets grandes ni instalar infraestructura.

## 2. Selección, volumen, calidad e integración

| ID | Requisito / grado de exigencia | Evidencia | Consecuencia para seleccionar datos |
|---|---|---|---|
| SEL-01 | Integrar como mínimo dos fuentes diferentes | E p. 6 | Dos fuentes reales con una relación analítica defendible, no dos exportaciones del mismo archivo |
| SEL-02 | Se recomienda al menos dos repositorios distintos; las fuentes deben cubrir consultas obligatorias | E p. 23 | Dos fuentes es obligatorio; dos repositorios es recomendación, no equivalencia automática |
| SEL-03 | Ecosistema urbano/IoT con datos estructurados, semiestructurados, históricos y de múltiples dispositivos | E pp. 1–6, 8 | Comprobar sensores/dispositivos y marcas temporales; un viaje de taxi no es por sí mismo lectura IoT |
| VOL-01 | Tabla titulada tamaño mínimo: 100 MB aceptable; 500 MB–1 GB recomendado; 1–5 GB avanzado; >5 GB muy avanzado | E p. 7 | Tratar 100 MB como referencia mínima conservadora; la misma página lo presenta como «Propuesta». Confirmar cómputo y alcance |
| VOL-02 | Escenario mínimo: 100 000 registros PostgreSQL; 500 000 documentos MongoDB; 1 000 000 registros procesados Spark | E p. 26; infografía p. 3 | Cumplir umbrales por tecnología; el volumen en bytes no sustituye los conteos |
| VOL-03 | Recomendado: más de cinco millones de registros totales | E p. 26 | No convertir recomendación en mínimo obligatorio |
| VOL-04 | Ampliación sintética permitida, documentando mecanismo | E p. 26 | Permiso académico, no obligación; prohibida por el usuario en esta fase |
| VOL-05 | Empezar con 1–5 GB y escalar a decenas de GB para rendimiento es recomendación | E p. 26 | No descargar ese volumen en fase 0 ni asumir que sea obligatorio |
| CAL-01 | Documentar fuente, licencia y descarga/limpieza | E p. 26 | Exigir ficha de procedencia y licencia antes de seleccionar |
| CAL-02 | PostgreSQL para maestros, referencias, transacciones limpias y agregados de alta calidad | E p. 8 | Necesitar catálogos reales y hechos compatibles; no inflar cantidad de sensores para lograr 100 000 filas |
| INT-01 | Integrar coherentemente cuatro sistemas, por ejemplo MongoDB → HDFS → Spark y datos limpios Spark → PostgreSQL | E p. 2 | IDs y formatos reutilizables; los ejemplos de flujo no fijan una única arquitectura obligatoria |
| INT-02 | Demostrar mediante experimentación cuándo y por qué cada tecnología; matriz comparativa argumentada | E pp. 17, 20–22 | Elegir datos que permitan comparar procesamiento y modelos, no solo instalar motores |
| INT-03 | Demostrar procesamiento distribuido; tamaño por sí solo no acredita Big Data | E pp. 7, 13–16 | Diseñar medición posterior de distribución, particiones, rendimiento y comportamiento, sin inventar resultados |

La enumeración de dominios en E pp. 4–6 incluye aire, clima, tráfico, transporte público, energía, estacionamientos, eventos, ruido, peatones, vehículos/bicicletas/motos, generación/demanda eléctrica y espacios públicos. Es el contexto del problema, no una lista explícita de fuentes obligatorias para cada dominio; **la tabla de KPIs del dashboard sí formula exigencias específicas**.

### Controles de calidad propuestos por el equipo, no umbrales oficiales

P pp. 1–2 e I pp. 4–5 proponen revisar nulos, duplicados, fechas, consistencia, IDs, unidades, licencias, geografía y muestras; no fijan porcentajes máximos de error. Para fase 1 habrá que medir, sin atribuir cifras inexistentes:

- Granularidad: estación física, dispositivo, variable y observación; una estación no demuestra automáticamente todos los sensores que se proponen modelar.
- Completitud por variable/sensor/período y banderas de validación del proveedor.
- Unicidad de claves, duplicados por observación y cobertura histórica real.
- Unidades y rangos físicos, distinción entre cero, nulo, dato inválido y ausencia de observación.
- Zona horaria original, cambios de horario de verano, frecuencia y períodos comunes.
- CRS de coordenadas, zonificación oficial y regla documentada de correspondencia espacial.
- Evidencia de licencia, versiones, URL/fecha de obtención y hashes de futuras muestras.
- Cardinalidad y cobertura de joins; no fabricar causalidad ni hacer producto cartesiano entre sensores.

I p. 4 propone `snake_case`, UTC conservando zona original, `sensor_id`, `zone_id`, `measurement_id`, `observed_at`, `measurement_type`, `value`, `unit`, `source_id`, `data_origin` (`observed/derived/synthetic`). Es **contrato propuesto, pendiente de aprobación**; no modelo ya implementado. PostgreSQL y MongoDB no comparten FK automática: la ingestión debe validar correspondencias.

## 3. Sprint 1: estructura y consultas obligatorias

### PostgreSQL (E pp. 8–10)

Entidades y atributos mínimos explícitos:

| Entidad | Atributos |
|---|---|
| Sensores | `id_sensor`, `nombre`, `tipo_sensor`, `fecha_instalacion`, `estado` |
| Ubicaciones | `id_ubicacion`, `nombre_zona`, `distrito`, `coordenadas` |
| Categorías de sensores | `id_categoria`, `nombre_categoria` |
| Usuarios del sistema | `id_usuario`, `nombre`, `correo` |
| Organismos responsables | `id_organismo`, `nombre`, `responsable` |

Obligatorio: modelo E-R, normalización hasta 3FN, PK, FK, índices adecuados y justificación. Las consultas implican relaciones sensor–ubicación, sensor–organismo y acceso a actividad; estas relaciones son necesidades inferidas de las consultas, no atributos enumerados literalmente en la lista mínima.

Demostrar `SELECT`, `WHERE`, `ORDER BY`, `DISTINCT`, `JOIN`/`INNER JOIN`/`LEFT JOIN`, `GROUP BY`, `HAVING`, `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`; subconsultas, CTE, funciones de ventana, fechas y uso de índices. E p. 2 menciona además vistas materializadas, particionamiento y optimización como dominio a demostrar: no omitirlos porque no figuren en las diez consultas. La consulta 9 pide vistas, sin exigir específicamente materializada.

Diez consultas (E p. 10; análisis de cobertura en la matriz):

1. Sensores por tipo.
2. Sensores por ubicación.
3. Cantidad de sensores activos e inactivos.
4. Número de sensores por organismo responsable.
5. Ubicaciones con mayor cantidad de sensores.
6. Sensores instalados por año.
7. Sensores sin actividad registrada.
8. Ranking de zonas monitoreadas.
9. Consulta utilizando vistas.
10. Consulta utilizando procedimientos almacenados o funciones.

Las preguntas sobre vehículos, temperatura, pérdida de envío, congestión, rutas y contaminación (E p. 9) son ejemplos adicionales, no una segunda lista de diez. «Sin actividad registrada» necesita inventario completo y ventana/definición de actividad; la primera lectura **no equivale** a fecha de instalación.

### MongoDB (E pp. 10–12)

Modelo documental para lecturas, eventos detectados, alertas automáticas, incidentes urbanos e información dinámica no estructurada; justificar modelo documental/NoSQL, flexibilidad y esquema. Los JSON ilustrativos de E p. 10 no constituyen una fuente real ni obligan a sus valores o coordenadas.

Obligatorio: `insertOne`, `insertMany`, `find`, `findOne`, `updateOne`, `updateMany`, `deleteOne`; filtros, operadores, proyecciones, ordenamiento, agregaciones, agrupaciones, índices y **Aggregation Framework**. P p. 3 propone documentos de prueba para operaciones destructivas: precaución del equipo, no ejecución autorizada aquí.

Diez consultas (E p. 12):

1. Lecturas de un sensor específico.
2. Lecturas en un rango de fechas.
3. Valores máximos y mínimos registrados.
4. Eventos críticos detectados.
5. Alertas emitidas por zona geográfica.
6. Promedio de mediciones por zona.
7. Promedio por tipo de sensor.
8. Incidentes registrados por categoría.
9. Consulta utilizando agregaciones.
10. Consulta utilizando filtros múltiples.

«Promedio de mediciones» requiere acordar si se promedian valores físicos o conteos; por seguridad proponer valores por variable/unidad, sin mezclar temperatura y contaminación. E p. 12 presenta el promedio de temperatura por zona como ejemplo, no resuelve todos los casos de esa ambigüedad.

## 4. Requisitos posteriores que condicionan los datasets

### Hadoop/HDFS (E pp. 2, 8, 13–14)

- Repositorio distribuido de históricos, datos raw/intermedios, registros de sensores, eventos y exportaciones JSON/CSV.
- Implementación futura pseudo-distribuida o Docker; configurar HDFS y estructura. No se instala en fase 0.
- Explicar bloques, replicación, tolerancia a fallos, escalabilidad, distribución entre nodos y procesamiento cercano a los datos.
- Demostrar `hdfs dfs -mkdir`, `-put`, `-ls`, `-cat`, `-get`, `-rm` en fase posterior autorizada.
- E p. 2 pide operaciones MapReduce o consultas Hive/Impala; E p. 8 asigna HDFS + MapReduce o Hive. Preparar almacenamiento y procesamiento batch, no reducir Hadoop a copiar archivos.
- Preguntas orientativas: mediciones por sensor, sensor con más datos, temperatura histórica media, eventos por zona y comportamiento por período. E pp. 13–14 **no enumera diez consultas obligatorias Hadoop**.
- Consecuencia: históricos identificables por fuente/período, sensores, eventos y zonas; formatos exportables. CSV comprimido o Parquet son preferencias (E p. 26), no exigencia exclusiva.

### Spark (E pp. 2, 15–16, 21, 26)

- ETL, transformaciones, acciones y análisis distribuido; preferentemente Spark SQL/DataFrames, Dataset API permitido. E p. 2 incluye joins, window functions y optimizaciones.
- Filtros, agrupaciones, joins, agregaciones, ordenamientos y consultas temporales.
- Ocho clases de análisis obligatorias: descriptivo, temporal, correlacional, predictivo **o de tendencias**, espacial, movilidad, anomalías y comparación. MLlib en un dibujo no convierte un modelo ML específico en obligación.
- Diez consultas/productos: sensores que generan más información; distribución geográfica de eventos; evolución temporal de indicadores; correlación entre variables; ranking de zonas con mayor actividad; tendencias por período; detección de anomalías; agrupamiento por categorías; comparación histórica entre años; dashboard analítico o reporte consolidado.
- Mínimo 1 000 000 de registros procesados: no se acreditó en esta fase.
- Consecuencia: al menos dos años comparables para comparación interanual, variables con coincidencia temporal/espacial para correlación, movilidad real, categorías, geografía y reglas trazables para eventos/anomalías. «Agrupamiento» no impone necesariamente clustering ML.
- Structured Streaming es opcional (E p. 2 y reto p. 22), aunque introducción/roles mencionen near-real-time/streaming. No presentar streaming como requisito cerrado sin aclaración.

### Dashboard (E pp. 17–21)

Panel principal único y selector de tecnología para ejecutar las consultas indicadas de PostgreSQL, MongoDB, Hadoop y Spark. No se evalúa principalmente sofisticación web; Streamlit recomendado, PowerBI segunda opción recomendada.

KPIs enumerados como mínimos en E p. 18:

| Dominio | Indicadores |
|---|---|
| Movilidad | Vehículos detectados; velocidad promedio; congestión promedio; accidentes/incidentes; tiempo promedio de recorrido |
| Ambiente | Temperatura global promedio; PM2.5 promedio; CO₂; humedad; número de alertas ambientales |
| Energía | Consumo total; promedio por zona; por hora; picos; variación respecto al período anterior |
| IoT | Número de sensores; mediciones recibidas; activos/inactivos; alertas; datos por minuto/hora/día; total de lecturas registradas por segundo |

Además: mínimo cuatro visualizaciones (serie temporal, comparación por zonas, distribución proporcional por tipo de sensor/vehículo y resultado **realmente generado por Spark**); filtros obligatorios de fechas/perfil horario, zona y tipo de medición/dispositivo; tabla con paginación o búsqueda; mapa para datasets con coordenadas; etiqueta de tecnología de origen en cada componente. Sensor, tipo de evento, fuente y rango de valores son filtros recomendados, no mínimos (E p. 19).

No obligatorios: login complejo, gestión de usuarios/perfiles, responsive avanzado, app móvil, microservicios, API REST completa, animaciones, diseño gráfico profesional o CRUD completo de todas las entidades (E pp. 19–20). La ausencia de gestión de usuarios en UI **no elimina** la entidad Usuarios del modelo PostgreSQL.

No asumir que escoger aire + tráfico basta: energía, CO₂, velocidad, recorridos e incidentes aún requieren cobertura o una aclaración docente del alcance.

## 5. Evidencias, calendario y responsables

E pp. 20–22, 27–28 exige documento técnico (fuentes, arquitectura, justificación, modelos relacional/documental, estrategia Big Data, procesamiento, resultados y conclusiones), código SQL DDL/DML, MongoDB/BSON, comandos HDFS, scripts/notebooks Spark y UI; matriz tecnológica/rendimiento argumentada y defensa en vivo con los cuatro componentes. Fuente y licencia se documentan según E p. 26. Los resultados deben obtenerse por ejecución posterior, no redactarse como ya medidos.

P propone José para fuentes/preparación/carga/respaldo, Daniel para PostgreSQL, Kembly para MongoDB, Fernanda para documentación; aprobación compartida de fuentes/IDs y revisión cruzada (P pp. 1–5). No se reasignaron responsabilidades aquí.

| Fecha de 2026 | Origen | Hito / estatus |
|---|---|---|
| 11 oct. | P p. 4 | Acceso y repositorio; propuesta interna, no verificada aquí |
| 12 oct. | P p. 4 | Fuentes y muestra; propuesta interna |
| 12–13 oct.; decisión 13 oct. | I p. 5 | Prueba de Madrid/NYC; propuesta preliminar |
| 14 oct. | P p. 4 | Modelos e IDs acordados; propuesta interna |
| 17 oct. | P p. 4 | Carga inicial; propuesta interna |
| 20 oct. | P pp. 1, 5 | Datos completos y respaldos de José; propuesta interna |
| 21 oct. | P p. 5 | Consultas preliminares; propuesta interna |
| 23 oct. | P pp. 1, 5 | Cierre técnico Daniel/Kembly; propuesta interna |
| 24–27 oct. | P p. 5 | Revisión cruzada, informe 25, congelamiento 26, demostración 27; propuestas internas |
| 28 oct. | P pp. 1, 5 | Primer avance declarado oficial por P; confirmar con docente, no aparece en E |
| 25 nov. | E p. 1 | Entrega final oficial |

## 6. Evaluación preliminar y fuentes candidatas

**Todos los números y ventajas siguientes son afirmaciones de I, no resultados verificados en fase 0.** La rúbrica de alternativas (I p. 1) usa pesos 20/15/15/10/10/10/10/10 para consultas/integración/dashboard/calidad/volumen/compatibilidad/facilidad/riesgo; no es la rúbrica académica E.

| Alternativa | Puntuación propuesta | Evaluación extraída de I pp. 2–3 | Pendientes |
|---|---:|---|---|
| Madrid: aire + tráfico + meteorología | 87/100 | Preferida provisionalmente; aire horario desde 2001 según I; misma ciudad e históricos municipales | Correspondencia estaciones–tráfico, frecuencias, CRS, validación, energía e incidentes; meteorología sin URL concreta en I |
| NYC: conteos automáticos + ambiente + 311 | 76/100 | Alternativa fuerte; I afirma ~1,88 millones de conteos de 15 minutos, segmentos/dirección/geometría; 311 aporta categorías/agencias | Muestreo no continuo; emparejar fechas y zonas; fuente ambiental no concretada; energía; 311 no equivale a accidente/alerta sensor |
| NYC: taxis + clima + 311 | 72/100 | Mucho volumen de viajes; variante menos alineada con sensores | Viaje no es lectura de sensor de tránsito; no reemplazar conteos por viajes sin justificar |
| Beijing Multi-Site + complementos | 79/100 | Respaldo ambiental; I afirma 420 768 observaciones horarias, 12 estaciones, 2013–2017, aire y meteorología | Nulos; insuficiente para 500 000 documentos si fila=documento; movilidad, energía, incidentes; varias variables en una fuente no acreditan dos fuentes |
| Londres LAQN + complementos | 77/100 | Red ambiental histórica y metadatos; alternativa ambiental sólida | Extracción por sitio/período, volumen, movilidad, energía e incidentes |

I no recomienda elegir solo por puntuación. Una celda de la matriz de cobertura debe pasar a verificada únicamente con ficha/metadatos y muestra real trazable; no basta una URL accesible.

Catálogo de códigos usados en el CSV:

| Código | URL / posible uso | Estatus fase 0 |
|---|---|---|
| MAD-AIR | https://datos.madrid.es/dataset/201200-0-calidad-aire-horario | Referencia de I; datos y metadatos no inspeccionados |
| MAD-TRAFFIC | https://datos.gob.es/es/catalogo/l01280796-trafico-historico-de-datos-del-trafico-desde-2013 | Referencia de I; pendiente descarga pequeña y diccionario |
| MAD-METEO | Meteorología municipal de Madrid | Sin URL concreta comprobada en I |
| NYC-COUNTS | https://data.cityofnewyork.us/Transportation/Automated-Traffic-Volume-Counts/7ym2-wayt | Referencia de I; no se verificó endpoint del dataset |
| NYC-311 | https://data.cityofnewyork.us/d/erm2-nwe9 | Referencia de I; no se inspeccionaron categorías/geografía |
| NYC-AIR | Complemento ambiental de Nueva York | Fuente exacta pendiente |
| BJ-AIR | https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data | Referencia de I; volumen/columnas aún no contrastados |
| LON-AIR | https://londonair.org.uk/london/asp/datadownload.asp | Página HEAD accesible; no implica extracción masiva viable |
| META | Metadatos/catálogos oficiales asociados a la ciudad elegida | Candidatos a identificar; no catálogo descargado |
| DERIVED | Resultado calculado de observaciones reales con regla y procedencia | No generado; no confundir con evento/alerta observada |
| PENDING | Fuente real adicional por identificar | Vacío sin cobertura comprobada |

E pp. 23–25 recomienda también OpenAQ, CityPulse, Kaggle/tráfico, IoTDataset, UCI, Data.gov y World Bank. Smart Data Models/FIWARE es **referencia de modelado, no dataset real**. La lista es recomendada, no cerrada; ejemplos como Online Retail no quedan automáticamente alineados con IoT urbano. I p. 3 menciona Chicago, Barcelona, openSenseMap y Metro Interstate como alternativas adicionales no priorizadas; no se auditaron en fase 0.

## 7. Atributos sin fuente real comprobada

Ningún campo de origen está verificado con muestras en esta fase. Los vacíos especialmente críticos, más allá de IDs/fechas/valores aparentemente disponibles, son:

| Exigencia | Vacío / regla para no inventar |
|---|---|
| `fecha_instalacion` | No documentada en candidatos. Nunca sustituir por primera observación sin etiquetar y aprobación |
| `estado` activo/inactivo | No comprobado. Estado administrativo y actividad durante una ventana son conceptos distintos |
| `nombre`, `tipo_sensor`, categorías | Identificar nombres/tipos oficiales; clasificaciones propias son derivadas, no metadatos observados |
| Organismo y `responsable`; vínculo sensor–organismo | Publicador no demuestra operador ni persona responsable; validar metadatos oficiales |
| Usuarios: `id_usuario`, `nombre`, `correo` | No aporta el informe una fuente real; son datos de aplicación, no sensores. Definir con docente/equipo, sin inventar identidades ni recopilar datos personales innecesarios |
| Zona, distrito, coordenadas | Presencia exacta, CRS y zonificación no comprobados; no inventar zonas ni equivalencias entre ciudades |
| Sensores sin actividad | Necesita inventario independiente de lecturas; ausencia en una muestra no prueba inactividad |
| Eventos críticos y alertas automáticas | No hay fuente de emisiones reales comprobada; detecciones por umbral pueden ser derivadas si se autoriza y se documenta, no alertas históricas emitidas |
| Incidentes por categoría | NYC-311 candidato, no validado; cobertura temporal/geográfica y semántica pendientes |
| CO₂ | Fuente pendiente. CO, NO₂ y PM2.5 no son sustitutos de CO₂ |
| Energía por zona/hora y períodos | Ninguna alternativa priorizada aporta fuente concreta comprobada; consumo no equivale a emisión ambiental |
| Velocidad, congestión, tiempo de recorrido, accidentes | Conteos no demuestran automáticamente estos atributos; evitar aproximaciones sin validación |
| Tasa de lecturas recibidas | `observed_at` no acredita hora de recepción; definir indicador histórico o incorporar `ingested_at` real posteriormente |
| Umbrales, severidad y anomalías | Reglas/unidades/estándares pendientes; el enunciado no aporta umbrales numéricos válidos para cada variable |

## 8. Inspección local y acceso a Internet

Repositorio: `/home/jp/Documentos/TEC/Bases/SmartCity/SmartCity` (el directorio externo `.../SmartCity` no es repositorio). Rama `main` con upstream `origin/main`, sin cambios al iniciar. No se encontró `AGENTS.md` en repositorio ni ancestros. No se consultaron credenciales ni estado de bases.

Archivos versionados iniciales: `.env.example`, `.gitignore`, `README.md`, `compose.yaml`, `data/.gitkeep`, `docs/.gitkeep`, `docs/README.md`, `mongodb/init/.gitkeep`, `postgres/init/.gitkeep`. No hay modelos, queries, muestras, ETL, dashboard ni manifiesto Python/entorno virtual dentro del repositorio. `data/*` está ignorado salvo `.gitkeep`; `research/datasets/` no está ignorado.

Inspección estática de Compose: PostgreSQL `16.6-alpine`, MongoDB `7.0.16`, volúmenes persistentes, red compartida y límites declarados de 512 MiB/0,25 CPU por servicio. Esto **no verifica** la configuración efectiva de Coolify ni sus recursos. No se inició Compose ni se modificó configuración.

Entorno local inspeccionado (no servidor remoto):

- Python del sistema: **3.12.3**, `/usr/bin/python3`; `pip`/`pip3` y `uv` presentes.
- Importables en ese intérprete: `requests` y biblioteca estándar (`csv`, `json`, etc.).
- No detectados en ese intérprete: `pypdf`, `pdfplumber`, `pandas`, `numpy`, `pyarrow`, `pymongo`, `psycopg`, `pyspark`. No afirma ausencia en todos los entornos del usuario.
- Ejecutables presentes: `pdftotext`, `pdfinfo`, `pdftoppm`, `git`, `curl`, `docker`, `psql`, `tailscale`.
- No encontrados en PATH: `java`, `hdfs`, `spark-submit`, `mongosh`. Su ausencia local no dice nada sobre Coolify.
- Extracción documental y CSV no requieren instalar paquetes. Un entorno Python aislado con dependencias de análisis queda como decisión futura, no se creó.

Pruebas externas mínimas HEAD, redirects habilitados, timeout 20 s, realizadas el 2026-10-09:

| URL solicitada | Resultado | Interpretación limitada |
|---|---|---|
| `https://datos.madrid.es/` | 200, HTML | Portal alcanzable; dataset/descarga no verificado |
| `https://data.cityofnewyork.us/` | Redirige a `https://www.nyc.gov/opendata`, 403 | Restricción en esa ruta/método; no prueba que la API/dataset sea inaccesible |
| `https://archive.ics.uci.edu/` | 200, HTML | Portal alcanzable; datos Beijing no verificados |
| `https://londonair.org.uk/london/asp/datadownload.asp` | 200, HTML | Página alcanzable; exportación y series no verificadas |

Hay conectividad HTTPS pública parcial. No se hicieron peticiones a bases remotas, descargas de archivos de datos ni pruebas de importación/rendimiento. La fase 1 está preparada **documentalmente**, no tiene datasets aceptados ni cobertura acreditada.
