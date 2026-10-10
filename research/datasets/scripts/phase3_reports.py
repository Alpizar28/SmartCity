"""Evidence-driven Phase3 matrices. No selection scores, downloads or production connections."""
import csv
import json
import xml.etree.ElementTree as ET

import pandas as pd

from download import ROOT
from phase3_validate import OUT

CITIES=['Madrid','NYC','London']
ALLOWED={'CUMPLE_VERIFICADO','FACTIBLE_NO_EJECUTADO','PARCIAL','NO_CUMPLE','NO_VERIFICADO'}


def get(name):return json.loads((OUT/name).read_text())
def prior(name):return json.loads((ROOT/'results'/name).read_text())
def write(name,text):
    from phase3_report_texts import render, spacing
    (ROOT/name).write_text(spacing(render(name,text)).strip()+'\n')


def fmt(n):return f'{int(n):,}'.replace(',',' ')


def main():
    validation=get('validation.json');prepared=get('prepared_data.json');sql=get('postgres_execution.json')
    conflicts=get('dot_conflicts.json');incidents=get('incident_checks.json');history=get('unit_history_checks.json')
    requirements=list(csv.DictReader((ROOT/'00_query_matrix.csv').open()))
    matrices=[];origins=[]
    # Per-requirement fields come directly from the preserved academic matrix.
    pg_transforms={
       'PG01':'canal lógico → categoría (fuente, variable, unidad); COUNT DISTINCT channel_id',
       'PG02':'JOIN canal → ubicación de fuente; no localizar hogares anónimos',
       'PG03':'estado administrativo faltante; NULL no se convierte a inactivo',
       'PG04':'organización propietaria/gestora separada del publicador; vínculo nullable',
       'PG05':'GROUP BY ubicación/HAVING/ORDER BY; no contar lecturas como sensores',
       'PG06':'fecha_instalacion DATE nullable; alta/apertura de sitio no sustituye instalación',
       'PG07':'NOT EXISTS contra lecturas de una ventana y catálogo independiente; no inferir falla',
       'PG08':'CTE + DENSE_RANK sobre canales por zona conocida, cobertura de muestra explícita',
       'PG09':'VIEW channel_by_type sobre sensor_scope; consulta y resultados contrastados',
       'PG10':'función SQL STABLE channels_at_location(text) RETURNS bigint; llamada contrastada'}
    city_sources={
       'Madrid':'aire ESTACION/MAGNITUD/PUNTO_MUESTREO/Hxx/Vxx + inventarios CODIGO_CORTO/ESTACION/LATITUD/LONGITUD; tráfico id/fecha/tipo_elem/error + distrito inventariado',
       'NYC':'EPA State/County/Site/Parameter/POC/Method/Date GMT/Time GMT/Units; DOT requestid/segmentid/direction/componentes fecha, como campañas separadas; boro/condado',
       'London':'LAQN SiteCode/SiteName/LocalAuthorityName/DataOwner/DataManager/DateOpened/Closed/MeasurementDateGMT; LCL LCLid/DateTime/kWh sin ubicación fina'}
    for city in CITIES:
        for req in requirements[:20]:
            ident=req['id'];tech=req['tecnologia']
            if ident.startswith('PG'):
                status='CUMPLE_VERIFICADO' if ident in ['PG09','PG10'] else ('NO_CUMPLE' if ident in ['PG03','PG06'] else 'PARCIAL')
                test='SQL nativo ejecutado y comparado con Python; '+('diagnóstico de ausencia, no respuesta al requisito' if ident in ['PG03','PG06'] else 'alcance de canales/sitios observado, no inventario físico completo')
                field_state='unavailable' if ident in ['PG03','PG06'] else 'observed + derived'
                transform=pg_transforms[ident]
                synthetic='No generada. Si se exige rellenar estado/instalación, falta fuente real o aceptación docente.' if ident in ['PG03','PG06'] else 'ninguna para la prueba; inventario físico/usuarios sigue pendiente'
                risk='identidad de canal ≠ analizador físico; inventario histórico parcial'
                if ident=='PG04':risk='Madrid/NYC: publicador no acredita operador; Londres DataOwner de sitio no persona responsable'
                if ident=='PG07':risk='catálogo de prueba de canales deriva de lecturas: cero sin actividad es tautológico; contraste independiente solo sitio y muestra'
                evidence=f'results/phase3/postgres_execution.json cities.{city}.queries.{ident}; proof_queries.sql; {city}_expected_sql.json'
            else:
                status='FACTIBLE_NO_EJECUTADO'
                if ident=='MG04':status='PARCIAL'
                if ident=='MG05':status='NO_CUMPLE'
                if ident=='MG08':status={'Madrid':'FACTIBLE_NO_EJECUTADO','NYC':'PARCIAL','London':'NO_VERIFICADO'}[city]
                field_state='derived (regla pendiente)' if ident=='MG04' else ('unavailable' if ident=='MG05' else 'observed + derived')
                transform={'MG01':'filtro por channel_id compartido, sin convertir campaña/hogar en sensor físico',
                    'MG02':'rango [inicio,fin), reloj explícito; UTC EPA/GMT LAQN, clocks locales conservados',
                    'MG03':'MIN/MAX por fuente/variable/unidad, valores elegibles; conservar extremos',
                    'MG04':'regla específica variable/unidad/duración y QA aprobada; IQR no significa crítico',
                    'MG05':'colección alerts con emitted_at, zona y evidencia de emisión real: no disponible',
                    'MG06':'GROUP zona/fuente/variable/unidad; NULL zona excluido, nivel espacial declarado',
                    'MG07':'GROUP tipo/variable/unidad; pesos/exposición explícitos, no promediar unidades distintas',
                    'MG08':'expediente único y categoría Madrid; NYC unique_key solicitud; TfL no auditado completamente',
                    'MG09':'pipeline $match/$group/$sort diseñado; referencia pandas ejecutada, NO Aggregation Framework nativo',
                    'MG10':'AND canal/fecha/valor válido; proyección y orden sin modificar lectura'}[ident]
                test='Python filtros/agrupaciones, referencias e integridad ejecutados; MongoDB nativo pendiente'
                if ident in ['MG04','MG05']:test='ausencia de evento crítico/alerta emitida comprobada en muestras; no generación de eventos para simular cumplimiento'
                if ident=='MG08':test='categorías/IDs únicos Python, semántica diferenciada en incident_checks.json'
                synthetic='ninguna necesaria para filtros; eventos críticos serían derived, no synthetic; alertas históricas no inventadas'
                risk='sin validación BSON, CRUD, índices, explain ni Aggregation Framework nativo'
                if ident=='MG06':risk+='; Madrid aire/meteo solo ciudad/sitio, NYC borough, LAQN autoridad; energía Londres sin zona'
                evidence=f'results/phase3/prepared_data.json {city}; {city}_python_aggregates.csv; scripts/phase3_mongo_queries.js (diseño); incident_checks.json'
            matrices.append({'alternative':city,'id':ident,'requirement':req['consulta'],'technology':tech,
                'required_fields':req['atributos_necesarios'],'source':city_sources[city], 'field_state':field_state,
                'transformations':transform,'test_performed':test,'evidence':evidence,'synthetic_dependency':synthetic,
                'risk':risk,'compliance_status':status})
    # Data provenance: field meaning first, never treating source opening/status as sensor installation/status.
    fields=['fecha_instalacion','estado_sensor','organismo_responsable','usuarios_sistema','alertas_emitidas','eventos_criticos','incidentes','energia','CO2_concentracion']
    configurations={
        'Madrid':[
            ('unavailable','Fecha alta de estación observada, NO instalación de dispositivo','inventario MAD-AIR: Fecha alta; diccionario AnexoI','ninguna imputación'),
            ('unavailable','Altas/bajas de sitio históricas, no estado administrativo de cada canal','diccionario M13 AnexoI','actividad_en_ventana solo derived'),
            ('unverified','Ayuntamiento/publicador y unidad municipal; vínculo operador individual no completo','01/02 catálogos; M14 Unidad responsable','completar relación con fuente oficial'),
            ('unavailable','No hay usuarios de aplicación en datasets','cinco entidades académicas; tabla proof.users vacía','registro real del equipo con consentimiento o fixture opcional'),
            ('unavailable','No se acreditan emisiones históricas por zona','muestras 02; sin colección emitida','no transformar lecturas en mensajes históricos'),
            ('derived','Detección posible por regla aprobada; aún NO calculada como crítica','Hxx/Vxx, variable y unidades; estadísticos QA','umbral/duración/versionado, no IQR=crítico'),
            ('observed','Accidentes registrados; detalle persona separado de expediente','MAD-CRASH num_expediente/tipo_accidente/fecha','agregar expediente solo cuando categoría coherente'),
            ('observed','Consumo municipal mensual, unidades/niveles múltiples','MAD-ENERGY SENSOR/CONSUMO/UNIDADES/MES','no repartir consumo mensual a horas'),
            ('unavailable','CO y NO2 no son CO2','diccionario de magnitudes Madrid','CO2 ambiente requiere fuente complementaria')],
        'NYC':[
            ('unavailable','No instalación individual publicada','EPA/DOT originales; primeras campañas no instalación','no usar min(time)'),
            ('unavailable','Campaña discontinua y qualifiers no equivalen a estado administrativo','DOT campaña; EPA qualifier; 311 status es trámite','no ausencia=falla'),
            ('unverified','DOT/EPA son publicadores, operador EPA por sitio pendiente','N01 metadata Agency; EPA sin campo operador en CSV','consulta fuente oficial de operador'),
            ('unavailable','Usuarios de aplicación no publicados','proof.users vacía; solicitudes 311 no usuarios app','registro autorizado o fixture opcional'),
            ('unavailable','NYCEM esquema/probe previo no acredita alertas por zona auditadas','01_http_evidence: NYCEM; sin datos 02 válidos','fuente complementaria con emisión y zonificación'),
            ('derived','Reglas PM2.5/tráfico posibles; no ejecutadas como críticas','EPA Units/Qualifier y DOT vol','unidad/ventana y calidad por canal'),
            ('observed','Solicitudes ciudadanas realmente registradas, NO hechos confirmados','311 unique_key/complaint_type/created_date/borough','categorizar como citizen_service_request'),
            ('observed','LL84 electricidad anual por propiedad; dos claves candidatas repetidas','LL84 sample report_year/property_id/electricity_use_grid_purchase','resolver propiedad padre/revisión antes de totalizar'),
            ('unavailable','CO2e anual de edificios no concentración de CO2','LL84 direct_ghg_emissions_metric; EPA PM2.5','no sustitución CO2e→CO2')],
        'London':[
            ('unavailable','DateOpened es apertura de sitio, no instalación del analizador','LAQN metadata @DateOpened','mantener columnas distintas'),
            ('unavailable','Operacionalidad de sitio por apertura/cierre es derived, no sensor admin','LAQN @DateClosed/Opened','no extrapolar a hogares/sensores'),
            ('observed','DataOwner/DataManager de sitio; persona responsable ausente','LAQN metadata @DataOwner/@DataManager','separar propietario, gestor y persona'),
            ('unavailable','LCLid identifica hogar anónimo, NO usuario de app','LCL LCLid; proof.users vacía','registro real autorizado o fixture opcional'),
            ('unavailable','Sin evidencia de alertas históricas emitidas por zona','LAQN endpoint RawAQData; no mensajes emitidos','no inventar emitted_at'),
            ('derived','Regla NO2/energía posible; detección crítica aún no ejecutada','LAQN Value GMT; LCL kWh, clock por confirmar','definir regla y cohorte; IQR no prueba incidente'),
            ('unverified','TfL complemento de Fase1 no sometido a auditoría completa de Fase2','01_sources_catalog/01_http_evidence','auditar IDs, categorías y accidentes antes de afirmarlo'),
            ('observed','Energía real semihoraria de hogares, sin geografía fina','LCLid/DateTime/KWH/hh, cuatro CSV','hora derivada con dos intervalos; no total ciudad'),
            ('unavailable','NO2 no CO2; energía no concentración','LAQN NO2/LCL kWh','fuente complementaria')]
    }
    for city in CITIES:
        for field,(origin,meaning,source,rule) in zip(fields,configurations[city]):
            origins.append({'alternative':city,'field':field,'data_origin':origin,'meaning':meaning,'source_evidence':source,
                'transformation_or_condition':rule,'synthetic_proposed':False,'synthetic_rows_generated':0})
        for name,explanation in [('actividad_en_ventana','COUNT de lecturas por canal/período, nunca estado administrativo'),
                                 ('agregados_temporales','promedios/sumas por variable y unidad, panel y exposición explícitos'),
                                 ('anomaly_candidate','IQR descriptivo, candidato QA, no evento crítico confirmado')]:
            origins.append({'alternative':city,'field':name,'data_origin':'derived','meaning':explanation,
                'source_evidence':'02_quality_metrics.csv y results/*-summary.json; pruebas phase3',
                'transformation_or_condition':'preservar inputs/método/ventana/unidad','synthetic_proposed':False,'synthetic_rows_generated':0})
        origins.append({'alternative':city,'field':'optional_demo_users','data_origin':'synthetic',
            'meaning':'Propuesta opcional: hasta cuatro cuentas de prueba, NO generadas ni necesarias para volumen',
            'source_evidence':'requisito académico Usuarios; no fuente de datos externa',
            'transformation_or_condition':'solo autorización posterior; user_demo_01..04; correos @example.invalid; namespace demo; ninguna identidad real',
            'synthetic_proposed':True,'synthetic_rows_generated':0})
    with (ROOT/'03_data_origin_matrix.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(origins[0]));w.writeheader();w.writerows(origins)

    def matrix_tables(technology):
        text=[]
        for city in CITIES:
            text += [f'## {city}', '', '| ID / requisito exacto | Campos / origen / relaciones | Transformación y prueba | Estado / riesgo |',
                     '|---|---|---|---|']
            for r in matrices:
                if r['alternative']!=city or r['technology']!=technology:continue
                text.append(f"| {r['id']} — {r['requirement']} | {r['required_fields']}. Fuente: {r['source']}. Estado: {r['field_state']}. | {r['transformations']}. {r['test_performed']}. Evidencia: `{r['evidence']}`. | **{r['compliance_status']}**. Síntesis: {r['synthetic_dependency']}. Riesgo: {r['risk']}. |")
            text.append('')
        return '\n'.join(text)

    pg_scope='\n'.join(f"| {c} | {prepared[c]['sensor_query_scope_channels']} | {prepared[c]['channels']} | {fmt(sql['cities'][c]['loaded_readings'])} |" for c in CITIES)
    write('03_postgresql_matrix.md',f'''
# Fase 3 — PostgreSQL: diez consultas por alternativa

## Lectura de estados y alcance

Se ejecutaron **10 diseños SQL por alternativa** en PostgreSQL 16 local aislado. No equivale a 10 requisitos cumplidos: PG03/PG06 solo diagnostican NULL; PG07 sobre un catálogo obtenido de lecturas devuelve cero por construcción. Nunca se toma un resultado vacío como evidencia de sensores instalados/inactivos inexistentes.

**Cobertura estricta: 2/10 CUMPLE_VERIFICADO por alternativa (vistas y función)**; 6/10 PARCIAL; 2/10 NO_CUMPLE. Dentro de las parciales, PG01/02/05/08 tienen prueba funcional nativa sobre **canales de medición**, por lo que **6/10 son funcionales si el docente acepta esa granularidad** (esas cuatro más PG09/10). No afirmar cumplimiento de inventario físico completo. No hay puntaje de selección.

Sensores físicos/analizadores requieren identificación y vigencias no acreditadas. `sensor_scope` excluye campañas DOT y hogares LCL: no contarlos como sensores instalados. Los hechos estructurados de esas fuentes siguen siendo válidos para el volumen SQL, en categorías propias.

| Alternativa | Canales en alcance de consultas de sensores | Todos los canales de hechos | Hechos reales cargados |
|---|---:|---:|---:|
{pg_scope}

Evidencia primaria: `results/phase3/postgres_execution.json`, log completo, `proof_queries.sql` y referencias Python independientes por ciudad. Muestras: Madrid enero/julio2025 y tráfico enero2025 estrato ID; NYC2023; Londres enero/julio2013.

## Cinco entidades mínimas (enunciado pp. 8–9)

| Entidad / atributos exigidos | Madrid | NYC | Londres | Tipos / conclusión |
|---|---|---|---|---|
| Sensores: id, nombre, tipo, instalación, estado | Sitio/magnitud/punto; técnica original conservada en raw | Canales EPA sitio/POC/método; DOT no dispositivo | Sitio/especie LAQN; hogar no dispositivo físico | TEXT IDs/nombres; FK categoría; DATE instalación y TEXT estado NULL. **PARCIAL** las tres |
| Ubicaciones: id, zona, distrito, coordenadas | Estación/ciudad; distrito de tráfico observado, ambiental no acreditado | EPA WGS84 + condado/borough; DOT CRS pendiente | LAQN autoridad/lat/lon; geografía de hogares ausente | TEXT; DOUBLE PRECISION lat/lon con CHECK y CRS explícito futuro. **PARCIAL** |
| Categorías: id, nombre | Magnitudes oficiales, unidades meteo provisionales | Parámetro/método EPA, conteo de campaña separado | NO2 / electricidad semihoraria por fuente | TEXT; categorización derivada del diccionario. Disponible; catálogo preliminar, no enum físico final |
| Usuarios: id, nombre, correo | Ausentes | Ausentes | Ausentes; LCLid no usuario | TEXT/UNIQUE correo; **NO_CUMPLE datos**, tabla de prueba vacía. Registro del equipo puede ser observado futuro |
| Organismos: id, nombre, responsable | Publicador/unidad municipal; operador individual incompleto | Agencia DOT; EPA no identifica operador por sitio en este CSV | DataOwner/DataManager de sitio reales | TEXT/relación nullable; persona responsable no presente. **PARCIAL** |

Las cinco estructuras pueden diseñarse; ninguna alternativa aporta completos los cinco conjuntos de atributos. No hay requisito de 100000 usuarios o sensores.

## Prueba relacional preliminar en 3FN

Relaciones: `organizations ← channels → categories`; `channels → locations`; `readings → channels`; `users` independiente y vacía. `source`, entidad original y `entity_kind` preservan contexto; categoría determina variable/unidad. Los hechos no repiten nombre de sitio, coordenadas ni unidad. PK TEXT determinista de fuente/canal/instante, FK de categoría/ubicación/organismo y lectura; UNIQUE canal/tiempo. Coordenadas/alta del sitio pertenecen a ubicación, instalación administrativa a dispositivo (NULL en prueba).

EPA ubicación = estado-condado-sitio, no POC/método; DOT ubicación de segmento separada de campaña; LCL usa una referencia **unknown** con geografía NULL, no casas ficticias. La prueba no identifica todos los analizadores físicos ni vigencias históricas: esquema definitivo debe añadir dispositivos acreditados, técnicas/vigencias, zonas cartográficas y M:N de organismos si procede. PK de procedencia no debe ocultar conflictos naturales.

Índices reales: PK, UNIQUE canal/instante, canal+fecha, FK de ubicación y categoría. Se guardó EXPLAIN; no se fuerza que el plan elija índice ni se inventa comparación de rendimiento. CTE/ventana PG08 y subconsulta NOT EXISTS PG07; JOIN/GROUP/HAVING/COUNT/ORDER/DISTINCT y agregados sobre hechos contrastados. Fechas son TIMESTAMP + clock explícito en esta prueba: EPA UTC; LAQN GMT; clocks locales no se renombran UTC. Modelo final deberá separar instante UTC de reloj local no resuelto.

Vistas materializadas/particiones/optimización del proyecto completo: **FACTIBLE_NO_EJECUTADO**, no probadas en este prototipo. Un índice no demuestra optimización ni procesamiento distribuido.

## Las diez consultas, evidencia y límites

{matrix_tables('PostgreSQL')}

## 100000 registros

Las tres alternativas **superaron 100000 hechos reales cargados con PK/FK en esta prueba nativa**, sin usuarios ficticios y sin producto cartesiano. Registros son observaciones/intervalos elegibles, no maestros inventados. Cumplimiento de volumen de la prueba: CUMPLE_VERIFICADO; cumplimiento final del proyecto depende de esquema definitivo, ventanas/QA y decisión académica sobre canales. No se duplica una fila por atributo para inflar conteos. Raw queda intacto.
''')

    write('03_mongodb_matrix.md',f'''
# Fase 3 — MongoDB: diez consultas por alternativa

**MongoDB nativo: 0/10 consultas ejecutadas por alternativa.** No hay `mongod`, `mongosh` ni imagen MongoDB local; se evitó instalar/descargar infraestructura. `psql`/Docker sí estaban disponibles. Python valida datos/filtros/agrupaciones; no es MongoDB, no valida Aggregation Framework, BSON, índices, explain ni CRUD nativo.

Cobertura de datos/diseño factible sin síntesis: **Madrid 8/10** (MG01/02/03/06/07/08/09/10), **NYC 7/10 + MG08 parcial** (solicitudes, no incidentes confirmados), **Londres 7/10** (MG08 TfL no auditado). MG04 derivable pero regla crítica pendiente; MG05 emisiones históricas por zona sin fuente. Esas cifras **no son cumplimiento verificado nativo**.

## Colecciones, IDs y flexibilidad preliminar

- `readings`: `_id` derivado de fuente+channel_id+instante original; source_key/raw_reference, channel_id compartido con SQL, variable, value numérico/NULL, unit, quality, original_time, clock, observed_at UTC solo si acreditado, location_id/zone cuando reales, data_origin=observed. Derivados y normalización se registran con método/inputs, no cambian el valor original. Documento por intervalo/canal de una medición; un registro tráfico con intensidad/velocidad/ocupación conserva **esas variables en un único documento**, no se expande por atributo.
- `incidents`: Madrid expediente único con categoría coherente, fecha/distrito y detalle por referencia; NYC unique_key con record_kind=citizen_service_request, categoría/estado/agencia; Londres TfL pendiente. No mezclar trámite con falla IoT ni accidente confirmado.
- `derived_events`: vacío; futuro rule_id/version, ventana, unidad, severidad, inputs y data_origin=derived. Una anomalía IQR no equivale a evento crítico de salud pública.
- `alerts`: vacío; emisión futura debe registrar emitted_at **real** y método/destino/zona, no fecha histórica copiada. Mensajes oficiales requieren una fuente efectiva y permiso.
- `energy_reports`: mensual Madrid/anual LL84 conservando propiedades padre/hijo, unidades y revisiones; LCL semihorario en lecturas. Geografía LCL NULL; tarifa no zona.

No hay FK automática con PostgreSQL: validación de ingestión comprueba channel_id/categoría/ubicación y versión de catálogo; pruebas Python y FK SQL verificaron la referencia de las muestras. No convertir POC/método, campaña, hogar o solicitud en dispositivos físicos nuevos.

Índices diseñados: UNIQUE(source_key/measurement_id), canal+instante, fuente/variable/unidad/zona/fecha; incidentes UNIQUE(source,incident_id), categoría+fecha. GeoJSON solo con WGS84 acreditado y geografía real. Índice unique no resuelve los conflictos DOT: conservar raw en cuarentena y rechazar/identificar ambigüedad antes de colección de lecturas. Fechas locales no resueltas deben filtrarse como reloj explícito de una fuente hasta acreditar zona; no convertir cadenas por la timezone del host.

`scripts/phase3_mongo_queries.js` contiene diez diseños nativos con guardia de nombre de DB desechable. No se ejecutó; no conectar a Coolify. Las previsualizaciones locales (500 documentos por alternativa) contienen valores reales y IDs, no son colección BSON cargada. CRUD: insertOne/insertMany idempotentes; find/findOne contrastados con raw; updateOne/updateMany solo anotaciones/revisiones; deleteOne solo copia desechable, no lecturas originales. **Todas esas operaciones CRUD nativas siguen FACTIBLE_NO_EJECUTADO**. No realizar borrados para «limpiar» históricos silenciosamente.

## Consultas y cumplimiento

{matrix_tables('MongoDB')}

## 500000 documentos sin doble conteo

| Alternativa | Capacidad real / evidencia | Estado |
|---|---|---|
| Madrid | {fmt(prepared['Madrid']['eligible_unique_readings'])} hechos elegibles locales; tráfico por sí solo 674704 intervalos no duplicados. Un documento por intervalo con múltiples campos reales, no por atributo | FACTIBLE_NO_EJECUTADO en Mongo; capacidad de datos comprobada |
| NYC | {fmt(prepared['NYC']['eligible_unique_readings'])} lecturas/campañas no ambiguas +124130 solicitudes locales; total236200, insuficiente localmente. Agregados API de enero+julio2023 acreditan531503 unique_key de solicitudes; sin descargar todos ni ejecutar Mongo | PARCIAL: requiere ampliar solicitudes reales o lecturas de años extras; si se exige500k SOLO lecturas de sensores, no acreditado |
| Londres | 3997252 claves hogar/timestamp en cuatro CSV locales; duplicados2748 y conflictos de valor globales medidos en Fase3. Muestra Jan/Jul347314intervalos únicos; no basta esa ventana sola, ampliar al histórico local | FACTIBLE_NO_EJECUTADO en Mongo; volumen real local acreditado |

No sumar raw y normalizado como dos mediciones distintas, no atribuir >500k al conjunto localNYC, no extrapolar volumen nacionalEPA a NYC. No se generó ni se necesita síntesis masiva de volumen. Derechos de redistribución LAQN y privacidad afectan publicación, no se resuelven con un índice.
''')

    # Ten mandatory future products: no Spark runtime here.
    spark_rows=[]
    for city in CITIES:
        for req in requirements[20:30]:
            ident=req['id'];status='FACTIBLE_NO_EJECUTADO';risk='Spark no ejecutado; cobertura/canales y unidades deben preservarse'
            if ident=='SP02':status={'Madrid':'FACTIBLE_NO_EJECUTADO','NYC':'PARCIAL','London':'NO_VERIFICADO'}[city];risk='evento/solicitud/incidente son conceptos distintos; no alertas históricas'
            if ident=='SP04':status='PARCIAL';risk={'Madrid':'co-localización NO2-temperatura parcial; unidad T83 provisional; exposición tráfico variable',
                'NYC':'146borough/día; campañas desiguales; 311 solo16fechas, no causalidad',
                'London':'cohorte ciudad no geografía fina; reloj julio no resuelto, correlación cambia al desplazar una hora'}[city]
            if ident=='SP09':status={'Madrid':'FACTIBLE_NO_EJECUTADO','NYC':'NO_VERIFICADO','London':'FACTIBLE_NO_EJECUTADO'}[city];risk='Madrid2025/2026: comparar meses comunes; LCL2012/2013 panel estable, LAQN solo2013; NYC local solo2023'
            if ident=='SP10':status='PARCIAL';risk='dashboard completo requiere CO2, alertas y movilidad/energía no cubiertas; resultados Spark todavía inexistentes'
            spark_rows.append({'alternative':city,'id':ident,'requirement':req['consulta'],'technology':'Spark',
                'required_fields':req['atributos_necesarios'],'source':city_sources[city],'field_state':'observed + derived / faltantes explícitos',
                'transformations':'DataFrames/SQL: filtrar QA, agrupar variable/unidad, joins únicos, ventanas por entidad/período; panel comparable',
                'test_performed':'verificación Python de fechas/IDs/agrupaciones e integración, NO Spark',
                'evidence':'results/phase3/validation.json; prepared_data.json; 00_query_matrix.csv; artifacts originales',
                'synthetic_dependency':'ninguna para histórico; faltantes no imputados','risk':risk,'compliance_status':status})
    matrices.extend(spark_rows)
    st=[]
    for city in CITIES:
        st += [f'## {city}', '| ID / producto | Campos y datos | Estado y condición |', '|---|---|---|']
        st += [f"| {r['id']} — {r['requirement']} | {r['required_fields']}; {r['field_state']}. {r['transformations']} | **{r['compliance_status']}** — {r['risk']}. Evidencia: {r['evidence']} |" for r in spark_rows if r['alternative']==city]
    write('03_spark_future_matrix.md',f'''
# Fase 3 — Viabilidad futura Hadoop/Spark

Las diez consultas del enunciado p.16 fueron contrastadas, además de los ocho análisis de p.15. **Spark/Hadoop no instalados ni ejecutados; ningún indicador Python se etiqueta como Spark.**

## Volumen y almacenamiento

Madrid: aire tiene1795279slotsV distintos por día/canal/hora publicados; >1M potencial sin fabricar sensores. Hay993374hechos elegibles en las ventanas normalizadas de prueba: **esa muestra sola es menor de1M**. Ampliar al CSV local completo, controlarDST/flags y técnicas. Tráfico13,2Mraw no es13,2Múnicos acreditados; muestra674704válidos únicos.

Londres:3997252claves únicas locales y cero conflictos devalor globales tras nuevo escaneoSQLite;119faltantes/no numéricos. >1Mregistros de fuente reales, procesamiento distribuido aún pendiente. NYC:236200hechos/solicitudes elegibles locales;531503solicitudes contabilizadas remotamente por API previa no bastan1M. DOTglobal1875154filas consultables pero cardinalidad/QA y período común no validados; **1MSparkNYC PARCIAL**, no afirmar que el archivoEPA nacional resuelve ese mínimo urbano.

HDFS futuro: particiones fuente/año/mes, raw inmutable, manifiestoSHA/versión, exportaciones JSON/CSV/Parquet; formato/particiones no sustituyen prueba distribuida. Ejecutar en fase posterior comandosmkdir/put/ls/cat/get/rm, y MapReduce o Hive/Impala con resultados comparables; bloques/replicación/fallos/multi-nodo se deben demostrar, no diseñar únicamente. HDFS no tiene una lista académica de diez consultas. LAQNno se replica públicamente sin resolver permiso.

## Diez productos obligatorios

{chr(10).join(st)}

## Ocho clases de análisis

Descriptivo: conteos/valores QA por canal, no campañas como sensores. Temporal: muestras y cobertura con huecos, no seriesrellenasde0. Correlacional: Madrid19 087pares; NYC146grupos; Londres1488horas condicionales; panel/estación/POC y exposición separados. Tendencias: pendientes de panel estable y mismo período, no ML obligatorio. Espacial: Madrid geografía estación/tráfico; NYCboro/EPA, DOTCRSpendiente; LondresLAQN, sinhogares geográficos. Movilidad: Madridintensidad y camposoriginalesvmed/carga/ocupación por tipo; NYCconteosdecampaña; LondresDfT100filas iniciales no demuestra movilidad continua. Anomalías: candidatosIQR/QA no se convierten en incidentes. Comparación: meses/años con exposición comparable y no totals de cohortes variables.

Años comunes: Madrid2025completo frente a2026enero–agostoenCSV; comparacionesJan/Jul2025–2026posibles, no diciembre2026. LCL2011–2014miembros locales, comparar2012/2013entre hogares presentes en ambos; LAQN2012pendiente de adquisición. NYCmaterial principal solo2023; otrosaños enAPI son potencial, no historia cruzada yaauditada.

Plan de pruebas posterior: leer≥1Mclaves no ambiguas, conteos exactos antes/después de filtros; joins sincrecimiento cartesiano; partition pruning/caching/explain/multi-nodo y tiempos/recursos medidos. Ningún benchmark actual demuestra dominioSpark, recepciónen vivo oBigData distribuido.
''')

    # Dashboard indicators are separately classified; title resemblance never grants availability.
    kpis=[
       ('Movilidad','Vehículos detectados','PARCIAL','PARCIAL','PARCIAL','Madrid intensidadveh/h≠conteo sin integración de duración; NYCvol intervalos reales de campañas; DfT100filas muestra inicial'),
       ('Movilidad','Velocidad promedio','PARCIAL','NO_CUMPLE','NO_CUMPLE','Madrid vmed original, validez por tipo/flags a cerrar; NYC/DfT conteo no velocidad'),
       ('Movilidad','Congestión promedio','PARCIAL','NO_CUMPLE','NO_CUMPLE','Madrid carga/ocupación son proxies medidos, umbral/métrica requiere definición; conteo no congestión'),
       ('Movilidad','Accidentes/incidentes','FACTIBLE_NO_EJECUTADO','PARCIAL','NO_VERIFICADO','Madrid expediente real2026; NYCsolicitudes, no accidente confirmado; LondresTfL pendiente'),
       ('Movilidad','Tiempo promedio de recorrido','NO_CUMPLE','NO_CUMPLE','NO_CUMPLE','No rutas/tiempos observados en núcleos auditados'),
       ('Ambiente','Temperatura global promedio','PARCIAL','NO_VERIFICADO','NO_VERIFICADO','MadridT83 disponible/unidad provisional/promedio de estaciones NO temperatura global planeta; NOAA no auditado completo'),
       ('Ambiente','PM2.5 promedio','FACTIBLE_NO_EJECUTADO','FACTIBLE_NO_EJECUTADO','NO_VERIFICADO','Madridmagnitud9; EPAPM2.5 cinco sitios/tresboroughs; LAQN muestraNO2noPM2.5'),
       ('Ambiente','CO₂','NO_CUMPLE','NO_CUMPLE','NO_CUMPLE','CO, NO2, CO2e anual y consumo no concentración ambientalCO2'),
       ('Ambiente','Humedad','PARCIAL','NO_VERIFICADO','NO_VERIFICADO','Madrid86real/unit percentprovisional; NOAA complementos sin prueba completa'),
       ('Ambiente','Número de alertas ambientales','NO_CUMPLE','NO_CUMPLE','NO_CUMPLE','Emisiones reales no acreditadas; umbral derivado requiere política y no es emisiónhistórica'),
       ('Energía','Consumo total','PARCIAL','PARCIAL','PARCIAL','Madrid medidores/niveles/unidades; LL84padre/revisión; LCLtotalcohorte, no ciudad'),
       ('Energía','Consumo promedio por zona','PARCIAL','PARCIAL','NO_CUMPLE','Madrid distrito mensual; LL84boroughanual; hogaresLCLsinzonafina'),
       ('Energía','Consumo por hora','NO_CUMPLE','NO_CUMPLE','PARCIAL','Mensual/anual no se reparte a horas; LCLdos medias horas únicas, clockpendiente'),
       ('Energía','Picos de consumo','PARCIAL','PARCIAL','PARCIAL','Picos mensuales/anuales no pico horario; LCL panel/clock requerido'),
       ('Energía','Variación respecto al período anterior','PARCIAL','PARCIAL','PARCIAL','Revisiones/submedidores/panel estable/períodoscomparables antes de totals'),
       ('IoT','Número de sensores','PARCIAL','PARCIAL','PARCIAL','Canales/sitios acreditados; no conteo automático de analizadores físicos'),
       ('IoT','Mediciones recibidas','PARCIAL','PARCIAL','PARCIAL','Históricoobservado≠received_at; ingestiónfutura permitirá contar recepciónreal'),
       ('IoT','Sensores activos/inactivos','NO_CUMPLE','NO_CUMPLE','NO_CUMPLE','Sin estadoadministrativo individual; actividadmuestreada nofalla'),
       ('IoT','Alertas generadas','NO_CUMPLE','NO_CUMPLE','NO_CUMPLE','Nadaemitido enesta fase; futura regla derived a aprobar'),
       ('IoT','Datos por minuto/hora/día','FACTIBLE_NO_EJECUTADO','FACTIBLE_NO_EJECUTADO','FACTIBLE_NO_EJECUTADO','Agrupaciónobserved_atreal, huecos/campañas explícitos, no recepciónstreaming'),
       ('IoT','Total de lecturas registradas por segundo','PARCIAL','PARCIAL','PARCIAL','Tasa deobservación no recepción histórica; medir ingested_at en ingestiónfutura')]
    dash='\n'.join(f'| {domain} | {label} | {a} | {b} | {c} | {explanation} |' for domain,label,a,b,c,explanation in kpis)
    for domain,label,a,b,c,explanation in kpis:
        for city,status in zip(CITIES,[a,b,c]):
            matrices.append({'alternative':city,'id':'DASH-'+label,'requirement':label,'technology':'Dashboard',
               'required_fields':explanation,'source':city_sources[city],'field_state':'ver 03_data_origin_matrix.csv',
               'transformations':'no confundir proxy/derivado con KPI observado; ventana/unidad/geografía explicitas',
               'test_performed':'análisis de atributos y muestras, NO interfaz implementada','evidence':'results/phase3/validation.json; original académico p18; raw originales',
               'synthetic_dependency':'ninguna generada; fuente/aceptación requerida para faltantes','risk':explanation,'compliance_status':status})
    write('03_dashboard_coverage.md',f'''
# Fase 3 — Cobertura del dashboard (enunciado pp.18–20)

No se construyó una interfaz ni se ejecutaron Spark/HDFS/MongoDB. Los estados indican **datos/definición de KPI**, no visualización funcionando. Orígenes y unidades en `03_data_origin_matrix.csv`; matriz completa en `03_compliance_matrix.csv`. Un indicador derivable no es un hecho urbano observado ni una emisión de alerta histórica.

| Dominio | KPI exacto | Madrid | NYC | Londres | Definición y evidencia de la limitación |
|---|---|---|---|---|---|
{dash}

## Visualizaciones, filtros y mapas

Serie temporal: factible sobre fuentes QA, mostrando huecos, campaña/ventana y timezone; Madrid variable/hora, NYCcampañasPM2.5/solicitudes, Londresenergía/NO2conclockcondicional. Comparativa por zonas: Madridtráficodistrito/aireciudad-sitio, NYCborough (Manhattan/StatenIsland sinEPA88101), LondresLAQNautoridad; **no energíaLCLporborough**. Proporciones por tipo: canales lógicos/variables/categorías, no dispositivos físicos inventados. Cuarto gráfico **debe provenir deSpark ejecutado**, ninguno existe aún.

Mapas: Madridinventariosdecimales y NYCsitiosEPAGeoWGS84; DOTWKTnativo solo despuésdeconfirmarCRS. LAQNsitios enmapa, hogaresLCLno. Coordenadaspublicadas plausibles no prueban exactitudinstrumental. Distrito ambientaldeMadrid requiere cartografíaoficial/vigencia; no asignar por proximidadsinvalidación.

Filtros obligatorios fecha/perfil, zona y tipomedición: disponibles para subconjuntos geográficos conocidos; valores desconocidos visibles como NULL/«no disponible», no ciudadcomo barrio. Sensor/periodo/categoría recomendados: IDsestables decanal y clases reales; campaña/hogar/solicitud con selectorpropio. Tabla detalle y paginación factibles, no implementadas. Etiquetas de origen deben reflejar tecnología realmente ejecutada, no renombrar referenciasPythoncomoMongo/Spark.

Panel únicoconselectorPG/Mongo/HDFS/Spark: diseño posterior; pruebaSQLactual no implementa integracióninterfaz. Los cuatrodominios completos no están cubiertos por ninguna alternativa. Cambiar KPI porproxy necesita decisión docente y etiquetaexplícita, no columna con nombreparecido.
''')

    # Unified requirement matrix for exact reproducible status counts, not narrative scores.
    for r in matrices:assert r['compliance_status'] in ALLOWED
    with (ROOT/'03_compliance_matrix.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(matrices[0]));w.writeheader();w.writerows(matrices)
    status_counts={c:{tech:pd.DataFrame([r for r in matrices if r['alternative']==c and r['technology']==tech]).compliance_status.value_counts().to_dict()
                  for tech in ['PostgreSQL','MongoDB','Spark','Dashboard']} for c in CITIES}
    summary={'coverage':status_counts,'postgresql_strict_verified':{c:2 for c in CITIES},
             'postgresql_functional_logical_scope':{c:6 for c in CITIES},
             'mongodb_data_supported_not_native':{'Madrid':8,'NYC':7,'London':7},'mongodb_native_executed':False,
             'postgres_rows':{c:sql['cities'][c]['loaded_readings'] for c in CITIES},
             'winner_selected':False,'phase4_started':False,'synthetic_measurements_generated':0}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))

    losses=validation['Madrid']['join'];ny=validation['NYC']['joins'];lon=validation['London']['join']
    sensitivity='\n'.join(f"| {r['July_shift_hours']} h | {r['matches']} | {r['left_match_pct']:.4f}% | {r['pearson_exploratory_only']:.6f} |" for r in lon['timezone_sensitivity'])
    write('03_integration_gaps.md',f'''
# Fase 3 — Integración: problemas, evidencia y tratamiento

## Cifras de Fase2 contrastadas

Recuento desde CSV/ZIP/sample original: Madrid **{fmt(validation['recounted_primary_raw_rows']['Madrid'])}** (76513filas diariasaire+56383meteo+13218804intervalostráfico), NYC**247526** (85106DOT+38290EPAlocal+124130solicitudes), Londres**4007440** (4000000energía+7440slotsLAQN). Son **filas raw de granularidades distintas**, no mediciones únicas ni indicadores comparables; excluyen complementos/inventarios. En particular14MfilasMadridno significa14Msensores. Evidencia `results/phase3/validation.json`; original/hash en manifiestos02 e inputs_manifest.csv.

## Madrid — 56,44% y pérdidas reales

{losses['matched']}/{losses['eligible_NO2']}NO2elegibles: **{losses['pct']:.6f}%**, enero/julio2025, NO2magnitud8frenteatemperatura83. El denominador incluye lecturasválidas de23sitios, no todasaire/meteo ni todoelrecurso. 14722lecturas sin sitio co-localizado;19099mapeadas,12sintemperatura elegible. Coincidencia temporal en sitiosmapeados99,94%, no56,44%de«fallas». Relación espacial validada por mismocódigoycoordenadas<1m en13sitios, no identidad dedispositivo.

Lista por sitio/mes/causa en `results/phase3/madrid_no2_losses.csv`; entidades con almenosuna pérdida: {', '.join(losses['unmatched_entities'])}. Se distinguen sitios sinco-localización de sitios con12huecosmeteo. Enero yjulio2025 sonperíodoscontrastados; H24terminaal día siguiente, no se etiquetaUTCsinvalidarDST. Aire/métodooriginal `PUNTO_MUESTREO` conserva técnica; clave estación/magnitudtemporal no acredita analizadorindividual persistente.

Unidadesaire: AnexoIIoficial (texto conservado `madrid_air_dictionary.txt`) confirma8NO2µg/m³,9PM2.5µg/m³,6COmg/m³. Meteo83/86/etc sonunidades provisionalesdenormalizador, diccionariotécnicocompleto pendiente: **unverified**, no se afirma corroborado porlatitud/nombre. Tráfico intensityveh/hno volumen acumulado;periodos1–30min requierenponderación/cobertura yvmedpor tipo.

Historia: AnexoIincluye fechasdebaja yrecodificacionesdeestaciones; inventarioactualincluyeFechaalta. Se examinaron esosregistros, pero son lifecyclede**sitios**, no instalación/estado individual. Noacreditan vigenciageográfica diaria oinventariocompleto porcanal2025. `catalog_activity.csv` contrastainventariosindependientes y muestra; ausencia no fallas. Energíamensual, concentraciónCO2y alertashistóricas no se cierran porlimpieza.

## NYC — clave DOT, campañas y el3,42%

4767grupos con dosvalores distintos,9534filas, campañas **{', '.join(conflicts['campaigns_with_conflicts'])}**. Se probó(requestid,segmentid,direction,yr,m,d,hh,mm), añadiendoWKT ytodosloscamposdescriptivos (boro,street,fromst,tost): **persisten4767extras en cada caso**, cero filasidénticas. No se encontróclavefísica correcta enlascolumnaspublicadas. Añadirvalor, contadorsecuencial oíndicefila identifica procedencia, no explica lasobservaciones. No sumarlascomo carriles sin evidenciadecontador/carril. Tratamiento: rawinmutable/cuarentena, exclusión conservadora delhecholimpio,consultaDOT/diccionario adicional. Noes solucionable soloborrando«duplicados».

DOT tiene219díasobservados enelarchivo y127segmentos brutos, pero75572lecturas no ambiguas y322gruposborough/día elegibles trasfiltro. No es sensorización continua delborough; min/maxno definenactividadesperada diariamente. EPA88101solo3boroughs/cinco sitios, UTCpreservaDST; se deriva calendariolocal exclusivamentealagregar.

Tráfico–EPA:146/322gruposDOT**45,34%**;737gruposEPA sinDOT y176DOTsinEPA. Tráfico–311:**11/322=3,416149%**; no porcentaje de solicitudes relacionadas ni cobertura geográfica de sensores. 311incluye16días solicitados/96gruposincluidoUnspecified; {ny['DOT_date_groups_in_311_sample_dates']}gruposDOT caenendías solicitados. Limita muestreo, no factibilidaddelaAPI: ampliar311enfechascampaña puede aumentar coincidencias pero no resuelveconflictos/coberturaEPA niacredita causalidad. Tresfuentes juntas1grupo,0,31%delosDOT. Detalle dekeys/left_only/right_only en `nyc_borough_day_matches.csv`.

311created_datees reporte, no fechadeincidente. PM2.5 de múltiplesPOC/métodos usa mediapor sitioy luegoborough; pierde horas/tecnologías ypicos. CO2eLL84anualnoCO2ambiente. WKTsolo candidatoEPSG2263, no uso enjoin; fuenteCRS/ubicaciones yfuenteshorariasenergía/velocidadpendientes.

## Londres —100% de timestamps no geografía ni sincronización

Suma dos medias horasúnicas/hogar/hora,233extras idénticosJan/Jul,44horas/hogar parcialesexcluidas. Agrega cohorte porhora y mediaNO2desitios. **1488/1488horas coinciden** (744enero+744julio) alinterpretar relojes sin desplazamiento, sin filasfaltantesde agregado. Panelvaría{lon['households_min']}–{lon['households_max']}hogares; algunasestacionesfaltan enalgunashoras. No significa100%delecturas emparejadas, dehogarescontemporáneos ni mismo barrio/dispositivo.

LocalizaciónfinaLCL:**0%**; sinlat/lon/borough, ciudadde procedencia como contexto, no ubicación medida. La pruebaSQLusa referenciaunknowncongeografíaNULL, no121casasficticias. Fuentecomplementaria sería necesaria si se exigenzonas energéticas; modelado no recuperacoordenadas inexistentes.

LAQNfechaGMTacreditada, LCLclockno. Sensibilidad exploratoria deslocarjulio(sin declarar correctoningún escenario):

| Desplazamiento julio LCL | Horas coincidentes | Cobertura izquierda | Pearson exploratorio NO validado como correlación urbana |
|---|---:|---:|---:|
{sensitivity}

La correlación de agregado cambiaaldesplazarhora; confirma que coincidenciatimestampsno acredita sincronización. Antesdeanalítica exigirdefiniciónGMT/BSTyDST/cohorteestable. Correlaciones mostradas son pruebas de sensibilidad, **no resultados Spark, causalidad ni correlaciones aceptadas**.

LicenciaLAQN: textoeducativo/informativo«NOTforoperationalorcommercialpurposes», redistribucióngeneralno acreditada. APIpúblicanoCCBYautomática. LCLCCBY4.0no concede derechosLAQN. Preservarlecturas/integracionesprivadas, métricasagregadasmínimas; consultarpermiso para dashboard público/exportaciones. No redistribuirrawporconveniencia académica.

## Clasificación de problemas

| Problema | Clasificación principal | Tratamiento / resolución actual |
|---|---|---|
| Duplicados idénticos LCL | Limpieza | Deduplicación en derivados, original intacto;4Mescaneados,2748extras,0conflictos globales |
| Cinco falsas colisiones EPA enDST | Modelado temporal | Ya resuelto enFase2: conservarUTC, prueba deregresión ejecutada |
| DOTclavesconvaloresdistintos | Fuente complementaria / no resuelto | Faltaidentidad física; cuarentena/no suma arbitraria |
| Madridtemporal12NO2sintemperatura | Modelado/limpieza | QA/ventanas y NULL, no imputar lectura inexistente |
| Madridno co-localizados/zonificación | Agregación o fuentecomplementaria | Co-localización parcial o ciudad; cartografía/vigenciapendiente |
| Inventarios históricos/instalación/estado | Fuentecomplementaria / potencialbloqueo | Alta/apertura no instalación; no síntesisadjunta a sensoresreales |
| NYC3,42%/campañas | Fuentecomplementaria / agregación | Ampliar311enfechascoincidentes; exposiciónno continua, nofallas |
| LCLreloj | Fuentecomplementaria / potencialbloqueo | Definicióntimezonependiente; sensibilidadno soluciona |
| LCLhogares sinzona | Fuentecomplementaria / bloqueo geográfico | No solucionable porlimpieza; no geografía sintética propuesta |
| LicenciaLAQN | No resuelto / potencialbloqueo | Permisos/alcance dedespliegue; cambiosdemodelono resuelvenderechos |
| Usuarios app | Datosobservados futuros o synthetic opcional | Hasta4fixtures explícitos solo autorizados; no generados |
| Alertas/eventos | Derived o fuentecomplementaria | Reglaaprobada futura; emisiónrealno acreditada. No generar historia ficticia |

No problema exige por naturaleza síntesis: obtener fuente, conservarNULL, aceptar alcance limitado o rechazar requisito. **Cero mediciones originales modificadas.**
''')

    suites=[]
    for file in ['legacy_tests.xml','tests.xml']:
        tree=ET.parse(OUT/file).getroot()
        for suite in tree.iter('testsuite'):
            suites.append({'file':file,**suite.attrib})
    total_tests=sum(int(s['tests']) for s in suites)
    assert all(int(s.get('failures',0))==0 and int(s.get('errors',0))==0 and int(s.get('skipped',0))==0 for s in suites)
    write('03_tests_report.md',f'''
# Fase 3 — Pruebas, comandos y límites

**{total_tests} pruebas aprobadas,0fallos/errores/omisiones:** {suites[0]['tests']} heredadas deFase2 y {suites[1]['tests']} deFase3. EvidenciaJUnit separada en `results/phase3/legacy_tests.xml` y `tests.xml`; no se sobrescribióJUnitdeFase2. Todaslaspruebas nuevas requieren resultadosreales guardados, no skip automático.

## Ejecución reproducible

Directorio: `research/datasets/`; entorno existentePython3.11.16 y `scripts/requirements.lock` deFase2. Nuevos paquetes instalados: **ninguno**. No psycopg/pymongo niMongoDB/Hadoop/Spark; SQLvía`docker exec psql`sobreimagenlocal yaexistente. Dockerforzadoa`unix:///var/run/docker.sock`, no contextoremoto.

```bash
.venv/bin/python scripts/phase3_validate.py
.venv/bin/python scripts/phase3_enrich.py
.venv/bin/python scripts/phase3_postgres.py
.venv/bin/python -m pytest tests/test_audit.py tests/test_saved_evidence.py -q --basetemp=/tmp/opencode/smartcity-phase3-legacy --junitxml=results/phase3/legacy_tests.xml
.venv/bin/python -m pytest tests/test_phase3.py -q --basetemp=/tmp/opencode/smartcity-phase3-tests --junitxml=results/phase3/tests.xml
.venv/bin/python scripts/phase3_reports.py
```

No correr`run_offline.py`para reproducirFase3: regenera losentregables02. Estosnuevosscripts sonofflineexceptointeraccionesconDockerlocal. Original académico extraído porpdftotext, SHA/path/pageevidence en`academic_evidence.json`, no modificaciónPDF. `inputs_manifest.csv`incluye documentación00/01/02,scripts/pruebas/logs/manifiestos/muestrasyartefactos; hashesdeoriginales contrastados alfinal. Se conserva lectura detodoslosformatos JSON/CSV/documentación y fingerprints de loscuerposgrandes; escaneoCRCcompleto tráfico y4Menergía, comparaciónnormalizaciónambientalMadrid yEPAlocal contraCSVoriginal.

## Aislamiento SQL

PostgreSQL `{sql['version']}`. Contenedor únicogeneradoporscript, `--rm`, `--network none`, `--pull never`, sinpuertos, memoria1GB/CPU1; bind **read-only** limitado a`private_results/phase3`. DatosPGen volumenanónimo nuevoydesechable, removidojuntoalcontenedor: **{sql['anonymous_volumes_removed']}**, contenedorremovido:**{sql['container_removed']}**. No Compose/Coolify/Tailscale ni basesexistentes. Confianza localdentrodecontenedor sinredno es configuración deproducción.

Hubodosintentospreparatoriosfallidos: primerreadinesscaptóservidortemporal deinitdbantesde reinicio; segundovolumentmpfs512MiBagotósu espacio alcrecerWAL/índices duranteCOPY. Se corrigió esperandofinaldeinitdb yusandovolumenanónimodescartable,no persistente delusuario. No se presentan como éxito; ejecucionesfinales completas registradasenJSON/log. Laactualprueba no es benchmarkdememoria512MBniservidorCoolify.

## Registro de pruebas

| Grupo | Qué se ejecutó / evidencia | Limitación |
|---|---|---|
| Legado22 | Budget/retry/403/503/ZIPCRC/pathseguro/H24/nulos/duplicados/DST/join +cinco assertions de métricasguardadas | No cubría todas consultas académicas/semántica, por eso se amplió |
| Recuento | CSVaire/meteo, ZIPtráfico completoCRC, DOT/EPA/311local y cuatroCSVenergía; númerosrawcontrastados | Rawfilas no equivalen a unicidad ni misma granularidad |
| Identificadores | SHAIDsdeterministas, PKúnicas, FKs Python yPGnativas, categorías yubicaciones | Identidadfísica deanalizadores sigue pendiente |
| SQL30 diseños | SELECT/JOIN/CTE/ventana/vista/función, resultadoSQLcomparado conPython, rowcount/suma/min/max | PG03/06ausencia, PG04vínculos incompletos, PG07catálogoderivadono acredita inventario |
| Restricciones9 | Porciudadse rechazóPKduplicada, FKhuérfana ytimestampNULL; transacciónfallida no dejólecturasficticias | No todo catálogo histórico ni concurrenciaimplementada |
| Fechas/unidades | H24, originalMadridvalores/flags, UTC EPAfrenteGMToriginal, sinfalseDSTduplicates | Unidadesmeteo/LCLclocktodavíaunverified |
| AgregaciónPython | Agrupacionesseparadasporfuente/variable/unidad contraoriginales, min/max/media, filtroscanal/día | NoAggregationFramework/BSONMongo |
| Integración | Denominadores/pérdidasMadrid, keysboroughdíaNYC, sensibilidadLCL1hora | Coincidencia no causalidad/geografíacompleta |
| LCLglobal | SQLiteclavessobre4M, comparaciónvaloresduplicados:0conflictos,2748extras | No ZIPentero/5567hogares, solo4miembros |
| Incidentes | ExpedienteycategoríaMadrid, reportes311etiquetados | TfLcomplemento sinauditoría completa; no incidentesconfirmados311 |
| Inmutabilidad | Todas las huellasdeinputs anteriores aFase3comparadas después | ArchivosFase3regenerables, nuevosoutputsno frozenraw |

SQL30ejecuciones≠30cumplimientos. PythonfiltrarJSON≠MongoDBejecutado. CRUDMongo, índices/BSON/geo/pipelinesnativos siguenpendientes; no hay indicadores Spark niHDFS ejecutados. Losfixturesprotocolodellegado son pruebas unitarias, no filaspara inflarvolumen.
''')

    write('03_feasibility_report.md',f'''
# Fase 3 — Validación académica y viabilidad técnica

**Evaluación de las tres alternativas terminada. Sin ganador, sin puntuaciones finales, sin Fase4.** Se contrastó elenunciado original y losartefactos00/01/02; se revisaron20consultasSprint1poralternativa,10Spark,cincoentidades y21KPIsdashboard. No se construyó elproyectocompleto ni se tocóinfraestructuraremota.

## Cobertura PostgreSQL/MongoDB

| Alternativa | PostgreSQL estricto verificado | PostgreSQL funcional condicionado | MongoDB nativo | MongoDB datos/diseño factible |
|---|---|---|---|---|
| Madrid | **2/10** (vista/función),6parciales,2sinestado/instalación | **6/10** si se acepta canal lógico; PG01/02/05/08 +9/10 | **0/10** ejecutado | **8/10**, críticos parcial/alertas faltan |
| NYC | **2/10**,6parciales,2sinestado/instalación | **6/10**, alcanceEPA; campañas excluidas delconteodesensores | **0/10** | **7/10 +incidentes parcial** (solicitudes) |
| Londres | **2/10**,6parciales,2sinestado/instalación | **6/10**, alcanceLAQN; hogares excluidos delconteodesensores | **0/10** | **7/10**, incidentesTfLsinverificar |

No es puntuación competitiva. Elrequisito deconsultas de estado/instalación no se«verifica» porque SQLdevuelva cero. PG04propietario/gestor desitioLondresmejor documentado, pero faltapersona/vínculodedispositivo; PG07necesitainventarioindependiente históricoyventanajustificada. Entidadesusuariosausente enlas tres; se puede registrarpersonas reales delequipo con consentimiento enimplementación futura, sininventarusuarios masivos.

## Volúmenes por motor

| Alternativa | ≥100kPostgreSQL | ≥500kMongoDB | ≥1MSpark |
|---|---|---|---|
| Madrid | **CUMPLE_VERIFICADO** en prueba local: {fmt(prepared['Madrid']['eligible_unique_readings'])}hechosconPK/FK | **FACTIBLE_NO_EJECUTADO**,993374observaciones elegibleslocales,674704intervalostráficosolos | **FACTIBLE_NO_EJECUTADO**, ampliarCSVairelocal completo>1MslotsV; muestraprueba993374<1M |
| NYC | **CUMPLE_VERIFICADO**:112070conteos/PM2.5no ambiguos; no requiere311niusuariosficticios | **PARCIAL**:236200hechos+solicitudeslocales;API531503unique_key311enero+julio, descargas/carga/semánticaporaceptar | **PARCIAL**:DOTglobal1875154rawpotencial, únicas/QA/ventanacomúnno acreditadas; local<1M |
| Londres | **CUMPLE_VERIFICADO**:354637hechoselegiblesdeventanaslocales | **FACTIBLE_NO_EJECUTADO**:3997252clavesenergéticasúnicaslocales, cero conflictosdevalor globales | **FACTIBLE_NO_EJECUTADO**:mismohistórico real>1M, distribuido pendiente |

Unintervaloconvariasvariables es undocumento, nocuatro. SlotsH01..H24son horasrealmente publicadas, no atributosarbitrariosconvertidosenregistros; no se cuentan además lasfilasrawdiariascomo medicionesnuevas. ConteosnacionalesEPAnoNYC. Ampliarhistóricos realesnotableMaestrosfantasma. Ningunamuestraescogida demuestra todasesasconsultascontodoslosKPIs.

## Problemas estudiados y origen

Madrid13 351700filasrawrecontadas y56,435351%NO2elegibleintegrado:14722sinco-localización,12faltantesdeT elegible. Sitios/mesesenCSV; unidadNO2confirmada ymeteo provisional; historiaaltas/bajas existe desitio,no instalaciónindividual. Energíahoraria/CO2/alertassiguenfaltando.

NYC247526rawlocalesrecontados; conflictosDOT4767claves en2campañas persistenañadiendotodoslosdescriptores. 45,34%DOT–EPA y3,42%DOT–311 por**gruposborough/día**, no filasni tasasfallas. 311muestreado16días; interseccióntriple1grupo. No hayclavecorrectaverificada decontador/carril. Identidad/técnica/campaña yquésepuedeagregar requieren aceptación.

Londres4007440rawrecontados;100%coincidencia dehorasinterpretadas,0%ubicaciónfina. Desplazarjulio±1hmodificacobertura/correlación exploratoria; relojpendiente. Se verificaron3997252clavesy0conflictos devalor en4Menergía completos; licenciasLAQNnohabilitan automáticamente dashboardpúblico/exportación.

Matriz deorigen:observed/derived/synthetic/unavailable/unverified; ningunaalertaemitida ni instalaciónsintética seatribuyó adispositivos reales. Eventoscríticos futurosderived requierennorma/variable/unidad/ventana; IQRsoloanomalíacandidata. **No hay dependencia sintética inevitable**: losfaltantes exigenfuente, aceptación deNULL/derivado o ajusteacadémico. Propuestaopcionalhasta4cuentasdemoprueba,@example.invalid, sinidentidadesreales;no generadas. No se proponen fechasfalsas sobre sensoresreales ni geografía ficticiadehogares.

## Pruebas y tecnología

{total_tests}pruebas aprobadas sinomisiones;30diseñosSQL contrastados,9pruebas negativas deconstraints, EXPLAINguardado; contenedor/volumenanónimoremovidos. MongoDBausente: Python y diseñosJS, **no cumplirAggregationFramework/CRUDnativo todavía**. Las22heredadas no probaban20consultas niQAsemánticacompleta. NoHDFS/Spark/dashboardimplementados. Evidencia en`results/phase3/`, derivadosprivadosen`private_results/phase3/`; SHA y comandosreproducibles.

## Viabilidad condicionada, sin ranking

- **Madrid:** viable para modelo preliminarrelacional/documentalambiental ytráficolocal; faltanatributosadministrativos, unidadesmeteo completas, energía porhora, CO2/alertas y recorridos; mapasair/distritohistóricorequierenfuente. No rechazo automático porbloqueo403antiguo, yaresuelto paraZIPauditado.
- **NYC:** viable para canalEPA y conteos/solicitudes separados, volumenSQLlocal acreditado. Condicionada poridentidadDOTconflictiva, sensordecampaña, años/cuotasvolumenMongo/Spark, geografíaCRS y dashboardsinvelocidad/energíahoraria/CO2. Solicitud311no llenaalertas ni accidenteconfirmado.
- **Londres:** viable para serieenergética dehogaresanónimos/ambientea nivelciudad, con volumen realamplio. Bloqueaenergíaporzona fina, timezoneLCLypermisoLAQN; incidentesmovilidadrequierencomplementoauditado. Consumo decohorteno totalurbano.

Si eldocente exige **todoslosatributosyKPIs reales exactamente como estánenumerados**, **ninguna alternativa estácompletamentecubierta**. Esto no significaque susdatosnosepuedan cargar niquerelajar silenciosamente losrequisitos sea aceptable.

## Recomendaciones para la decisión de Fase4

1. Obtener aceptación explícita de«canal/sitio»frenteadispositivo, instalaciónNULL/sitioalta y estadoadministrativo desconocido; no aprobar sustitutosporconveniencia.
2. Acordar eventoscríticosderived/noalertashistóricas, categoríasdesolicitud311 yfuentesextra paraCO2, energía porzona/hora,velocidad/recorridos.
3. Si energía geográficaesineludible, exigir complemento realaLCL; si dashboardpúblico, resolver LAQNpor escritoantesdeelegir.
4. NYC: resolver identidadcontadorde las2campañas o aprobarcuarentena/exposición; acreditarCRS y ampliar conteosúnicos antesdeprometer500klecturas/1MSpark.
5. Madrid: cerrardiccionariometeo e inventariosporépoca/zonas; verificarvmed/tipos/cobertura antesdeKPIvehículos/congestión; fuentehorariaenergíareal.
6. Probar MongoDBnativo enentornoaislado disponible posterior, CRUD/pipelines/índices y semánticaBSON; mantenerPG/MongoIDsestablesyproveniencia.
7. Evaluar costo deadquirir loscomplementos ycondicionesdepublicación, sinreducirdecisión avolumen/Pythoncoincidencias. No asignarpuntuaciones finales enestafase.

## Artefactos entregados

Ocho archivos requeridos: `03_postgresql_matrix.md`, `03_mongodb_matrix.md`, `03_integration_gaps.md`, `03_data_origin_matrix.csv`, `03_spark_future_matrix.md`, `03_dashboard_coverage.md`, `03_feasibility_report.md`, `03_tests_report.md`. Matriz machine-readable adicional `03_compliance_matrix.csv`, scripts `phase3_validate.py`, `phase3_enrich.py`, `phase3_postgres.py`, `phase3_mongo_queries.js`, `phase3_reports.py`, pruebas`test_phase3.py` y evidencias en`results/phase3/`.

**Detenerse aquí. Fase4noiniciada; datasetdefinitivonoelegido; sincommit/push/merge ni cambiosremotos.**
''')
    print('Eight Phase3 deliverables and machine-readable compliance matrix generated.')


if __name__=='__main__':main()
