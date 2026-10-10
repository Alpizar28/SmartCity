# Fase 1 — Tres alternativas para auditoría

**Shortlist cerrada; dataset definitivo NO elegido. Fase 2 NO iniciada.**

La selección prioriza evidencia de acceso, integración urbana/temporal, campos reales, volumen potencial y esfuerzo antes del Sprint 1. No usa las puntuaciones preliminares de fase 0. Orden de presentación no constituye adjudicación definitiva.

## 1. Madrid — paquete municipal ambiental, climático, energético y de incidentes

**Fuentes:** MAD-AIR + MAD-METEO como núcleo probado; MAD-ENERGY + MAD-CRASH; MAD-TRAFFIC y su inventario como movilidad condicionada. Son datasets distintos del mismo ayuntamiento, no dos repositorios independientes.

- [Aire CSV 2025](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/resource/201200-1-calidad-aire-horario-csv/download/201200-1-calidad-aire-horario-csv.csv): 206, cabecera y fechas reales; recurso de 20,17 MB.
- [Meteorología CSV 2025](https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios/resource/300352-180-meteorologicos-horarios-csv/download/300352-180-meteorologicos-horarios-csv.csv): 206; recurso de 15,27 MB.
- [Energía mensual CSV](https://datos.madrid.es/dataset/300430-0-consumo-energia-edificios/resource/300430-0-consumo-energia-edificios-csv/download/300430-0-consumo-energia-edificios-csv.csv): 206; sensor/edificio/distrito/consumo.
- [Accidentes CSV 2026](https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle/resource/300228-34-accidentes-trafico-detalle/download/300228-34-accidentes-trafico-detalle.csv): 206; expedientes/categorías/geografía.
- [Catálogo tráfico histórico](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/downloads): catálogo 200 inicial, ZIP 403. **No descarga acreditada del histórico**.

**Integración defendible:** Madrid ciudad/hora entre aire y meteorología desde 2019; distrito/mes para energía; distrito/fecha para incidentes; tráfico por ID inventariado y período si se resuelve acceso. Ventana propuesta 2024–2025 para comparación, 2019–2026 para expansión; cobertura/joins aún no medidos.

**Por qué auditar:** formatos municipales coherentes, diccionarios y flags, energía con medidor y geografía real, incidentes reales, poca heterogeneidad institucional. Granularidad horaria permite potencial de 100k PG / 500k Mongo / 1M Spark sin crear sensores falsos, pero los conteos útiles siguen pendientes.

**Riesgos principales:** 403 de tráfico intermitente, geografía aire/meteo no comprobada, fechas de instalación/estado administrativo, consumo solo mensual, CO₂ y alertas emitidas sin fuente. No aceptar si el tratamiento de estos KPIs no se resuelve.

**Primera pregunta de auditoría:** ¿se puede obtener tráfico por un mecanismo oficial y conectar los inventarios correctamente, manteniendo volumen y período común sin síntesis?

## 2. NYC — conteos automáticos + EPA/NOAA + servicios urbanos y edificios

**Fuentes:** NYC-COUNTS + NYC-AIR EPA, NOAA LaGuardia, 311 y LL84; NYCEM como mensajes reales condicionados, NYPD accidentes pendiente. Hay repositorios independientes NYC/EPA/NOAA.

- [Conteos JSON](https://data.cityofnewyork.us/resource/7ym2-wayt.json?$limit=2): 200; total de endpoint **1 875 154**; 2023: **85 106**, comprobados por agregado.
- [EPA PM2.5 horario 2023 ZIP nacional](https://aqs.epa.gov/aqsweb/airdata/hourly_88101_2023.zip): 206, prefijo CSV; filtro y cantidad NYC pendientes.
- [NOAA LaGuardia 2023 CSV](https://noaa-global-hourly-pds.s3.amazonaws.com/2023/72503014732.csv): 206; estación y coordenadas reales.
- [311 JSON 2020–presente](https://data.cityofnewyork.us/resource/erm2-nwe9.json?$limit=2): 200; categorías/agencias/estado del trámite.
- [LL84 energía JSON](https://data.cityofnewyork.us/resource/5zyy-y8am.json?$limit=1): 200; **103 259 reportes**, 2022–2024 comprobados; energía anual, CO₂e separado.
- [NYCEM mensajes](https://data.cityofnewyork.us/resource/8vv7-7wx3.json?$limit=2): 503; esquema 200 confirma envío/tipo/cuerpo, no zona explícita.

**Integración defendible:** borough/hora entre campañas y sitios ambientales, contexto UTC NOAA; borough/año para energía. Período candidato 2022–2024 y ancla 2023, sujeto a cobertura real EPA y campañas. No contar todo New York State como NYC ni inferir sensor físico a partir de campaña.

**Por qué auditar:** API concreta accesible pese al 403 de la raíz previo; cantidad de origen suficiente globalmente; incidentes/organismos/categorías reales y mensajes emitidos localizados. Buena adecuación al modelo documental; diversidad de fuentes mejora comparación tecnológica.

**Riesgos principales:** WKT proyectado/correcciones ATR, campañas no continuas, filtro EPA no acreditado aún, energía anual, ausencia de velocidad/recorridos/instalación/estado, NYCEM 503 y zona desde texto pendiente. CO₂e no cubre concentración de CO₂.

**Primera pregunta de auditoría:** ¿cuántas observaciones únicas/útiles y sitios EPA de NYC coinciden con campañas DOT, y a qué granularidad geográfica sin joins artificiales?

## 3. Londres — LAQN + energía semihoraria UKPN + DfT/NOAA/TfL

**Fuentes:** LON-AIR/metadatos + LON-ENERGY UKPN, DfT conteos, NOAA Heathrow y TfL accidentes. Más de dos datasets/repositorios distintos.

- [LAQN MY1/NO2 2013-01-01](https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/SiteCode=MY1/SpeciesCode=NO2/StartDate=2013-01-01/EndDate=2013-01-02/Json): 200; 24 horas GMT.
- [Inventario LAQN](https://api.erg.ic.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json): 200; 258 sitios históricos/actuales, fechas apertura/cierre, propietario/gestor.
- [UKPN LCL ZIP particionado](https://data.london.gov.uk/download/vqm0d/04feba67-f1a3-4563-98d0-f3071e3d56d1/Partitioned%20LCL%20Data.zip): 200, prefijo ZIP/CSV válido; ~796 MB, **solo 4096 bytes leídos**; ~167 millones de filas documentadas, no contadas.
- [DfT conteos London 2013](https://roadtraffic.dft.gov.uk/api/raw-counts?filter%5Bregion_id%5D=6&filter%5Byear%5D=2013&page%5Bsize%5D=2): 200; 16 956 filas según paginación, días de campaña.
- [NOAA Heathrow 2013](https://noaa-global-hourly-pds.s3.amazonaws.com/2013/03772099999.csv): 206; cabecera/coordenadas.
- [TfL accidentes 2013 CSV](https://tfl.gov.uk/cdn/static/cms/documents/2013-gla-data-extract-attendant.csv): 206; borough/fecha/severidad.

**Integración defendible:** hora–ciudad para energía y ambiente, zona–hora/día solo entre fuentes con geografía. Ventana 2012–2013; no todos los hogares tienen cobertura uniforme. No ubicar hogares anónimos junto a estaciones LAQN.

**Por qué auditar:** es el finalista con energía genuina semihoraria y metadatos de ciclo de vida/propietario de sitio. Volumen documentado muy superior a mínimos, permite elegir subconjunto y estudiar Spark sin síntesis. Conservar diferencia entre sitio y dispositivo.

**Riesgos principales:** hogares sin borough/coordenadas, restricciones LAQN educativas/no comerciales, ZIP grande que ignora Range, campañas DfT no continuas, instalación individual/estado/CO₂/alertas/velocidad/recorridos no cubiertos. La energía por zona sigue bloqueada aunque haya energía por hora.

**Primera pregunta de auditoría:** ¿puede delimitarse un subconjunto pequeño, completo y reproducible de LCL y un conjunto LAQN compatible, aceptando explícitamente integración energética a nivel ciudad y la licencia LAQN?

## 4. Por qué estas tres y no las reservas

- **Chicago** es la primera reserva: IoT auténtico con 277 sensores, velocidad GPS estimada, accidentes y energía anual. Pero el aire empieza en 2025-09 y el tráfico termina en 2026-04: ventana común corta y mala comparación interanual. Podría superar a un finalista cuya auditoría falle; no se autoriza su sustitución automática.
- **Beijing** tiene UCI bien documentado y NOAA independiente como repositorio, más energía raster estimada. Peor cobertura de movilidad/incidentología/alertas, coordenadas UCI y volumen de 500k pendientes. Los datos aire+meteo ya integrados en UCI son una sola fuente descargada.
- **Barcelona** tiene históricos y licencia ambiental clara, pero las pruebas de tráfico y CSV fallaron por timeout. Mayor incertidumbre de acceso que los núcleos de los finalistas.
- **openSenseMap/OpenAQ** sirven para explorar sensores y transportes de datos; no se encontró paquete con segunda fuente local compatible superior. La caja Berlin no integra Madrid; agregadores no acreditan independencia del monitor original.

## 5. Cierre y puerta de entrada a fase 2

| Criterio de fase 1 | Resultado |
|---|---|
| Al menos 8 fuentes concretas | **30 catalogadas**, distinguiendo principales/complementos/metadatos y pendientes |
| Tres alternativas compuestas | Madrid,NYC,Londres; roles/períodos/claves y vacíos documentados |
| Mecanismo de principales | Dos fuentes centrales accesibles por alternativa; tráfico Madrid, EPA filtrado NYC y geografía LCL conservan condiciones explícitas |
| Información faltante | Campos exactos en [riesgos](01_source_risks.md), sin datos inventados |
| Integración preliminar | Ciudad/período y campos publicados; joins/cobertura **no auditados** |
| Justificación para auditoría | Ventajas, riesgos y primeras preguntas por alternativa, no aceptación definitiva |

«Alternativa completa» aquí es **un paquete de propuesta completo**, no una declaración de que todos los atributos académicos están cubiertos. Si se exige 100% de cobertura real sin derivados ni vacíos, **ninguna de las tres está demostrada como aceptable**. Ese límite se comunica antes de fase 2, no se oculta tras puntuaciones.

Autorización futura debe precisar presupuesto de descargas/muestras, períodos y auditorías locales; **no autoriza por defecto acceso remoto ni cambios de infraestructura**. No hay push/merge, instalación de servicios ni fase 2 automática. **Detenerse y esperar autorización.**
