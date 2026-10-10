# Fase 1 — Descarga y evidencia HTTP

## 1. Qué se verificó

La bitácora permanente [01_http_evidence.csv](01_http_evidence.csv) registra **cada probe HTTP del script local**: ID, URL solicitada/final, método, fecha UTC, código o error, Content-Type, Content-Length/Range, bytes efectivamente leídos, límite, SHA-256 de esos bytes y evidencia breve. Las páginas leídas adicionalmente con webfetch/websearch se citan en el informe; no se confunden con los probes del script. Las muestras crudas y respuestas completas/limitadas permanecen temporalmente en `/tmp/opencode/smartcity-phase1/`; no son datasets versionados ni garantías de retención permanente.

IDs del catálogo se resuelven en esa bitácora. SHA de un prefijo **no es hash del archivo completo**. `Content-Length` puede referirse al cuerpo HTTP comprimido en páginas HTML: no sirve para medir el tamaño descomprimido ni contar registros. Si falta, no se rellena con estimaciones. 200 de HTML no acredita CSV ni existencia de un dataset; se cotejaron campos/ZIP/catálogo cuando correspondía.

Las comprobaciones se realizaron 2026-10-10 01:59–02:09 UTC. Usaron `requests`, streaming, timeout conexión 15 s/lectura 40 s y máximo seis peticiones concurrentes. Datos grandes: lectura limitada a 4096/8192/16384 bytes; metadatos generalmente hasta 524288 bytes, excepcionalmente 1,5 MB para el esquema LL84 y catálogo EPA. No se instalaron dependencias ni se conectó a infraestructura privada.

## 2. Enlaces principales y resultados

Todos son URL oficiales/publicadas salvo templates claramente marcados. «Verificado» se refiere al mecanismo limitado, no a integridad de todo el archivo.

