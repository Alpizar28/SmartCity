"""Human-readable Phase3 report prose, with values read from executed evidence."""
import json
import re
import xml.etree.ElementTree as ET

from download import ROOT

R=ROOT/'results/phase3'


def get(name):return json.loads((R/name).read_text())
def number(x):return f'{int(x):,}'.replace(',',' ')


def spacing(text):
    """Only explicit technical prose corrections; never infer Spanish word splits."""
    replacements={
        'porciudad':'por ciudad','conPK/FK':'con PK/FK','sinco-localización':'sin co-localización',
        'filasraw':'filas raw','sinlat':'sin lat','sinpuertos':'sin puertos',
        'validezvmed':'validez vmed','SQLvía':'SQL vía','descriptor':'descriptor',
        'datoobservado':'dato observado','estadosensor':'estado sensor','localprincipal':'local principal',
        'relojjulio':'reloj de julio','timestampGMT':'timestamp GMT','campañas36401y36828':'campañas 36401 y 36828',
        'valoresduplicados':'valores duplicados','unidadesaire':'unidades aire','memoria1GB':'memoria 1 GB',
        'sitioco-localizado':'sitio co-localizado','mapeadas':'mapeadas','temperaturaválida':'temperatura válida',
        'análisisPython':'análisis Python','fuentesQA':'fuentes QA','porépoca':'por época',
        'fuentecomplementaria':'fuente complementaria','datoslocales':'datos locales',
        'todoslos':'todos los','detodos':'de todos','todaslas':'todas las','entodas':'en todas',
        'sinauditoría':'sin auditoría','sansíntesis':'sin síntesis','clasificaciónprincipal':'clasificación principal',
        'geografíafina':'geografía fina','zonafina':'zona fina','estadoadministrativo':'estado administrativo',
        'canallógico':'canal lógico','canaleslógicos':'canales lógicos','datooriginal':'dato original',
        'observacionesreales':'observaciones reales','sitiosmapeados':'sitios mapeados',
        'bloqueogeográfico':'bloqueo geográfico','datosprivados':'datos privados','factibilidaddatos':'factibilidad de datos',
        'Spark1M':'Spark 1M','NoHDFS':'No HDFS','niHDFS':'ni HDFS','noMLobligatorio':'no ML obligatorio',
        'ventanaslocales':'ventanas locales','porvariable':'por variable','panelfijo':'panel fijo',
        'panelestable':'panel estable','fuente/año':'fuente/año','particionesfuente':'particiones fuente',
        'despuésdeconfirmar':'después de confirmar','trasfiltro':'tras filtro','fechascoincidentes':'fechas coincidentes',
        'datosregistrados':'datos registrados','originalintacto':'original intacto','datosduplicados':'datos duplicados',
        'lasfuentes':'las fuentes','lalectura':'la lectura','losdatos':'los datos','laslecturas':'las lecturas',
        'condatos':'con datos','enlos':'en los','ental':'en tal','datosantes':'datos antes',
        'localNYC':'local NYC','porcelda':'por celda','indicadorurbano':'indicador urbano',
        'laAPI':'la API','fuenteAPI':'fuente API','provenienciatrazable':'proveniencia trazable',
        'fuentesextra':'fuentes extra','globales':'globales','conflictosdevalor':'conflictos de valor',
        'estadoNULL':'estado NULL','clavesenergéticas':'claves energéticas','unidadesprovisionales':'unidades provisionales',
        'county':'county','enjoin':'en join','sinDOT':'sin DOT','enBronx':'en Bronx','noManhattan':'no Manhattan',
        'UTCevita':'UTC evita','cultu':'cultu','LicenciaLAQN':'Licencia LAQN','licenciaLAQN':'licencia LAQN',
        'fuenteTfL':'fuente TfL','APIprevia':'API previa','horaGMT':'hora GMT','textoeducativo':'texto educativo',
        'LCLsin':'LCL sin','LCLno':'LCL no','EPAparcial':'EPA parcial','DOTCRSpendiente':'DOT CRS pendiente',
        'TimeGMT':'Time GMT','hipótesisEPSG':'hipótesis EPSG','fuenteCRS':'fuente CRS',
        'porPOC':'por POC','UTC/GMT':'UTC/GMT','BSONMongo':'BSON Mongo','sinBSON':'sin BSON',
        'nativoMongoDB':'nativo MongoDB','correlaciónurbana':'correlación urbana',
        'MapReduceoHive':'MapReduce o Hive','windowyexplain':'window y explain','por sísoloBigData':'por sí solo Big Data',
        'originalesEPA':'originales EPA','SQLlocal':'SQL local','CSVaire':'CSV aire','ZIPentero':'ZIP entero',
        'ZIPtráfico':'ZIP tráfico','EPAlocal':'EPA local','scriptsprivados':'scripts privados',
        'datasetsoriginales':'datasets originales','medicionesficticias':'mediciones ficticias',
        'H24representa':'H24 representa','CO2e':'CO₂e','CO2':'CO₂','NO2':'NO₂','PM2.5':'PM₂.₅',
    }
    lines=[];code=False
    for line in text.splitlines():
        if line.startswith('```'):code=not code;lines.append(line);continue
        if not code:
            chunks=re.split(r'(`[^`]*`)',line)
            for i in range(0,len(chunks),2):
                s=chunks[i]
                for old,new in replacements.items():s=s.replace(old,new)
                protected=[]
                def hold(m):protected.append(m.group());return '\x00'+str(len(protected)-1)+'\x00'
                s=re.sub(r'\b(?:PG|MG|SP|H)\d{2}\b|\bLL84\b|NO₂|CO₂e?|PM₂\.₅',hold,s)
                s=re.sub(r'(?<=\d)(?=[A-Za-záéíóúñ])|(?<=[A-Za-záéíóúñ])(?=\d)',' ',s)
                s=re.sub(r',(?=[A-Za-záéíóúñ])',', ',s)
                for n,value in enumerate(protected):s=s.replace('\x00'+str(n)+'\x00',value)
                chunks[i]=s
            line=''.join(chunks)
        lines.append(line)
    return '\n'.join(lines)


