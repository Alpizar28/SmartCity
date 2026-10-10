"""Build phase2 reports from actual offline outputs; estimates explicitly separate."""
import csv
import json
import platform
import re
import importlib.metadata
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from download import ROOT
from quality import dump

R=ROOT/'results';P=ROOT/'private_results'
MAIN=['MAD-AIR','MAD-METEO','MAD-TRAFFIC','NYC-COUNTS','NYC-AIR','NYC-311','LON-AIR','LON-ENERGY']


def get(name):return json.loads((R/(name+'.json')).read_text())
def n(value):return f'{int(value):,}'.replace(',',' ')
def pct(value):return f'{float(value):.2f}%'
def write(name,text):
    # Expand compressed technical prose without touching code, paths, URLs or identifiers.
    replacements={
        'fuentesprincipales':'fuentes principales','fuentesdeobservaciones':'fuentes de observaciones',
        'dosfuentes':'dos fuentes','tresfuentes':'tres fuentes','cuatroinventarios':'cuatro inventarios',
        'poralternativa':'por alternativa','sinfuente':'sin fuente','porzona':'por zona','zonafina':'zona fina',
        'año2023':'año 2023','enero2023':'enero 2023','enero2025':'enero 2025','julio2023':'julio 2023',
        'periodo2013':'período 2013','Jan2025':'Jan 2025','eneroGMT':'enero GMT','julioGMT':'julio GMT',
        'porhora':'por hora','porhoracoincidente':'por hora coincidente','porhogar':'por hogar',
        'horaH24':'hora H24','H01es':'H01 es','H24es':'H24 es','datosdiarios':'datos diarios',
        'No hay':'No hay','datosoriginales':'datos originales','rawintacto':'raw intacto',
        'seconservan':'se conservan','nose':'no se','Sinproducto':'Sin producto',
        'semánticade':'semántica de','sintéticospara':'sintéticos para','paramuestras':'para muestras',
        'concordanciacondicional':'concordancia condicional','registroshistóricos':'registros históricos',
        'antesdefase3':'antes de fase 3','Antesdefase3':'Antes de fase 3','fase3':'fase 3',
        'Fase2':'Fase 2','fase2':'fase 2','porGit':'por Git','SQLiteendisco':'SQLite en disco',
        'tipoCSV':'tipo CSV','enstreaming':'en streaming','enstream':'en stream',
        'nodevice':'no device','noautomática':'no automática','noduplicados':'no duplicados',
        'cadadía':'cada día','cadaJSON':'cada JSON','delZIP':'del ZIP','elZIP':'el ZIP',
        'laPK':'la PK','no horaria':'no horaria','sincoincidencia':'sin coincidencia',
        'sincorrespondencia':'sin correspondencia','sinmatch':'sin match','notodos':'no todos',
        'sinco-localización':'sin co-localización','sitiosco-localizados':'sitios co-localizados',
        'coords':'coordenadas','Rawdiario':'Raw diario','NO2elegibles':'NO2 elegibles',
        'NO2elegible':'NO2 elegible','NO2delpar':'NO2 del par','deobservaciones':'de observaciones',
        'observacionesNO2':'observaciones NO2','defuente':'de fuente','defuentes':'de fuentes',
        'delospuntos':'de los puntos','delosgrupos':'de los grupos','deltotal':'del total',
        'Del ladoNO2':'Del lado NO2','del ladoNO2':'del lado NO2',
        'tabla viva':'tabla viva','rangoexploratorio':'rango exploratorio','radioexploratorio':'radio exploratorio',
        'consumo totaldeLondres':'consumo total de Londres','deLondres':'de Londres',
        'la muestra':'la muestra','mismaclave':'misma clave','claveambigua':'clave ambigua',
        'clavesconflictivas':'claves conflictivas','claves únicas locales':'claves únicas locales',
        'novehículos':'no vehículos','lecturas únicas':'lecturas únicas','deintervalos':'de intervalos',
        'deduplicados':'de duplicados','dereportede':'de reporte de','fechadehecho':'fecha de hecho',
        'reporteciudadano':'reporte ciudadano','dehecho':'de hecho','notificaciónemitida':'notificación emitida',
        'deregistros':'de registros','dereporte':'de reporte','es fechade':'es fecha de',
        'No se sehace':'No se hace','se sehace':'se hace','seafirma':'se afirma','noafirmar':'no afirmar',
        'faltade':'falta de','deQA':'de QA','inclusoWKT':'incluso WKT',
        'campoCRS':'campo CRS','bboxplausible':'bbox plausible','datos numéricos':'datos numéricos',
        'centinelas':'centinelas','instalaciónindividual':'instalación individual',
        'estadoadministrativo':'estado administrativo','responsablepersonal':'responsable personal',
        'usuariosaplicación':'usuarios de aplicación','concentraciónCO₂':'concentración CO₂',
        'tiempoderecorrido':'tiempo de recorrido','alertashistóricas':'alertas históricas',
        'emisionesCO₂e':'emisiones CO₂e','energiaLL84':'energía LL84','energíaLL84':'energía LL84',
        'sin unidades':'sin unidades','porvariable':'por variable','sinzona':'sin zona',
        'memoriapor':'memoria por','Controlesdememoria':'Controles de memoria',
        'datos dinámicos':'datos dinámicos','Datos dinámicosnosnapshot':'Datos dinámicos no snapshot',
        'presupuestario':'presupuestario','autoridades/recurso':'autoridades/recurso',
        'autorización nueva':'autorización nueva','nuevaautorización':'nueva autorización',
        'bloqueada':'bloqueada','nofase3':'no fase 3','sin ganador':'sin ganador',
    }
    lines=[];code=False
    for line in text.strip().splitlines():
        if line.startswith('```'):code=not code;lines.append(line);continue
        if not code:
            parts=re.split(r'(`[^`]*`)',line)
            for i in range(0,len(parts),2):
                for old,new in replacements.items():parts[i]=parts[i].replace(old,new)
                parts[i]=re.sub(r'(?<=\d)(?=(?:filas|sitios|slots|valores|hogares|registros|puntos|columnas|horas|días|fechas|grupos|extras|claves|bytes|miembros|solicitudes|datos|pruebas|observaciones|meses|fuentes|reportes|pares|intervalos)\b)', ' ', parts[i])
                parts[i]=re.sub(r'(?<=%)(?=[A-Za-záéíóúñ])',' ',parts[i])
            line=''.join(parts)
        lines.append(line)
    (ROOT/name).write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    summaries={s:get(s+'-summary') for s in MAIN}
    schemas={p.name.removesuffix('-schema_quality.json'):json.loads(p.read_text()) for p in R.glob('*-schema_quality.json')}
    ma=get('MAD-AIR-annual_counts');mm=get('MAD-METEO-annual_counts');mt=get('MAD-TRAFFIC-full_counts')
    ep=get('NYC-AIR-full_counts');lc=get('LCL-expanded_counts')
    mi=get('Madrid-integration');ni=get('NYC-integration');li=get('London-integration')
    ver=get('verification');categories=get('NYC-311-categories')
    records=list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    def response(name):
        r=next(r for r in reversed(records) if r['id']==name and r['status']=='200')
        return json.loads((ROOT/r['path']).read_text())
    jan=response('311-count-2023-01-01')[0];jul=response('311-count-2023-07-01')[0]
    dot_global=response('DOT-global')[0]
    env={'python':platform.python_version(),'platform':platform.platform(),
         'packages':{name:importlib.metadata.version(name) for name in ['requests','pandas','numpy','pyarrow','pyproj','pytest','openpyxl']}}
    dump(R/'environment.json',env)
    quality_table='\n'.join(f"| {s} | {n(d['observations'])} | {n(d['entities'])} | {n(d['missing_values'])} | {n(d['duplicate_keys'])} | {pct(100*d['coordinate_valid_rows']/d['observations'])} |" for s,d in summaries.items())
    tests=ET.parse(R/'tests.xml').getroot();suite=tests.find('testsuite')
    testtext=f"{suite.attrib['tests']} pruebas, {suite.attrib['failures']} fallos, {suite.attrib['errors']} errores"
    write('02_audit_report.md',f'''
# Fase 2 — Auditoría real de tres alternativas

**Auditoría ejecutada; sin ganador, sin esquemas finales y sin fase 3.** Existen pruebas descargadas y analizadas de las ocho fuentes principales. La viabilidad del proyecto completo sigue **condicionada** para las tres alternativas: la auditoría no acredita atributos que no existen.

## Alcance, descarga y trazabilidad

Se releeron todos los entregables 00/01, README y bitácora antes de programar; se inspeccionó Python y se creó un entorno aislado (Python {env['python']}). No se modificaron los documentos previos; hashes en `results/prior_files_hashes.json`. Los requisitos confirmados son 10 consultas PG, 10 Mongo, 100k PG / 500k Mongo / 1M Spark y dos fuentes; no se ejecutaron motores de datos. No surgió una contradicción académica que requiriese reabrir los PDF oficiales.

**12 fuentes de observaciones/reportes descargadas y analizadas**, ocho principales y cuatro complementarias: energía e incidentes Madrid, LL84 NYC y DfT Londres. **Cuatro inventarios adicionales**: aire, meteo y puntos de tráfico Madrid; sitios LAQN. Total: {len(schemas)} fuentes perfiladas. Un ZIP con cuatro CSV LCL no se cuenta como cuatro fuentes independientes; dos ventanas por sitio LAQN siguen siendo la misma fuente.

Transferencia de cuerpos realmente leídos: **{n(ver['downloaded_entity_bytes'])} bytes ({ver['downloaded_entity_bytes']/1e6:.2f} MB decimales)**, incluyendo prefijos, errores, reintentos y documentación. Límite 1 000 000 000 bytes, restante {n(ver['remaining_bytes'])}. Esto no cuenta overhead TLS/TCP ni dependencias Python; estas últimas tampoco acercan el total al límite. Manifiesto con {ver['http_attempt_records']} intentos y {ver['files_hash_verified']} archivos cuyos SHA/tamaños se verificaron. Las solicitudes Range completas tienen `complete_response=True`, **no significa dataset completo**. La integridad de EPA ensamblado y de cada miembro LCL está documentada separadamente en `02_artifact_manifest.csv`.

Fechas reales UTC del manifiesto: {min(r['retrieved_at_utc'] for r in records)}–{max(r['retrieved_at_utc'] for r in records)}. Los logs usan hora local del sistema. Se preservaron respuestas sin alteraciones en `raw/` ignorado; Parquet, joins y SQLite de cardinalidad en `private_results/` ignorado. No se redistribuyen lecturas LAQN ni solicitudes individuales 311.

## Muestreo progresivo

- **A:** prefijos 4–8 KiB, metadatos y licencias. Se cotejó parseo, cabecera y tipo real, no solo HTTP.
- **B Madrid:** enero y julio **2025**, todas las estaciones/variables publicadas; tráfico completo enero 2025, muestra determinista de puntos con `id % 20 == 0` a lo largo de los 31 días. No representa todas las vías uniformemente: ID no es aleatorio y distribución por distrito puede sesgarse.
- **B NYC:** todos los conteos 2023 en páginas de 10k (85 106 filas), EPA todo 2023 filtrado por estado/condado; 311 {len(categories['sample_dates'])} días completos, semana consecutiva 6–12 enero más días 1/8/15/22/29 de enero/julio. Se amplió esa semana tras medir baja coincidencia de campañas. El patrón inicial favorece domingos en enero/sábados en julio: **no extrapolar frecuencias de categorías como si fuera muestra aleatoria**. Campos proyectados omiten direcciones/narrativas innecesarias.
- **B Londres:** NO2 horario, cinco sitios LAQN y dos meses completos (enero/julio 2013); energía de todos los hogares presentes en enero/julio en cuatro miembros completos iniciales del ZIP. Selección de hogares no aleatoria, no equivalente a muestra representativa de todo Londres.
- **C:** CSV Madrid completos (aire/meteo 2025–agosto 2026), ZIP tráfico completo, ZIP EPA nacional ensamblado por rangos y procesado por chunks, cuatro miembros LCL completos con CRC. Nunca se descargó el ZIP LCL completo (~796 MB).

EPA tuvo una interrupción tras 11 862 016 bytes durante la descarga monolítica inicial; ese registro no tiene `error` relleno debido a una excepción de urllib3 anterior a la corrección del manejador, pero `complete_response=False` y el log acreditan el fallo. Se continuó mediante rangos verificables de 1 MiB, con tres desconexiones transitorias/reintentos. No se declaró válido el ZIP hasta ensamblarlo y leer el miembro completo validando CRC. Se añadieron captura de excepciones de transporte y nombres de archivo inmutables por intento. No hubo evasión de restricciones.

## Registros efectivos y calidad de las muestras normalizadas

Cada fila de Madrid H01–H24 es una observación horaria distinta publicada, no sintética; no se cuentan a la vez fila diaria y 24 horas como 25 mediciones. Los números de esta tabla son **muestras normalizadas**, no filas de todos los archivos.

| Fuente | Observaciones muestra | Entidades de la fuente | Valor ausente/no numérico | Extras de clave duplicada | Coordenadas válidas de observaciones |
|---|---:|---:|---:|---:|---:|
{quality_table}

`entity` no implica sensor físico: en DOT es campaña/segmento/dirección; en LCL hogar anónimo; en 311 solicitud. En `02_quality_metrics.csv` se encuentran atributos originales, tipos inferidos/declarados, nulos, cardinalidad y estadísticas. Los JSON `*-summary.json` contienen estadísticas por variable/unidad, flags y geografía; `*-coverage.csv` contienen series por canal/mes, huecos, duplicados y frecuencia observada. Para 311 son eventos por zona/día, **no una cadencia esperada de sensor**. Cobertura temporal calculada entre primeros/últimos puntos de cada canal/mes no equivale a cobertura del mes completo ni de la red entera.

### Madrid

- Aire: {n(ma['raw_rows'])} filas diarias, {n(ma['hourly_slots'])} slots reales, 23 estaciones y 126 pares estación/magnitud; {n(ma['flags_full_year']['V'])} slots V, {n(ma['flags_full_year']['N'])} N y 3 M. Cero duplicados de clave diaria; cero referencias de estación ajenas al inventario actual. Los invalidantes permanecen en raw, incluso cuando el valor es 0.
- Meteo: {n(mm['raw_rows'])} filas, {n(mm['hourly_slots'])} slots, 26 estaciones/94 pares; {n(mm['flags_full_year']['V'])} V y {n(mm['flags_full_year']['N'])} N. `PUNTO_MUESTREO` **100% vacío**, por lo que no es clave válida; usar namespace/red + estación/magnitud/fecha/hora. Los inventarios explicitan VV81/DV82/T83/HR86/PB87/RS88/P89. Las unidades meteo del normalizador son contrato provisional a cerrar con diccionario técnico; no declarar toda unidad validada solo por el rótulo del inventario.
- **Tráfico accesible:** los antiguos recursos 161/160 ahora devolvieron ZIP 200/prefijos válidos; el recurso 137 da 404. Se escogió el recurso 73, enero de 2025, del catálogo oficial para coincidir con aire/meteo. ZIP de 93 223 315 bytes, {n(mt['raw_rows'])} filas y {n(mt['points'])} puntos; miembro CSV leído completamente con CRC. Muestra por estrato de ID: {n(mt['sample_rows'])} intervalos, cero duplicados de (id, fecha, tipo). `periodo_integracion` varía **1–30 minutos**: no es siempre 15. Intensidad es tasa veh/h, no conteo; la integración solo usa promedio de señal, no total de vehículos.
- Inventario de tráfico: 5083 IDs únicos; en muestra normalizada 242 puntos, parte no localizada en inventario vigente. El join cartográfico usa columnas decimales publicadas; se conservan UTM y ETRS89 originales. No se inventan distritos ambientales ni se transforma un punto cercano en la misma estación.
- Energía municipal: 35 803 filas; ID de edificio vacío en 65,553%, GRUPO vacío en 91,649%, consumo ausente en 0,053%. Hay 100 extras bajo una clave candidata que incluye campos opcionales: **no prueba de 100 mediciones duplicadas**. Replantear clave/jerarquía antes de sumar. Consumo mensual y unidades heterogéneas.
- Accidentes 2026: 33 322 filas de detalle y 14 388 expedientes únicos; 18 934 repeticiones del expediente esperables en personas/vehículos, no duplicados de incidente. No se emparejan con enero de 2025 como si coincidieran.

### Nueva York

- DOT 2023: 85 106 filas, 127 segmentos/150 canales campaña-segmento-dirección; 80 339 claves temporales únicas. **4 767 grupos con dos valores distintos**, incluso agregando WKT; cero filas completas idénticas. No se resolvieron sumando/escogiendo arbitrariamente: 9 534 filas se excluyen solo del join conservador, no de raw. Quedan 75 572 observaciones no ambiguas.
- EPA 88101: 9 350 315 filas nacionales examinadas en streaming, 104 903 del estado de Nueva York, **38 290 NYC** y cinco sitios. Solo condados 005 (Bronx), 047 (Brooklyn), 081 (Queens); **cero registros Manhattan/Staten Island para este parámetro/archivo**, no ausencia de toda la red EPA. Todas las unidades son µg/m³ (LC), datum WGS84. **Cero duplicados reales** de clave canal/fecha UTC. Hay 1 792 filas con qualifier; 36 498 observaciones numéricas/sin qualifier se usan conservadoramente. Un qualifier no significa automáticamente medición inválida: exclusión provisional para join, no borrado. La validación detectó que quitar timezone antes de comprobar claves producía cinco falsos duplicados el 5 de noviembre; se corrigió conservando UTC y se añadió regresión DST. Las dos horas locales 01:00 son instantes distintos, no conflictos de la fuente.
- PM2.5 máximo: 412 µg/m³; 1 999 candidatos IQR. No se eliminó el extremo ni se afirmó causa; distinguir un episodio ambiental real de error requiere QA/publicador. Concentración de CO₂ no existe aquí.
- 311: **{n(summaries['NYC-311']['observations'])} solicitudes únicas auditadas**, 16 fechas; {categories['closed_before_created']} casos con `closed_date` anterior a `created_date`; coordenadas ausentes en 1,477%. Son problemas/semántica de trámites a revisar, no estado de sensores. Categorías y agencias reales en `NYC-311-categories.json`; se agregan sin afirmar que todos los reportes sean eventos confirmados.
- WKT proyectado DOT: EPSG 2263→4326 como **hipótesis**; 85 106 puntos quedan en un bbox plausible, pero falta declaración oficial de CRS. Los adjuntos referenciados por assetId dieron 404 en la ruta probada. El join aceptado utiliza borough publicado, no esa transformación sin confirmar.
- Energía LL84: 200 reportes de 2023 perfilados; dos extras de (propiedad, año), granularidad anual. El esquema declara electricidad kWh/kBtu y emisiones CO₂e. La búsqueda oficial «hourly energy» devuelve principalmente LL84 anual, no una fuente horaria urbana acreditada. No convertir consumo anual en lecturas horarias.

### Londres

- LAQN: 7 440 slots NO2 de cinco sitios; 117 vacíos (1,57%), cero duplicados. Cinco sitios abiertos antes de 2013, ninguno cerrado antes del período. Dos valores negativos hasta −0,5 µg/m³ conservados como señales QA/instrumentales por revisar, no errores borrados. `Latitude/Longitude` plausibles; campos llamados `LatitudeWGS84` contienen metros/proyección y **no se interpretan como grados**. Apertura/cierre de sitio no es fecha de instalación del analizador.
- LCL: **{n(lc['rows_complete_members'])} filas efectivamente leídas**, {lc['households']} hogares en cuatro miembros, rango {lc['first']}–{lc['last']}; {lc['nonnumeric_or_missing_energy']} valores no numéricos/ausentes, cero negativos. Cardinalidad exacta en SQLite local: **{n(lc['unique_household_timestamp_keys'])} claves hogar/timestamp**, {n(lc['duplicate_key_extra_rows'])} extras. No se afirmó CRC/integridad del ZIP entero: solo miembros extraídos completos, tamaño/CRC/SHA verificados. El último miembro truncado del prefijo no se analizó.
- Enero/julio: 347 547 filas, 120 hogares; 233 extras idénticos, cero conflictos de valor, 347 314 intervalos únicos. Al integrar se deduplican idénticos sin modificar fuente y se rechazan 44 horas/hogar incompletas. No hay coordenadas/borough de hogar: integración fina **fallida (0%)**. Cohorte total no es consumo total de Londres.
- DfT: 100 filas complementarias de 2013 analizadas, 32 columnas, sin duplicados de (punto, fecha, hora, dirección); 16 956 registros del filtro según API previa. Es muestra inicial de acceso/esquema, **no muestra representativa de 30 días**; conteos de campañas, no monitoreo diario ni velocidad.

## Resultados de integración

Madrid aire–meteo: **{n(mi['coverage']['matched_groups'])} pares sitio/hora**, {pct(mi['air_row_spatiotemporal_pct'])} de observaciones NO2 elegibles; en sitios co-localizados, {pct(mi['coverage']['left_match_pct'])} de coincidencia temporal. Tráfico–aire: {n(mi['traffic']['coverage']['matched_groups'])} grupos en radio exploratorio de 1 km; {pct(mi['traffic']['point_geographic_match_pct'])} de los puntos elegibles y {pct(mi['traffic']['coverage']['left_match_pct'])} de grupos temporales relacionados. No equivalencia dispositivo/estación.

NYC DOT–EPA: **{n(ni['DOT_EPA']['matched_groups'])}/{n(ni['DOT_EPA']['left_groups'])} borough/día**, {pct(ni['DOT_EPA']['left_match_pct'])}. DOT–311: {n(ni['DOT_311']['matched_groups'])}/{n(ni['DOT_311']['left_groups'])} grupos, {pct(ni['DOT_311']['left_match_pct'])}; las tres fuentes simultáneas: {ni['three_source_groups']} grupo ({pct(ni['three_source_pct_of_DOT_groups'])}). No confundir este bajo porcentaje con imposibilidad de obtener 311 más días: limita la muestra.

Londres: **1 488/1 488 horas coincidentes (100%)**, 744 de enero y 744 de julio; ciudad/contexto de procedencia, **0% correspondencia hogar→zona fina**. Enero GMT es plausible; julio exige confirmar timezone LCL (o estudiar desplazamiento de una hora). La coincidencia numérica sin timezone acreditada no prueba sincronización real.

Detalle de reglas, denominadores, pérdidas y fallos en `02_integration_results.md` y `*-integration.json`; filas integradas reproducibles pero ignoradas porGit. Sin producto cartesiano ni enlacesficticios.

## Validación y estado

{testtext}; evidencia JUnit `results/tests.xml`, pruebas de presupuesto/reintentos/403/ZIP/CRC/granularidad/duplicados/geografía/joins. `verify.py` valida hashes, presupuesto y conservación de fases anteriores. Proceso completo offline por chunks de 100k; pico RSS de la ejecución completa en `results/runtime.json`. No es benchmark de Spark ni estimación de recursos Coolify.

Madrid: **auditable, condicionado** por QA/unidades, inventarios vigentes y KPIs sin fuente; el bloqueo 403 histórico ya no impide el tráfico auditado. NYC: **auditable, condicionado** por conflictos de claves, cobertura EPA parcial y campañas. Londres: **auditable a nivel ciudad, bloqueado para energía por zona fina con estas fuentes**, timezone y licencia pendientes. Todos superan investigación superficial; ninguno queda aceptado al 100% para el proyecto.

Antes de fase 3: cerrar granularidad/semántica admitida, atributos administrativos/usuarios, licencia/redistribución, CO₂/alertas/velocidad/recorridos y energía por zona/hora; verificar vigencia histórica de inventarios, timezone, claves conflictivas y volumen de ventanas comunes. **No hay ganador. No hubo conexión remota, generación sintética, commit/push/merge o comienzo de fase 3.**
''')

    write('02_integration_results.md',f'''
# Fase 2 — Integraciones medidas

Programa: `scripts/integrate.py`. Inputs normalizados de `private_results/*.parquet`, denominadores y resultados numéricos en `results/*-integration.json`. Todos los originales se conservan. Se seleccionan valores numéricos/flags elegibles y claves no ambiguas; duplicados idénticos se deduplican **solo en derivados**. Grupos conflictivos se excluyen del join, nunca se «resuelven» sumando sin identidad física. Validación `one_to_one`/`many_to_one` evita producto cartesiano.

## Madrid aire–meteorología

Entidades independientes porred;13sitios con **mismo código corto y coordenadas publicadasdistancia<1m**. Esto demuestra co-localización de puntospublicados, no equivalencia de analizadores ni instalación simultánea. Inventarios24aire/26meteo; muestra23sitiosaire. {pct(mi['geographic_air_site_match_pct'])}desitiosambientales de muestra se co-localizan.

NO2 magnitud8 ytemperatura83, enero/julio2025. H01esfin deprimerahora;H24media23–24h se lleva a00hdel día siguiente. Datos enhora local Madrid, ambosmisma semántica; períodos fuera deDST. Se conserva magnitud/unidad, no se mezclanvariables.

De{n(mi['eligible_air_NO2_rows'])}observacionesNO2elegibles,{n(mi['spatially_mapped_air_NO2_rows'])}están en sitiosco-localizados({pct(mi['air_row_spatial_pct'])});{n(mi['air_row_spatial_unmatched'])}sinco-localización. Se relacionan **{n(mi['coverage']['matched_groups'])}**, {pct(mi['air_row_spatiotemporal_pct'])}deltotalNO2elegible. Entre19 099observaciones espacialmente mapeadas:12sintemperatura válida; cobertura temporal{pct(mi['coverage']['left_match_pct'])}. Del lado meteo:16 904observaciones sinNO2delpar. Se pierden sitios no co-localizados, otrasvariables yflags noV; no se rellenanfaltantes.

## Madrid tráfico–aire

Inventario porIDreal, decimal lat/lonpublicados;242puntos enmuestra,240conlecturasflagsNelegibles;239deestosconcoordenadas.76puntos elegibles dentrode1km del sitioambiental máscercano: **{pct(mi['traffic']['point_geographic_match_pct'])}**. Radioexploratorio elegido para prueba, no equivalencia causal ni unazonaoficial. Publicadas coordenadasdecimales ≠precisiónGPS/acreditación de exactitud; inventarioactual no prueba vigenciaenero2025.

674704intervalos elegibles:213688vinculados espacialmente({pct(mi['traffic']['spatial_row_match_pct'])}),461016fuera/singeografía. Se agregan por hora y sitio de contexto, asignando timestamp de tráfico como inicio de intervalo y aire como fin dehora. **13918/14093grupos** conNO2válido({pct(mi['traffic']['coverage']['left_match_pct'])});175sincorrespondencia. Del ladoNO2enero:2967grupos sintráfico seleccionado.

`periodo_integracion`varía1–30min; el promedio de intensidad en esta prueba es **promedio de señales reportadas**, no total de vehículos ni estimador ponderado deexposición. Antes de correlación válida cerrar semántica inicio/fin, duración/coberturadeintervalos y ponderación. Se pierde información de puntos/direcciones eintervalos al agregar; no sumarlas tasasveh/h como conteos.

## NYC DOT–EPA–311

DOT campaña/segmento/dirección, no sensor permanente. Se excluyen9534filas declaveambigua con valoresdistintos:75572elegibles. EPA estado36ycondados005/047/061/081/085; cinco sitios soloenBronx/Brooklyn/Queens. FechaGMT se convierte aAmerica/New_Yorkpara coincidir con calendarioNYC; `Date Local`EPAes hora estándar, no relojDST. DOT/311calendario local es supuesto a cerrar condiccionario; join diario reduce pero no elimina elriesgo fronterizo.

Correspondencia espacial mediante **borough declarado**; conversion WKT2263→4326solo hipótesis auditada (bboxplausible), no usada para joins. 311boroughnormalizado capitalización; `Unspecified`queda sincoincidencia enDOT. No hay referencia de311a sensor, ni se inventa. EPAtecnologías/POCse mantienen al cargar; para agregados promediar por sitio primero ydespués porborough con iguales pesos de sitio, perdiendo detail/horas/metodos.

| Join | Grupos izquierdos | Grupos derechos | Ambos | Izq sin match | Der sin match | Cobertura izq | Cobertura der |
|---|---:|---:|---:|---:|---:|---:|---:|
| DOT–EPA borough/día | {ni['DOT_EPA']['left_groups']} | {ni['DOT_EPA']['right_groups']} | {ni['DOT_EPA']['matched_groups']} | {ni['DOT_EPA']['left_unmatched']} | {ni['DOT_EPA']['right_unmatched']} | {pct(ni['DOT_EPA']['left_match_pct'])} | {pct(ni['DOT_EPA']['right_match_pct'])} |
| DOT–311 borough/día | {ni['DOT_311']['left_groups']} | {ni['DOT_311']['right_groups']} | {ni['DOT_311']['matched_groups']} | {ni['DOT_311']['left_unmatched']} | {ni['DOT_311']['right_unmatched']} | {pct(ni['DOT_311']['left_match_pct'])} | {pct(ni['DOT_311']['right_match_pct'])} |

Tresfuentes: **{ni['three_source_groups']}grupo**,{pct(ni['three_source_pct_of_DOT_groups'])}delosgruposDOT. Muestra31116fechas no es eluniverso; consultasadicionales de mismosmeses podrían aumentarlo, pero no se inventan resultados. DOTsumas son conteos en intervalos observados, no volumen total delborough; campañas/díasdiscontinuos sesgan correlaciones. 311created_datees fecha dereporte, no fechadehecho necesariamente. No hay causalidad ni alertas automáticas acreditadas.

## Londres aire–consumo

LAQNNO2de5sitios yLCL120hogaresanónimos. Contextogeográfico común **Londres ciudad de lamuestra**, no coordenadas individuales. **Prueba de hogar→borough/zona fina fallida:0%**, sincolumna paraasignar, no se infiere a partir deestación próxima.

Deduplicación de233repeticiones idénticas a347314intervalosenergéticos. Sumados solamentedos intervalos únicos de30min porhogar/hora;44horas/hogar parciales excluidas. Agregado de cohorte eléctrica porhora, concentración media de los sitios conlectura; no «consumo totaldeLondres». Cohorte varía108–119hogares porhoracoincidente; dinámica de panelcontamina tendencias si no se selecciona cohorte estable posteriormente.

**1488horasizq/1488der/1488coincidentes,0sinmatch,100%temporal por timestampsinterpretados**. Enero744horasGMTconcordantes; julio744concordancia **condicional** a timezoneLCLno acreditada. LAQNesGMT; relojLCLpodría serUTC/localBST. Si se desplaza1hora los resultados/fases cambiarán: no afirmar sincronización real ni correlaciones hastaresolverlo. Apertura/cierre desitios valida período2013, no fechas de medidores.

Se pierden variación geográfica, hogar/cohorteindividual, medias horas, máximoslocales ambiental y panel completo; no se rellenan missing valores con0. Integraciónestacional no garantiza interanualidad. Exportaciones integradas permanecen ignoradas porGit porprudencia deprivacidad/licenciaLAQN.

## Resultado

Hay pruebasreales de almenosdosfuentes poralternativa; no todos los joinsniómbitos tienen éxitopleno. Madridco-localización valida una relaciónmásespecífica que mera ciudad; NYCdemuestra coincidenciaparcial; Londrespermite cohorteciudad pero **nozonafina**. Los porcentajes no sonpuntajes deldataset ni comparables sin susdenominadores.
''')

    # Deterministic stratified serialization estimates, with measured Parquet sizes kept separate.
    storage=[]
    for s in MAIN:
        df=pd.read_parquet(P/(s+'.parquet'))
        idx=np.linspace(0,len(df)-1,min(1000,len(df)),dtype=int)
        encoded=df.iloc[idx].to_json(orient='records',date_format='iso')
        storage.append({'source':s,'measured_parquet_rows':len(df),'measured_parquet_bytes':(P/(s+'.parquet')).stat().st_size,
            'serialization_sample_rows':len(idx),'estimated_json_bytes_per_document':len(encoded.encode())/len(idx),
            'estimated_json_bytes_500k':round(len(encoded.encode())/len(idx)*500000),
            'assumptions':'uniform index1000selected normalized records; JSONUTF8, noBSON/index/replica overhead; not measuredDBstorage'})
    pd.DataFrame(storage).to_csv(R/'storage_estimates.csv',index=False)
    storage_table='\n'.join(f"| {x['source']} | {n(x['measured_parquet_rows'])} | {n(x['measured_parquet_bytes'])} | {x['estimated_json_bytes_per_document']:.1f} | {x['estimated_json_bytes_500k']/1e6:.1f} MB |" for x in storage)
    write('02_volume_analysis.md',f'''
# Fase 2 — Volumen real y estimaciones

No se cargóPG/Mongo/Spark ni se crearon sensoresficticios. Se examina capacidad de alimentación, no cumplimiento de ejecución de losmotores. Maestros pequeños no alcanzan100k: PGnecesita hechos estructurados históricos reales. Granularidad horariaMadrid representa horaspublicadas, no división artificial devariablespara inflarregistros. Raw diario yobservacionesnormalizadas no son nuevas fuentes ni se sumancomo25mediciones.

## Cantidades medidas

| Alternativa | Registros efectivamente procesados | Unicidad / utilidad acreditada | Límites |
|---|---|---|---|
| Madrid aire/meteo | {n(ma['raw_rows'])}+{n(mm['raw_rows'])}filas; {n(ma['hourly_slots'])}+{n(mm['hourly_slots'])}slots horarios publicados | 0duplicados diarios; {n(ma['flags_full_year']['V'])}+{n(mm['flags_full_year']['V'])}slotsV | Recurso2025–ago2026, unidades, DST/semánticaV/M; no sensores adicionales |
| Madrid tráfico | {n(mt['raw_rows'])}filas enero2025,{n(mt['points'])}puntos | Muestra {n(mt['sample_rows'])},0duplicados de(id,fecha,tipo);674704flagsN | Unicidad deTODOelZIPno medida: no llamar13,2Mlecturas únicas |
| NYCconteos | 85106filas2023 | 80339claves,4767conflictivas,75572no ambiguas | Totalendpoint{n(int(dot_global['n']))}no acreditado único globalmente |
| EPA NYC | {n(ep['national_rows'])} filas nacionales recorridas para filtrar {n(ep['NYC_rows'])} locales | 38 290 claves UTC únicas, 36 498 observaciones sin qualifier | Solo tres boroughs; filas nacionales NO cuentan como NYC |
| 311 | {n(summaries['NYC-311']['observations'])}filas de16días | Todas unique_key únicas enmuestra | Son solicitudes, no lecturas de dispositivo |
| Londres energía | {n(lc['rows_complete_members'])}filas de4CSVcompletos,{lc['households']}hogares | **{n(lc['unique_household_timestamp_keys'])}claves únicas medidas** porSQLiteen disco;{lc['nonnumeric_or_missing_energy']}valoresausentes/no numéricos | Conflictos devalor globales no perfilados; muestraJan/Julsolo233extras idénticos |
| Londres aire | 7440slots5sitios/2meses | 7323valores numéricos,0duplicados | Flags de ratificación adicionales no publicados enendpoint; presencia numérica no garantizaQA |

311 consultaagregada enero2023:{n(int(jan['n']))}filas y{n(int(jan['unique_ids']))}unique_keydistintos; julio:{n(int(jul['n']))}y{n(int(jul['unique_ids']))}. **{n(int(jan['unique_ids'])+int(jul['unique_ids']))}solicitudes únicas consultables** en dosmeses disjuntos: evidencia deAPI, no todos descargados. Si changed-live-table, recuentos/versiónpuedenvariar; no se afirma snapshottransaccional.

## Umbrales por tecnología

- **Madrid100kPG/500kMongo/1MSpark:** capacidad real acreditada por slots horariosV de aire/meteo delrecurso completo (cadafuente>1M); hay clavesdiariasúnicas yhorasdistintas. Tráficomuestraya>500kintervalos únicos elegibles. Estas conclusiones no requieren síntesis ni multiplicacióncartesiana; la representación deobservaciónhoraria debe aceptarse académicamente. Energía/movilidad/KPIscompletos siguenotrascondiciones.
- **NYC100kPG:** muestra dehechos no ambiguosDOT+EPA supera112k; 311añade124130solicitudes únicas, sincontarcomo sensores. **500kMongo:**531503unique_keyde311comprobados poragregadoAPIenenero+julio, suficiente para documentosdesolicitud si se acepta esagranularidad. **1MSpark:** condicionado; DOTglobal1,875Mfilasconsultables y añosextras reales, pero unicidad/QAglobal sinmedir. Extrapolando exclusivamente para planificación la razón dedatosDOTno ambiguos2023(75572/85106≈88,80%) alendpointglobal se esperaría≈1,665M; **estimación,no prueba**. Alternativamente311otrosmeses requiere contarIDsdistintos antesdeafirmar1M. Losconteos2023+EPA+311descargados no alcanzan1M.
- **Londres100kPG/500kMongo/1MSpark:** **{n(lc['unique_household_timestamp_keys'])}claves energéticas únicas locales** enmiembros completos; incluso descontando conservadoramente todoslos119faltantes supera1M. Capacidad real, no extrapolación de167Mpublicados. No implica energía porzona ni instalación demedidor; fechaentidad hogarno persona.

Maestros: Madrid24sitiosaire/26meteo/5083puntos tráfico, LAQN258sitios históricos/actuales; conteosno equivalen a dispositivosactivos. SQLhechos ydocumentos deben preservar claves, unidad, fuente, flags y tiempo; no diseñamos esquemasfinales aquí.

## Almacenamiento

EPAZIP completo76 998 372bytes →CSV2 625 915 829bytes (~34,1×). Se leyóstreaming; **no se materializó CSVnacional** en disco. ZIPtráfico93 223 315bytes contieneCSVcuyo tamañodecompresión está en `MAD-TRAFFIC-full_counts.json`. LCL20MBdeprefixred generó4CSVcompletos de~50MBcadauno; SHA/CRC ybytes en `02_artifact_manifest.csv`. El almacenamiento lógico/descomprimido no es descarga red.

| Fuente | Filas Parquet medidas | Bytes Parquet medidos | JSON estimado bytes/doc | JSON estimado500k |
|---|---:|---:|---:|---:|
{storage_table}

EstimaciónJSON:1000índicesuniformes por muestra normalizada, serializaciónUTF8yfechasISO; no BSON, índices, WAL, réplicas ni overheadMongo/PG. Parquetbytes son archivos reales medidos, no equivalentes a uso deDB. Datatypes/control de compresión pueden alterar ratios; **no existe benchmark de rendimiento remoto**. `results/storage_estimates.csv` separa columnasmeasured/estimated.

Períodos adicionales: Madrid recurso2025–2026ya auditado ycatálogohistórico; tráfico unmesaporta granvolumen; NYCaños2000/2006–2026discontinuosagregados en `DOT-years` (no todoslosaños desde2000); LCL2011–2014enmiembrosauditados, LAQN2013coincide. Para comparación interanual auditar ventanas equivalentes/canales estables; volumen no resuelve cobertura/intersección ni licencias.

**Síntesis: ninguna generada y ninguna necesaria para obtener volumen potencial deestasfuentes; ausenciasdeatributos/KPIs no se rellenan por eso.**
''')

    write('02_blockers.md','''
# Fase 2 — Bloqueos y condiciones pendientes

## Acceso y validación de fuentes

- **Resuelto para el recurso auditado:** tráfico Madrid ya no403; recurso73enero2025ZIPcompleto/CRCválido. 161/160200actualmente,137404. No generalizar a todocatalogo ni afirmar que se evadió elbloqueo: se usaronURLs oficiales sin proxies/credenciales.
- **Resuelto EPA:** ZIPnacional ensamblado por rangosdespuésdefallotransitorio; CRCdelCSVcompleto verificado. FiltroNYCreal38 290filas, no lasnacionales.
- **LCLZIP entero no validado:** prefijo20MBcon4miembros completos; CRC/tamaño/SHA propios, último truncado ignorado. Núcleoenergético síauditado, no auditoría exhaustiva5567hogares.
- **CRSDOTpendiente:** WKTproyectado candidatoEPSG2263, bboxconsistente insuficiente; rutaadjuntosporassetId404. Join porboroughesposible, mapas/proximidad requieren declaraciónoficial.
- **LAQNlicencia restringida:** condiciones«informational and educational purposes only» y«NOT for operational or commercial purposes». Usoeducativo local es compatible con la finalidad declarada; nohay permiso general de redistribución acreditado. Se conserva raw e integraciones ignorados; métricas agregadas no copian tablascompletas. Antesdepublicar/downloaddashboard revisar permiso publicador/propietarios; no CC BYasumida.
- MadridCCBY4.0confirmada; UKPNCCBY4.0enficha, DfTOGLv3enpáginaoficial. NYCterms y EPAdisclaimer descargados para revisión; no asumirlicenciaCCBYporSocrata. DatosEPApúblicos/condiciones originales, revisar excepciones y citar proveedor.

## Semántica y calidad

1. **Madridrecursos móviles:** aire ymeteo contienen2025-01-01–2026-08-31, no «anual2025»como sugería laprimera fila deFase1. Se documenta esta corrección aquí sin sobrescribir00/01históricos. URLs/hashes/período realdeestaauditoría sonautoridad sobre alcanceactual.
2. Inventariosaire/meteoactuales muestran13co-localizaciones; conservarred/canal, no declarar dispositivos equivalentes. Fechas«alta»deaire son altasdesitio, no instalación deanalizador. VigenciahistóricadeinventariotráficoJan2025aúnnoacreditada.
3. MadridmeteoPUNTO_MUESTREO100%vacío; necesitaclavecompuesta propia. HoraH24esfin23–24h, DSTMadridelimina lahora repetida según diccionarioM13. No forzar24horas reales cadadíaDST. Enero/julioseleccionados evitanambigüedad.
4. Tráfico integra1–30min: intensidadveh/h, velocidadnohomogénea por tipo, promedio de señal enprueba no total decarros; requiere ponderación/cobertura antesdeanalítica definitiva. ErrorNesNoErrorpor diccionario; valorabsurdono seborra solo porIQR.
5. DOT4767grupos con valores diferentespara mismaclaveinclusoWKT. Identidaddecontadorfísico/número decarril no publicado; revisión conDOT/diccionario necesaria. Añadirvalor alaPKpara ocultarconflictos no losresuelve.
6. Un qualifier EPA no siempre es invalidante. El join conservador excluyó 1 792 registros calificados; revisar su significado antes de usar extremos/imputar. EPA no tiene duplicados reales de clave UTC en la muestra: quitar timezone creaba cinco falsas colisiones durante el cambio de hora de noviembre; se corrigió y probó. La ausencia de 88101 en Manhattan/Staten Island no equivale a falta de todo tipo PM2.5: otros parámetros/tecnologías no fueron auditados, no inventar cobertura.
7. 311created_datees reporte;149cierres anterioresacreación enmuestra, coordenadasausentes1,477%, categoríasheterogéneas. No son todosaccidentes ni alertasdeIoT. Claveunique_keyúnica realenla muestra.
8. LCL233duplicadosidénticosJan/Jul, 119valoresno numéricos/faltantes en4Mexpandidos; timestampssemihorarios sinzona explícita. JulioGMTvsBSTtodavía indeterminado. Deduplicaciónoriginalnoautomática; rawintacto.
9. **Londresenergíazonafina bloqueada:** ningún borough/lat/lonhogar;0%demapeofino. Total decohorte varía108–119hogares/hora; no totaldeLondres. No asignarloshogaresaestaciones/zonas inventadas.
10. DosvaloresLAQNnegativos, PM2.5EPAmáximo412 eIQRtráficopicos son **señalesrevisables**, no prueba dedatoerróneo. No eliminaciónautomática.

## Cobertura académica transversal

Instalaciónindividual, estadoadministrativo, responsablepersonal, usuariosaplicación, concentraciónCO₂, alertashistóricasemitidasporzona ytiempoderecorrido siguen sinfuenteacreditada. NYCenergíaLL84anualno horaria; Madridenergíamensualno horaria; Londreshorariaderivableperosinzonafina. ConteosNYC/DfTno velocidad. Una tasa histórica deobservaciones no tasa derecepción en vivo.

Resolverconequipo/docente camposfaltantes/derivadosaceptados, no con síntesisautorizada implícitamente. Ningún paquete es«100%listo». Capacidad1MSparkNYCcondicionada a cardinalidad/QA ampliada; otrasdos acreditan >1Mobservaciones/claves reales con lasrestriccionesindicadas.

## Cobertura de auditoría y límites

Ochofuentesprincipales realmenteanalizadas;12fuentesdeobservaciones/reportes+4inventariosperfilados. DfT100filas yLL84200son pruebascomplementariasdegranularidad/esquema, **no muestrasrepresentativas deperíodoscompletos**. No hay conexión remota/pruebasdeDB/rendimientoSpark. Estadísticos exactos se refieren alalcancede cadaJSON, no a fuenteentera. LCLmiembros inicialessesgados, tráficoestratoIDdeterminista,311díasseleccionados.

Las tres auditoríasdelasfuentes centrales fueron ejecutadas; integraciónfinaLondresfalla explícitamente. El alcance deFase2está documentado y cerradoconcondiciones, **no aceptación definitivade datasets ni selección ganadora**. Fase3necesita autorización nueva.
''')

    write('02_reproduction.md',f'''
# Fase 2 — Reproducción

Directorio de trabajo: `research/datasets/` del repositorio SmartCity. Fases 00/01 no modificadas; conservarlas porque los scripts reutilizan las URLs de `01_http_evidence.csv`. No seguir las instrucciones de infraestructura del README raíz para esta auditoría. Ningún script conecta a PostgreSQL/MongoDB/Coolify/Tailscale.

## Entorno

Sistema Python 3.12.3 sin pandas/NumPy/PyArrow/pyproj/pytest al comenzar. Entorno aislado Python {env['python']} creado por uv. Paquetes principales en `scripts/requirements.txt`; versiones resueltas en `results/environment.json` y `scripts/requirements.lock`. Para reproducir con Python 3.11:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r scripts/requirements.lock
```

Entorno/descargas/derivados ignorados por `.gitignore` local. No subir `raw/`, `private_results/`, `.venv/` ni SQLite. No se modifican fuentes; las transformaciones quedan separadas.

## Ejecución offline con archivos locales

```bash
.venv/bin/python scripts/verify.py
.venv/bin/python scripts/audit.py all
.venv/bin/python scripts/integrate.py
.venv/bin/python -m pytest tests -q --basetemp=/tmp/opencode/smartcity-phase2-tests --junitxml=results/tests.xml
.venv/bin/python scripts/build_reports.py
```

`audit.py` admite `madrid`, `traffic`, `epa`, `nyc`, `london`, `complements`, `all`; no accede a red. Muestras definidas en código: Madrid enero/julio 2025, tráfico ID%20=0 en enero 2025; NYC DOT 2023 completo/311 en 16 días; LAQN cinco sitios × dos meses; LCL miembros iniciales completos con CRC y selección enero/julio 2013. No hay muestras sintéticas ni parámetros escondidos. `quality.py` y `readers.py` son reutilizables; `integrate.py` guarda reglas, denominadores y correspondencias faltantes. También puede ejecutarse todo con `.venv/bin/python scripts/run_offline.py`, que conserva `results/offline_run.log`.

Controles de memoria: CSV por chunks de 100k filas; EPA filtra localmente en stream antes de acumular, sin materializar su CSV nacional de 2,6 GB; tráfico conserva solo el estrato de ID; LCL acumula dos meses y cuenta claves exactas en SQLite en disco (cache 8 MiB). Miembros ZIP limitados a 70 MB descomprimidos, validación de paths/CRC/longitud antes de procesar. Pico medido en la última ejecución completa: {n(get('runtime')['peak_rss_kib'])} KiB; reservar aproximadamente 1,5–2 GB para reproducir. No se promete operar en 512 MB ni se acredita rendimiento remoto.

Estadísticos originales en `*-schema_quality.json`; tipos declarados provienen de Socrata cuando hay metadatos, o quedan pendientes/descripción básica de estructura. Estadística física normalizada por variable/unidad en `*-summary.json`. Estadísticas numéricas sobre IDs/códigos son diagnósticos de formato, no interpretación física. Rangos/unidades que requieren validación adicional se indican en los bloqueos.

## Adquisición en entorno limpio o actualización autorizada

Estas órdenes realizan red pública y **consumen el presupuesto**. Ejecutar **secuencialmente**: no correr varios downloaders concurrentes sobre un mismo manifiesto, pues el control de presupuesto/append no tiene lock entre procesos.

```bash
.venv/bin/python scripts/download.py initial --budget 1000000000
.venv/bin/python scripts/download.py official --budget 1000000000
.venv/bin/python scripts/download.py nyc --budget 1000000000
.venv/bin/python scripts/download.py madrid-traffic --budget 1000000000
.venv/bin/python scripts/download.py epa --budget 1000000000
.venv/bin/python scripts/download.py complements --budget 1000000000
```

En una reproducción nueva, EPA se ensambla desde cero por rangos de 1 MiB. Esta corrida reutilizó 11 862 016 bytes de una descarga interrumpida, registrados en manifiesto. Comprobar inicio/fin/total de `Content-Range` antes de ensamblar. SHA del archivo completo en `results/epa_assembly.json` y `02_artifact_manifest.csv`. Si cambian rango/ETag/tamaño, revalidar versión; CRC detecta inconsistencias, no asumir continuidad entre versiones.

Timeout conexión 15 s/lectura 90 s, hasta dos intentos solo en fallos transitorios/429/5xx, backoff 2 s/Retry-After hasta 120 s; 403/401/404 sin reintentos ni evasión. Paginación secuencial, pausa de un segundo y orden explícito SODA, límites 10k DOT/5k 311. No hay snapshot transaccional entre páginas de tablas vivas: guardar fecha/versión/hash y verificar duplicados. `$offset` puede desplazarse si cambia la tabla durante la adquisición.

Límite acumulado de 1 GB persistido en `02_download_manifest.csv`, incluyendo intentos fallidos/prefijos. Si se ignora Range, el stream se cierra al alcanzar el cap; `complete_response` significa respuesta completa, no «dataset válido». `BudgetExceeded` detiene red; el script rechaza presupuesto superior a 1 GB. Aumentarlo requiere autorización expresa y cambio posterior. Logs en `results/download.log`. Reutilización exige archivo/SHA coincidente; cada nuevo intento tiene un path distinto, no sobrescribe las fuentes.

## Validación de evidencia

`verify.py` comprueba tamaño/SHA de cada respuesta contabilizada, presupuesto, hashes de 00/01 y artefactos locales. Resultado: **{testtext}**, evidencia JUnit. Los pequeños fixtures/mocks de las pruebas **no son datos sintéticos para aumentar datasets**. Se prueban 403 sin retry, 503 con backoff, presupuesto persistido, Range ignorado, ZIP truncado/CRC/path seguro, H24, ceros/nulos, duplicados/gaps, conflictos de valor y prevención de joins cartesianos. Cinco pruebas adicionales comprueban los resultados guardados de fuentes reales.

`build_reports.py` regenera reportes desde resultados locales; no invoca scraping ni servicios remotos. Los tres manifiestos/métricas CSV son UTF-8 con cabecera. Si se amplían muestras, volver a ejecutar auditoría/integración/reportes antes de presentar un diagnóstico actualizado.

## Proveniencia/licencias

Referenciar organismo/recurso/fecha/hash del manifiesto. Licencias: Madrid CC BY 4.0 (M25), UKPN CC BY 4.0 (L03), LAQN uso educativo restringido (L11), EPA descripción/disclaimer y términos NYC descargados. Revisar permisos vigentes antes de publicar. No se descargaron direcciones/narrativas 311; lecturas LAQN e integraciones permanecen locales e ignoradas por Git.

No instalar servicios, generar esquemas finales SQL/MongoDB, seleccionar ganador ni realizar commit/push/merge. **Fase 2 cerrada; Fase 3 pendiente de autorización.**
''')

    # Preserve source records as JSON evidence, with a compact auditable global summary.
    dump(R/'phase2_summary.json',{'main_sources':len(MAIN),'observation_sources_with_complements':12,
        'reference_inventories':4,'profiled_sources':len(schemas),'downloaded_bytes':ver['downloaded_entity_bytes'],
        'primary_raw_rows_audited':{
            'Madrid':ma['raw_rows']+mm['raw_rows']+mt['raw_rows'],
            'NYC':sum(schemas[s]['rows'] for s in ['NYC-COUNTS','NYC-AIR','NYC-311']),
            'London':lc['rows_complete_members']+schemas['LON-AIR']['rows']},
        'tests':dict(suite.attrib),'no_winner_selected':True,'phase3_started':False})


if __name__=='__main__':main()
