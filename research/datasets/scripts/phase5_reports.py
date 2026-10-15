"""Generate reviewable Phase5 documents from measured evidence, never access engines/network."""
import csv
import json
import xml.etree.ElementTree as ET

from phase5_legacy_contract import ROOT, OUT, PRIVATE, VERSION, digest


def write(name, text):
    (ROOT/name).write_text(text.strip()+'\n')


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(str(v).replace('|','/') for v in r)+' |' for r in rows])


def dictionary(prep):
    rows = []
    # field, meaning, SQL type, BSON type, original field, origin, availability, null, unit, rule/method
    common = [
      ('sensor_id','Dispositivo físico acreditado; NO canal','text FK sensors','string/null','No publicado',None,'unavailable',True,'n/a','NULL hasta evidencia individual; nunca igualar a channel_id'),
      ('station_id','Sitio de una red; namespaces separados','text FK stations','string','ESTACION / id','derived','available',False,'n/a','SHA256 sca-id-v1, fuente+clave de sitio; no fusionar aire/meteo por código'),
      ('zone_id','Distrito publicado; no barrio inferido','text FK zones','string/null','Inventario tráfico.distrito','derived','partial',True,'n/a','madrid:district:1..21; aire/meteo NULL; vigencia histórica pendiente'),
      ('channel_id','Serie lógica; variable/técnica o feed de tráfico','text FK channels','string','ESTACION+MAGNITUD+PUNTO_MUESTREO / id+tipo_elem','derived','available',False,'n/a','Hash de tupla JSON; técnica preservada; meteo punto vacío es NULL explícito'),
      ('measurement_id','Observación o intervalo real único','text PK observations','string','channel_id+observed_at+timestamp_role','derived','available',False,'n/a','SHA256; sin valor, fila ni versión de snapshot en identidad'),
      ('_id','Identidad Mongo igual a measurement_id','proyección measurement_id','string','measurement_id','derived','available',False,'n/a','Igualdad exacta, no ObjectId aleatorio'),
      ('observed_at','Etiqueta temporal normalizada a UTC','timestamptz','date','ANO/MES/DIA/Hxx / fecha','derived','conditional_clock',False,'UTC','Europe/Madrid explícito; rechazar DST ambiguo/inexistente; tráfico/meteo conversión provisional rotulada'),
      ('measurement_type','Variable principal, NO identificación de analizador','FK vía channel -> measurement_types','string','MAGNITUD / intensidad','derived','available',False,'n/a','Namespace fuente:código; tránsito tiene intensidad principal y payload multivariable'),
      ('value','Valor publicado elegible; no interpolado','double precision','double/int','Hxx / intensidad','observed','available',False,'según unit','Parse decimal finito; flag V aire/meteo, N tráfico; tráfico no negativo; conservar extremos'),
      ('unit','Unidad física acreditada','measurement_types.unit text','string/null','Diccionario aire AnexoII / tráfico diccionario Fase1','derived','partial',True,'unidad física','Aire ug/m3 o mg/m3; tráfico veh/h; meteo NULL hasta diccionario, nunca copiar mapa aire'),
      ('source_id','Dataset de origen, no una nueva fuente por exportación','FK vía stations/source_versions','string','Identificador de manifiesto','derived','available',False,'n/a','MAD-AIR/MAD-METEO/MAD-TRAFFIC controlados'),
      ('source_version','Snapshot completo inmutable','text FK source_versions','string','02_download_manifest.sha256','derived','available',False,'SHA256','64 hex; debe coincidir con raw_reference.sha256; fuente debe coincidir con canal'),
      ('data_origin','Naturaleza de la observación','text CHECK','string enum','Medición original / método / fixture','derived','available',False,'n/a','observed/derived/synthetic; mediciones actuales observed; campos normalizados derivados en provenance'),
      ('original_time','Reloj local conservado antes de conversión','timestamp','string ISO local','fecha / día+Hxx','derived','available',False,'Europe/Madrid wall clock','H24 avanza a 00:00 siguiente; no filtrar por mes UTC'),
      ('original_timezone','Zona IANA propuesta/documentada de origen','text CHECK','string','Diccionario aire; hipótesis para meteo/tráfico','derived','conditional_clock',False,'IANA','Europe/Madrid, nunca timezone del host; hipótesis no equivale a prueba del proveedor'),
      ('timestamp_role','Qué significa el timestamp','text CHECK','string','Hxx / fecha','derived','available',False,'n/a','hour_end aire/meteo; publisher_label tráfico; no afirmar inicio/fin de tráfico sin diccionario'),
      ('timestamp_status','Nivel de evidencia del reloj','text','string','Diccionario aire / formato fuente','derived','available',False,'n/a','documented_local o etiqueta assumed...pending; no eliminar etiqueta al importar'),
      ('quality_flag','Bandera original de validación','text','string','Vxx / error','observed','available',False,'n/a','V o N válidos según fuente; N ambiental NO es N tráfico; flag no estado de dispositivo'),
      ('unit_status','Acreditación de unidad','measurement_types.unit_status text','string','Diccionario y evidencia previa','derived','available',False,'n/a','verified_dictionary / documented_phase1_dictionary / pending_dictionary'),
      ('candidate_unit','Hipótesis meteorológica NO adoptada','measurement_types.candidate_unit text','string/null','Mapa provisional Fase3','derived','partial',True,'unidad candidata','81 m/s,82 degrees,83 degC,86 percent,87 hPa,88 W/m2,89 mm; no científico hasta validar'),
      ('interval_minutes','Duración de integración publicada de tráfico','integer CHECK 1..30','number/null','periodo_integracion','observed','traffic_only',True,'min','Entero 1..30; no cambiar fecha a inicio/fin por conveniencia'),
      ('element_type','Clase de punto de tráfico','derivada del source_key canal','string','tipo_elem','observed','traffic_only',True,'n/a','URB/M30/C30 observados; no excluir URB por asumir enum incompleto'),
      ('measurements','Payload opcional del mismo intervalo','jsonb','object','ocupacion/carga/vmed','observed','traffic_only',True,'heterogéneas separadas','Nunca generar un documento adicional por variable; no promedio entre unidades'),
      ('measurements.*.value','Valor opcional por variable','jsonb number/null','number/null','ocupacion/carga/vmed','observed','partial',True,'percent / km/h','No obligatorio para intensidad; vmed URB no se acepta como velocidad medida (raw cero preservado)'),
      ('measurements.*.raw_value','Valor opcional exacto de origen','jsonb string','string','Texto CSV original','observed','traffic_only',True,'según variable','NaN/ausente se conserva como texto raw y valor normalizado NULL'),
      ('measurements.*.applicability','Límite de uso por tipo','jsonb text','string','QA tipo_elem','derived','available',True,'n/a','requires_type_specific_QA o URB_zero_not_accepted_as_measured_speed'),
      ('source_key','Clave original de la observación/canal','channels.source_key jsonb','array','Campos originales completos','observed','available',False,'n/a','Aire: estación,magnitud,punto,día,Hxx; tráfico:id,fecha,tipo; no incluir value'),
      ('raw_reference','Localizador verificable de procedencia','jsonb NOT NULL','object','Archivo original SHA y fila/columna','derived','available',False,'n/a','path+sha256+row+column y member para ZIP; fila física 1-based, header=1'),
      ('provenance','Origen por campo y disponibilidad separada','derivable; conservar en staging/exportación','object','Método phase5-normalize-v1','derived','available',False,'n/a','value observed; UTC/IDs derived; unidad faltante NULL y unit_availability pending, no cuarta clase'),
      ('payload_hash','Huella de contenido para replay/conflictos','staging ledger / propuesta ingestión','string','Documento canónico sin localizador de fila','derived','available',False,'SHA256','No es PK; misma PK distinto payload se bloquea/cuarentena, nunca sobrescribir silenciosamente'),
      ('schema_version','Versión de formato','text CHECK','string','Código de contrato','derived','available',False,'n/a',VERSION),
      ('catalog_version','Versión del catálogo compartido','manifest de catálogos','string','Código y hashes de catálogos','derived','available',False,'n/a','draft-v1 + SHA catálogo en preparation.json; no revisión automática de historia'),
      ('transformation_method','Algoritmo de normalización','manifest ETL','string','scripts fase5 + hashes','derived','available',False,'n/a','phase5-normalize-v1; scripts exactos fijados en configuración'),
    ]
    extra = [
      ('stations','name','Nombre de sitio publicado','text','string/null','ESTACION / nombre','observed','partial',True,'No sustituir con nombre ficticio de sensor'),
      ('stations','source_key','Código de sitio de la red','text UNIQUE(source_id,key)','string','CODIGO_CORTO / CÓDIGO_CORTO / id','observed','available',False,'Conservar red y ceros si existieran'),
      ('stations','inventory_present','Existe en inventario independiente de sitios','boolean','bool','Inventario auxiliar auditado','derived','available',False,'No prueba identidad física, instalación ni vigencia enero2025'),
      ('locations','latitude','Latitud decimal publicada','double CHECK [-90,90]','double/null','LATITUD / latitud','observed','partial',True,'No GeoJSON ni EPSG4326 asegurado por bounding box'),
      ('locations','longitude','Longitud decimal publicada','double CHECK [-180,180]','double/null','LONGITUD / longitud','observed','partial',True,'Longitud y latitud deben estar ambas presentes o NULL'),
      ('locations','original_coordinates','Representación geográfica sin transformar','catálogo/JSON original','object/null','ETRS89 DMS, X/Y ETRS89 o utm_x/y','observed','partial',True,'Campos originales preservados; datum/huso de cada grupo pendientes de ratificación'),
      ('locations','coordinate_crs','Declaración de CRS y estado','text','string','Nombres ETRS89 y metadatos auxiliares','derived','partial',False,'unverified_decimal_geographic; EPSG25830 candidato, no transformación ejecutada'),
      ('locations','historical_location_verified','Geografía válida en fecha de observación','boolean','bool','Vigencia inventario pendiente','derived','pending',False,'false no es prueba de posición errónea; no asignar zonas por proximidad'),
      ('locations','inventory_reference','Fuente/versión/localizador de inventario','source_versions FK + referencia','object/null','Manifiesto snapshot auxiliar','derived','available',True,'sha/path/resource_id; ausente cuando sitio no inventariado'),
      ('sensors','installation_date','Instalación del dispositivo físico','date','date/null','No publicado',None,'unavailable',True,'NULL; alta de sitio y primera lectura no sustituyen instalación'),
      ('sensors','administrative_status','Estado administrativo individual','text CHECK active/inactive','string/null','No publicado',None,'unavailable',True,'NULL desconocido; no convertir falta de datos a inactive'),
      ('sensors','status_effective_at','Fecha de validez del estado administrativo','timestamptz','date/null','No publicado',None,'unavailable',True,'Solo evidencia administrativa fechada'),
      ('sensors','identity_evidence_reference','Prueba de identidad física','text NOT NULL','string','Inventario de dispositivos pendiente',None,'unavailable',False,'Bloquea poblar sensors; tabla vacía explícita'),
      ('sensors','organization_id','Vínculo acreditado dispositivo-organismo','text FK organizations','string/null','No relación individual completa',None,'partial',True,'Publicador de dataset no es automáticamente operador del dispositivo'),
      ('organizations','responsible_person_or_role','Persona/cargo responsable documentado','text','string/null','No persona completa publicada',None,'unavailable',True,'No inventar nombres; cargo solo con referencia oficial'),
      ('users','user_id/name/email','Identidad de aplicación','text PK/name/email UNIQUE','string','Registro real consentido del equipo futuro',None,'pending',False,'Tabla vacía; no usar víctimas o personas de accidentes'),
      ('users','consent_reference','Evidencia de autorización de datos personales','text NOT NULL','string','Consentimiento futuro',None,'pending',False,'No se recogieron correos ni se fabricaron usuarios'),
      ('activity','first_observed_at/last_observed_at','Actividad temporal de canal','vista timestamptz','date','MIN/MAX observed_at','derived','available',True,'Separada del estado; ventana y muestra declaradas'),
      ('events','rule_id/rule_version/threshold/unit/algorithm','Política de evento derivado','diseño pendiente','object','Regla oficial/aprobada futura',None,'pending',False,'No generar eventos críticos hasta aprobar unidad, duración, QA, severidad y referencia'),
      ('alerts','emitted_at','Instante real de emisión de alerta','timestamptz propuesto','date','Emisión real futura / fuente oficial',None,'unavailable',False,'Replay: ejecución actual, observed_at histórico separado; no mensaje histórico inventado'),
      ('incidents','incident_id/category/occurred_at','Expediente observado de accidente2026','modelo complemento separado','string/string/date','num_expediente/tipo_accidente/fecha/hora','observed','separate_2026',True,'14388 expedientes auditados; 2 categorías NULL; sin sensor causal atribuido'),
      ('energy_reports','period/value/unit','Consumo mensual por medidor/nivel','modelo complemento separado','date/number/string','AÑO/MES/CONSUMO/UNIDADES','observed','separate_monthly',False,'No desagregar a horas; distinguir kWh/kvarh/m3 y medidores generales/submedidores'),
      ('locations','location_id','Identidad de ubicación/snapshot distinta de dispositivo','text PK','string','station_id+current-inventory','derived','available',False,'Hash estable; historial de ubicaciones revisable, no vigencia2025 acreditada'),
      ('sensor_categories','category_id','Código de categoría lógica propuesta','text PK','string','source_id+magnitud/intensidad','derived','available',False,'Por variable en borrador; no categoría de dispositivo físico acreditada'),
      ('sensor_categories','name','Nombre de categoría de catálogo','text NOT NULL','string','Código fuente como etiqueta','derived','available',False,'Etiqueta honesta; revisión docente de granularidad pendiente'),
      ('organizations','organization_id','Identificador de organismo real','text PK','string','Fuente administrativa futura',None,'pending',False,'Tabla vacía hasta evidencia; no inventar vínculo'),
      ('organizations','name','Denominación de organismo acreditado','text NOT NULL','string','Referencia oficial futura',None,'pending',False,'Publisher está separado en sources; no sustituye operador'),
      ('organizations','evidence_reference','Prueba de cargo/relación','text','string/null','Documento oficial futuro',None,'pending',True,'Guardar recurso/versión y fecha de vigencia'),
      ('users','user_id','ID propio de aplicación','text PK','string','Registro consentido futuro',None,'pending',False,'No medidor ni víctima; sin usuarios generados'),
      ('users','name','Nombre de usuario consentido','text NOT NULL','string','Registro consentido futuro',None,'pending',False,'No inventado para completar requisitos'),
      ('users','email','Correo de aplicación consentido','text UNIQUE NOT NULL','string','Registro consentido futuro',None,'pending',False,'No publicar datos personales; validar sintaxis y consentimiento'),
      ('users','demo_only','Marca para usuario demostrativo autorizado','boolean','bool','Decisión de equipo/docente futura','derived','pending',False,'False para usuario real consentido; ningún usuario demo generado'),
      ('sensors','name','Nombre de dispositivo físico acreditado','text NOT NULL','string','Inventario físico futuro',None,'unavailable',False,'No copiar nombre de estación como identidad de analizador'),
      ('channels','catalog_basis','Universo de catálogo de canales','text CHECK','string','Lecturas fuente / inventario futuro','derived','available',False,'observations en esta fase; no inventario independiente de canales físicos'),
      ('sources','name','Etiqueta del dataset fuente','text NOT NULL','string','Identificador de manifiesto','derived','available',False,'MAD-AIR/MAD-METEO/MAD-TRAFFIC, no nombre de operador'),
      ('sources','publisher','Publicador institucional','text NOT NULL','string','Portal y documentación municipal','observed','available',False,'Ayuntamiento de Madrid; no relación de ownership individual'),
      ('source_versions','original_path','Archivo inmutable de snapshot','text NOT NULL','string','02_download_manifest.path','observed','available',False,'Ruta relativa original verificada por hash, no datos reconstruidos'),
      ('source_versions','acquired_at','Instante real de adquisición','timestamptz','date/null','02_download_manifest fecha registrada','observed','available_not_loaded',True,'No se rellena con observed_at; prueba SQL deja NULL y conserva manifiesto exacto'),
      ('zones','name','Etiqueta de distrito publicado','text NOT NULL','string','distrito como código','derived','available',False,'madrid:district:n; no nombre de barrio inventado'),
      ('zones','level','Granularidad geográfica','text CHECK district/city','string','distrito inventariado','derived','available',False,'district; ciudad no equivale a distrito'),
      ('raw_reference','path/sha256/row/column/member','Localización original de cada valor','JSONB','object','Manifiesto+fila física+columna+ZIP miembro','derived','available',False,'row>=2; SHA completo; member solo ZIP'),
      ('measurements','*.unit/*.data_origin','Unidad y origen de cada variable opcional','JSONB','object','Diccionario tráfico / variable raw','derived','partial',False,'percent/km/h por variable y observed, sin sumar heterogéneas'),
    ]
    complement_rows = list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    complements = {s:next(r for r in reversed(complement_rows) if r['id']==s+'-file' and r['path'])
                   for s in ('MAD-CRASH','MAD-ENERGY')}
    snapshots = ';'.join(r['id']+'='+r['sha256'] for r in prep['source_snapshots'])
    for field,meaning,sql,bson,origin_field,origin,status,nullable,unit,rule in common:
        rows.append({'scope':'observation', 'attribute':field, 'meaning':meaning, 'postgresql_type':sql,
            'bson_type':bson, 'data_origin':origin or '', 'original_field':origin_field, 'unit':unit,
            'nullable':str(nullable).lower(), 'availability':status, 'validation_constraints':rule,
            'transformation':rule, 'source_id':'MAD-AIR;MAD-METEO;MAD-TRAFFIC',
            'source_version':snapshots, 'evidence':'05_data_contract.md; scripts/phase5_contract.py; preparation.json'})
    for scope,field,meaning,sql,bson,origin_field,origin,status,nullable,rule in extra:
        scope_source = {'incidents':'MAD-CRASH', 'energy_reports':'MAD-ENERGY',
            'locations':'212629-0-estaciones-control-aire-inventory;300360-0-meteorologicos-estaciones-inventory;MAD-TRAFFIC-META-file',
            'stations':'212629-0-estaciones-control-aire-inventory;300360-0-meteorologicos-estaciones-inventory;MAD-TRAFFIC-META-file',
            'sensors':'PENDING_PHYSICAL_INVENTORY', 'organizations':'PENDING_ADMINISTRATIVE_SOURCE',
            'users':'PENDING_CONSENTED_APPLICATION_REGISTRATION', 'events':'PENDING_APPROVED_RULE',
            'alerts':'PENDING_EMISSION_SOURCE', 'activity':'DERIVED_CANONICAL_OBSERVATIONS'}.get(scope,'MAD-AIR;MAD-METEO;MAD-TRAFFIC')
        rows.append({'scope':scope, 'attribute':field, 'meaning':meaning, 'postgresql_type':sql,'bson_type':bson,
            'data_origin':origin or '', 'original_field':origin_field, 'unit':'degrees' if field in ('latitude','longitude') else 'n/a',
            'nullable':str(nullable).lower(), 'availability':status, 'validation_constraints':rule, 'transformation':rule,
            'source_id':scope_source,
            'source_version':complements['MAD-CRASH']['sha256'] if scope=='incidents' else
                             (complements['MAD-ENERGY']['sha256'] if scope=='energy_reports' else
                              (snapshots if scope not in ('users','sensors','organizations','events','alerts') else 'pending: no value fabricated')),
            'evidence':'05_data_contract.md; phase3/incident_checks.json; 02_download_manifest.csv'})
    with (ROOT/'05_data_dictionary.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return len(rows)


def main():
    prep = json.loads((OUT/'preparation.json').read_text())
    mongo = json.loads((OUT/'mongodb_execution.json').read_text())
    pg = json.loads((OUT/'postgresql_sample.json').read_text())
    dictionary_rows = dictionary(prep)
    passed = None
    if (OUT/'tests.xml').exists():
        suites = list(ET.parse(OUT/'tests.xml').getroot().iter('testsuite'))
        if all(int(s.attrib.get(k,0))==0 for s in suites for k in ('failures','errors','skipped')):
            passed = sum(int(s.attrib['tests']) for s in suites)
    counts = prep['counts']
    total = sum(r['effective_documents'] for r in counts.values())
    source_table = table(['Recurso','Archivo','Versión SHA256','URL oficial'],
        [[r['id'],'`'+r['path']+'`','`'+r['sha256']+'`',r['url']] for r in prep['source_snapshots']])
    count_table = table(['Fuente enero2025','Registros/slots seleccionados','Elegibles estructurales únicos','Rechazados','Duplicados/conflictos'],
        [[s,r['selected_records'],r['effective_documents'],r['selected_records']-r['effective_documents'],
          str(r['duplicate_extras'])+'/'+str(r['conflicting_keys'])] for s,r in counts.items()])
    write('05_dataset_manifest.md',f'''
# Fase 5 — Manifiesto del núcleo inicial propuesto

**Madrid sigue condicionado (63,665/100 de Fase4).** Esta fase autoriza preparación y pruebas locales, no ratifica la decisión académica ni una carga definitiva. Contrato `{VERSION}` para revisión de los cuatro integrantes.

## Archivos originales y versiones

{source_table}

Origen: Ayuntamiento de Madrid; CC BY4.0 documentada en Fase1, atribución obligatoria. Los seis snapshots fueron verificados por SHA completo. No se descargó ningún dataset de nuevo. E/P/I originales conservan los hashes de Fase4, y las 48 pruebas de continuidad pasaron otra vez; evidencia `results/phase5/preflight.json` y `baseline_tests.xml`.

## Selección exacta de registros

- Aire y meteo: filas originales con `ANO=2025` y `MES=1`, todos los sitios, magnitudes y puntos/técnicas publicados; H01..H24 se expanden a **horas realmente publicadas**, no mediciones artificiales. Aire:3905 filas diarias/93720 slots; meteo:2892/69408. Conservar H24 del31 de enero (endpoint local1 de febrero, UTC31 de enero23:00). No incluir julio ni seleccionar por mes UTC.
- Tráfico: miembro `{prep['cache']['member']}` del ZIP auditado; estrato determinista `int(id)%20=0` durante enero completo. Conserva los nueve campos originales y número de fila, no solo intensidad. Se recuperaron los campos faltantes mediante una extracción dirigida del ZIP local; no se repitió una auditoría general ni se extrapoló unicidad a los13.218.804 registros del ZIP completo.
- Elegibilidad: flag V ambiental o N tráfico, valor principal finito; intensidad no negativa, tipo URB/M30/C30, duración entera1..30min, fecha de enero, unicidad y referencias de catálogo. Unidades meteo siguen **NULL/candidatas**; elegibilidad estructural no valida automáticamente interpretación científica, reloj o geografía histórica.
- Inventarios completos de sitios/puntos se conservan como catálogo independiente de sitios; canales observados no equivalen a un inventario independiente de dispositivos. Sitios sin datos no se califican como averiados.

{count_table}

Total estructural único: **{total}**, distinto de los993374 hechos enero+julio de Fase3. Identidades exactas en `private_results/phase5/identity_ledger.sqlite`; SHA de ledger, cache y muestra en `preparation.json`. No versionar ese ledger ni datos voluminosos.

## Separaciones obligatorias

MAD-CRASH2026: mismo archivo/hash de Fase4,14388 expedientes, no33322 accidentes; dos categorías desconocidas. Solo complemento separado2026, no presente en la muestra nativa de enero2025 ni relacionado causalmente con sensores. MAD-ENERGY: recurso mensual municipal separado (snapshot y período publicado en manifiesto02), unidades/niveles distintos; nunca consumo horario por división del mensual. Accidente2025 requeriría recurso real y validación futura autorizada. No se atribuyen CO2 ni tiempos de recorrido a CO, NO2, velocidad o intensidad.

Las condiciones académicas, unidades, clocks provisionales, CRS y vigencias quedan abiertas. Núcleo propuesto, **no fuentes definitivamente aprobadas**.
''')
    write('05_data_contract.md',f'''
# Fase 5 — Contrato común de datos `{VERSION}`

Estado: **borrador implementable localmente, pendiente de revisión y aceptación**. Diccionario exhaustivo del DTO y campos críticos administrativos/complementarios: `05_data_dictionary.csv` ({dictionary_rows} entradas). CSV incluye significado, tipos SQL/BSON, columna original, origen, unidad, nulos, disponibilidad, restricciones, transformación, fuente/versión y evidencia. Un campo no disponible queda NULL: no recibe una falsa etiqueta observed.

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

`observed_at`: TIMESTAMPTZ SQL / BSON Date real; JSON Extended `{{"$date":"...Z"}}`, **no string BSON**. Conservar original_time naive, original_timezone=Europe/Madrid, timestamp_role y timestamp_status. Los rangos son [desde,hasta); selección base por fecha del registro fuente. H24 es media23–24h con endpoint al día siguiente según diccionario aire p.7–8 (`results/phase3/madrid_air_dictionary.txt`). No asumir que el timestamp de tráfico es inicio o fin: publisher_label y periodo_integracion separado.

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
''')
    write('05_postgresql_design.md',f'''
# Fase 5 — Modelo PostgreSQL preliminar para Daniel

DDL: `scripts/phase5_postgresql.sql`; consultas: `phase5_postgresql_queries.sql`. **No migración definitiva**. Esquema local draft5,12 tablas (más vistas/funciones), revisable y con vacíos visibles.

## Relaciones, normalización y tipos

- sources1:N source_versions; fuente/versión con SHA y path, publicador no propietario.
- zones1:N locations; locations1:N stations (en muestra1:1), estaciones de redes independientes.
- sensor_categories1:N measurement_types; cada tipo define fuente, unidad acreditada/candidata y estado.
- stations1:N sensors físicos acreditados y1:N channels; sensors0..1:N channels. Sin evidencia, sensor_id NULL, tabla sensors vacía.
- organizations1:N sensors, solo vínculo acreditado; usuarios de aplicación independientes con correo UNIQUE y consentimiento, tabla users vacía.
- channels1:N observations; observations N:1 source_versions. PK y UNIQUE natural independientes del payload; hechos structured sin inventar maestros.

3FN: identidad de fuente, zona, estación, categoría, unidad/tipo, dispositivo y canal se guarda una vez en su catálogo; observations no repite station_id,zone_id,unit,measurement_type ni source_id, pues canal/snapshot los determinan. La vista observation_contract reconstruye DTO. original_time/reloj, QA, duración, procedencia y valor dependen de la observación. measurements JSONB es payload semiestructurado opcional de ese intervalo, no copias de hechos para inflar volumen. Historial de geografía/organismos requiere tablas de vigencia posteriores antes de reportar enero como validado; no afirmar3FN elimina ese vacío histórico.

PK/FK para todas las referencias; UNIQUE(station_id,source_key), UNIQUE(channel_id,observed_at,timestamp_role), CHECK de origen, fecha/reloj, rango de coordenadas, duración y valor finito. Trigger rechaza fuente de snapshot distinta de estación/canal/tipo. Sensores exigen identity_evidence_reference para poblarse. Instalación/estado/vínculo organismo permiten NULL; usuarios no se crean sin consentimiento. Correo de víctima no es usuario del sistema.

Índices B-tree de PK/UNIQUE, sensor estación/categoría/organismo, canal estación y tiempo observación. El UNIQUE natural ya cubre canal+fecha; evitar duplicarlo sin EXPLAIN. Particiones mensuales y BRIN temporal si benchmark justifica; no implementadas. Particionar requeriría revisar PK global (incluir clave partición o registry de IDs) y cargas tardías. Materialized view diaria por tipo/unidad/zona, refresh y benchmark siguen propuestos, no acreditados.

## Compatibilidad con las diez consultas

| ID | Viabilidad exacta / cierre requerido |
|---|---|
| PG01 |SQL por tipo sobre sensores vacíos no cumple inventario; alternativa por canal revisable por profesor |
| PG02 |Ubicación de sitios disponible parcial; dispositivo físico y vigencia pendientes; canal→sitio explícito |
| PG03 |Bloqueada estricta: sin estado administrativo; actividad en ventana no sustituto silencioso |
| PG04 |Bloqueada estricta: sin vínculo individual completo ni responsable acreditado; publisher separado |
| PG05 |Ranking de canales por ubicación viable condicionado; no conteo de lecturas como sensores |
| PG06 |Bloqueada estricta: no fecha instalación; alta de sitio/primera lectura separadas |
| PG07 |NOT EXISTS diseñado; inventario independiente de sitios existe, pero no inventario físico ni completo de canales históricos; ausencia ≠ falla |
| PG08 |CTE/DENSE_RANK diseñado; zonas tráfico parciales y geografía ambiental desconocida; aceptar alcance muestreado |
| PG09 |Vista nativa local ejecutada; contrato físico completo no acreditado |
| PG10 |Función nativa local ejecutada y rotulada canales, no sensores inventados |

Se mantienen las2/10 estrictas y6/10 funcionales condicionadas de Fase3 como evidencia histórica; no prometer10/10 por escribir diez SQL sobre tablas vacías. Nuevos diseños no son automáticamente aprobación académica.

## Ingestión y muestra local

Staging por snapshot/lote; validar y conservar rechazos; transacción de catálogos+hechos por lote. INSERT...ON CONFLICT solo permite replay idéntico; comparar payload/versión antes, cuarentena en cambios. No sobrescribir hechos corregidos sin política histórica. Orden:fuentes/versiones→zonas/ubicaciones→estaciones→tipos→canales→observaciones. Exportación CSV/Parquet comparte IDs.

Prueba nativa aislada: **{pg['counts']['observations']} hechos**, {pg['counts']['channels']} canales, {pg['counts']['stations']} sitios del inventario/observados; **0sensores físicos y0usuarios**. DDL/vistas/función/consultas, PK/FK/trigger probados y valores comparados con referencia independiente. Tiempo medido de preparación/insert:{pg['preparation_and_insert_seconds']:.3f}s, no rendimiento de100k ni remoto. Evidencia `results/phase5/postgresql_sample.json`; contenedor y volúmenes eliminados. Hay {total} hechos estructurales locales candidatos; la muestra5k no acredita mínimo100k en este esquema definitivo aún no autorizado.
''')
    write('05_mongodb_design.md',f'''
# Fase 5 — Modelo MongoDB preliminar para Kembly

## Colecciones propuestas

| Colección | Granularidad / referencias | Estado |
|---|---|---|
| readings |Hora real ambiental o intervalo multivariable de tráfico; _id=measurement_id, channel/station/zone/source_version compartidos |Muestra5k nativa local; estándar |
| derived_events |Evento por regla/version/inputs, observed_at y derived_at |Sin generar; umbral/unidad/duración/QA/severidad pendientes |
| alerts |Emisión demostrada por event_id y zone_id, emitted_at real |Sin mensajes; histórico/replay requieren fuente o aprobación |
| incidents_2026 |Un expediente de accidente2026; categoría NULL visible; personas/detalles fuera |Complemento separado; no probado nativamente en enero |
| energy_reports_monthly |Medidor/nivel/unidad/mes real |Complemento separado; no energía horaria |
| dynamic_metadata |Payload semiestructurado/versionado con raw_reference |Especificación; no metadatos ficticios |
| crud_demo |Tres fixtures de operación sin mediciones |Solo DB desechable; synthetic y no cuentan para500k |

**Tráfico:**677724 registros del estrato,674704 elegibles y únicos,3020 flag desconocido;0duplicados/conflictos por clave completa y payload. Examen incluye id/fecha/tipo_elem/intensidad/duración, no solo el resumen anterior. URB611153, M3048797, C3017774 en registros seleccionados; todas las clases legítimas conservadas. `vmed=0` URB no se presenta como velocidad medida; raw0 se conserva y el valor opcional analítico queda NULL. Opcionales ausentes no invalidan intensidad/duración válidas. La semántica temporal y geografía histórica aún necesitan cierre.

## Documento y tipos

Ejemplo **real** de cada fuente, con procedencia, en `results/phase5/examples.extjson`; los5000 originales de muestra y catálogos completos están ignorados en private_results/phase5. `{json.dumps({'_id':'measurement:<hash>', 'sensor_id':None, 'channel_id':'channel:<hash>', 'station_id':'station:<hash>', 'zone_id':None, 'observed_at':{'$date':'2025-01-01T00:00:00Z'}, 'measurement_type':'MAD-AIR:8', 'value':'valor real del ejemplo adjunto', 'unit':'ug/m3', 'data_origin':'observed'}, ensure_ascii=False)}` es estructura ilustrativa, no otra lectura generada.

BSON Date para observed_at, double/int para value, NULL para sensor/unidad/zona desconocidos, objetos anidados de measurements y raw_reference. $jsonSchema estricto valida campos requeridos, tipos y enum de origen en la prueba; no afirma una FK remota. Usar catálogos versionados e integridad previa al lote. Desnormalizar en Mongo para consultas evita joins repetidos; misma regla de IDs y mismas unidades que SQL.

## Índices y estándar frente a time-series

Estándar elegida para Sprint1: _id único y UNIQUE(channel_id,observed_at,timestamp_role); índices channel+time, source+type+time y zone+type+time. EXPLAIN natural y con hint de demostración guardados; no confundir hint con elección automática del optimizador. No 2dsphere sin CRS confirmado. No TTL sobre evidencia histórica.

Time-series sería candidata futura con timeField=observed_at, metaField={{source_id,channel_id,measurement_type,unit}}, granularity según frecuencia. Reduce almacenamiento/buckets y facilita análisis temporal, pero **no admite índice UNIQUE como colección estándar**; deduplicación requiere registry externo/ETL. Restricciones de update/delete dependen de versión (7.0 frente a8.x): no prometer CRUD arbitrario sobre valores ni trasladar validator/índices sin comprobar documentación. Mantener events/alerts/incidents/crud_demo estándar. La prueba ejecutada no usa time-series ni acredita esos beneficios.

## Consultas y alcance

Diseños nativos locales ejecutados: MG01 canal, MG02 rango UTC, MG03 extremos separados por variable/unidad, MG06 distritos publicados de tráfico, MG07 tipo/variable con unidad conocida, MG09 Aggregation Framework y MG10 filtros múltiples. Siete diseños, **no siete requisitos físicos plenamente aprobados**. MG01/07 necesitan aceptar canal/variable; MG06 excluye zonaNULL y tiene geografía histórica pendiente; meteo sin unidad no se promedia como grados.

MG04 bloqueada por política de críticos; MG05 por emisión/zonas no acreditadas; MG08 tiene expedientes2026 auditados, pero permanece fuera de esta muestra2025 y requiere ingestión separada/prueba propia. No contar colecciones vacías como evidencia. CRUD update/delete solo crud_demo; lecturas originales intactas. Reimportación misma muestra no añade documentos; misma PK/payload distinto debe bloquearse, no ocultarse con timestamp de ingestión en la identidad.

Limitación: no500k cargados, cluster/sharding/producción ni comparación de versiones. La muestra solo demuestra mecánica y coherencia local.
''')
    write('05_ingestion_plan.md','''
# Fase 5 — Pipeline reproducible y limitado

## Arquitectura propuesta

Originales inmutables + manifiesto02/SHA → filtro de enero/estrato existente → validación de campos/QA → tiempo local explícito/UTC condicionado → IDs deterministas → catálogos compartidos + ledger de identidad → muestra/exportaciones → PostgreSQL estructurado y MongoDB documental locales → CSV/Parquet futuros para HDFS/Spark. Derivados/eventos/alertas son otra rama después de aprobar reglas. Sin flujo ni servidor definitivo.

## Comandos desde research/datasets

```bash
.venv/bin/python scripts/phase5_verify.py
.venv/bin/python scripts/phase5_prepare.py --dry-run
.venv/bin/python scripts/phase5_prepare.py --sample-size 5000
.venv/bin/python scripts/phase5_postgres_sample.py
.venv/bin/python scripts/phase5_native.py --engine mongodb
.venv/bin/python scripts/phase5_reports.py
.venv/bin/python -m pytest tests -q --basetemp=/tmp/opencode/smartcity-phase5-tests --junitxml=results/phase5/tests.xml
.venv/bin/python scripts/phase5_verify.py --final
```

Dry-run verifica seis hashes y muestra el plan, sin escribir, extraer ni conectar motores. Preparación no tiene DSN ni carga masiva: exporta1000..10000 documentos como máximo. Docker ejecuta sobre unix:///var/run/docker.sock explícito; --network none, sin puertos publicados ni credenciales remotas. Scripts nativos requieren imagen local (--pull=never), DB/nombre aleatorio y mount inputs readonly. Imágenes usadas: postgres16-alpine y mongo7.0; digest/versión registrados. Imágenes Docker descargadas en esta fase son infraestructura de prueba, no nuevos datasets ni presupuesto de adquisición02. Nunca usar Compose raíz, .env privado o URI compartida.

## Controles implementados

- Fuente/versión: hashing completo y localizadores de fila/columna/miembro. Cache de tráfico conserva nueve columnas; solo se reutiliza si fingerprint y hash coinciden. Escritura temporal + os.replace; originales nunca sobrescritos.
- Lotes: extracción CSV100k, commits ledger10k y Mongo insertMany500. Prueba SQL limitada5k. Preparación writer con flock; no procesos concurrentes sobre mismo directorio.
- Unicidad: ledger SQLite local en disco, PK determinista y payload_hash; conserva conflicto de misma clave hasta excluirla. No SQL/Mongo voluminosos. Ceros válidos, NULL≠0, flags sin convertir a estado, extremos sin borrado automático.
- Reanudación: cache publicado solo al completar CRC; archivo parcial no cuenta. Ledger incompleto se reconstruye determinísticamente desde inputs/cache, no salta filas sin verificar. Output de éxito se publica al terminar; sin preparation.json válido no se importa. Commit parcial se reevalúa, no se acepta como conjunto final. Coste: replay de la validación, no checkpoint por offset arbitrario.
- Idempotencia: run completo con mismos scripts/configuración/hashes se reutiliza y vuelve a verificar hashes de outputs. Configuración nueva o output alterado aborta: nueva versión/directorio y revisión explícita. En motores: IDs/UNIQUE + comparación de payload antes del upsert; replay igual no añade datos. No usar ON CONFLICT DO UPDATE para mediciones sin política de correcciones.
- Error: fallo de hash/clock/catálogo fatal; flags/campos inválidos contados y retenidos en original/ledger con valid=false; conflictos excluidos. Logs prepare.log, ledger y JSON de conteos. Excepciones nativas guardan salida/error y ejecutan finally de cleanup de recursos propios.
- Integridad: source/type/channel/station/zone con catálogo hash; trigger SQL y validator BSON complementan validación previa. PostgreSQL y MongoDB no comparten transacción: futuro outbox/manifest de lote con estados pending/SQL_committed/Mongo_committed/reconciled y replays idempotentes, **especificación, no implementado remoto**.

## Ingestión futura, después de revisión/autorización

José prepara exportación completa en ruta privada con misma regla; Daniel valida staging y carga por transacción (catálogos primero), Kembly valida BSON y upserts por lote; comparar IDs/payload/counts de cada lote y aprobar errores. Extensión necesaria: exportador completo actualmente limitado, ledger de lotes/errores durable por motor, reconciliación de escrituras parciales, backup/restore, recursos/benchmark e inventarios/relojes/unidades. No ejecutar esos pasos masivos aquí.

Exportaciones sample.csv/sample.parquet generadas con source_id/versión/IDs/UTC/tipo/unidad/origen; son solo5k. Partición futura source/year/month por calendario y manifest; HDFS -put/batch/Spark no ejecutados. schema_arrow/timestamp UTC explícito y diccionario NULL deben validarse al ampliar; no llamar procesamiento distribuido a Parquet local.
''')
    write('05_volume_strategy.md',f'''
# Fase 5 — Volumen sin inflación ni síntesis masiva

{count_table}

**{total} observaciones estructurales únicas de enero**, no993374 enero+julio. Tráfico conserva un documento por intervalo con variables juntas. Reglas precisas en manifiesto/prepare; no aumentar por raw diario+horas, atributos separados, cross products, fixtures o exportaciones redundantes.

| Objetivo | Disponible bruto | Elegible validado | Efectivamente probado en motor | Pendiente |
|---|---|---|---|---|
| PostgreSQL≥100000 |93720slotsaire+69408meteo+677724tráfico seleccionado |{total}; solo tráfico674704 basta estructuralmente |5000 hechos en draft5;993374 en modelo local anterior, no reutilizar como carga nueva |Aceptar hechos como registros; unidad/clock/catálogos y carga autorizada después |
| MongoDB≥500000 |677724intervalos tráfico del estrato |674704,0duplicados/conflictos,3020flagsdesconocidos excluidos |5000documentos mixtos,3000tráfico; no500k |Margen174704=34,94%; clocks/tipo/granularidad y carga nativa masiva posteriores |
| Spark≥1000000 |1795279slotsVaire del histórico local2025–ago2026, más otros |No cardinalidad UTC/QA anual definitiva en esta fase; núcleoenero{total}<1M |0registros ejecutados por Spark |Ampliar real al histórico, controlar DST/sitios/unidades/panel comparable y ejecutar distribuido |

Cantidad observada no es aceptabilidad científica plena: meteo66005 con unidadNULL; reloj provisional meteo/tráfico; ubicación histórica pendiente. Datos para sensores físicos estrictos: **0identidades acreditadas**, no674704sensores. No filtrar zonasNULL para aparentar precisión; si el contrato final las exige, recontar elegibles antes de prometer mínimos.

## Almacenamiento y estimaciones separadas

Cinco archivos originales principales/complementos de Madrid:145308605bytes de Fase4, distinto de bytes del núcleo restringido y almacenamientoDB. Cache y hashes privados en preparation.json. La muestra tiene tamaño medido JSON/CSV/Parquet; cualquier estimación de500k BSON/índices/disco parte de esta muestra y debe etiquetarse estimación, nunca benchmark remoto. No se aseguró funcionamiento en512MiB/0,25CPU del Compose estático; prueba local1GiB/1CPU.

En results/phase5/storage.json se separan bytes reales de sample y cache, promedioJSON y proyección lineal para674704documentos de tráfico. No incluye índices,WAL,buckets,réplicas,backups ni distribución. No sumar ledger+cache+exportación como nuevas mediciones. La ampliación histórica es procedimiento pendiente, no volumen anual normalizado ya acreditado.

**Síntesis de mediciones:0generada y0necesaria para potencialSQL/Mongo.** Para Spark ampliar fuentes reales antes de plantear síntesis. No hay necesidad demostrada de generador sintético; por eso no se generan semillas/distribuciones como solución aprobada. Si después faltan datos, presentar por separado modelo, semilla, restricciones/distribuciones/autocorrelación/unidades/origen y evaluación contra reales para autorización. Tres fixtures CRUD no métricos no cuentan como sensores, usuarios ni lecturas.
''')
    plan = mongo.get('explain',{}).get('queryPlanner',{}).get('winningPlan',{})
    timings = table(['Operación local','Milisegundos medidos'],[[k,round(v,3)] for k,v in mongo.get('timings_ms',{}).items()])
    write('05_native_mongodb_test.md',f'''
# Fase 5 — Prueba nativa MongoDB local

**Ejecución nativa: {mongo['native_executed']}**. Versión:{mongo.get('version','no ejecutada')}; imagen `{mongo['image']}`; digest `{';'.join(mongo['repo_digests'])}`. No se sustituyó MongoDB por Python: mongosh envió operaciones a mongod dentro de un contenedor desechable, DB `{mongo['database']}`.

## Entrada, aislamiento y prueba

{prep['sample_size']} documentos reales ({prep['sample_by_source']}), con SHA `{digest(PRIVATE/'sample.extjson')}`. Muestra por cuotas de primeras observaciones válidas en el orden del snapshot, reproducible pero **no representativa de toda la ciudad ni benchmark de500k**. Catálogos compartidos:{pg['counts']['channels']} canales/{pg['counts']['stations']} sitios; memberships y relaciones coinciden con los catálogos SQL locales. sensor_id NULL; ninguna identidad física fabricada.

Socket local fijo, red none, sin puertos publicados, localhost127.0.0.1 dentro del contenedor, inputs readonly, límite1GiB/1CPU. No conexión con MongoDB remoto, Coolify ni Tailscale. Contenedor eliminado:{mongo.get('container_removed',False)}; sus volúmenes anónimos eliminados:{mongo.get('anonymous_volumes_removed',False)}. Las imágenes descargadas permanecen como cache local Docker, no son servicios ni datos de producción.

Mongo8.0 abortó al arrancar por incompatibilidad declarada con kernels Linux6.19+ (SERVER-121912). Se conserva `mongodb8_startup_failure.json`/`mongodb8_server.log`; no se desactivaron controles ni se cambió kernel. Se eligió7.0 para prueba, compatible con rama mayor del Compose estático; patch/digest local distintos de7.0.16 deben validarse antes de reproducir en otra versión. Las fases anteriores quedan como evidencia histórica de0nativas, no se reescribieron.

## Operaciones y resultados

MG01 canal, MG02 rango UTC, MG03 extremos, MG06 zonas tráfico, MG07 variables/unidades, MG09 Aggregation Framework ($match→$group→$sort) y MG10 filtros múltiples. Conteos/extremos/sumas comprobados contra referencia independiente y muestra fuente. MG06/07 excluyen unidad/zonaNULL según regla; su alcance no sustituye requisitos físicos/zonas completas. MG04/05 no ejecutadas (regla/emisión), MG08 no ejecutada (accidentes2026 fuera de muestra2025).

Validator BSON rechazó string donde se exige Date; PK/índice único rechazaron duplicado. Índices compuestos creados; explain('executionStats') natural y con hint guardados completos, sin prometer rendimiento remoto ni que un hint sea selección automática. Plan ganador natural: `{json.dumps(plan,ensure_ascii=False)}`.

Reimportación idéntica:{mongo.get('idempotent_reimport',{})}. CRUD insertOne/Many,find/findOne,updateOne/Many,deleteOne en crud_demo; tres fixtures synthetic no métricos separados,0observaciones originales mutadas. Siete diseños locales ejecutados, **no declaración7/10académicas estrictas ni500kdocumentos cargados**.

{timings}

Tiempos de una única corrida local, incluyen estado/cache y no tienen intervalo estadístico. Logs/JSON: `mongodb_execution.json`, `mongodb_execution.log`, `mongodb_server.log`, `sample_reference.json`; reproducción en `05_ingestion_plan.md`. Si no existe imagen/daemon compatible, el script falla y no presenta native_executed=true.
''')
    write('05_academic_decisions.md','''
# Fase 5 — Riesgos y decisiones académicas abiertas

Ninguna ratificación/aceptación docente fue recibida. La autorización del usuario para esta fase permite preparación/pruebas locales, **no reemplaza acta del equipo ni interpretación de la rúbrica**. Fuente E pp.8–12,18–19,26; P pp.1–5; Fase4 se preserva.

| Asunto | Evidencia / brecha | Decisión del equipo | Consulta al profesor / condición |
|---|---|---|---|
| Sensor físico vs canal |sensor_id NULL; canales/sitios reales; técnicas de aire preservadas |Revisar IDs/diseño sin renombrar |¿Acepta consultas de canales como alcance alternativo? Si exige dispositivos, buscar inventario; no cumple íntegramente |
| Instalación |No fecha individual; alta de sitio/primera lectura separadas |Mantener NULL y referencia |PG06 estricta bloqueada; confirmar si acepta consulta alternativa explícita |
| Activos/inactivos |QA/actividad no son estado administrativo ni falla |Ventanas/flags por fuente, unknown visible |PG03 estricta bloqueada; no inferir avería por ausencia |
| Organismos/responsables |Publicador conocido, relación individual incompleta |Conseguir cargo/gestor con fuente |PG04 requiere relación real o alcance aprobado; no inventar persona |
| Usuarios demostrativos |Los datasets no son directorio; tabla users vacía |Registrar miembros reales con consentimiento o solicitar fixtures aislados |¿Datos de aplicación propios satisfacen el modelo? Usuarios sintéticos requieren aprobación; los tres fixtures CRUD no son usuarios |
| Alertas y críticos |Sin política validada ni emisiones reales |Proponer regla/unidad/duración/QA/versiones |MG04/05 bloqueadas; ¿acepta derived/replay con emisión actual? No historia oficial inventada |
| Incidentes |14388 expedientes de2026 auditados; dos categorías NULL |Colección separada, minimización de datos personales |MG08 puede demostrarse en período propio después; confirmar presentación distinta sin falso join |
| CO2 |No concentración ambiental |Buscar complemento real compatible si autorizado |CO/NO2/CO2e no sustitutos; KPI bloqueado o alcance explícito |
| Energía horaria |Mensual con unidades/niveles distintos |No dividir a horas; evitar doble cómputo de medidores |KPI horario bloqueado; fuente nueva o ajuste aprobado |
| Tiempos de recorrido |No recorridos/tiempos observados |Velocidad/intensidad no son tiempo de viaje |KPI bloqueado; complemento o ajuste expreso |
| Accidentes2026/tráfico2025 |No período común |Prohibir unión contemporánea/causal |Si análisis conjunto requerido, accidente2025 real auditado; no mover fechas |
| Derived/synthetic |IDs/UTC/agregados derived; cero mediciones synthetic |Mantener linaje/namespace y reglas |¿Acepta derivados/granularidad? No inflación de500k por atributos ni generador unilateral |
| Unidades/clocks/CRS |Unidad meteo NULL; clocks meteo/tráfico provisionales; CRS/geografía histórica pendientes |José acredita metadatos y versiona correcciones |Profesor decide alcance, no certifica metadatos ausentes; bloquear análisis científico sin cierre técnico |
| Mínimos/fuentes/fecha |832668 elegibles;5k nativas; dos datasets≠dos repositorios |Capacidad/plan y ratificación de los cuatro |Confirmar100k hechos/500k intervalos,100MB, dos repositorios,28oct y alcance de21KPIs |

Acta pendiente: firmas de José/Daniel/Kembly/Fernanda, fechas, entidad aceptada, campos NULL, reglas, fuentes complementarias y alcance de KPIs. Puertas:14oct IDs/modelos/alcance;17oct carga inicial autorizada futura;20oct mínimos/backups;23oct veinte consultas con evidencia;24–28oct revisión/informe/demo según P. Si una puerta no cierra, registrar PARCIAL/NO_CUMPLE y replanificar, no declarar listo para entregar.

Ninguna fuente está aquí aprobada definitivamente; no hay síntesis masiva ni cambios en el servidor compartido.
''')
    write('05_team_handoff.md','''
# Fase 5 — Entrega al equipo y arranque concreto Sprint1

## José — Fuentes, limpieza, generación y cargas

1. Revisar manifiesto05 y conteos de enero:832668 elegibles,674704 de tráfico. Conservar originales/hashes y coordinar ratificación conjunta.
2. Acreditar unidades meteo, relojes meteo/tráfico, CRS/vigencias del inventario y reglas de opcionales por URB/M30/C30; corregir mediante versión revisada, no silenciosamente.
3. Reproducir dry-run/prepare y preparar exportación/lotes completos **solo después de autorización futura**; esta herramienta limita salida5k. No generador sintético necesario por ahora.
4. Con Daniel/Kembly definir manifests por lote/replay/reconciliación; medir recursos/disco y respaldo/restauración antes de mínimos20oct. Esta fase no autoriza carga definitiva remota.

## Daniel — PostgreSQL

1. Revisar DDL draft5 y3FN; validar cardinalidades, tipos, constraints/trigger e índices; recibir muestra/catálogos compartidos de José.
2. Reproducir5k nativas y rechazo PK/FK/fuente; completar relaciones físicas solo con inventario acreditado. Usuarios/organismos no se rellenan artificialmente.
3. Preparar PG01–10 y dejar explícito alcance canal/NULL/bloqueos PG03/04/06/07; acordar alternativas con docente antes de afirmar cumplimiento.
4. Tras revisar:staging/idempotencia, vista materializada/refresh, particionamiento si justificado, EXPLAIN y prueba100k autorizada; cierre23oct.

## Kembly — MongoDB

1. Reproducir prueba nativa7.0 con sample.extjson y IDs exactos SQL. Revisar estándar frente a time-series y validator/índices.
2. Completar diseño/readings y CRUD exclusivamente sobre copias; consultar explain natural y evidencia MG01/02/03/06/07/09/10.
3. Proponer política MG04/MG05 con linaje/emisión y fuente; no eventos críticos ni alertas históricas por conveniencia. Ingerir incidentes2026 separadamente para prueba MG08 después de autorización.
4. Con José validar lotes≥500k reales, referencias/snapshot/payload y respaldo/restauración en entorno autorizado futuro; no confundir5k nativas con500k ni canal consensuado con sensor físico.

## Fernanda — Diagramas, documentación, evidencia y trazabilidad

1. Consolidar acta y preguntas al profesor de05_academic_decisions; conservar firmas pendientes y matriz sin falsas aprobaciones.
2. Dibujar E-R y documental con DDL/colecciones de esta fase y verificar con Daniel/Kembly; distinguir sensor/sitio/canal/observación. Los diagramas del avance siguen para revisión, no son arquitectura aprobada.
3. Enlazar diccionario CSV, versiones/hash, JSON/logs nativos y veinte casos con estados; registrar meteo/clock/geografía provisionales.
4. Coordinar prueba cruzada24oct, informe25, freeze26, demo27 y avance28 según P y confirmación docente. HDFS/Spark/UI para asignación posterior, no ejecutados aquí.

## Puertas y qué puede empezar ya

Ya: revisión del contrato, reproducción local acotada, consultas/diseños sobre muestra y preguntas al docente. Antes14: modelos/IDs/alcance aceptados;17: carga inicial futura autorizada;20: mínimos reales y restauración;23: cierre técnico con veinte consultas;24–28: revisión y entrega. Mantener margen de esfuerzo54–84h-persona de Fase4 como estimación revisable con avances reales; tiempos nativos medidos no reemplazan estimación de trabajo.

Cada integrante entrega instrucciones, resultados y limitaciones para que otro las reproduzca. Ninguna tarea de este listado autoriza automáticamente cambios en Coolify/Tailscale/producción/commit/push/merge. Fase5 se detiene al entregar este paquete preliminar.
''')
    examples = json.loads((PRIVATE/'sample.extjson').read_text())
    selected = [next(d for d in examples if d['source_id']==s) for s in counts]
    (OUT/'examples.extjson').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
    traffic = [d for d in examples if d['source_id']=='MAD-TRAFFIC']
    average = sum(len(json.dumps(d,ensure_ascii=False).encode()) for d in traffic)/len(traffic)
    storage = {'measured_sample_bytes':{f:(PRIVATE/f).stat().st_size for f in ['sample.extjson','sample.csv','sample.parquet']},
      'measured_traffic_cache_bytes':(PRIVATE/'traffic_selected.parquet').stat().st_size,
      'measured_mean_serialized_traffic_json_bytes':average,
      'estimated_json_bytes_674704':round(average*674704), 'not_BSON_indexes_WAL_or_remote_benchmark':True}
    (OUT/'storage.json').write_text(json.dumps(storage,indent=2)+'\n')
    write('05_acceptance_checklist.md',f'''
# Fase 5 — Lista de aceptación de la fase, no de producción

| Criterio solicitado | Estado / evidencia |
|---|---|
| Contrato definido para revisión |Cumplido como borrador `{VERSION}`; no ratificado |
| Origen/transformación/disponibilidad por atributo |DiccionarioCSV{dictionary_rows}entradas, fuente/versión y NULL explícitos |
| Modelos SQL/documental preliminares |DDL/consultas y diseños05; tablas físicas vacías y colecciones pendientes visibles |
| Estrategia devolumen justificada |{total}elegibles estructurales enero y674704tráfico;5k nativas, no cargasmínimas definitivas |
| Pipeline inicial reproducible |Dry-run, preparación/lotes/cache/ledger/locks/ID/proveniencia/replay y exportaciónlimitada; ingestióncompleta/distribuida propuesta |
| Mongo nativo local si posible |{mongo['native_executed']}; versión{mongo.get('version')},5k,Aggregation Framework,CRUDdemo,índices/explain,cleanup |
| Prueba SQL adicional limitada |{pg['native_executed']};5k,DDL/FK/trigger/vistas/función,catálogos iguales;cleanup |
| Diferencias de fecha/granularidad |Enero conH24;accidentes2026 yenergíamensual separados;no CO2/recorridos ficticios |
| Aprobacionespendientes explícitas |Matriz05_academic_decisions y actapendiente cuatro/docente; clocks/unidades/CRS/inventarios no cerrados |
| Plan concreto Sprint1 |Handoff porintegrante ypuertas14/17/20/23/24–28oct |

Continuidad: las 48 pruebas anteriores fueron reproducidas (baseline_tests.xml). Pruebas finales heredadas+nuevas aprobadas: **{passed if passed is not None else 'pendiente de ejecución'}**, con cero fallos, errores u omisiones cuando el JUnit está aprobado. Conteo exacto y resultados en `results/phase5/tests.xml` y `final_checks.json`. Hashes de fases0–4 verificados, sin sobrescrituras. El primer enum incompleto de tipos de tráfico se conserva en superseded_type_filter.json: se corrigió URB antes de la prueba aceptada, no se descubrieron 611153 filas inválidas. La preparación anterior al ajuste de proveniencia es evidencia supersedida, no otra población.

**No producción:**faltan aprobación, estado/instalación/organismos/usuarios,meteo/clocks/geografía,MG04/05/08nativas,mínimos cargadosdefinitivamente,backup/restore,benchmarkremoto,HDFS/Spark/dashboard. No remoto,Coolify,Tailscale,cargamasiva,medicionessintéticasmasivas,commit/push/merge ni implementación definitiva. **Detenerse al finalizar Fase5.**
''')
    print('Generated 11 Phase5 deliverables and measured examples/storage evidence.')


if __name__=='__main__':
    main()