| Alternativa / fuente | Descarga/API concreta | Evidencia y alcance |
|---|---|---|
| Madrid aire anual 2025 | [CSV](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/resource/201200-1-calidad-aire-horario-csv/download/201200-1-calidad-aire-horario-csv.csv) | M07 206; 8192/20 166 384 bytes; cabecera H/V y enero 2025 |
| Madrid meteorología anual 2025 | [CSV](https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios/resource/300352-180-meteorologicos-horarios-csv/download/300352-180-meteorologicos-horarios-csv.csv) | M17 206; 8192/15 267 750 bytes; cabecera H/V |
| Madrid energía mensual | [CSV](https://datos.madrid.es/dataset/300430-0-consumo-energia-edificios/resource/300430-0-consumo-energia-edificios-csv/download/300430-0-consumo-energia-edificios-csv.csv) | M08 206; 8192/10 055 231; sensor/distrito/consumo/unidades |
| Madrid accidentes recurso 2026 | [CSV](https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle/resource/300228-34-accidentes-trafico-detalle/download/300228-34-accidentes-trafico-detalle.csv) | M18 206; 8192/6 595 925; expediente repetido por personas |
| Madrid inventario tráfico | [CSV](https://datos.madrid.es/dataset/202468-0-intensidad-trafico/resource/202468-306-intensidad-trafico/download/202468-306-intensidad-trafico.csv) | M16 206; 8192/714 026; id, distrito, coordenadas |
| Madrid histórico tráfico | [Descargas](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/downloads) | M03 200 catálogo inicial; ZIP recursos 161/160/137: M15/M23/M24 **403**; sin CSV comprobado |
| NYC conteos | [JSON dos filas](https://data.cityofnewyork.us/resource/7ym2-wayt.json?$limit=2) | N02 200; mecanismo SODA comprobado |
| NYC PM2.5 EPA nacional 2023 | [ZIP](https://aqs.epa.gov/aqsweb/airdata/hourly_88101_2023.zip) | N10 206; 4096/76 998 372; prefijo primer CSV; filtro NYC pendiente |
| NYC meteorología LaGuardia | [CSV 2023](https://noaa-global-hourly-pds.s3.amazonaws.com/2023/72503014732.csv) | N17 206; prefijo estación/coords; archivo 8 079 148 |
| NYC 311 2020–presente | [JSON](https://data.cityofnewyork.us/resource/erm2-nwe9.json?$limit=2) | N04 200; N14 agregado total timeout |
| NYC energía LL84 | [JSON un reporte](https://data.cityofnewyork.us/resource/5zyy-y8am.json?$limit=1) | N07 200; esquema N12 completo, N13 agregado |
| NYC notificaciones emitidas | [Esquema](https://data.cityofnewyork.us/api/views/8vv7-7wx3.json) / [datos](https://data.cityofnewyork.us/resource/8vv7-7wx3.json?$limit=2) | N18 200; N19 **503**. Fecha de envío sí publicada en esquema, geografía no explícita |
| Londres sitios LAQN | [JSON inventario](https://api.erg.ic.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json) | L01 200; 258 registros históricos/actuales |
| Londres MY1/NO2 un día | [JSON 2013-01-01](https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/SiteCode=MY1/SpeciesCode=NO2/StartDate=2013-01-01/EndDate=2013-01-02/Json) | L02 200; 24 lecturas GMT |
| Londres smartmeter LCL | [ZIP particionado](https://data.london.gov.uk/download/vqm0d/04feba67-f1a3-4563-98d0-f3071e3d56d1/Partitioned%20LCL%20Data.zip) | L06 **200 ignoró Range**; solo 4096 bytes leídos; Content-Length 795 722 689; header CSV extraído parcialmente |
| Londres DfT | [API dos conteos 2013](https://roadtraffic.dft.gov.uk/api/raw-counts?filter%5Bregion_id%5D=6&filter%5Byear%5D=2013&page%5Bsize%5D=2) | L04 200; paginación total 16 956; usar región 6 London |
| Londres NOAA Heathrow | [CSV 2013](https://noaa-global-hourly-pds.s3.amazonaws.com/2013/03772099999.csv) | L12 206; 8192/8 322 378 |
| Londres accidentes TfL | [CSV 2013](https://tfl.gov.uk/cdn/static/cms/documents/2013-gla-data-extract-attendant.csv) | L10 206; 8192/6 079 284 |
| Beijing UCI | [ZIP](https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip) | B01 HEAD 200; B05 GET 200,4096 bytes; ZIP dentro ZIP, no CSV interno leído |
| Beijing NOAA | [CSV 2013](https://noaa-global-hourly-pds.s3.amazonaws.com/2013/54511099999.csv) | B03 206,8192/6 937 352; B04 servicio por fechas también 200 |
| Beijing energía estimada | [API Figshare](https://api.figshare.com/v2/articles/25398559) / [ZIP publicado](https://ndownloader.figshare.com/files/45007633) | B07 API200 y tamaño/licencia; ZIP **no descargado/probado** |
| Barcelona aire | [CKAN](https://opendata-ajuntament.barcelona.cat/data/api/action/package_show?id=qualitat-aire-detall-bcn) | C02 200; recurso CSV C06 timeout |
| Barcelona tráfico | [CKAN trams](https://opendata-ajuntament.barcelona.cat/data/api/action/package_show?id=trams) | C05/C07 timeout; ficha timeout adicional |
| Chicago aire | [JSON](https://data.cityofchicago.org/resource/xfya-dxtq.json?$limit=2) | H02 200; sensor/coords/valores; H08 agregado timeout |
| Chicago congestión | [JSON](https://data.cityofchicago.org/resource/kf7e-cur8.json?$limit=2) | H04 200; H09 min/max fechas 200 |
| Chicago accidentes | [JSON](https://data.cityofchicago.org/resource/85ca-t3if.json?$limit=2) | H06 200; categoría/fecha/id |
| Chicago energía | [JSON](https://data.cityofchicago.org/resource/xq83-jr8c.json?$limit=1) | H07 200; un reporte no presentado, no afirmar consumo válido |
| openSenseMap caja Berlin | [JSON caja](https://api.opensensemap.org/boxes/582473be40198a001010e1a3) | S02 200; S03 una hora de sensor 200; URL completa en bitácora |
| OpenAQ | [API sin clave](https://api.openaq.org/v3/locations?limit=1) / [objeto AWS](https://openaq-data-archive.s3.amazonaws.com/records/csv.gz/locationid=2178/year=2022/month=05/location-2178-20220503.csv.gz) | O01 401; O03 206 objeto completo 797 bytes; ciudad/licencia proveedor pendientes |

NYC-CRASH tiene URL concreta en catálogo pero **no se probó**; no aparece como descarga acreditada aquí. Los candidatos ambientales NYC Health Real-Time y el indicador municipal `c3uy-2p5r` se exploraron, pero no se adoptaron como sustitutos de lecturas regulatorias horarias con sitio/fecha.

## 3. Reproducción segura de prefijos (solo si se autoriza repetir)

Este patrón cierra el stream al alcanzar el límite, incluso si el servidor ignora Range. No usar `curl URL -o archivo.zip` sin límite para comprobar un ZIP grande. Un `head` sobre un pipe no es control suficiente de bytes remotos si hay buffering.

```python
import hashlib
import requests

def read_prefix(url, limit=8192):
    with requests.get(url, headers={"Range": f"bytes=0-{limit-1}"},
                      timeout=(15, 40), stream=True) as r:
        r.raise_for_status()
        body = bytearray()
        for chunk in r.iter_content(4096):
            body.extend(chunk[:limit-len(body)])
            if len(body) >= limit:
                break
        return {
            "url": r.url, "status": r.status_code,
            "content_range": r.headers.get("Content-Range"),
            "content_length": r.headers.get("Content-Length"),
            "bytes_read": len(body),
            "sha256_prefix": hashlib.sha256(body).hexdigest(),
            "prefix": bytes(body),
        }
```

Un prefijo CSV puede terminar a mitad de registro o carácter: conservar encoding original, inspeccionar solo líneas completas, no ejecutar conteos/calidad globales. Madrid aire/meteo/energía/accidentes tienen BOM y separador `;`; números con coma decimal aparecen en energía/coordenadas. No reemplazar comas indiscriminadamente en campos de texto.

Para ZIP EPA/LCL se leyó cabecera local (`PK\x03\x04`, longitud de nombre y extra), y un `zlib.decompressobj(-15)` produjo **solo un prefijo limitado** del primer CSV cuando el método era deflate. No se obtuvo central directory completo, integridad ZIP, CRC de todo el miembro ni total de filas. UCI tiene ZIP anidado: la misma descompresión no proporcionó CSV; no atribuirle cabecera verificada. OpenAQ objeto gzip 797 bytes pudo descomprimirse completo; es un objeto pequeño no representativo de un histórico urbano.

## 4. Métodos de descarga futura por proveedor, no ejecutados

### Madrid

1. Seleccionar recurso por **año/mes y título del catálogo**, no por sufijo numérico supuesto. URLs de recursos tienen IDs estables pero contenido/cobertura pueden actualizarse.
2. Antes de cada descarga, comprobar cabecera/tamaño/Content-Type y presupuesto. Para aire/meteo 2024–2025, recuperar recursos correspondientes; no llamar «histórico desde 2001» a un único CSV anual.
3. Tráfico: actualmente bloqueo. Reintento limitado de URL oficial cuando se autorice, revisar comunicación de disponibilidad del publicador o contacto oficial. **No evasión de CDN, proxies ni rotación de IP**. Si persiste, considerar reserva y no simular archivo descargado.
4. Guardar hashes completos y manifest solo cuando fase 2 autorice descarga; permisos/licencias se conservan con cada versión.

### Socrata NYC/Chicago

Schema: `/api/views/{dataset_id}.json`; datos: `/resource/{dataset_id}.json` o `.csv`. Se comprobó acceso anónimo a los endpoints listados; no garantiza uso ilimitado. Emplear select de columnas y filtros antes de paginar; respetar 429/Retry-After, sin crear tokens en esta fase.

Ejemplos exactos **ya consultados**:

```text
https://data.cityofnewyork.us/resource/7ym2-wayt.json?$select=count(*)%20as%20n,min(yr)%20as%20first_year,max(yr)%20as%20last_year
https://data.cityofnewyork.us/resource/7ym2-wayt.json?$select=count(*)%20as%20n&$where=yr%3D2023
https://data.cityofnewyork.us/resource/5zyy-y8am.json?$select=count(*)%20as%20n,min(report_year)%20as%20first_year,max(report_year)%20as%20last_year
https://data.cityofchicago.org/resource/kf7e-cur8.json?$select=min(time)%20as%20first_date,max(time)%20as%20last_date
```

Paginación futura: orden total estable por claves naturales; filtros de año/fecha; no `$offset` sin `$order` ni asumir snapshot entre páginas de tablas vivas. Guardar corte/versionado y deduplicar claves. 311 tiene universo actualizado continuamente y total timeout: no repetir agregados masivos automáticamente. Consultas NY energía pueden devolver strings `Not Available`; convertir con regla, no `float()` a ciegas. Conservación de entidades padre/hijo y reportes revisados por auditar.

### EPA/NOAA

AirData publica archivos por parámetro/año con documentación. PM2.5 88101 fue probado; 88502 u otros parámetros **no fueron comprobados** ni deben deduplicarse contra 88101 sin examinar sitio/método. Filtro local del CSV nacional antes de contar: estado/condado/sitio y fechas, después unidades/qualifiers/POC. No descargar archivo nacional completo sin autorización/presupuesto explícito.

NOAA: S3 público `https://noaa-global-hourly-pds.s3.amazonaws.com/{year}/{station}.csv` probado para tres estaciones/años concretos. No implica que todos los años existan. Alternativa pequeña por fechas, B04 comprobada:

```text
https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly&stations=54511099999&startDate=2013-03-01&endDate=2013-03-02&format=csv
```

La ruta `www.ncei.noaa.gov/data/global-hourly/access/2013/54511099999.csv` devolvió 403, mientras S3 y el servicio oficial funcionaron: mecanismos publicados distintos, sin saltarse autenticación. Diccionario ISD oficial [PDF](https://www.ncei.noaa.gov/data/global-hourly/doc/isd-format-document.pdf), probe T01; normalizar escalas, QC y sentinelas antes de promediar.

### Londres

- LAQN patrón probado: `/AirQuality/Data/SiteSpecies/SiteCode={site}/SpeciesCode={species}/StartDate={date}/EndDate={date}/Json`. Inventario y catálogo de especies primero; extraer ventanas pequeñas por sitio/especie/año tras autorización. Límite final/exclusividad, huecos y ratificación se validan, no asumir que toda respuesta es completa.
- UKPN/LCL: la ficha publica ZIP completo y particionado. Ninguno se descargó completo; el particionado sigue siendo un archivo grande. Fase 2 debe acordar presupuesto y estrategia de subset (p. ej. un ZIP con archivos particionados y extracción controlada) antes de red; soporte Range **no demostrado**. No prometer acceso aleatorio remoto a cada CSV porque el ZIP contiene 168 archivos.
- DfT: [documentación API](https://roadtraffic.dft.gov.uk/api-documentation). Filtros `filter[region_id]=6`, `filter[year]`, `page[size]`, `page[number]`. Respuesta incluye total/links; se probaron años 2012 y 2013. Para bulk CSV, obtener URL del catálogo oficial y verificar tamaño; no usar API nacional sin filtros por defecto.
- TfL: descargar solo `attendant`/colisiones y año elegido cuando se autorice; casualty y vehicle son detalles relacionados, no fuentes independientes para inflar conteos.

### Reservas

- UCI: ZIP publicado anidado; requiere extracción acotada y validación de CSV en fase 2. No asumir 420 768 documentos válidos porque la ficha cuenta instancias.
- Figshare: API devuelve archivos y licencias. ZIP `45007633` 198 MB no se probó; lista ciudades `45008041` 3105 bytes es una comprobación futura pequeña antes de abrir GeoTIFF. Su contenido Beijing no se acreditó aún.
- Barcelona: CKAN `package_show` aire sí funciona a veces; `trams` y CSV probados timeout. No confundir JSON de metadatos con DataStore habilitado: ese mecanismo no se comprobó. URLs reales de recursos salen de `resources[].url`.
- openSenseMap: caja/UUID y endpoint histórico específico comprobados; límites de rango y continuidad por sensor a revisar antes de ampliar. PDDL documentada, registro de caja no instalación.
- OpenAQ: API v3 requiere API key; no creada/solicitada. AWS público probado para un objeto según documentación; obtener ubicación/proveedor/licencia y claves de objetos reales, no fabricar IDs para una ciudad ni usar endpoints retirados v1/v2 como solución.

## 5. Enlaces descartados y errores que no deben propagarse

- M11 (`201300-0-estaciones-calidad-aire`) dio 404: ID exploratorio incorrecto, **no inventario aceptado**.
- M19/M20/M22 devolvieron páginas HTML 200 de rutas exploratorias para episodios NO2/ozono y estaciones meteorológicas, sin recursos/dataset acreditados. No se incluyen como fuentes reales ni evidencia de alertas.
- N08 hostname exploratorio de archivo realtime NYC falló DNS; no URL oficial de descarga acreditada. N11 devolvió indicadores municipales, no inventario de observaciones horarias de sensores.
- N15 slug exploratorio `link-traffic-speeds` falló; no fuente de velocidad validada.
- H03 ruta exploratoria GitHub AoT 404; no concluye que todas las fuentes Chicago estén inaccesibles.
- Z01 búsqueda Zenodo de London Li-840 no devolvió un candidato usable. No seleccionar una medición londinense de 2010 como si cubriera 2013.
- Revisar URL oficial y contenido, no únicamente código HTTP. El portal Madrid mostró 200 y 403 para fichas entre pruebas: registrar ambos, no borrar el fracaso ni negar el acceso inicial.

## 6. Integridad puntual de prefijos

Estos hashes son de los bytes leídos, conservados también en bitácora. No acreditan integridad de recursos completos.

```text
M07 8192 bytes 17374cd397ad8b23f4a2b1136151c84002e58a102735e3638cab21ffd658214a
M17 8192 bytes d30103115cf7c1d60a9c6d678d0b12814d891f68b070e1ac83bc114f33d04714
M08 8192 bytes 2ab7e7024484a4892f1d8374f36b332232db838588bf2b8fe9f47bce41d29e7e
N10 4096 bytes da5548ba787db957a04f55b36f692bbecf68c4c6611bb9d95a885eb7bcba5392
L06 4096 bytes 89efc032c4c2cbe73b8943127052b88f92c739980032c31efaf46dfe5ad6d766
O03 797 bytes 96b8ce580eeb7ad1fe5fdfacaf5ffe430bc84f50cb52fd4a9c6cabbe879772c9
```

**Detención:** estos métodos son documentación, no autorización para iniciar descarga/auditoría ni ejecutar comandos posteriores.
