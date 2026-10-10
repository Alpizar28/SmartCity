# Fase 1 — Investigación de fuentes SmartCity

**Finalizada para investigación y shortlist; no aceptación de datos ni inicio de fase 2.** Fecha de trabajo: 9 de octubre de 2026; las verificaciones registradas por el reloj del entorno abarcan **2026-10-10 01:59–02:09 UTC**. Los resultados HTTP son puntuales, no garantías futuras.

## 1. Alcance y autoridad

Se leyeron los cuatro entregables de fase 0. Se mantienen los requisitos documentados allí: 10 consultas PostgreSQL, 10 MongoDB, 100 000 registros relacionales, 500 000 documentos, 1 000 000 registros procesados posteriormente con Spark y al menos dos fuentes distintas. No se reabrieron cuestiones académicas resueltas ni se usaron las notas preliminares de I para seleccionar.

Se investigaron **30 fuentes concretas** de Madrid, Nueva York, Londres, Beijing, Barcelona, Chicago, openSenseMap y OpenAQ, incluyendo inventarios y complementos. El catálogo distingue datos principales de metadatos auxiliares y fuentes cuyo acceso sigue fallando. Dos datasets distintos del mismo portal satisfacen la propuesta de integración de fuentes, pero no se presentan como dos repositorios independientes.

Etiquetas de evidencia:

- **C — comprobado:** respuesta HTTP, metadatos devueltos o campos observados en un prefijo/muestra pequeña.
- **D — documentado:** afirmación del organismo/repositorio o diccionario; no conteo local de todo el archivo.
- **E — estimado:** fórmula de capacidad o supuesto de planificación, nunca resultado de auditoría.
- **P — pendiente:** sin prueba suficiente; incluye licencias, coordenadas y cobertura no confirmadas.

No se perfilaron datasets completos, no hubo importaciones, generación sintética, conexiones a PostgreSQL/MongoDB ni modificaciones a Coolify/Tailscale. Se consultaron APIs públicas HTTPS con límites pequeños y agregados de catálogo. Se descargaron diccionarios PDF de menos de 1 MB cada uno y prefijos de archivos; **no datasets grandes**. El ZIP London LCL ignoró Range y respondió 200: se cerró el stream tras 4096 bytes, no se descargaron sus ~796 MB. Consultar [métodos y evidencias](01_download_methods.md).

## 2. Madrid: mayor coherencia municipal, acceso al tráfico pendiente

### MAD-AIR — Calidad del aire horaria desde 2001