def tables(text,end):
    return text[text.index('## Madrid'):text.index(end)].strip()


def render(name,draft):
    p=get('prepared_data.json');s=get('postgres_execution.json');v=get('validation.json')
    if name=='03_postgresql_matrix.md':
        matrix=tables(draft,'## 100000 registros')
        scope='\n'.join(f"| {c} | {p[c]['sensor_query_scope_channels']} | {p[c]['channels']} | {number(p[c]['eligible_unique_readings'])} |" for c in ['Madrid','NYC','London'])
        return f'''# Fase 3 — PostgreSQL: diez consultas por alternativa

## Disponibilidad, diseño y ejecución

Se ejecutaron diez diseños SQL por alternativa en PostgreSQL 16 local desechable, con referencias calculadas independientemente en Python. **No son diez requisitos cumplidos**: los diagnósticos PG03/PG06 muestran ausencia de estado/instalación y PG07 sobre canales extraídos de lecturas es incompleto como prueba de inventario.

**Cobertura estricta: 2/10 CUMPLE_VERIFICADO (vista y función), 6/10 PARCIAL y 2/10 NO_CUMPLE por alternativa.** PG01/02/05/08 son funcionales sobre canales lógicos: junto a PG09/10 serían **6/10 funcionales si el docente acepta esa granularidad**, no un inventario completo de analizadores físicos.

La vista `sensor_scope` excluye campañas DOT y hogares LCL del conteo de sensores. Esas observaciones siguen siendo hechos válidos para el volumen relacional, con tipo de entidad propio.

| Alternativa | Canales del alcance de sensores | Todos los canales de hechos | Hechos cargados con PK/FK |
|---|---:|---:|---:|
{scope}

## Cinco entidades mínimas y tipos

| Entidad / atributos exigidos | Datos disponibles | Ausencias y cumplimiento |
|---|---|---|
| Sensores: id, nombre, tipo, instalación, estado | Madrid estación/magnitud/punto; NYC sitio/POC/método EPA; Londres sitio/especie LAQN | Identidad física, DATE instalación y TEXT estado administrativo no completos: PARCIAL las tres |
| Ubicaciones: id, zona, distrito, coordenadas | Madrid sitios y distrito de tráfico; EPA WGS84/borough; LAQN autoridad local/lat/lon | Madrid distritos ambientales/historia, DOT CRS y hogares LCL sin geografía fina: PARCIAL |
| Categorías: id, nombre | Código/variable/unidad de diccionarios y fuente, categoría derivada trazable | Catálogo preliminar disponible; unidad meteo pendiente, no enum final de dispositivos |
| Usuarios: id, nombre, correo | Ninguna cuenta de aplicación en los datasets; tabla de prueba vacía | NO_CUMPLE datos actuales. LCLid y solicitante 311 no son usuarios de la aplicación |
| Organismos: id, nombre, responsable | Publicador/unidad Madrid y agencia DOT; LAQN DataOwner/DataManager de sitio | Operador individual y persona responsable no completos: PARCIAL |

IDs/nombres/categorías son TEXT; instalación DATE; tiempo TIMESTAMP y reloj explícito; valor/lat/lon DOUBLE PRECISION, coordenadas con CHECK; nombres de organismo/persona separados; correo UNIQUE. La prueba distingue ausencia NULL de un estado inactivo. Un alta/apertura de sitio no se copia a instalación de analizador.

## Modelo preliminar 3FN, no esquema final

Relaciones: `organizations ← channels → categories`, `channels → locations`, `readings → channels`; `users` independiente y vacía. La categoría determina variable/unidad y el sitio determina nombre/coordenadas; los hechos no repiten esas propiedades. PK determinista de fuente/canal/instante, FK de canal/categoría/ubicación/organismo y UNIQUE canal/tiempo. La identidad natural sigue siendo revisable: un hash no resuelve el conflicto de un contador físico.

EPA ubicación = estado-condado-sitio, separada de POC/método; DOT segmento separado de campaña; LCL referencia `unknown` sin geografía, no casas ficticias. Un modelo final necesita dispositivos acreditados, vigencias de sitios/técnicas, cartografía y relaciones históricas de organismos.

Se crearon índices PK/UNIQUE, canal+fecha, categoría y ubicación. EXPLAIN guardado, sin forzar elección de índice ni inventar rendimiento. PG08 calcula y contrasta tanto conteos como DENSE_RANK mediante CTE; PG07 usa NOT EXISTS; se validan JOIN/GROUP/HAVING/ORDER y agregados de hechos. PG09 consulta una vista real y PG10 invoca una función SQL STABLE. Particiones, vistas materializadas y optimización completa siguen FACTIBLE_NO_EJECUTADO.

Fechas: EPA conserva UTC, LAQN GMT; Madrid y LCL preservan reloj original con etiqueta explícita. No se fuerza UTC a horas locales no resueltas. Ventanas: enero/julio 2025 Madrid y tráfico enero 2025, NYC 2023, Londres enero/julio 2013.

## Matrices por alternativa

{matrix}

## 100000 registros y evidencia

Las tres alternativas superaron 100000 hechos reales cargados con PK/FK: **CUMPLE_VERIFICADO para volumen de esta prueba local**, no para el proyecto completo. No se inventaron sensores/usuarios ni se hizo un producto cartesiano. Los datos originales permanecen intactos.

Evidencia: `results/phase3/postgres_execution.json`, `postgres_execution.log`, `proof_queries.sql`, referencias `*_expected_sql.json`, CSV privados y pruebas `test_phase3.py`. PG07 necesita un inventario independiente y ventana completa: el cero del catálogo de prueba no acredita ausencia de sensores sin actividad.
'''
    if name=='03_mongodb_matrix.md':
        matrix=tables(draft,'## 500000 documentos')
        return f'''# Fase 3 — MongoDB: diez consultas por alternativa

**Ejecución nativa: 0/10 por alternativa.** No hay mongod, mongosh ni imagen MongoDB local; no se descargó infraestructura pesada. Python validó filtros, fechas, IDs y agrupaciones, pero **no es Aggregation Framework ni CRUD/BSON/índices de MongoDB**.

Cobertura de datos/diseño factible: **Madrid 8/10**, **NYC 7/10 más MG08 parcial** (solicitudes), **Londres 7/10** (TfL pendiente). Eventos críticos requieren regla aprobada; alertas emitidas por zona no están acreditadas. Estas cifras no son cumplimiento nativo verificado.

## Documentos, colecciones e identificadores

`readings`: un documento por observación/intervalo real, con ID determinista, channel_id/location_id compartidos con SQL, fuente, clave original, fecha/reloj, variable, valor/unidad, flags y procedencia. Un registro de tráfico conserva intensidad/velocidad/ocupación como campos del mismo documento: no se divide por atributo para aumentar volumen. Raw diario Madrid y horas normalizadas no se cuentan como dos series distintas.

`incidents`: expediente Madrid, solicitud 311 con record_kind=citizen_service_request y fuente TfL solo cuando se audite. `energy_reports`: mensual Madrid/anual LL84, sin mezclar unidades ni propiedad padre/hijo. `derived_events` y `alerts` están vacíos: un candidato IQR no es evento crítico ni mensaje histórico emitido. Derivaciones futuras necesitan regla/versionado/inputs y emitted_at real al emitir.

GeoJSON solo con WGS84 confirmado; hogar LCL sin zona/lat/lon. UTC/GMT se conservan cuando son conocidos; reloj local no resuelto no se convierte con la timezone del host. Las previsualizaciones JSON (500 filas reales por alternativa) no son documentos BSON cargados.

No hay FK entre motores: validar referencias y versión de catálogo al ingerir. Índices diseñados: UNIQUE de identidad natural, canal+fecha, fuente/variable/unidad/zona/fecha, incidente+fuente y categoría+fecha. Claves DOT conflictivas deben quedar en cuarentena, no ocultarse añadiendo el valor a la PK.

`scripts/phase3_mongo_queries.js` incluye diez diseños con guardia de nombre de DB desechable. CRUD propuesto: insertOne/insertMany idempotentes, find/findOne contrastados, updateOne/updateMany solo anotaciones, deleteOne solo copia desechable. **Ninguna operación CRUD nativa ejecutada.** Originales sin modificaciones/borrados.

## Matrices por alternativa

{matrix}

## 500000 documentos sin síntesis

| Alternativa | Capacidad de datos | Cumplimiento del motor |
|---|---|---|
| Madrid | {number(p['Madrid']['eligible_unique_readings'])} observaciones elegibles locales; 674704 intervalos de tráfico únicos por sí solos | FACTIBLE_NO_EJECUTADO en MongoDB |
| NYC | 112070 lecturas/conteos no ambiguos +124130 solicitudes locales =236200. API previa contabiliza531503 unique_key de enero+julio2023, no todos descargados | PARCIAL: ampliar datos reales; si500k exige solo lecturas de sensores, no acreditado |
| Londres | 3997252 claves hogar/timestamp locales,2748 extras duplicados y cero conflictos de valor globales. Ventana Jan/Jul sola no llega500k | FACTIBLE_NO_EJECUTADO; usar más histórico local |

No contar EPA nacional como NYC ni consultas agregadas como documentos cargados. Permisos LAQN/privacidad afectan redistribución. No se generó ni se necesita síntesis masiva para alcanzar volumen potencial.
'''
    if name=='03_feasibility_report.md':
        return '''# Fase 3 — Validación académica y viabilidad técnica

**Fase 3 terminada: tres alternativas evaluadas, sin ganador y sin Fase 4.** Se revisaron el enunciado original, fases 0/1/2, veinte consultas Sprint1 por alternativa, diez productos Spark, cinco entidades y los21KPIs del dashboard.

## Cobertura de consultas

| Alternativa | PostgreSQL estricto verificado | SQL funcional condicionado a canales lógicos | MongoDB nativo ejecutado | MongoDB datos/diseño factible |
|---|---|---|---|---|
| Madrid | 2/10;6parciales,2no cumplidas | 6/10 | 0/10 | 8/10 |
| NYC | 2/10;6parciales,2no cumplidas | 6/10, alcanceEPA | 0/10 | 7/10 +incidentes parcial |
| Londres | 2/10;6parciales,2no cumplidas | 6/10, alcanceLAQN | 0/10 | 7/10 |

Las dos verificadas estrictas son vistas y función SQL. Cuatro más funcionan sobre canales/sitios, pero no prueban dispositivos físicos completos. Estado/instalación no disponibles; organismo incompleto y actividad necesitan inventarios independientes. Se ejecutaron30diseñosSQL, no30cumplimientos académicos. Python no sustituye MongoDB nativo.

## Volúmenes

| Alternativa | ≥100k PostgreSQL | ≥500k MongoDB | ≥1M Spark |
|---|---|---|---|
| Madrid | CUMPLE_VERIFICADO:993374hechos cargados conPK/FK | FACTIBLE_NO_EJECUTADO:observaciones locales suficientes, sin duplicar atributos | FACTIBLE_NO_EJECUTADO:ampliar CSV aire local completo; muestra993374<1M |
| NYC | CUMPLE_VERIFICADO:112070hechos no ambiguos | PARCIAL:236200hechos/solicitudes locales;531503IDs311 en API previa requieren descarga/carga y aceptación semántica | PARCIAL:1,875MrawDOT globales no son1Múnicos/QA verificados; local insuficiente |
| Londres | CUMPLE_VERIFICADO:354637hechos cargados | FACTIBLE_NO_EJECUTADO:3997252claves energéticas únicas locales | FACTIBLE_NO_EJECUTADO:histórico real>1M, ejecución distribuida pendiente |

Maestros pequeños no se inflan a100k. Intervalo multivariable se conserva en un documento, no varios por atributo. No sumar raw y normalizado como mediciones nuevas. No se generaron mediciones sintéticas ni se modificaron originales.

## Hallazgos contrastados

- Madrid:13.351.700filas principales raw, de granularidades distintas. Integración19.087/33.821NO2elegibles=56,435351%;14.722sin co-localización y12sin temperatura válida. Unidades aire confirmadas; meteo provisional. Altas/bajas históricas son de sitios, no instalación individual.
- NYC:247.526filas locales. Conflictos DOT:4.767grupos/9.534filas en campañas36401y36828; persisten con todos los descriptores disponibles. DOT–EPA146/322gruposborough/día=45,34%; DOT–31111/322=3,42%por muestra de16fechas. Ninguna clave física correcta acreditada; no sumar conflictos arbitrariamente.
- Londres:4.007.440filas raw,3.997.252claves energéticas únicas locales y cero conflictos de valor globales. 100%de1488timestamps agregados coincide sin desplazar reloj, no100%de geografía/sincronización. Geografía fina de hogares0%; relojjulio y licenciaLAQN pendientes.

## Datos reales frente a sintéticos

Instalación/estado individual, usuarios, concentraciónCO2 y emisiones históricas de alertas no están completos. Eventos críticos futuros serían **derived** con política específica, no incidentes observados. Solicitudes311 son registros reales, no accidentes confirmados; CO2e anual no concentraciónCO2.

No existe síntesis inevitable: buscar fuente, conservarNULL, solicitar aceptación de derivado/alcance o declarar incumplimiento. Única propuesta synthetic opcional: hasta cuatro cuentas de prueba, namespace demo y correos@example.invalid, no generadas. Alternativa preferible: registrar miembros reales del equipo con consentimiento. No se proponen fechas ficticias sobre estaciones reales ni geografía inventada de hogares.

## Pruebas y viabilidad

42pruebas aprobadas (22heredadas +20nuevas), sin fallos/errores/omisiones. SQL local aislado cargó hechos, validóPK/FK/nulos, CTE/ranking, vista/función y agregados contra Python; contenedor y volumen anónimo eliminados. MongoDB/Hadoop/Spark/dashboard no implementados ni remotos consultados. Comandos, logs ySHA en `03_tests_report.md` y `results/phase3/`.

**Las tres son técnicamente viables para subconjuntos, condicionadas para el proyecto completo. Ninguna cubre todos los atributos/KPIs estrictos actuales.** Madrid requiere unidades/inventarios y energía horaria/CO2/alertas/recorridos; NYC exige claves DOT, exposición, ampliación de volumen y fuentes de velocidad/energía; Londres bloquea energía por zona fina y requiere timezone/permisos/complementos de movilidad e incidentes.

## Decisiones específicas para Fase4

1. Acordar con docente canal/sitio frente a dispositivo físico, instalaciónNULL y estado administrativo desconocido; no aprobar sustitutos silenciosos.
2. Acordar eventos críticos derivados y semántica de solicitudes311; conseguir fuentes deCO2/alertas/energía horaria/recorridos si los mínimos siguen estrictos.
3. Madrid: cerrar diccionario meteo, inventarios por época/distritos y validez de intensidad/vmed/duración antes de KPIs de movilidad.
4. NYC: pedir identidad de contador/carril para dos campañas o aprobar cuarentena; confirmarCRS y ampliar cardinalidad/QA antes de prometer500klecturas/1MSpark.
5. Londres: obtener geografía energética real o aprobar alcance de cohorte-ciudad; confirmar GMT/BST y permiso LAQN antes de dashboard público/exportaciones.
6. Ejecutar MongoDB nativo cuando exista entorno aislado, incluyendo CRUD/BSON/pipelines/índices. Comparar años/paneles estables y ejecutar Spark≥1M en fase posterior autorizada.
7. Considerar costo de complementos, permisos y requisitos bloqueantes, sin asignar puntuación final ni escoger ganador aquí.

## Entregables y parada

Ocho archivos requeridos `03_*`: matrices PostgreSQL/MongoDB, gaps de integración, origenCSV, futuroSpark, coberturaDashboard, informe de viabilidad y pruebas. Matriz adicional `03_compliance_matrix.csv`, scripts `phase3_*.py`/`.js`, `test_phase3.py`, JUnit/logs/manifiestos. Reproducción completa: `.venv/bin/python scripts/phase3_run.py` desde `research/datasets/`.

**Sin commit/push/merge, cambios Coolify/Tailscale ni cargas de producción. Fase4no iniciada.**
'''
    if name=='03_tests_report.md':
        tests=[]
        for file in ['legacy_tests.xml','tests.xml']:
            tests.extend(list(ET.parse(R/file).getroot().iter('testsuite')))
        total=sum(int(x.attrib['tests']) for x in tests)
        return f'''# Fase 3 — Pruebas y reproducción

**{total} pruebas aprobadas:22 heredadas y20 nuevas;0fallos/errores/omisiones.** JUnit separados en `results/phase3/legacy_tests.xml` y `tests.xml`; no se sobrescribió la evidencia de Fase2.

## Comandos

Desde `research/datasets/`, con el entorno Python3.11.16 y `scripts/requirements.lock` existente; paquetes nuevos instalados:ninguno.

```bash
.venv/bin/python scripts/phase3_run.py
```

Ejecuta secuencialmente:

```bash
.venv/bin/python scripts/phase3_validate.py
.venv/bin/python scripts/phase3_enrich.py
.venv/bin/python scripts/phase3_postgres.py
.venv/bin/python -m pytest tests/test_audit.py tests/test_saved_evidence.py -q --basetemp=/tmp/opencode/smartcity-phase3-legacy --junitxml=results/phase3/legacy_tests.xml
.venv/bin/python -m pytest tests/test_phase3.py -q --basetemp=/tmp/opencode/smartcity-phase3-tests --junitxml=results/phase3/tests.xml
.venv/bin/python scripts/phase3_reports.py
.venv/bin/python scripts/phase3_finalize.py
```

No usar `run_offline.py` para esta fase: regenera los entregables02. Phase3 no modifica esos archivos. Datos/muestras deben existir localmente; no hay nuevas descargas. Enunciado original extraído conpdftotext ySHA en `academic_evidence.json`.

## Aislamiento y ejecución nativa

Versión:{s['version']}. Imagen PostgreSQL16 ya disponible; Docker forzado a socket LOCAL`unix:///var/run/docker.sock`, `--network none`, sin puertos, `--pull never`, memoria1GB/CPU1. Bind read-only exclusivamente para CSVprivados de prueba. Volumen anónimo nuevo, descartado con contenedor. Contenedor eliminado:{s['container_removed']}; volúmenes eliminados:{s['anonymous_volumes_removed']}. No Compose, Coolify, Tailscale o bases existentes.

Dos intentos iniciales fallaron: uno conpsql durante arranque y otro por agotamiento deltmpfs512MiB duranteCOPY. Se endureció readiness para esperar final deinitdb y se cambió a volumen anónimo desechable. No se reportan esos intentos como exitosos ni se promete operar en512MB. Ejecuciones finales completas con códigos0 en `run.log`; SQL/results/planes en `postgres_execution.*`.

## Registro de verificaciones

| Grupo | Evidencia y resultado | Límite |
|---|---|---|
| Legado22 | Budget/retry/403/503/ZIPCRC/path/H24/nulos/DST/joins y assertions de métricas reales | No probaba todas las consultas académicas |
| Nuevas20 | Tres pruebas de ejecución nativa, tres de IDs/FK/datos ausentes, dos de normalización Madrid, EPA UTC/valor, DOT claves, coberturas Madrid/NYC/Londres, LCL global, incidentes/nulos, unidades, tres agregaciones e inmutabilidad | Datos/semántica aún parciales, no proyectos completos |
| SQL |30diseños, referencias Python, conteos/sumas/min/max, vista, función y CTE/DENSE_RANK | PG03/06 diagnósticosNULL; PG07 catálogo derivado no inventario completo |
| Restricciones |9rechazos reales (PKduplicada, FKhuérfana, timestampNULL porciudad) | Fixtures mínimos en transacciones fallidas, ninguna medición ficticia persistida |
| Raw |CSVaire/meteo, ZIPtráfico leído completo conCRC, originalesEPAlocal, DOT/311 y4Menergía | Raw filas no equivalen a observaciones únicas |
| LCL |3.997.252claves,2748extras,0conflictos de valor globales, porSQLite en disco | Cuatro miembrosCRC completos, no ZIPentero ni5567hogares |
| Incidentes |14.388expedientesMadrid;14.386categorías conocidas y2NULL, sin conflictos |33.322detalles no son33.322accidentes;311solicitud no confirmado |
| Unidades/reloj |Unidadesaire contra diccionario; H24 yEPA UTC exactos |Meteo/unidad ytimezoneLCL quedan pendientes |
| Inmutabilidad |Hashes/tamaños de documentación previa, scripts, pruebas, métricas, logs, manifiestos y cuerpos/derivados anteriores |DatosPhase3 regenerables, originales intactos |

`inputs_manifest.csv` conserva fingerprints; `validation.json`, `dot_conflicts.json`, `catalog_activity.csv`, `incident_checks.json`, `unit_history_checks.json`, referenciasSQL y agrupacionesPython detallan resultados. `phase3_finalize.py` valida entregables, sintaxis, matrices y hashes previos; guarda `final_checks.json` y `outputs_manifest.csv` (excluye el log activo del runner). Raw/derivados privados ignorados porGit.

MongoDB no disponible: filtros y agrupaciones Python +diseñosJS, sin CRUD/BSON/índices/Aggregation Framework nativo. Hadoop/Spark/dashboard no ejecutados. Las pruebas sobre formas/protocolo del legado no se usan para aumentar volumen. **30SQLejecutados no equivalen a30requisitos cumplidos.**
'''
    if name=='03_integration_gaps.md':
        a=v['Madrid']['join'];n=v['NYC']['joins'];l=v['London']['join']
        sensitivity='\n'.join(f"| {r['July_shift_hours']}h | {r['matches']} | {r['left_match_pct']:.4f}% | {r['pearson_exploratory_only']:.6f} |" for r in l['timezone_sensitivity'])
        return f'''# Fase 3 — Integración: evidencia y tratamientos

## Recuento de Fase2

Madrid **13.351.700** filas principales:76513diarias aire+56383meteo+13218804tráfico. NYC **247.526**:85106DOT+38290EPAlocal+124130solicitudes. Londres **4.007.440**:4000000energía+7440LAQN. Recontados desde originales/ZIP y muestras; **son granularidades distintas**, no cantidades de dispositivos ni mediciones únicas comparables. Complementos/inventarios excluidos. Evidencia `validation.json`, hashes en manifiestos02/inputs_manifest.csv.

## Madrid

**19087/33821NO2elegibles=56,435351%**, enero/julio2025, magnitud8 frente a temperatura83. 14722lecturas sin sitio co-localizado;19099mapeadas y12sin temperatura elegible. Coincidencia temporal dentro de sitios mapeados99,94%. Los13sitios co-localizados se identificaron por código y coordenadas<1m, no identidad de analizador. El porcentaje no es tasa de fallas ni cobertura de todo el archivo.

Pérdidas por sitio/mes/causa: `madrid_no2_losses.csv`. Sitios con alguna pérdida: {', '.join(a['unmatched_entities'])}. Catálogo independiente contrastado en `catalog_activity.csv`: Urb.Embajada(MAD-AIR:55)sin lecturas de la muestra, no evidencia de estado inactivo. Distritos ambientales/historia de inventario siguen pendientes.

H24 representa fin23–24h y se lleva a00h siguiente; enero/julio evitan transicionesDST. `PUNTO_MUESTREO` de aire incluye técnica, no inventario de dispositivos persistentes; meteo100%vacío. Unidades aire verificadas con AnexoII (NO2/PM2.5µg/m³, COmg/m³); meteo sigue provisional. AnexoI contiene altas/bajas/recodificaciones de sitio, **no instalación individual** ni vigencia cartográfica completa en2025.

Tráfico intensidadveh/h no conteo: intervalos de integración1–30min, ponderación/exposición y validezvmed/carga por tipo pendientes. Energía municipal mensual no responde energía horaria; concentraciónCO2 y alertas históricas no se resuelven limpiando valores.

## NYC

**4767grupos con dos valores distintos,9534filas**, campañas36401y36828. Clave campaña-segmento-dirección-fecha/hora:4767extras; añadirWKT ytodos los descriptores (boro,street,fromst,tost) no los elimina. Cero filas originales idénticas. No hay clave física correcta acreditada: índice de fila/localizador de raw identifica procedencia, no carril/contador. Conservar cuarentena y75572lecturas no ambiguas; no sumar conflictos como si fueran carriles.

DOT tiene219días observados en el archivo, campañas discontinuas, no actividad esperada constante del borough. EPA88101 cubre cinco sitios enBronx/Brooklyn/Queens; noManhattan/StatenIsland para este parámetro. UTC evita falsas colisionesDST, calendario local se deriva solo al agregar. CRS delWKT candidato2263 pendiente, no usado enjoin aceptado.

DOT–EPA **146/322gruposborough/día=45,34%** (176DOTsinEPA,737EPAsinDOT). DOT–311 **11/322=3,416149%**: porcentaje de gruposDOT con solicitudes en la muestra, **no porcentaje de solicitudes ligadas ni tasa de fallas**. 311solo16fechas/96grupos; los11gruposDOT que caen en fechas solicitadas sí coinciden. Ampliar311en fechas de campaña puede aumentar cobertura, pero no corrige identidadDOT, desigual exposición niEPAparcial. Intersección triple:1grupo/322(0,31%). Detalle en `nyc_borough_day_matches.csv`.

311created_date es reporte, no fecha de hecho. AgregadosEPA promedian primero sitio, despuésborough, perdiendoPOC/métodos/horas/picos. LL84CO2e anual no concentraciónCO2. Energía horaria, velocidad y recorridos requieren fuente real adicional.

## Londres

Se deduplicaron233extras idénticos enJan/Jul;44horas/hogar parciales excluidas. Suma de dos intervalos únicos semihorarios por hogar/hora →cohorte; promedioNO2 de sitios disponibles. **1488/1488timestamps coinciden**(744enero+744julio)sin desplazar reloj. No es100%de lecturas/hogares emparejados, sincronización demostrada ni geografía.

Panel108–119hogares por hora; **0%ubicación fina de hogares**: sinlat/lon/borough. ReferenciaSQLunknowncon geografíaNULL, no casas inventadas; cohorte no totalLondres. LAQNtimestampGMT; LCLtimezone pendiente. Sensibilidad al desplazar julio:

| DesplazamientoLCL | Horas coincidentes | Coberturaizquierda | Pearson exploratorio |
|---|---:|---:|---:|
{sensitivity}

Ningún desplazamiento se declara correcto: la variación prueba la necesidad de confirmarGMT/BST, no valida una correlación urbana niSpark/causalidad. LCL global:3997252claves únicas/2748extras/0conflictos de valor, nuevo escaneo4M, solo cuatro miembros completosCRC.

LicenciaLAQN permite finalidadinformativa/educativa y excluyeoperativa/comercial; no se acredita redistribución general. API pública no licenciaCCBY; LCLCCBY no concede derechosLAQN. Mantener lecturas/integraciones privadas y consultar permiso para dashboard/exportación pública.

## Clasificación y resolución

| Problema | Categoría | Estado/tratamiento |
|---|---|---|
| LCLduplicados idénticos | Limpieza | Deduplicación derivada comprobada, raw intacto |
| Falsos duplicadosEPA DST | Modelado temporal | Resuelto conservandoUTC, regresión aprobada |
| DOTvalores conflictivos | Fuente complementaria/no resuelto | Falta identidad; cuarentena, no sumas arbitrarias |
| Madrid12huecos y no co-localizados | Modelado/agregación o complemento | QA/NULL y alcance parcial; fuente/cartografía para zonas |
| Inventarios históricos/instalación/estado | Fuente complementaria/potencial bloqueo | Alta/apertura de sitio no instalación individual |
| CampañasNYC/3,42% | Fuente complementaria/agregación | Ampliar fechas311 y controlar exposición; no ausencia=falla |
| LCLreloj | Fuente complementaria/potencial bloqueo | Confirmar definición de tiempo, sensibilidad no resuelve |
| HogaresLCLsin zona | Fuente complementaria/bloqueo espacial | No recuperable por limpieza; no geografía sintética |
| LicenciaLAQN | No resuelto/potencial bloqueo | Permiso/alcance de publicación |
| Usuariosapp | Observado futuro/synthetic opcional | Registro autorizado o hasta4fixtures de prueba, no generados |
| Eventos/alertas | Derived o fuente complementaria | Política aprobada y evidencia de emisión; sin historia ficticia |

Ningún problema exige síntesis inevitable: buscar fuente, mantenerNULL, aceptar alcance/derivado o declarar incumplimiento. **Originales sin modificaciones.**
'''
    if name=='03_spark_future_matrix.md':
        matrix=draft[draft.index('## Madrid'):draft.index('## Ocho clases')]
        repairs={'146borough/día':'146 borough/día','311 solo16fechas':'311 solo 16 fechas',
            'Madrid2025/2026':'Madrid 2025/2026','LCL2012/2013':'LCL 2012/2013','LAQN solo2013':'LAQN solo 2013',
            'NYC local solo2023':'NYC local solo 2023','CO2':'CO₂'}
        for old,new in repairs.items():matrix=matrix.replace(old,new)
        return f'''# Fase 3 — Futuro Hadoop/Spark

**No Hadoop/Spark instalado ni ejecutado.** Diez productos y ocho clases de análisis del enunciado contrastados; pruebasPython no se etiquetan como resultadosSpark.

## Volumen real y períodos

Madrid:993374hechos elegibles de prueba, menor que1M. CSVaire local completo ofrece1795279slotsV; ampliar y controlarDST/técnicas. Tráfico13,2Mrawno son13,2Múnicos verificados. Londres:3997252claves energéticas locales,119faltantes/no numéricos y cero conflictos globales, suficiente capacidad real>1M. NYC:236200hechos/solicitudes locales, DOTglobal1875154rawpotencial; cardinalidad/QA/período común aún no acreditados. **NYC1M siguePARCIAL.**

Comparación anual: Madrid2025frente a2026enero–agosto, comparar meses comunes, no diciembre2026; LCL2012/2013panelestable disponible, LAQNsolo2013auditado; NYClocalprincipal2023, añosextraAPI no equivalen a comparación ejecutada.

## Diez productos obligatorios

{matrix}

## Ocho clases de análisis y riesgos

Descriptivo: conteos/valores por canalQA; temporal: huecos/campañas no rellenados con0; correlacional: Madrid19087pares, NYC146grupos, Londres1488horas condicionales, sin causalidad. Tendencias: panel/exposición estable y períodos comparables, noMLobligatorio. Espacial: Madridinventarios/distrito tráfico, NYCboro/EPA yDOTCRSpendiente, LondresLAQNsin hogares geográficos. Movilidad: intensidad/campos de tráfico por tipo, campañasDOT/DfTno continuidad. Anomalías: IQR/QA candidatos, no incidentes. Comparación: controlar muestras/estaciones/POC, no totals de cohortes variables.

## HDFS y demostración distribuida posterior

Raw inmutable, manifiestoSHA/versión, particionesfuente/año/mes y JSON/CSV/Parquet exportables. Ejecutar mkdir/put/ls/cat/get/rm yMapReduceoHive/Impala; demostrar bloques, replicación, fallos y nodos. No hay lista académica de diez consultasHadoop. LAQNno exportable públicamente sin permiso.

Plan posterior: procesar≥1Mclaves no ambiguas, contar antes/después deQA, comprobar joins sin multiplicación, ejecutarSQL/DataFrames/windowyexplain, medir recursos/tiempos/particiones y distribución. Ningún archivo grande ni análisisPython demuestra por sísoloBigData distribuido.
'''
    if name=='03_dashboard_coverage.md':
        table=draft[draft.index('| Dominio |'):draft.index('## Visualizaciones')]
        return '''# Fase 3 — Dashboard: cobertura y riesgos

No se implementó UI ni se ejecutóMongoDB/Hadoop/Spark. Los estados de la tabla evalúan datos/semántica, no componentes funcionando. Orígenes en `03_data_origin_matrix.csv`, matriz completa en `03_compliance_matrix.csv`. Un proxy no se renombra KPI observado.

'''+table+'''
## Visualizaciones y filtros

Serie temporal: fuentesQA, mostrando huecos, ventana/campaña y reloj. Comparativa por zonas: Madridtráficodistrito y ambientesitio/ciudad; NYCboroughconEPAparcial; LondresLAQNautoridad, **no energíaLCLporborough**. Proporciones por tipo: canales/variables/categorías, no analizadores físicos inventados. Cuarto gráfico debe ser **resultado realmente generado por Spark**, aún inexistente.

Mapa: Madrid coordenadaspublicadas de inventarios yEPAWGS84; DOTsolo despuésdeconfirmarCRS. LAQNpuntos, LCLhogares sin ubicación. Coordenadas plausibles no acreditan precisión/vigenciahistórica. Distrito ambientalMadrid requiere cartografíaoficial, no proximidad inventada.

Filtros obligatorios período/zona/tipo: disponibles en subconjuntos geográficos conocidos; NULL visible como no disponible, ciudad no barrio. Sensores/categorías recomendados conIDcanal estable y selectores separados para campaña/hogar/solicitud. Tabla detalle/paginación y panel único conselectorPG/Mongo/HDFS/Spark siguen sin implementar.

Etiquetas tecnológicas deben indicar el motor ejecutado: no PythoncomoMongo/Spark. Los cuatro dominios completos no están cubiertos por ninguna alternativa; CO₂, alertas reales, tiempo de recorrido, estado e instalación individual siguen sin acreditarse. Energía mensual/anual y total de cohorte no KPIs horarios/ciudad intercambiables.
'''
    return draft