[Ficha oficial](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario). Organismo: Ayuntamiento, Dirección General de Sostenibilidad y Control Ambiental. Condiciones municipales CC BY 4.0 [comprobadas](https://datos.madrid.es/pages/condiciones-de-uso). Archivos anuales ZIP/CSV; el CSV examinado comienza en enero de **2025**, no contiene toda la historia desde 2001. C: Range 206, tamaño total de ese recurso **20 166 384 bytes**, prefijo 8192 bytes.

Campos C: `PROVINCIA`, `MUNICIPIO`, `ESTACION`, `MAGNITUD`, `PUNTO_MUESTREO`, `ANO`, `MES`, `DIA`, `H01..H24`, `V01..V24`. El diccionario oficial descargado, 707 858 bytes, explica códigos de estación, magnitud, técnica y banderas. PM2.5/PM10/NO2/O3 se expresan en µg/m³; CO en mg/m³. **CO no es CO₂**. No todas las estaciones miden todos los contaminantes.

Las coordenadas no están en el prefijo de lecturas; deben proceder de inventario/cartografía oficial. El anexo identifica nombres/códigos, no acredita instalaciones de dispositivos ni estado administrativo. Clave candidata: fuente + punto de muestreo + fecha + hora, pendiente de unicidad/DST. La expansión de columnas horarias sería una transformación de observaciones reales, no generación sintética; su granularidad debe aprobarse, y los inválidos no deben inflar conteos útiles.

### MAD-METEO — Meteorología municipal desde 2019

[Ficha](https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios), C/D: cobertura anunciada 2019-01-01–2026-08-31, misma dirección responsable y CC BY 4.0. Recurso anual 2025: C 206, **15 267 750 bytes**, misma estructura diaria de 24 valores/flags. `ESTACION=102`, `MAGNITUD=81` en el prefijo; `PUNTO_MUESTREO` puede estar vacío. D: temperatura, humedad, viento y otras magnitudes meteorológicas; las unidades exactas y códigos deben fijarse mediante su diccionario antes de normalizar, no copiar los del aire.

Son dos redes/datasets distintos, con período común **2019–2026** documentado. Una estación meteorológica 102 no es la estación ambiental 102 por coincidencia numérica. Es viable una integración temporal de indicadores municipales; el join local por distancia/distrito sigue condicionado a coordenadas oficiales y medición de cobertura.

### MAD-TRAFFIC + MAD-TRAFFIC-META

[Histórico desde 2013](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico) y [puntos de medida](https://datos.madrid.es/dataset/202468-0-intensidad-trafico). El diccionario oficial, 991 314 bytes, describe `id`, `fecha`, `tipo_elem`, `intensidad`, `ocupacion`, `carga`, `vmed`, `error`, `periodo_integracion`; intensidad en vehículos/hora, velocidad en km/h, ocupación y carga porcentuales. D: habitual integración de 15 minutos, intervalos y errores a verificar por archivo. Velocidad no está disponible de forma equivalente para todos los puntos.

C: el catálogo de descargas fue accesible inicialmente; **tres ZIP probados devolvieron 403** (recursos 161, 160, 137) y la ficha también devolvió 403 en una comprobación posterior. No se sorteó el bloqueo ni se atribuyó al dataset una muestra inexistente. Sí se obtuvo prefijo del inventario: `id`, `cod_cent`, `tipo_elem`, `distrito`, `utm_x/y`, `longitud/latitud`; recurso **714 026 bytes**. Permite clave de unión `id` con el histórico si la auditoría demuestra correspondencia temporal del inventario. No prueba fecha de instalación ni estado.

### MAD-ENERGY + MAD-CRASH

[Energía municipal](https://datos.madrid.es/dataset/300430-0-consumo-energia-edificios): C prefijo y diccionario de 167 499 bytes. Datos **mensuales**, desde marzo de 2020 (D), recurso 10 055 231 bytes (C). Campos reales `SENSOR`, `ID` edificio, barrio/distrito con códigos, coordenadas, `CLASE`, `GRUPO`, `UNIDADES`, `CONSUMO`. Hay kWh, kvarh y m³, que no se suman juntos. Riesgo adicional: medidores generales/submedidores y grupos pueden solaparse; el consumo total requiere jerarquía y evitar doble cómputo. Un nombre de sensor energético sí está publicado, pero no demuestra instalación ni propietario individual.

[Accidentes](https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle): C 206, recurso 2026 de 6 595 925 bytes. `num_expediente`, fecha/hora, distrito, tipo de accidente, UTM, datos de persona/vehículo. **Una fila puede ser una persona involucrada, no un accidente**: el expediente se repite en la muestra. No contar filas como incidentes únicos. No son alertas emitidas por un sensor.

Conclusión: paquete municipal técnicamente defendible con aire + meteorología ya accesibles, energía e incidentes reales y tráfico condicionado. Mejor integración por distrito/período; todavía faltan geografía de aire/meteo, instalación/estado, energía horaria, CO₂ ambiental y alertas históricas emitidas. No declarar cobertura completa del dashboard.

## 3. Nueva York: API funcional, volumen comprobado y mejor variedad documental

### NYC-COUNTS

[Automated Traffic Volume Counts](https://data.cityofnewyork.us/d/7ym2-wayt), DOT. C: JSON de dos filas con `requestid`, `boro`, `yr/m/d/hh/mm`, `vol`, `segmentid`, `wktgeom`, calles y dirección. El agregado público devuelve **1 875 154 filas**, años **2000–2026**; el filtro `yr=2023` devuelve **85 106 filas**. Son conteos del endpoint al momento de consulta, no conteos descargados ni 1,875 millones de sensores. D: intervalos de 15 minutos y campañas discontinuas, actualización semestral.

`wktgeom=POINT (1035363.4 185093.4)` no son grados WGS84. CRS por confirmar en el diccionario (posible sistema estatal proyectado, no darlo por probado). `requestid` identifica campaña/solicitud, `segmentid` segmento; **no existe prueba de ID físico permanente del contador**. Adjuntos de metadatos incluyen diccionario y `ATR Location_Errors2025.xlsx`: hay correcciones geográficas que auditar. No contiene velocidad/recorrido/congestión.

### NYC-AIR + NYC-WEATHER

Se eligió como complemento ambiental auditable **EPA AQS AirData PM2.5 horario 2023**, no el dataset NYC de indicadores de salud como si fueran lecturas. [Descargas oficiales](https://aqs.epa.gov/aqsweb/airdata/download_files.html), archivo nacional `hourly_88101_2023.zip`: C 206, **76 998 372 bytes** comprimidos; se descomprimió solo el comienzo del primer miembro desde 4096 bytes de ZIP. Encabezado: estado/condado/sitio, parámetro, POC, latitud/longitud/datum, fecha/hora local y GMT, `Sample Measurement`, `Units of Measure`, método, MDL, incertidumbre y qualifiers. Son mediciones regulatorias de proveedores estatales/locales, archivadas por EPA; no un inventario del DOT.

Filtro geográfico previsto: estado 36 y condados NYC **005, 047, 061, 081, 085**, validando existencia de cada sitio y sus unidades, sin asumir cobertura en los cinco boroughs. **El prefijo del ZIP nacional no demuestra registros de NYC ni conteo local**: condición de auditoría. POC/método pueden producir series simultáneas que no deben colapsarse sin regla.

Meteorología independiente: NOAA ISD/Global Hourly, estación **72503014732 LaGuardia**, C prefijo 2023, coordenadas 40.77945, -73.88027, archivo 8 079 148 bytes. Campos `TMP`, `DEW`, `WND`, `SLP`, flags y sentinelas codificados. Temperatura/débil resolución temporal a normalizar; humedad puede derivarse de temperatura y punto de rocío con fórmula explícita, no atributo observado garantizado. Una estación aeroportuaria no representa todos los barrios. ISD aporta UTC y puede tener varios informes por hora, no una fila regular/hora.

### NYC-311 + NYC-ENERGY + NYC-ALERT + NYC-CRASH

[311](https://data.cityofnewyork.us/d/erm2-nwe9): metadatos C confirman **2020–presente**; no asumir que conserva 2010–2019. C: solicitud, categoría, agencia, fecha, estado, dirección, borough; coordenadas pueden faltar. Estado de una solicitud **no es estado de un sensor**. El agregado total agotó timeout; no se inventa total. Suficiencia de volumen del paquete puede descansar en conteos DOT multi-anuales, no exclusivamente en 311.

[Local Law 84](https://data.cityofnewyork.us/d/5zyy-y8am), DOB: C **103 259 filas**, años reportados **2022–2024**. Campos reales propiedad/BBL, energía anual por combustible, kWh/kBtu, borough, latitud/longitud en esquema; emisiones `direct_ghg_emissions_metric` y otros campos en toneladas **CO₂e**. Es un informe anual de propiedades, con autodeclaración y revisiones, no series horarias ni sensores individuales. CO₂e de energía **no equivale a concentración ambiental de CO₂ en ppm**. Nombres largos, valores `Not Available` y propiedades padre/hijo exigen normalización y control de doble conteo.

[NYCEM Emergency Notifications](https://data.cityofnewyork.us/d/8vv7-7wx3): fuente **real de mensajes emitidos**, hallazgo distinto de 311. C: esquema `record_id`, `date_and_time` (envío), `notificationtype`, `notification_title`, `email_body`; organismo NYCEM, frecuencia diaria D. La muestra de datos devolvió **503**. No tiene columna geográfica explícita en esquema: clasificación territorial desde texto sería derivada y requiere validación; no afirmar cobertura de alertas por zona ni alerta automática de sensor. [Colisiones NYPD](https://data.cityofnewyork.us/d/h9gi-nx95) es un complemento concreto pendiente de prueba HTTP, útil para accidentes, no sustituto de conteos.

Licencias municipales: términos de NYC, no CC BY acreditada por defecto; guardar cláusulas y atribución aplicables antes de redistribuir muestras. NOAA/EPA: condiciones de datos públicos estadounidenses, revisar excepciones de terceros; no inventar una licencia SPDX universal.

Conclusión: integración por borough/hora para conteos–aire–meteorología y borough/año para energía; mezcla de repositorios públicos distintos, amplio volumen pero coincidencia de campañas y CRS difíciles. Ventana candidata **2022–2024**, ancla 2023; no existe aún conteo de intersección entre fuentes.

## 4. Londres: energía semihoraria e inventario más rico; geografía energética limitada

### LON-AIR + LON-AIR-META

[LAQN API](https://www.londonair.org.uk/Londonair/API), ERG Imperial College London y autoridades locales financiadoras. C: API devuelve **258 registros de sitios**, incluyendo históricos cerrados, no 258 sensores actualmente activos. `SiteCode`, nombre/tipo, autoridad local, `DateOpened`, `DateClosed`, `DataOwner`, `DataManager`, latitud/longitud. MY1 Marylebone Road: abierto 1997-05-26; propietario Westminster. El campo `DataManager` conserva King's College London en ese registro: no reescribirlo por asumir que coincide con el operador actual.

La API MY1/NO2 para 2013-01-01 devolvió **24 lecturas horarias**, fecha GMT y valores. D: NO2/O3/PM en µg/m³ y CO en mg/m³; catálogo de especies disponible. **No es CO₂**. C: `LatitudeWGS84`/`LongitudeWGS84` en MY1 tienen valores ~6,7 millones/-172 000, mientras `Latitude`/`Longitude` son 51.52254/-0.15459. El nombre de columna no basta para identificar CRS; se debe validar, y no usar aquellos como grados.

Las [condiciones LAQN](https://www.londonair.org.uk/london/asp/copyright.asp) autorizan usos informativos/educativos, **NO operativos/comerciales**. No es una licencia abierta CC BY acreditada. El proyecto académico parece compatible con uso educativo, pero redistribución de datos y despliegue deben revisarse; datos de menos de 12 meses pueden cambiar con ratificación. Apertura/cierre de estación es información real útil para un ciclo de vida de sitio, no fecha de instalación de cada analizador.

### LON-ENERGY

[UK Power Networks Low Carbon London](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d). D: 5567 hogares, noviembre 2011–febrero 2014, alrededor de **167 millones de filas**, ~10 GB descomprimidos, licencia CC BY 4.0 en ficha C. C: respuesta 200 del ZIP publicado, `Content-Length=795722689`; prefijo ZIP y primeras filas descomprimidas con `LCLid`, `stdorToU`, `DateTime`, `KWH/hh (per half hour)`. Ejemplo MAC000002 desde 2012-10-12. El nombre de recurso «168 archivos de un millón» no permite inferir exactamente 168 millones de lecturas útiles.

Suma de intervalos semihorarios produce energía horaria real derivada (kWh), si ambos intervalos son válidos y se define el período. **Los hogares no tienen coordenadas ni borough en el esquema comprobado**. Solo agregación a Londres/ciudad es defendible con estos datos; no asignarlos a estaciones ambientales ni a distritos artificiales. Household ID tampoco acredita ID de medidor físico ni instalación.

### LON-COUNTS + LON-WEATHER + LON-CRASH

[DfT Raw Counts](https://roadtraffic.dft.gov.uk/downloads): C API sin credencial para Londres `region_id=6`, 2013, devuelve `count_point_id`, fecha/hora, dirección, autoridad, coordenadas y categorías de vehículos. Total de metadatos paginados **16 956 filas** para ese filtro; conteos de días de campaña, **no todos los días del año**. No usar AADF anual como observación horaria. DfT enlaza OGL v3. NOAA Heathrow 03772099999: C CSV 2013, 8 322 378 bytes, 51.4775/-0.461389, esquema ISD. Es contexto de ciudad, no clima observado en cada estación.

[TfL accidentes 2013](https://tfl.gov.uk/corporate/publications-and-reports/road-safety): C recurso `2013-gla-data-extract-attendant.csv`, 6 079 284 bytes, con referencia AREFNO, borough, easting/northing, fecha/hora, severidad y vehículos; no bajar vehículos/personas para duplicar accidentes. Uso/licencia específicos pendientes, no heredar OGL de DfT automáticamente.

Período de integración: 2012–2013, ancla 2013, con energía/aire/tráfico/clima/accidentes reales. Granularidad común **hora–ciudad** para energía; zona–día/hora solo entre fuentes con geografía real. E: 100 hogares × 365 × 48 = 1 752 000 intervalos potenciales/año; una fórmula de selección futura, no un conteo medido. Buen candidato para Spark/energía y fechas de sitios; limitaciones para energía por zona, velocidad, recorridos, CO₂ y alertas emitidas.

## 5. Alternativas investigadas y no seleccionadas

### Beijing: UCI + NOAA + electricidad raster estimada

[UCI Multi-Site](https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data) documenta **420 768 filas**, 12 estaciones, 2013-03-01–2017-02-28, CC BY 4.0. Seis contaminantes PM2.5, PM10, SO2, NO2, CO, O3 (µg/m³ según ficha), temperatura/DEWP °C, presión hPa, lluvia mm, viento m/s/dirección. Faltantes `NA`. Aire BMEMC y meteorología CMA emparejada por estación próxima vienen **en un único dataset integrado**, no son dos descargas independientes. ZIP accesible C, primer miembro es otro ZIP; no se obtuvo CSV interno ni se fingió una muestra tabular. Nombres de estación no proporcionan coordenadas verificadas.

NOAA aeropuerto **54511099999** aporta segunda fuente independiente (repositorio NOAA con procedencia internacional de informes, no mediciones CMA originales garantizadas independientes físicamente). C prefijo 2013: 6 937 352 bytes, 40.080111/116.584556. Ventana común 2013–2017 D. Sirve contexto meteorológico urbano y contraste, no vínculo sensor-aeropuerto ficticio. En vez de duplicar o descomponer variables solo para superar 500 000 documentos, hace falta seleccionar historia NOAA suficiente y contar observaciones válidas; no se acredita aquí ese umbral.

[Yan/Huang, Scientific Data](https://www.nature.com/articles/s41597-024-03684-4) y [Figshare 25398559](https://doi.org/10.6084/m9.figshare.25398559.v1): C API licencia CC BY 4.0, ZIP **198 361 539 bytes**, 93 GeoTIFF mensuales abril 2012–diciembre 2019, resolución 1 km, proyección Albers. Son **estimaciones publicadas de consumo eléctrico mediante modelo**, no telemetría de medidores y no sintéticos generados por este equipo. Unidades/bandas/rangos locales y presencia efectiva de Beijing pendientes de muestra raster/listado de ciudades. Sin movilidad, alertas ni incidentes compatible comprobado. Queda fuera por esfuerzo GIS y vacíos académicos, no por la puntuación previa.

### Barcelona: buenas fichas, extracción inestable

[Aire detallado](https://opendata-ajuntament.barcelona.cat/data/dataset/qualitat-aire-detall-bcn): C CKAN devuelve licencia CC BY 4.0, 106 recursos, histórico mensual hasta diciembre 2018 en listado; schema vigente incluye estación/contaminante, año/mes/día y H/V 01–24. Metadatos indican catálogos separados de estaciones y contaminantes y necesidad de usar inventario del mismo año (o anterior). Esquema antiguo tenía latitud/longitud; no trasladarlos como existentes en todos los archivos nuevos. CSV de enero 2026 agotó timeout.

[Tramos de tráfico](https://opendata-ajuntament.barcelona.cat/data/dataset/trams): D publicación de estado de tramos y archivo histórico CSV; API CKAN y ficha agotaron timeout reiteradamente. Escala de estado/congestión no equivale a conteo, velocidad o tiempo observado sin diccionario. No hay licencia, volumen ni segunda descarga principal acreditados para esta alternativa. Reserva, no una fuente ficticiamente validada.

### Chicago: competidor sólido, descartado por ventana histórica corta común

[Open Air Chicago Individual Measurements](https://data.cityofchicago.org/d/xfya-dxtq): C esquema/muestra de sensores Clarity Node-S, `datasourceid`, nombre, coordenadas, PM2.5/NO2 calibrados, temperatura/humedad y `record_id`. D: **277 sensores no regulatorios**, implantación verano 2025, histórico desde septiembre 2025, actualización diaria. No usar esa implantación colectiva como fecha exacta de cada sensor. Los módulos black carbon figuran offline en descripción; muestra no demuestra cobertura de todas las variables. Unidades se deben confirmar por diccionario antes de convertir NO2/PM.

[Traffic Tracker Historical Regions](https://data.cityofchicago.org/d/kf7e-cur8): C muestra de velocidad estimada, región, conteo de buses/lecturas y límites espaciales; agregado min/max confirma **2018-03-09–2026-04-30**, y metadatos dicen que ya no se actualiza. D: estimación por GPS de buses CTA, intervalos de diez minutos y 29 regiones, no medidores fijos. [Crashes](https://data.cityofchicago.org/d/85ca-t3if) tiene muestra C de IDs, fecha, categoría, severidad e información vial; [Energy Benchmarking](https://data.cityofchicago.org/d/xq83-jr8c) muestra C de edificio, estado del reporte, año, área y coordenadas. Es energía anual, no horaria ni estado de sensor. Licencia/condiciones municipales específicas por revisar antes de reutilización; no atribuir CC BY a partir de Socrata.

Paquete defendible por zona/tiempo y puede sustituir una alternativa si fracasa su auditoría. Solo ~8 meses comunes aire–tráfico (septiembre 2025–abril 2026), atraviesa dos años parciales pero no dos ciclos anuales comparables: peor para comparación interanual y tendencias que las tres elegidas. No descartar todo Chicago por Array of Things: es otra red; una URL AoT exploratoria dio 404 y no prueba estado del nuevo Open Air Chicago.

### openSenseMap / OpenAQ

openSenseMap es más que un portal: se comprobó una caja concreta **582473be40198a001010e1a3**, Freie Universität Berlin, 13.302834/52.457219, sensores con UUID, unidad/modelo, historial de posiciones y `createdAt`. API de una hora del sensor de temperatura devuelve lecturas. `createdAt` de caja es registro en plataforma, **no instalación**. La lectura repetida **-37.41 °C** en Berlín y PM antiguos/extremos son señales para auditar, no prueba global de mala calidad ni anomalía física confirmada. PDDL 1.0 documentada por senseBox; guardar condiciones vigentes antes de elegir. Caja de Berlín no es complemento de Madrid/Londres. Para alternativa Berlin haría falta una segunda fuente local probada, no acreditada aquí.

OpenAQ v3 devolvió **401 sin API key**. Sin crear cuenta ni obtener credenciales. La [documentación AWS](https://docs.openaq.org/aws/quick-start) muestra archivo público alternativo: C objeto ubicación 2178/2022-05-03, 797 bytes gzip, CSV con ubicación/sensor, coordenadas, fecha, parámetro, valor y unidad. Esa muestra no prueba cobertura de ninguna ciudad finalista ni que el agregador sea una segunda fuente independiente del mismo monitor EPA/LAQN. Licencia depende de proveedor; revisar endpoint de licencias cuando se autorice API. Útil como transporte/descubrimiento, no para contar dos veces el mismo origen físico.

## 6. Comparación y selección

| Alternativa | Evidencia que la distingue | Integración preliminar defendible | Debilidad decisiva | Esfuerzo relativo propuesto, no medido |
|---|---|---|---|---|
| Madrid | Aire/meteo/energía/accidentes con prefijos; inventario tráfico con IDs y geografía | Municipio y período; distrito/coordenadas cuando se verifiquen inventarios | Tráfico ZIP 403; energía mensual; instalación/estado/CO₂/alertas | Medio, con riesgo de acceso |
| NYC | Conteos exactos públicos; JSON flexible; energía, agencias y fuente de mensajes reales | Borough/período, campañas y sitios EPA; energía a año | CRS/cobertura EPA NYC pendiente; energía anual; mensajes 503 y sin zona explícita | Medio–alto |
| Londres | Apertura/cierre/propietario de sitios; aire 2013; energía semihoraria y CSV de accidentes | Ciudad/hora para energía; zona/hora/día para fuentes geográficas | Hogares anónimos sin zona; licencia LAQN restrictiva; tráfico de campañas | Alto por tamaño/extracción, mitigable con límites |
| Chicago | Red 277 sensores + velocidades regionales + incidentes + energía | Regiones/tiempo, con cruce espacial por validar | Aire desde 2025 y tráfico terminado abril 2026; energía anual | Medio, reserva fuerte |
| Beijing | UCI cerrado/documentado + NOAA + raster independiente | Contexto ciudad/hora y energía mensual raster | Sin movilidad/incidentes/alertas; geografía y conteos por motor insuficientes | Alto por GIS y complementos |
| Barcelona | CKAN/diccionario e históricos ambientales | Potencial de ciudad/tramos | Timeouts en segunda fuente y descarga principal | Alto por incertidumbre de acceso |
| openSenseMap/OpenAQ | API/sensor real o archivo público mínimo | Solo tras seleccionar origen/caja y segunda fuente local | Licencias por proveedor, continuidad, identidad/independencia | Variable |

La elección es **shortlist de tres paquetes para auditar**, no aceptación definitiva. «Completa» significa propuesta compuesta que incluye fuentes, roles, períodos, métodos y vacíos de cada dominio; **no significa que todas las consultas y KPIs tengan datos reales acreditados**. Ninguna alternativa demostró esa cobertura estricta. Véanse [arquitecturas](01_candidate_architectures.md), [riesgos](01_source_risks.md) y [shortlist](01_shortlist.md).

La viabilidad de integración se apoya en ciudad/período y atributos publicados; no se midió porcentaje de emparejamiento ni se ejecutó join. Los paquetes no dependen de generación sintética para obtener volumen básico potencial, pero pueden requerir una decisión expresa sobre atributos administrativos y KPIs sin fuente antes de aprobarlos.
