"""Decision reports only: no schemas, loads, synthesis, network or engine calls."""
import csv
import json
import re

from phase4_evaluate import ROOT, OUT, CITIES, LABELS, WEIGHTS, get


def prose(text):
    """Explicit corrections for technical shorthand; never infer arbitrary word splits."""
    replacements = {
        'dePp':'de P pp.', 'novsí':'nov sí', 'enE':'en E',
        'horasproductivas':'horas productivas', 'Madridlimpieza':'Madrid limpieza',
        'integraciónmedia':'integración media', 'NYCalta':'NYC alta',
        'porconflictos':'por conflictos', 'LCLlimpiezamedia':'LCL limpieza media',
        'ygeografía':'y geografía', 'estadoaprobados':'estado aprobados',
        'Modelosaprobados':'Modelos aprobados', 'LCLotrosmeses':'LCL otros meses',
        'revisióncruzada':'revisión cruzada', 'esperaexterna':'espera externa',
        'niSprint':'ni Sprint', 'hútiles':'h útiles', 'excedercapacidad':'exceder capacidad',
        'ydependen':'y dependen', 'deesperas':'de esperas', 'picoRSSoffline':'pico RSS offline',
        'cargaMongo':'carga Mongo', 'oinfraestructura':'o infraestructura',
        'Composeestático':'Compose estático', 'efectivaCoolify':'efectiva Coolify',
        'deC3':'de C3', 'alcanceaprobado':'alcance aprobado',
        'RutaA':'Ruta A', 'RutaB':'Ruta B', 'Bno cambiaalta':'B no cambia alta',
        'SinA/B':'Sin A/B', 'permanecenNO_CUMPLEaunque':'permanecen NO_CUMPLE aunque',
        'vacíaejecute':'vacía ejecute', 'PG01tipo':'PG01: tipo',
        'PG02ubicación':'PG02: ubicación', 'PG03estado':'PG03: estado',
        'PG04organismo':'PG04: organismo', 'PG05rankingubicación':'PG05: ranking de ubicación',
        'PG06instaladosaño':'PG06: instalados por año', 'PG07sinactividad':'PG07: sin actividad',
        'PG08zonas':'PG08: zonas', 'PG09vista':'PG09: vista', 'PG10función':'PG10: función',
        'NYCsoloEPA':'NYC solo EPA', 'LondresLAQN':'Londres LAQN',
        'DISTINCTvs':'DISTINCT vs', 'EPAboro':'EPA borough', 'CRSDOT':'CRS DOT',
        'LAQNautoridad':'LAQN autoridad', 'LCLNULL':'LCL NULL',
        'GISMadrid':'GIS Madrid', 'fuenteCRS':'fuente CRS',
        'FKsinhuérfanos':'FK sin huérfanos', 'zonaconfuente':'zona con fuente',
        'UNKNOWNvisible':'UNKNOWN visible', 'enlas':'en las',
        'inventarioA':'inventario A', 'oactividad':'o actividad',
        'ventanaB':'ventana B', 'esperaindefinida':'espera indefinida',
        'ausenciacampaña':'ausencia de campaña', 'Madridgestor':'Madrid gestor',
        'NYCoperadorEPA':'NYC operador EPA', 'LAQNowner':'LAQN owner',
        'managersitio':'manager de sitio', 'ydesconocidos':'y desconocidos',
        'lecturascomo':'lecturas como', 'crecepor':'crece por',
        'oconsultaaltade sitio':'o consulta alta de sitio', 'yrotulada':'y rotulada',
        'fechasinventadas':'fechas inventadas', 'EXISTSsobrecatálogoindependiente':'EXISTS sobre catálogo independiente',
        'rankfuncional':'rank funcional', 'coberturaMadrid':'cobertura Madrid',
        'boroughEPA':'borough EPA', 'autoridadLAQN':'autoridad LAQN',
        'yDENSE_RANK':'y DENSE_RANK', 'empatesvs':'empates vs',
        'VIEWvs':'VIEW vs', 'refreshaparte':'refresh aparte',
        'Funciónnativa':'Función nativa', 'inputsNULL':'inputs NULL',
        'Cincoentidades':'Cinco entidades', 'usuariosdel':'usuarios del',
        'organismogestor':'organismo gestor', 'cargodocumentado':'cargo documentado',
        'segúnalcance':'según alcance', 'hSQLMadrid':'h SQL Madrid',
        'conDiagrama':'con diagrama', 'Maestrospequeños':'Maestros pequeños',
        'hechosreales':'hechos reales', 'versionacordada':'versión acordada',
        'BSONdesdeQAreal':'BSON desde QA real', 'IDestable':'ID estable',
        'ylocation':'y location', 'InstanteUTCsolo':'Instante UTC solo',
        'conteosinserted':'conteos inserted', 'ycountDocuments':'y countDocuments',
        'devalores':'de valores', 'elvalor':'el valor', 'aPK':'a PK',
        'MG01sensor':'MG01: sensor', 'MG02rango':'MG02: rango',
        'MG03extremos':'MG03: extremos', 'MG04críticos':'MG04: críticos',
        'MG05alertaszona':'MG05: alertas por zona', 'MG06zonas':'MG06: zonas',
        'MG07tipo':'MG07: tipo', 'MG08incidentes':'MG08: incidentes',
        'MG09aggregation':'MG09: aggregation', 'MG10filtros':'MG10: filtros',
        'nohogar':'no hogar', 'findnativo':'find nativo', 'FechasBSON':'Fechas BSON',
        'bordes[':'bordes [', 'contratotiempo':'contrato temporal',
        'TestsUTC':'Tests UTC', 'conteosvs':'conteos vs', 'QApor':'QA por',
        'retenerextremos':'retener extremos', 'maxnativos':'max nativos',
        'notNULL':'not NULL', 'IQRno':'IQR no', 'implicaerróneo':'implica erróneo',
        'QAaprobada':'QA aprobada', 'noIQRcrítico':'no IQR crítico',
        'umbralno':'umbral no', 'parafabricarcaso':'para fabricar un caso',
        'fuenteoficial':'fuente oficial', 'oemisiónactual':'o emisión actual',
        'replayaprobado':'replay aprobado', 'nogarantizada':'no garantizada',
        'vacíocumple':'vacío cumple', 'Promediopor':'Promedio por',
        'EPAborough':'EPA borough', 'noLCLfino':'no LCL fino',
        '$groupvs':'$group vs', 'NULLdeclarados':'NULL declarados',
        'unidadvs':'unidad vs', 'detallepersona':'detalle de persona',
        'sinincident.sensor_idinventado':'sin incident.sensor_id inventado',
        'categoríaUNKNOWN':'categoría UNKNOWN', 'saliday':'salida y',
        'ANDcanal':'AND canal', 'hMongoMadrid':'h Mongo Madrid',
        'kúnicosno':'k únicos, no', 'kSQL':'k SQL', 'actualC':'actual C',
        'kMongoMadrid':'k Mongo Madrid', 'localesC':'locales C',
        'MSpark':'M Spark', 'anualC':'anual C', 'únicoC':'único C',
        'NYCdescarga':'NYC descarga', 'todasC':'todas C', 'decolumna':'de columna',
        'acreditaCRS':'acredita CRS', 'dehallazgo':'de hallazgo', 'deltotal':'del total',
        'porhoras':'por horas', 'EnergíaLCL':'Energía LCL', 'zonafinaC':'zona fina C',
        'noC3':'no C3', 'yKPIfaltantesC':'y KPI faltantes C',
        'asignarSprint':'asignar Sprint', 'yprobar':'y probar',
        'comparaciónanual':'comparación anual', 'gráficosuno':'gráficos, uno',
        'Sparkreal':'Spark real', 'copiararchivo':'copiar archivo',
        'cargainicial':'carga inicial', 'pruebacruzada':'prueba cruzada',
        'cotizadascomo':'cotizadas como', 'Kemblypueden':'Kembly pueden',
        'enparalelo':'en paralelo', 'enborradores':'en borradores',
        'poranticipado':'por anticipado', 'Riesgomoderado':'Riesgo moderado',
        'cerrarmeteo':'cerrar meteo', 'DOTidentidad':'DOT identidad',
        'geografíacohorte':'geografía de cohorte', 'Factibleestimada':'Factible estimada',
        'BSONporvalidar':'BSON por validar', 'SQLfactible':'SQL factible',
        'clockexplícito':'clock explícito', 'zonafalsa':'zona falsa',
        'restauraciónno':'restauración no', 'klocales':'k locales',
        'Volumenamplio':'Volumen amplio', 'aúnpendientes':'aún pendientes',
        'siPG':'si PG', 'yMG':'y MG', 'adquisiciónen':'adquisición en',
        'porTfL':'por TfL', 'alcancedocente':'alcance docente',
        'primeravance':'primer avance', 'hprevistas':'h previstas',
        'yposibleexceso':'y posible exceso', 'decididoequipo':'decidido por equipo',
        'yplanrevisado':'y plan revisado', 'faltanconsultas':'faltan consultas',
        'documentarNO_CUMPLE':'documentar NO_CUMPLE', 'Noesquemas':'No esquemas',
        'enestafase':'en esta fase',
        'SQLestrictas':'SQL estrictas', 'SQLfuncional':'SQL funcional',
        'canalesEPA':'canales EPA', 'canalesLAQN':'canales LAQN',
        'campañasDOT':'campañas DOT', 'incidentespor':'incidentes por',
        'datoslocales':'datos locales', 'datos/diseño':'datos/diseño',
        'consultassemánticas':'consultas semánticas',
        'sinespera':'sin espera', 'deFase':'de Fase',
        'dejoin':'de join', 'deunidad':'de unidad', 'dealertas':'de alertas',
        'dedatos':'de datos', 'deejecución':'de ejecución', 'decontrato':'de contrato',
        'decanales':'de canales', 'dedispositivos':'de dispositivos',
        'desitio':'de sitio', 'delmes':'del mes', 'delcontrato':'del contrato',
        'dedocente':'de docente', 'delavance':'del avance', 'delnúcleo':'del núcleo',
        'elrespaldo':'el respaldo', 'elproblema':'el problema', 'elsensor':'el sensor',
        'lascondiciones':'las condiciones', 'losatributos':'los atributos',
        'lasvariables':'las variables', 'losdatos':'los datos',
        'enLondres':'en Londres', 'enMadrid':'en Madrid', 'enFase':'en Fase',
        'enelrespaldo':'en el respaldo', 'enelcontrato':'en el contrato',
        'porvariable':'por variable', 'porintervalo':'por intervalo',
        'porzona':'por zona', 'porunidad':'por unidad', 'pormotor':'por motor',
        'porcampaña':'por campaña', 'porfecha':'por fecha',
        'sinfuente':'sin fuente', 'sinpermiso':'sin permiso', 'sinred':'sin red',
        'sincronía':'sincronía', 'sincontrato':'sin contrato', 'sinmuestra':'sin muestra',
        'sinzona':'sin zona', 'singeografía':'sin geografía',
        'noplena':'no plena', 'noatributo':'no atributo', 'no confirmado':'no confirmado',
        'noejecutados':'no ejecutados', 'nocumplimiento':'no cumplimiento',
        'nocertificación':'no certificación', 'nocaridad':'no caridad',
        'noambigüedad':'no ambigüedad', 'noambiguos':'no ambiguos',
        'no identificado':'no identificado', 'nomedidos':'no medidos',
        'no medida':'no medida', 'nolecturas':'no lecturas', 'noalertas':'no alertas',
        'noinstalación':'no instalación', 'noestado':'no estado',
        'nooperador':'no operador', 'nodeclarar':'no declarar',
        'noduplicar':'no duplicar', 'no inventar':'no inventar',
        'noecosistema':'no ecosistema', 'no calidad':'no calidad',
        'yalertas':'y alertas', 'yequipo':'y equipo', 'yrecursos':'y recursos',
        'ypermisos':'y permisos', 'yreloj':'y reloj', 'ydocente':'y docente',
        'yprimeracarga':'y primera carga', 'ycatálogos':'y catálogos',
        'yref':'y ref', 'yreplanificación':'y replanificación',
        'yresultado':'y resultado', 'yfirmas':'y firmas',
        'ytareas':'y tareas', 'ysalida':'y salida', 'ymatriz':'y matriz',
        'fuenteindividual':'fuente individual', 'modeloaceptado':'modelo aceptado',
        'relojLCL':'reloj LCL', 'clockLCL':'clock LCL', 'licenciaLAQN':'licencia LAQN',
        'Usoeducativo':'Uso educativo', 'usoLAQN':'uso LAQN',
        'datosLCL':'datos LCL', 'geografíaLCL':'geografía LCL',
        'energíaLCL':'energía LCL', 'LCLdatos':'LCL datos',
        'LCLexpandir':'LCL: expandir', 'filasLCL':'filas LCL',
        'clavesLCL':'claves LCL', 'DOTglobales':'DOT globales',
        'DOTglobal':'DOT global', 'DOTraw':'DOT raw',
        'cohorteno':'cohorte no', 'cohorteeléctrica':'cohorte eléctrica',
        'únicos/QA':'únicos/QA', 'IDscompartidos':'IDs compartidos',
        'QAglobal':'QA global', 'BSONcorrecto':'BSON correcto',
        'emitted_atactual':'emitted_at actual', 'observed_athistórico':'observed_at histórico',
        'COUNTDISTINCT':'COUNT DISTINCT', 'DENSE_RANKempates':'DENSE_RANK empates',
        'NOTEXISTS':'NOT EXISTS', 'GROUPBY':'GROUP BY',
        'backup/restore':'backup/restore', 'entornoautorizado':'entorno autorizado',
        'reglaoficial':'regla oficial', 'reglaversionada':'regla versionada',
        'reglaválida':'regla válida', 'timezones':'timezones',
        'valoresvs':'valores vs', 'resultadoesperado':'resultado esperado',
        'metadatosreales':'metadatos reales', 'unidadpendiente':'unidad pendiente',
        'fuenteadicional':'fuente adicional', 'fuentecomplementaria':'fuente complementaria',
        'fenomenoglobal':'fenómeno global', 'registrofísico':'registro físico',
        'esquemafinal':'esquema final', 'modelofinal':'modelo final',
        'sitiocanal':'sitio/canal', 'muestrareal':'muestra real',
        'entornoaisladoautorizado':'entorno aislado autorizado',
        'inventarioindependiente':'inventario independiente',
        'actividadenventana':'actividad en ventana',
        'Condicionadoconriesgoalto':'Condicionado con riesgo alto',
        'responsabilidadesp':'responsabilidades p.',
        'resuelvencontador':'resuelven contador',
        'unidadmeteorológica':'unidad meteorológica',
        'refreshenmanifest':'refresh en manifiesto',
        'modificaoriginales':'modifica originales',
        'ejecuciónPGguardada':'ejecución PG guardada',
        'regeneracionesprevias':'regeneraciones previas',
        'snapshotsseleccionadosCSV':'snapshots seleccionados CSV',
        'tienenSLAacreditado':'tienen SLA acreditado',
        'resuelveigualausencia':'resuelve la misma ausencia',
        'alertashistóricas':'alertas históricas',
        'diccionariooficial':'diccionario oficial',
        'ydossourcescoherentes':'y dos fuentes coherentes',
        'solucionableporlimpieza':'solucionable por limpieza',
        'sincolocalización':'sin co-localización',
        'yradioexploratorio':'y radio exploratorio',
        'cartografíaoficial':'cartografía oficial',
        'actualenZIPauditado':'actual en ZIP auditado',
        'actualizaciónoficial':'actualización oficial',
        'Corrupciónirrecuperable':'Corrupción irrecuperable',
        'recursooficialinaccesible':'recurso oficial inaccesible',
        'docenteacordaralcance':'docente: acordar alcance',
        'Josébuscarcomplementolocal':'José: buscar complemento local',
        'identidadcontador':'identidad de contador',
        'Campañasdiscontinuas':'Campañas discontinuas',
        'exposicióncampaña':'exposición por campaña',
        'sinfuenteadicional':'sin fuente adicional',
        'ynoadquisiciónviable':'y no adquisición viable',
        'exportaciónpúblicano':'exportación pública no',
        'operativoobligatorio':'operativo obligatorio',
        'ycorrelaciónhoraexacta':'y correlación a hora exacta',
        'Tablausuariosvacía':'Tabla usuarios vacía',
        'responsableindividualausente':'responsable individual ausente',
        'cuentasrealesconsentidas':'cuentas reales consentidas',
        'Exigenciafuenteexterna':'Exigencia de fuente externa',
        'asignaciónposterior':'asignación posterior',
        'identidadDOTresuelta':'identidad DOT resuelta',
        'controlarexposición':'controlar exposición',
        'yfuentescomplementarias':'y fuentes complementarias',
        'clavesDOTconflictivas':'claves DOT conflictivas',
        'DOTglobalrawpotencial':'DOT global raw potencial',
        'Entornoautorizado':'Entorno autorizado',
        'NYCadquisiciónextra':'NYC adquisición extra',
        'complementostodosKPIs':'complementos de todos los KPIs',
        'planesSQLguardados':'planes SQL guardados',
        'identidadsemántica':'identidad semántica',
        'Madridcartografía':'Madrid cartografía',
        'individualausente':'individual ausente',
        'oactividadenventanaB':'o actividad en ventana B',
        'estadoacreditados':'estado acreditados',
        'ocriterioaceptado':'o criterio aceptado',
        'Catálogoindependiente':'Catálogo independiente',
        'instalaciónausente':'instalación ausente',
        'SoloDATEverificada':'Solo DATE verificada',
        'oconsultaaltadesitio':'o consulta alta de sitio',
        'independienteMadrid':'independiente Madrid',
        'NYCEPArequiereexterno':'NYC EPA requiere externo',
        'NOTEXISTSsobrecatálogoindependiente':'NOT EXISTS sobre catálogo independiente',
        'resultadoesperado':'resultado esperado',
        'particiónjustificados':'partición justificados',
        'ksensoresniusuarios':'k sensores ni usuarios',
        'ocultarconflictos':'ocultar conflictos',
        'FiltrocanalrealMadrid':'Filtro canal real Madrid',
        'Reglaválidaunidad':'Regla válida: unidad',
        'eventoderivednoconfirmado':'evento derived no confirmado',
        'Sinfuentehistórica':'Sin fuente histórica',
        'Promedioporunidad':'Promedio por unidad',
        'Madridzonaacreditada':'Madrid zona acreditada',
        'nomediaheterogénea':'no media heterogénea',
        'Resultadosporclase':'Resultados por clase',
        'NYCsolicitudaceptadaoNYPD':'NYC solicitud aceptada o NYPD',
        'LondresTfLauditar':'Londres TfL a auditar',
        'UnaIDporincidente':'Una ID por incidente',
        'Intersecciónfiltros':'Intersección de filtros',
        'SQLnativoactual':'SQL nativo actual',
        'Londresdatoslocales':'Londres datos locales',
        'NYCadquisiciónrealAPI':'NYC adquisición real API',
        'SparkMadridnormalizaciónanual':'Spark Madrid normalización anual',
        'Londresuniquehistórico':'Londres histórico único',
        'ejecucióndistribuidatodas':'ejecución distribuida todas',
        'dictamenunidadesmeteoMadrid':'dictamen unidades meteo Madrid',
        'ycatálogoindependiente':'y catálogo independiente',
        'EnergíaLCLporzonafina':'Energía LCL por zona fina',
        'coordenadasficticias':'coordenadas ficticias',
        'cuentasconsentidas':'cuentas consentidas',
        'vínculogestorsensor':'vínculo gestor–sensor',
        'cuentasdemoopcionales':'cuentas demo opcionales',
        'aprobaciónfuentes':'aprobación fuentes',
        'consultassemánticas':'consultas semánticas',
        'dependenciasexternas':'dependencias externas',
        'bajoaceptacióncanales':'bajo aceptación de canales',
        'reutilizaciónCSVprueba':'reutilización CSV de prueba',
        'Mongorequiereadquisición':'Mongo requiere adquisición',
        'Viablecondicionado':'Viable condicionado',
        'porbloqueoirreversible':'por bloqueo irreversible',
        'niresultadosficticios':'ni resultados ficticios',
        'autorizaciónposterior':'autorización posterior',
        'vigenciahistórica':'vigencia histórica',
        'exportacioneshistóricas':'exportaciones históricas',
        'enentornoautorizado':'en entorno autorizado',
        'kdocumentosúnicos':'k documentos únicos',
        'extrapolarPGlocal':'extrapolar PG local',
        'odiagnósticosNULLno':'o diagnósticos NULL no',
        'Mclavesenergéticas':'M claves energéticas',
        'aceptacióncohorte':'aceptación de cohorte',
        'cuarentenaDOTaceptada':'cuarentena DOT aceptada',
        'deinstalaciónindividual':'de instalación individual',
        'deinfraestructura':'de infraestructura',
        'mezclarhogaresLondres':'mezclar hogares Londres',
        'conPK/FK':'con PK/FK', 'porcriterio':'por criterio', 'sitiosco':'sitios co',
        'noBSON':'no BSON', 'noSpark':'no Spark', 'noMongo':'no Mongo', 'sinubicación':'sin ubicación',
        'sincronía':'sincronía', 'slotsVaire':'slots V aire', 'datosreales':'datos reales',
        'sinredistribución':'sin redistribución', 'sinzonas':'sin zonas', 'LCLlocales':'LCL locales',
        'clockDOT':'clock DOT', 'DOTpendiente':'DOT pendiente', 'LCLGMT':'LCL GMT',
        'LL84padres':'LL84 padres', 'noN':'no N', 'sinH':'sin H', 'poratributo':'por atributo',
        'noatributo':'no atributo', 'nohora':'no hora', 'noUA':'no UA',
        'slotsV':'slots V', 'diccionariometeo':'diccionario meteo', 'fase3':'fase 3',
        'crecimiento':'crecimiento', 'No sensor':'No sensor', 'antes14':'antes 14',
        'laAPI':'la API', 'Mongo nativo':'MongoDB nativo', 'semánticanativa':'semántica nativa',
        'cargaSQL':'carga SQL', 'Recurso':'Recurso', 'ClaveDOT':'Clave DOT',
        'proveedorDOT':'proveedor DOT', 'descargasextra':'descargas extra', 'por tipo':'por tipo',
        'soloalcance':'solo alcance', 'después17':'después 17', 'antesde':'antes de',
        'enrecurso':'en recurso', 'yvolumen':'y volumen', 'yprueba':'y prueba',
        'ycontrato':'y contrato', 'yJSON':'y JSON', 'yperíodo':'y período', 'yTfL':'y TfL',
        'yfechas':'y fechas', 'yQA':'y QA', 'ydatos':'y datos', 'yjoin':'y join',
        'ysensores':'y sensores', 'ycatálogos':'y catálogos', 'sinrespuesta':'sin respuesta',
        'clavescorrectas':'claves correctas', 'sincierre':'sin cierre', 'conlimpieza':'con limpieza',
        'conPK':'con PK', 'de10':'de 10', 'de4':'de 4', 'porciudad':'por ciudad',
        'porfase':'por fase', 'porfuente':'por fuente', 'porcriterio':'por criterio',
        'sinmedir':'sin medir', 'no lecturas':'no lecturas', 'soloperíodo':'solo período',
        'no todos':'no todos', 'de preparación':'de preparación', 'degestor':'de gestor',
    }
    for old,new in replacements.items(): text=text.replace(old,new)
    text=re.sub(r'(\d)(?=(?:canales|intervalos|hechos|locales|claves|slots|sitios|horas|fechas|criterios|totales|subcriterios|estados|puntos|pruebas|filas|expedientes|atributos|casos|bytes)\b)',r'\1 ',text)
    text=re.sub(r'\b(Madrid|Londres|NYC|Los|El|por|para|del|de|antes|después|contiene|los|sobre|total|movilidad|ambiente|energía|IoT)(?=\d)',r'\1 ',text)
    protected=[]
    def hold(m): protected.append(m.group());return '\x00'+str(len(protected)-1)+'\x00'
    text=re.sub(r'(?:PG|MG|SP)\d{2}|LL84|NO₂|CO₂|PM₂\.₅',hold,text)
    text=re.sub(r',(?=[A-Za-záéíóúñ¿])', ', ', text)
    for i,token in enumerate(protected):text=text.replace('\x00'+str(i)+'\x00',token)
    return text


def write(name,text): (ROOT/name).write_text(text.strip()+'\n')
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
        ['| '+' | '.join(str(x) for x in row)+' |' for row in rows])


def main():
    totals=get('results/phase4/scores_summary.json')['totals']
    details=list(csv.DictReader((OUT/'subscores.csv').open()))
    scores=list(csv.DictReader((ROOT/'04_scores.csv').open()))
    by={(r['alternative'],int(r['criterion_id'])):float(r['score_points']) for r in scores if r['criterion_id']!='TOTAL'}
    comparison=table(['Criterio','Peso','Madrid','Nueva York','Londres'],
        [[label,weight,*[f'{by[(c,i)]:.2f}' for c in CITIES]] for i,(label,weight) in enumerate(zip(LABELS,WEIGHTS),1)]+
        [['Total',100,*[f'{totals[c]:.3f}' for c in CITIES]]])
    sections=[]
    for i,label,weight in zip(range(1,9),LABELS,WEIGHTS):
        rows=[r for r in details if r['criterion_id']==str(i) and r['alternative']=='Madrid']
        sections.append(f'### C{i}. {label} ({weight} puntos)\n')
        sections.append(table(['Subcriterio / peso','Madrid: rating y justificación','Nueva York','Londres'],
            [[r['subcriterion']+' / '+r['subweight'],*[prose(x['rating_0_4']+'/4 — '+x['rationale'])
                for c in CITIES for x in details if x['alternative']==c and x['criterion_id']==str(i) and x['subcriterion']==r['subcriterion']]] for r in rows]))
        sections.append('\n**Evidencia, faltantes y sensibilidad del criterio:**')
        for r in rows:
            sections.append('- '+prose(r['subcriterion'])+': '+r['evidence']+'. Falta: '+
                            prose(r['missing_evidence'])+'. Recalcular si: '+prose(r['rescore_condition'])+'.')
        sections.append('')
    sensitivity={c:{'base':totals[c],'without_volume':round(totals[c]-by[(c,5)],4),
                   'without_spatial_temporal':round(totals[c]-by[(c,6)],4)} for c in CITIES}
    (OUT/'sensitivity.json').write_text(json.dumps(sensitivity,indent=2))
    write('04_final_comparison.md',f'''
# Fase 4 — Comparación técnica final

**Se recomienda Madrid como núcleo preferido condicionado. No hay aprobación del equipo ni declaración de cumplimiento completo.** La prioridad es Sprint 1 y la reutilización posterior en HDFS/Spark; la decisión no deriva del87 inicial ni del tamaño raw.

## Evidencia comparada

| Resultado | Madrid | Nueva York | Londres |
|---|---|---|---|
| PostgreSQL estricto verificado |2/10 (PG09/10) |2/10 |2/10 |
| SQL funcional condicionado a canales lógicos |6/10;460canales de prueba |6/10;9canalesEPA, no campañasDOT |6/10;5canalesLAQN, no hogares |
| MongoDB factible por datos/diseño |8/10 |7/10 más incidentes parcial |7/10;TfL no verificado |
| MongoDB nativo ejecutado |0/10 |0/10 |0/10 |
| Hechos cargados conPK/FK en prueba local |993374 |112070 |354637 |
| Datos para500kdocumentos |674704intervalos tráfico solos;993374hechos locales |236200locales;531503IDs311 consultados enAPI, no descargados todos |3997252clavesLCLlocales; ventana Jan/Jul sola no basta |
| Datos para1MSpark |1795279slotsVaire locales, normalización/QA anual pendiente |1875154DOTrawglobales potenciales, unicidad/QA no medida |3997252claves energéticas locales, distribución no ejecutada |
| Integración medida |19087/33821NO2elegibles;13sitios co-localizados |146/322DOT–EPA y11/322DOT–311,borough/día |1488/1488horas interpretadas; hogares con zona fina0% |
| Riesgo diferencial |Unidades meteo, inventarios históricos, energía horaria/KPIs faltantes |4767clavesDOTconflictivas, campañas y mínimos adicionales |LicenciaLAQN, relojLCL y geografía de hogares ausente |

Los56,44%,45,34%y100% **no son métricas comparables de calidad**: sus denominadores y supuestos difieren. El3,42%NYC está condicionado por16fechas311; no significa imposibilidad de descargar más solicitudes. Londres conserva la ventaja de energía semihoraria, no energía por zona fina.

## Rúbrica y reglas explícitas

Se usa la ponderación de **I p.1**,20/15/15/10/10/10/10/10,total100. Es una rúbrica de planificación propuesta, **no la calificación oficial E p.28**. Ratings iguales para todas:0ausente,1potencial con dependencia bloqueante,2prerrequisitos parciales,3prerrequisitos medidos suficientes para alcance limitado con cierres pendientes,4subcriterio acreditado dentro de su alcance. Puntos =peso_subcriterio×rating/4. Las calificaciones son juicios de ingeniería sustentados en evidencia, no mediciones universales ni probabilidades de éxito.

Para coberturas se usan fórmulas, no redondeos de consultas:
- SQL estricto:4×verificadas/10; SQL funcional:4×funcionales condicionadas/10; MongoDB nativo:4×verificadas/10=0.
- SoporteMongo:4×media de créditos(CUMPLE1,FACTIBLE0,75,PARCIAL0,25,NO_CUMPLE/NO_VERIFICADO0).
- Spark potencial:créditos1/0,60/0,30/0/0; el descuento expresa falta de ejecución distribuida.
- Dashboard:créditos1/0,75/0,40/0/0, por dominio; pesos movilidad4,ambiente4,energía4,IoT3. Un PARCIAL no se declara KPIcubierto; se usan los21estados exactos deFase3.

Créditos y esfuerzo son convenciones explícitas que se pueden discutir. No se asigna crédito nativo aPython. Puntos de disponibilidad y trabajo de adquisición se separan; no se suman raw y normalizado como observaciones nuevas. Una dependencia crítica no queda aceptada porque el total sea mayor.

{comparison}

**Puntuación final:** Madrid {totals['Madrid']:.3f}, Londres {totals['London']:.3f}, Nueva York {totals['NYC']:.3f}/100. Decimales son precisión aritmética, no intervalos estadísticos. `04_scores.csv` contiene24criterios y3totales; `results/phase4/subscores.csv` contiene{len(details)}subcriterios con evidencia y condiciones individuales.

## Justificación completa por subcriterio

{chr(10).join(sections)}

## Diferencias respecto a la propuesta inicial

| Alternativa | Puntuación inicial no medida | Evaluación actual | Qué cambió |
|---|---:|---:|---|
| Madrid |87 |{totals['Madrid']:.3f} |Tráfico ahora descargado; volumen SQL e integración probados. Se penalizan ausencias administrativas, meteo provisional, historia/zonas y energía horaria/KPIs faltantes |
| Nueva York |76 |{totals['NYC']:.3f} |EPA local confirmado; se descubrieron conflictos DOT persistentes y mínimos adicionales no acreditados localmente |
| Londres |77 |{totals['London']:.3f} |LCL ahora cardinalizado y útil para energía horaria; penalizaciones por permisos, reloj, ausencia geográfica e incidentes sin auditoría completa |
| Beijing |79 |No reevaluado |Fuera de las tres auditorías; no es respaldo plenamente validado |

I no desglosa ratings originales por criterio: **no se puede reconstruir una resta causal exacta de87 a {totals['Madrid']:.3f}**. Cambian el paquete (LCL en Londres), los hallazgos y la base probatoria. No se toma el ranking preliminar como resultado experimental.

## Robustez y decisión independiente del total

Sin volumen(C5), sobre90puntos: Madrid{sensitivity['Madrid']['without_volume']:.2f},NYC{sensitivity['NYC']['without_volume']:.2f},Londres{sensitivity['London']['without_volume']:.2f}. Sin compatibilidad espacial/temporal(C6):Madrid{sensitivity['Madrid']['without_spatial_temporal']:.2f},NYC{sensitivity['NYC']['without_spatial_temporal']:.2f},Londres{sensitivity['London']['without_spatial_temporal']:.2f}. La preferencia se mantiene: no depende únicamente de volumen o porcentajes dejoin.

Mover1rating en un criterio completo de10puntos cambia2,5puntos; cambios acumulados y nueva evidencia pueden cambiar el orden. Confianza cualitativa **media-alta en la preferencia relativa**, **baja en cumplimiento completo sin aprobaciones**. No son porcentajes de probabilidad.

Vetos:rechazo docente de unidadcanal/estado/instalación sin fuente real; todos losKPIs estrictos sin complementos; derechos incompatibles; mínimos útiles insuficientes en contrato aceptado; imposibilidad de ejecución nativa para23oct. Mayor puntuación no supera veto. Ninguna alternativa está validada para todos los atributos estrictos actuales.

Madrid reduce trabajo incremental:datos locales suficientes, categorías reales e incidentes por expediente, mismo municipio e integración más específica entre redes. Londres es respaldo condicionado por volumen y energía horaria; NYC añade proveedorDOT y adquisición adicional a la ruta crítica. La elección exige aprobar alcance, no ocultar brechas. **Fase5no iniciada; no implementación del dataset.**
''')
    # Exact source URLs and hashes are taken from the existing snapshot, not reconstructed.
    manifest=list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    ids=['MAD-AIR-file','MAD-METEO-file','MAD-TRAFFIC-Jan2025',
         '212629-0-estaciones-control-aire-inventory','300360-0-meteorologicos-estaciones-inventory',
         'MAD-TRAFFIC-META-file','MAD-ENERGY-file','MAD-CRASH-file']
    resources=[]
    for ident in ids:
        r=next(r for r in reversed(manifest) if r['id']==ident and r['path'])
        resources.append([ident,r['url'],'`'+r['sha256']+'`','`'+r['path']+'`'])
    resource_table=table(['Recurso/ID de manifiesto','URL oficial exacta','SHA256 snapshot','Archivo local'],resources)
    write('04_selected_dataset.md',f'''
# Fase 4 — Madrid: núcleo preferido condicionado

## Estado y confianza

| Nivel de decisión | Estado |
|---|---|
| Recomendación técnica |**Madrid**,{totals['Madrid']:.3f}/100, por evidencia y menor trabajo incremental Sprint1 |
| Selección provisional |**Condicionada** para ratificación; no implementación autorizada |
| Aprobación del equipo |Pendiente de José,Daniel,Kembly,Fernanda; no firmas simuladas |
| Cumplimiento verificado |2/10SQLestrictas,6/10funcionales condicionadas,volumenSQLlocal;Mongo0/10nativas |

Confianza media-alta en la preferencia relativa; media en calendario si se cierran condiciones antes del14oct; baja en cumplimiento completo sin docente/complementos. Bajo exigencia de todos los atributos/KPIs reales estrictos, **ninguna alternativa está plenamente aprobable ahora**.

## Fuentes concretas recomendadas

**Núcleo:** MAD-AIR(calidad del aire), MAD-METEO(meteorología), MAD-TRAFFIC(enero2025). **Complementos:** MAD-CRASH(expedientes2026) para incidentes y MAD-ENERGY(consumo municipal mensual) para energía limitada. **Auxiliares:** inventarios aire/meteo/puntos de tráfico. Son cinco datasets del mismo portal, no cinco repositorios; los inventarios no son otra medición física. E p.6 exige dos fuentes distintas y E p.23 recomienda dos repositorios: aclarar si el docente convierte la recomendación en requisito.

{resource_table}

El hash, fecha y archivo del manifiesto fijan la versión aunque cambie la URL. Aire/meteo realmente cubren2025-01-01–2026-08-31, no solo2025 como el campo histórico`period`. Tráfico corresponde a enero2025. **Accidentes2026 no se unen a enero2025 como contemporáneos**: son otra colección fechada. Para una serie conjunta elegir y auditar el recurso2025 posteriormente, no acreditado aquí. Energía mensual solo se une a agregados del mes con jerarquía/unidad correctas.

Ventana Sprint1 propuesta: aire/meteo enero+julio2025 y tráfico enero2025, ya probados. Para MongoDB≥500k priorizar674704 intervalos de tráfico no ambiguos locales, un documento por intervalo con todas sus variables; otras colecciones aportan variabilidad. SQL≥100k hechos reales y catálogos pequeños. No son674704 sensores ni se prometen993374 filas en el esquema definitivo sin repetir controles de contrato/QA.

Cantidad real frente a mínimos: la carga SQL de prueba equivale a 9,93 veces 100k; los 674704 intervalos de tráfico representan 1,35 veces 500k, margen de 174704 antes de nuevos filtros del contrato. Para Spark la muestra elegible de 993374 queda 6626 por debajo de 1M: ampliar al histórico local de aire con 1795279 slots V y comprobar normalización anual/QA, no generar filas artificiales. Los cinco archivos originales seleccionados suman **145308605 bytes** contando cada snapshot una vez (tráfico ZIP comprimido); no es almacenamiento PG/Mongo ni presupuesto total de transferencia. Cumplimiento de la interpretación académica de 100MB aún requiere confirmación. Evidencia: `results/phase4/selected_storage_evidence.json`.

## Observado, derivado, sintético y ausente

- **observed:** Hxx/Vxx, variables de tráfico/flags/duración, coordenadas/códigos publicados, consumo mensual/unidad, expediente/categoría/fecha/distrito. Fecha de alta es observada únicamente como alta de sitio, no instalación de analizador.
- **derived:** IDs/namespaces, categorías, normalización de horas reales, agregados separados por variable/unidad y co-localización; actividad en ventana y zonificación por cartografía oficial futuras. Críticos requieren regla versionada aprobada; no se han ejecutado como críticos.
- **synthetic:** ninguna medición necesaria para volumen ni generada. Hasta cuatro cuentas demo opcionales, solo con autorización posterior y aisladas; preferir cuentas reales consentidas. No fechas/estados ficticios sobre sensores reales ni consumo mensual repartido a horas.
- **unavailable/unverified:** instalación/estado individual, operador/responsable personal completo, emisiones históricas de alertas, concentraciónCO2, recorridos, energía horaria, unidades meteo/vigencia histórica completas.

Replay futuro sobre historia: emitted_at sería fecha real de ejecución actual y observed_at histórico separado, origen derived/replay. **No acredita un mensaje que Madrid emitió en2025.** Necesita autorización y aceptación docente; el umbral no se elige para forzar una consulta no vacía.

## Consultas y Sprint 2

PG09/10 verificadas; PG01/02/05/08 funcionales sobre canales, requieren granularidad/ubicación aceptadas. PG03/06 no cumplidas; PG04 operador y PG07 inventario independiente parciales; Usuarios aún vacía. MG01/02/03/06/07/08/09/10 con datos/diseño, falta ejecución BSON/pipelines/índices/CRUD; MG04 política y MG05 emisión/alcance pendientes. Plan de todas en `04_implementation_feasibility.md`.

HDFS raw/exportaciones históricas viables, comandos/batch/distribución no ejecutados. Spark: 8/10 factibles y 2 parciales en Fase3. Normalizar histórico local ≥1M y comparar enero/julio 2025–2026 con panel equivalente; no comparar diciembre2026 inexistente. Correlación NO2–temperatura: 19087 pares, condicionada a unidad/semántica. Tráfico con radio de 1km exploratorio, no causalidad. Eventos/accidentes por distrito a su fecha, no sensor causante inventado.

Dashboard no completo: movilidad con intensidad/vmed/carga por tipo y exposición; PM2.5 real, temperatura/humedad pendientes de unidad; energía mensual, no horaria; IoT con canales/cadencia, no estado administrativo ni recepción original. CO2, tiempo de recorrido, energía horaria y alertas históricas exigen fuente real o alcance docente. El gráfico Spark debe provenir de ejecución Spark, no Python.

## Puertas de aceptación (futuras)

1. **Antes del 14oct:** aprobación conjunta y docente sobre entidad canal, PG03/06/usuarios/organismo, eventos/alertas/KPIs. Sin fuente o aceptación no garantizar 10/10.
2. **Antes del 17oct:** contrato de IDs/clock/QA/BSON y primera carga en entorno autorizado. José cierra diccionario/cartografía o alcance limitado aceptado; Daniel/Kembly comparan originales y referencias.
3. **Antes del 20oct:** ≥100k hechos SQL, ≥500k documentos únicos, cero huérfanos, conteos QA/duplicados y respaldo/restauración; recursos realmente medidos, no extrapolar PG local a Coolify.
4. **Antes del 23oct:** veinte consultas semánticamente aceptadas y ejecutadas, CRUD, planes/pipelines, resultados y prueba cruzada. Colecciones vacías o diagnósticos NULL no cierran PG03/06/MG05.

## Contingencia sin migración tardía

**Respaldo: Londres, condicionado**, por ≥1M claves energéticas locales y energía semihoraria; no por el 100% de join. Antes del 14oct debe resolverse permiso educativo/exportación, clock GMT/BST, aceptación de cohorte-ciudad sin energía por borough y TfL si se exigen incidentes. Sin esas puertas **no es respaldo listo para cargar**. NYC es tercera opción solo con identidad/cuarentena DOT aceptada y volumen ampliado verificado.

Disparadores de cambio temprano: rechazo del contrato que el respaldo sí resuelva con fuente real; imposibilidad de dos fuentes coherentes/QA útiles; prioridad de energía horaria aceptando alcance LCL; derechos incompatibles o integridad irrecuperable del núcleo; conteos bajo mínimos sin expansión real viable. Comprobar que el problema se resuelve en el respaldo: todos carecen de instalación individual/CO2/alertas históricas. No cambiar solo para ocultar un bloqueo común.

**Después del 17oct evitar migración completa; después del 20oct solo por problema irreversible legal/integridad/datos con decisión explícita equipo/docente y replanificación.** Problemas de infraestructura se tratan primero con lotes/índices/recursos, no otra ciudad. Preferir complemento real compatible con Madrid (accidentes2025, CO2, energía horaria, recorridos) para vacíos puntuales, aún no acreditado; no mezclar hogares Londres con zonas Madrid. Buscar un complemento no es aprobar el dataset ni autorizar una descarga. **Detenerse aquí, sin Fase5.**
''')
    write('04_decision_evidence.md','''
# Fase 4 — Evidencia de decisión

## Autoridad y revisión

E=enunciado28páginas:dosfuentesp6,cincoentidadesp8–9,PGp10,Mongop12,HDFSp13–14,Sparkp15–16,21KPIs/visualizaciónp18–19,mínimosp26,rúbricap28. Página3infográfica sintexto completo:usar p26para mínimos. P=plan6páginas:responsabilidadesp1–4/hitosp4–5. I=propuesta5páginas:pesosp1/notas87/79/76/77p2,expresamente no medidas. La rúbricaI no es la académicaE.

Se leyeron completos todos los entregablesMD00/01/02/03, matricesCSV, resultados priorizados y los tresPDF. Textos extraídos en `results/phase4/E_original.txt`, `P_original.txt`, `I_original.txt`;SHA/path/páginas en `evidence_checks.json`. READMEprevio yJSON03sinselección describen su fase histórica;no se sobrescribieron.

## Afirmación → artefacto → significado

| Hallazgo | Artefacto/campo | Interpretación y límite |
|---|---|---|
| SQL2/10estrictas,6/10condicionadas | `phase3/summary.json`→postgresql_strict_verified/postgresql_functional_logical_scope; `03_compliance_matrix.csv` |PG09/10nativas;no30cumplimientos por30diseños |
| Mongo8/7/7factibles,0nativas | `summary.json`→mongodb_data_supported_not_native/mongodb_native_executed |Python no BSON/CRUD/Aggregation Framework |
| Cargas993374/112070/354637 | `phase3/postgres_execution.json`→cities.*.loaded_readings; `prepared_data.json`→eligible_unique_readings |Hechos nativos en prueba local conPK/FK;no cargas finales/remotas |
| ReferenciasSQL iguales aPython | `postgres_execution.json`→cities.*.queries.*.equals_python_reference; `*_expected_sql.json`; `proof_queries.sql` |Mismo alcance,referencia independiente,no calidad global |
| Raw13351700/247526/4007440 | `phase3/validation.json`→recounted_primary_raw_rows; `phase2_summary.json` |Granularidades distintas,no sensores ni claves únicas |
| Madrid19087/33821 y13sitios | `Madrid-integration.json`→air_row_spatiotemporal_matched/eligible_air_NO2_rows/co_located_sites; `phase3/madrid_no2_losses.csv` |14722sinco-localización,12sinT;56,435351%NO2elegible,no tasa de falla |
| Tráfico674704intervalos elegibles | `Madrid-integration.json`→traffic.normalization; `MAD-TRAFFIC-summary.json` |MuestraID%20,0duplicados;13,2Mrawno cardinalizados globalmente |
| Aire1795279slotsV | `MAD-AIR-annual_counts.json`→flags_full_year.V/raw_duplicate_keys |2025–ago2026;normalizaciónDST/QA final,noSpark |
| DOT4767conflictos | `phase3/dot_conflicts.json`→groups/conflicting_rows/candidate_duplicate_extras/campaigns_with_conflicts |9534filas,2campañas;descriptores no resuelvencontador,cero duplicados idénticos |
| NYC146/322 y11/322 | `NYC-integration.json`→DOT_EPA/DOT_311; `phase3/validation.json`→NYC.joins |Borough/día,16fechas311,no fracción de solicitudes ni fallas |
| NYC531503IDs311consultables | `02_volume_analysis.md`;respuestas APIdeenero/julio en `02_download_manifest.csv` |242173+289330IDs de meses disjuntos,no todosdescargados/cargados |
| LCL3997252claves/0conflictos | `phase3/validation.json`→London.expanded.unique_keys/conflicting_extra_values;SQLiteprivado |4CSV/121hogares,2748extrasidénticos,119faltantes,no167M/ZIPentero |
| Londres100%temporal/0%geográfico | `London-integration.json`→coverage/household_fine_zone_mapping_pct; `validation.json`→London.join |1488horas interpretadas,clockjulio pendiente,panel108–119 |
| Unidades aire vsmeteo | `phase3/unit_history_checks.json`→Madrid; `madrid_dictionary_provenance.json` |Aire confirmado;nombre de magnitud no acredita unidadmeteorológica |
| Incidentes14388,2categoríaNULL | `phase3/incident_checks.json`→Madrid; `MAD-CRASH-incidents.json` |33322detalles no accidentes,solo2026auditado |
| DerechosMadrid/LAQN | `01_source_risks.md`; `02_blockers.md`;probesM25/L11-refreshenmanifest |CCBYmunicipal conatribución;usoLAQNeducativo no redistribución general |
| 42pruebas previas | `phase3/legacy_tests.xml`22 +`phase3/tests.xml`20; `run.log` |Sin fallos/errores/omisiones;no pruebas deMongo/Spark/remoto |
| AislamientoSQL/cleanup | `postgres_execution.json`→network/published_ports/container_removed/anonymous_volumes_removed |Contenedor único sinred,no servicios existentes alterados |

## Verificaciones nuevas sin repetir auditoría completa

Se verificaron hashes/tamaños de **todos** los archivos en `phase3/inputs_manifest.csv` y `outputs_manifest.csv`,incluidosraw yderivados, y los cinco recursos de datos seleccionados. Se reconcilió matriz153filas conresumenJSON,conteosnativos/denominadores/conflictos yJUnit42pruebas;no se repitióescaneo de13Mtráfico/4MLCLnicargaPG. Copiar textoPDF yhash no modificaoriginales. Cero red/descargas nuevas;presupuesto Fase2sinconsumo adicional.

Comandos desde `research/datasets/`:

```bash
.venv/bin/python scripts/phase4_evaluate.py
.venv/bin/python scripts/phase4_reports.py
.venv/bin/python -m pytest tests/test_audit.py tests/test_saved_evidence.py tests/test_phase3.py tests/test_phase4.py -q --basetemp=/tmp/opencode/smartcity-phase4-tests --junitxml=results/phase4/tests.xml
.venv/bin/python scripts/phase4_finalize.py
```

Se volvieron a ejecutar las42pruebas anteriores y se agregaron6de Fase4: reconciliación de pesos/subcriterios/totales por ciudad, ausencia de crédito nativo/aprobación humana, sensibilidad y entregables/cobertura de20brechas. Las pruebas03 leen resultados PostgreSQL guardados y originales; no lanzan contenedor ni consultan remoto. No usar `phase3_run.py`/`run_offline.py` en esta fase, pues repetirían cargas/regeneraciones previas. Dependencias: entorno Python3.11.16/lock existente y pdftotext; ninguna infraestructura o paquete nuevo.

Resultados: `evidence_checks.json`, `subscores.csv`, `scores_summary.json`, `sensitivity.json`, snapshotsseleccionadosCSV,JUnitnuevo y `final_checks.json`/`outputs_manifest.csv`. Puntajes reproducibles desde misma evidencia;horas-persona/riesgos son juicios,no benchmarks. No se recibieronfirmas,respuesta docente ni permisos jurídicos nuevos;licencias no fueron reconsultadas enred,no garantía indefinida.
''')
    write('04_open_risks.md','''
# Fase 4 — Riesgos abiertos

Severidad:Crítica impide aceptación legal/semántica,Alta amenaza mínimos/rediseño/fecha,Media exige QAacotada. Probabilidad **cualitativa estimada de persistencia sin mitigación**,no estadística de fallos. Esperas de proveedor/docente no son horas de implementación ni tienenSLAacreditado.

| ID/alternativa | Severidad/probabilidad | Impacto | Mitigación/responsable | Reconsiderar si… |
|---|---|---|---|---|
| R01Todas:instalación/estado/identidad |Crítica/Alta |PG03/06yunidadsensor no completas |Daniel+docente antes14:dispositivo acreditado oalcance canal/sitio explícito;NULLvisible |Rechazaalcance yno hayfuente individual:ningunaaprobada,backupno resuelveigualausencia |
| R02Todas:críticos/alertas |Alta/Alta |MG04/05no cubiertas estrictas |Kembly+docente:regla válidaQA/unidad/duración,emisión actualreplay autorizada ofuente histórica oficial |Exige alertashistóricas conzona sinfuente;no reinterpretar incidentes ni inventarmensajes |
| R03Todas:Mongo nativo/recursos |Alta/Media |BSON,CRUD,pipelines,500k/backup no ejecutados |José+Kembly:entornoaisladoautorizado,lotes/índices/count/restore,estimado2–4hconfiguración incluidoenplan |17octsinentorno ysinplan cabe fecha23;no migrarciudad porproblema de motor |
| R04Madrid:unidadesmeteo |Alta/Media |Temperatura/humedad/correlaciones provisionales |José:diccionariooficial ytests2–4h,excluirunidadno acreditada de análisis |14octsinunidad ydossourcescoherentes dependen deella;usar aire+tráfico ocomplemento aprobado |
| R05Madrid:historia/operadores |Alta/Alta |PG04/07/zonasparciales |José+Daniel:AnexoI/códigos/vigencias/cargodocumentado,inventarioindependiente4–6hactivo+espera |Docenteexige instalación/estado poranalizador sinfuente;no solucionableporlimpieza |
| R06Madrid:espacial |Media/Alta |14722NO2sincolocalización;76/240puntos tráfico≤1km |José:declarar13sitios/NULL,pérdidas yradioexploratorio;cartografíaoficial,4–6hGIS |Requiere todaslaszonas/mapeoperfecto,no admitepérdidas yno haycomplemento |
| R07Madrid:duración/vmed |Alta/Media |Intensidad no conteo,1–30min;vmedvaría portipo |Daniel+José:inicio/fin,solapes,pesos/cobertura/QApor tipo,2–4h |No haycampo válido paraKPIexacto;fuenteextra/alcance,no sumar tasascomoautos |
| R08Madrid:acceso/versiones |Media/Media |URLs móviles;403antiguo,no actualenZIPauditado |José:snapshotsSHA/CRClocales;actualizaciónoficial solo autorizada |Corrupciónirrecuperable +recursooficialinaccesible afecta2fuentes/mínimos |
| R09Madrid:energíahoraria/CO2/recorridos |Crítica/Alta siKPIsestrictos |Mensual nohoraria,concentración/tiemposausentes |Fernanda+docenteacordaralcance;Josébuscarcomplementolocal4–8h sinhallazgo garantizado |TodosKPIs estrictos yno complementos aceptados;no aprobarpleno pornota63,67 |
| R10NYC:DOTclaves |Alta/Alta |4767grupos/9534filas(11,20%raw)fuera del join conservador |Daniel:identidadcontador/carril o cuarentena aprobada,8–16h+esperaproveedor |14octsinclave/alcance yse exige contadorfísico,riesgo noaceptable para23 |
| R11NYC:exposición/CRS/EPA |Alta/Alta |Campañasdiscontinuas,solo3boroughsEPA,CRSno confirmado |José:exposicióncampaña,CRSoficial y311fechas comunes,4–8h |Exige continuidad/5boroughs/comparación espacialfina sinfuenteadicional |
| R12NYC:mínimos/interanualidad |Alta/Media-Alta |236200locales<500k,1Msolo potencialraw |José+Kembly:IDsdistintos/QA/descargas posteriores autorizadas,6–12h+red |20octno cumplevolumen útil ynoadquisiciónviable;no respaldo listo |
| R13Londres:licenciaLAQN |Crítica/Media-Alta |Usoeducativo plausible,exportaciónpúblicano acreditada |Fernanda+José:permiso/alcance,rawprivado,2–6h+espera |Publicación/uso operativoobligatorio incompatible opermisodenegado |
| R14Londres:clockLCL |Alta/Media-Alta |100%timestampno sincronía;Pearson cambia±1h |José:documentarGMT/BST/DSToficial ytests4–8h;seriesseparadas hasta entonces |17octsinclock ycorrelaciónhoraexacta obligatoria |
| R15Londres:geografíaLCL |Crítica/Alta |0%hogares localizados,energíazonafina bloqueada |Docente+equipo:cohorte-ciudad aceptada ofuente real independiente;no GISfake |Energíaborough estricta sincomplemento,no migrarpara resolverhorarioa costa dezona |
| R16Londres:movilidad/incidentes/panel |Alta/Media-Alta |DfT100filas,TfLno auditado,panel108–119 |José+Kembly:auditarTfL/díasDfT,panelcomparable6–10h |23octsinMG08/movilidad/aprobación,no20consultas completas |
| R17Todas:usuarios/personas |Media/Alta |Tablausuariosvacía,responsableindividualausente |Equipo:cuentasrealesconsentidas/cargodocumentado1–2h;confirmarNULL |Exigenciafuenteexterna no disponible;no inventar identidades |
| R18Todas:Sprint2 |Alta/Media |HDFS/Spark/UIno ejecutados,volumen no distribución |Equipo:asignaciónposterior,panelinteranual ybenchmark/explain/particiones |25novsin1Mprocesadoni integración,nocumplimiento;noPython=Spark |

## Madrid: resolubilidad manteniendo núcleo

Unidades meteo se cierran con documentación/validación sin cambiar fuente de lecturas; si no se acreditan, excluir esas variables del análisis científico. Co-localización parcial se resuelve por alcance13sitios y pérdidas declaradas, no fabricando matches; cartografía oficial puede añadir distritos. Historia de sitios tiene altas/bajas/recodificaciones documentadas, pero **no acredita instalación/estado individual**; esos campos necesitan otra fuente o decisión docente. Se puede conservar el núcleo bajo aceptación expresa, no declarar vigencia histórica completa tras unjoin.

## NYC: calendario

Cuarentena deja75572conteos/112070hechos conEPA:suficienteSQL pero no identidadDOTresuelta. Riesgo aceptable solo con alcanceaprobado y ampliaciónMongo/Spark comprobada. RespuestaDOT sinSLA **no es aceptable como dependencia crítica obligatoria de23oct**. Campaña no representa continuidad de todo elborough;controlarexposición, no ausencia=falla.

## Londres: implementación académica válida condicionada

Demo educativa privada puede ser compatible conLAQN,pero no es permiso general de redistribución. Series de energía yambiente separadas son posibles;joinhourly ygeografía tienen condiciones independientes. Clockconfirmado no crea boroughdehogares. Respaldo válido solo si docente/equipo aceptan cohorte-ciudad,derechos yfuentescomplementarias;no todos losKPIsestrictos.

Revisión en14/17/20/23oct;responsable registra evidencia de mitigación/aceptación. Un plan no cierra riesgo. No tareas remotas,descargasnuevas niFase5ejecutadas ahora.
''')
    write('04_implementation_feasibility.md','''
# Fase 4 — Brechas y viabilidad del primer avance

**Estimaciones, no ejecución.** Hitos14/17/20/23/28oct2026 dePp4–5,no rúbrica docente independiente. Entrega25novsí consta enE. Supuesto de capacidad:desde10hasta23oct,4integrantes×2horasproductivas/día≈112horas-persona brutas;80–96útiles al reservar coordinación. Disponibilidad real no confirmada. Esperas de proveedor/docente no acotadas y excluidas de bandas activas.

## Esfuerzo incremental estimado

| Trabajo restante | Madrid | NYC | Londres | Dependencia/complejidad |
|---|---:|---:|---:|---|
| Contrato,metadatos,limpieza,modelado compartido |10–16h |20–34h |16–28h |Madridlimpieza/integraciónmedia;NYCalta porconflictos/exposición;LCLlimpiezamedia ygeografía no resoluble |
| SQL Daniel:3FN/FK/index/consultas/vistas/funciones/tests |12–18h |14–22h |12–20h |Contrato,organismos,instalación/estadoaprobados,inventarioindependiente |
| Mongo Kembly:BSON/CRUD/consultas/pipelines/índices |16–24h |18–28h |18–28h |Entornoautorizado,IDs/fechas/documentos/reglas alertas |
| ETL/lotes/conteos/backup+restore José |8–14h |10–18h |10–16h |Modelosaprobados/recursos;NYCadquisiciónextra,LCLotrosmeses |
| Informe,revisióncruzada,demo Fernanda+todos |8–12h |10–16h |8–12h |Resultados auténticos/modelos/matriz,20consultas |
| **Total horas-persona** |**54–84h** |**72–118h** |**64–104h** |No tiempo transcurrido ni benchmark;no esperaexterna niSprint2/complementostodosKPIs |

Las filas de brechas siguientes son un desglose orientativo, **no sumarlas otra vez** al total. Madrid cabe mejor en80–96hútiles si las condiciones se cierran14oct;NYC/Londres pueden excedercapacidad ydependen deesperas. Ninguna banda garantiza20/20.

Medido anteriormente:picoRSSoffline948904KiB,42tests,conteos/planesSQLguardados. **No se midió tiempo de implementación/cargaMongo/backups oinfraestructura remota.** PostgreSQL de prueba1GB/CPU1no acredita Composeestático512MiB/0,25CPU ni configuración efectivaCoolify. Capacidad/índices/disco/restore deben probarse después, no extrapolar.

## Clasificación de pendientes

C1=Datos reales disponibles,transformación pendiente;C2=Datos derivados de observaciones;C3=Datos sintéticos necesarios;C4=Fuente complementaria necesaria;C5=Decisión de modelado pendiente;C6=Confirmación del profesor necesaria;C7=Bloqueo técnico. Varias categorías pueden coexistir. **Ningún requisito tiene demostrada necesidad inevitable deC3**:NULL/fuente/alcanceaprobado preceden a inventar datos.

## PostgreSQL: de2/10verificadas a10/10funcionales

RutaA:inventario histórico real de dispositivos con instalación/estado/operador. RutaB:docente acepta canales/sitios,actividad/alta como consultas alternativas **explícitamente diferenciadas**. Bno cambiaalta de sitio a instalación real. SinA/B PG03/06permanecenNO_CUMPLEaunque la consulta vacíaejecute. No existe limpieza que garantice20atributos ausentes.

| Consulta | Pendiente y particularidades por ciudad | Clase | Horas activas estimadas / dependencia | Prueba de aceptación posterior |
|---|---|---|---|---|
| PG01tipo |Categorías reales;aceptar canal. NYCsoloEPA,LondresLAQN,no campañas/hogares |C1,C5,C6 |1–2;contrato |COUNTDISTINCTvs catálogo/version,identidadsemántica |
| PG02ubicación |Madridcartografía/vigencia;EPAboro/CRSDOT;LAQNautoridad,LCLNULL |C1,C4,C5,C6 |1–3SQL+4–6GISMadrid;fuenteCRS |FKsinhuérfanos,zonaconfuente,UNKNOWNvisible,no tarifa=zona |
| PG03estado |Administrativo individualausente enlas3;inventarioA oactividadenventanaB aceptada |C4,C2,C6 |2–4+esperaindefinida;inventario/ventana |Fecha/estadoacreditados ocriterioaceptado;NULL≠inactivo,ausenciacampaña≠falla |
| PG04organismo |Madridgestor/vínculo;NYCoperadorEPA;LAQNowner/managersitio,no persona individual |C1,C4,C5,C6 |2–4+fuente;granularidad |Relación/cargo con evidencia,vigencia ydesconocidos visibles |
| PG05rankingubicación |Catálogoindependiente,no conteo de lecturascomo sensores |C1,C5,C6 |1–2;PG01/02 |Ranking/empates correctos,conteo no crecepor nuevas lecturas |
| PG06instaladosaño |Todas instalaciónausente;alta/apertura/primera lectura separadas |C4,C5,C6 |1–2query+espera fuente/aceptación |SoloDATEverificada oconsultaaltadesitio aprobada yrotulada,no fechasinventadas |
| PG07sinactividad |Catálogo independienteMadrid/LAQN;NYCEPArequiereexterno;universo/ventana justificados |C1,C4,C2,C5 |2–4+inventario;PG03 |NOTEXISTSsobrecatálogoindependiente,no0tautológico;sinmuestra≠falla |
| PG08zonas |CTE/rankfuncional;zona/coberturaMadrid,boroughEPA,autoridadLAQN |C1,C2,C5,C6 |1–2;PG02/05 |Conteos yDENSE_RANKempatesvs referencia,pérdidas/exposición |
| PG09vista |Patrón nativo ya probado;adaptar al contrato final |C1,C5 |0,5–1+tests;modelo |VIEWvs base;materializada/refreshaparte |
| PG10función |Patrón probado;parámetros fecha/zona útiles |C1,C5 |0,5–1+tests;modelo |Funciónnativa,inputsNULL/rango/vacío,resultadoesperado |

Cincoentidades:usuariosdel equipo consentidos,organismogestor/cargodocumentado,ubicación/categoría/sensor segúnalcance;C1/C4/C5/C6. Incluido12–18hSQLMadrid,conDiagrama3FN/PK/FK/índices/planes/materializada/particiónjustificados. Maestrospequeños+hechosreales, no100ksensoresniusuarios. PG09/10prueba03no equivale esquema final aprobado.

## MongoDB: de factibilidad a consultas nativas

Prerequisitos C1/C5/C7:entornoaisladoautorizado/versionacordada,JSON/BSONdesdeQAreal,IDestable ylocation/channel/catalog_version compartidos. InstanteUTCsolo cuando acreditado,reloj local explícito;índices únicos/lotes e idempotencia. Capturar conteosinserted/rejected/unique ycountDocuments,checksum devalores/resultado vs original. No ocultarconflictos agregando elvalor aPK.

| Consulta/operación | Qué falta y diferencias | Clase | Horas activas estimadas / dependencia | Evidencia requerida |
|---|---|---|---|---|
| MG01sensor |FiltrocanalrealMadrid/EPA/LAQN,nohogar/campaña |C1,C5,C6 |0,5–1;colección/catálogo |findnativo,IDs/orden/valoresvs raw |
| MG02rango |FechasBSON,clock,bordes[desde,hasta),H24/DST |C1,C5 |1–2;contratotiempo |TestsUTC/NULL/fronteras,conteosvs referencia |
| MG03extremos |QAporvariable/unidad;retenerextremos/nulos |C1,C5 |0,5–1;QA |min/maxnativos,notNULL=0,IQRno implicaerróneo |
| MG04críticos |Reglaválidaunidad/duración/QAaprobada,noIQRcrítico |C2,C5,C6 |2–4+espera aprobación |rule_version/inputs/severidad/bordes;eventoderivednoconfirmado,umbralno elegido parafabricarcaso |
| MG05alertaszona |Sinfuentehistórica;fuenteoficial oemisiónactual/replayaprobado |C4,C2,C5,C6 |2–4+busqueda4–8nogarantizada |emitted_atactual/observed_athistórico,zona real,prueba de emisión,no vacíocumple |
| MG06zonas |Promedioporunidad,Madridzonaacreditada,EPAborough,LAQNautoridad,noLCLfino |C1,C2,C4,C5,C6 |1–2;PG02/time |$groupvs Python,pesos,cobertura/NULLdeclarados |
| MG07tipo |Categoría/variable/unidad,nomediaheterogénea |C1,C2,C5 |0,5–1;catálogo |Resultadosporclase/unidadvs original |
| MG08incidentes |Madrid14388expedientes/2NULL;NYCsolicitudaceptadaoNYPD;LondresTfLauditar |C1,C4,C5,C6 |Madrid1–2;otras3–6+adquisición |UnaIDporincidente,detallepersona separado,sinincident.sensor_idinventado,categoríaUNKNOWN |
| MG09aggregation |Diseño existe,no pipeline ejecutado |C1,C5,C7 |1–2;colección/índice |Aggregate/explain nativos/etapas/saliday referencia |
| MG10filtros |ANDcanal/fecha/valor/QA,proyección/orden |C1,C5 |0,5–1;MG01/02/03 |Intersecciónfiltros/BSONcorrecto/explain |
| CRUD/index/schema/≥500k |Todos pendientes;alteración solo copias desechables |C1,C5,C7 |Incluido16–24hMongoMadrid |insertOne/Many,find/findOne,updateOne/Many,deleteOne;variabilidad,idempotencia,índices,≥500kúnicosnoatributos |

## Otros requisitos pendientes

- **Volúmenes:**100kSQLnativoactualC1/C5;500kMongoMadrid/LondresdatoslocalesC1/C7,NYCadquisiciónrealAPI C1/C4/C7;1MSparkMadridnormalizaciónanualC1/C5,LondresuniquehistóricoC1,NYCdescarga/QA C1/C4,ejecucióndistribuidatodasC7.
- **Fuentes administrativas/cartografía/CRS/reloj:**C4/C5/C6,dictamenunidadesmeteoMadrid,CRSDOT,relojLCL ycatálogoindependiente;nombre decolumna/bbox no acreditaCRS.
- **CO2/recorridos/energía horaria/alertas históricas:**C4/C6;búsqueda inicial4–8h sin garantía dehallazgo compatible,fuera deltotal si alcance completo adicional. CO/CO2e no concentración;no energía mensual dividida porhoras. EnergíaLCLporzonafinaC4/C6,no coordenadasficticias.
- **Usuarios/responsable:**C1/C5si cuentasconsentidas/cargodocumentado;vínculogestorsensor C4/C6. Hasta4cuentasdemoopcionales serían synthetic solo autorizadas,namespace/demo@example.invalid,0generadas;noC3necesidad ni volumen.
- **HDFS/batch/Spark/UI:**C1/C2/C5/C7yKPIfaltantesC4/C6;fuera deltotalSprint1,asignarSprint2 yprobar1M,distribución,comparaciónanual y4gráficosunoSparkreal. No simplemente copiararchivo/Python.

## Fechas, dependencias y puertas por alternativa

Ruta crítica: **respuesta docente+aprobaciónfuentes/IDs →contrato14 →cargainicial17 →QA/conteos/backups20 →consultassemánticas/CRUD/planes23 →pruebacruzada24 →informe25 →freeze26/demo27 →avance28**. No dependenciasexternas cotizadascomo«2h». Daniel/Kemblypueden trabajar enparalelo enborradores,no cerrar atributos poranticipado.

| Hito | Madrid | NYC | Londres |
|---|---|---|---|
|14contrato |Riesgomoderado bajoaceptacióncanales/faltantes;cerrarmeteo/zonas |Alto:DOTidentidad/CRS,campañas yvolumen |Alto:permisos/reloj/geografíacohorte/TfL |
|17primera carga |Factibleestimada,reutilizaciónCSVprueba;BSONporvalidar |SQLfactible,Mongorequiereadquisición adicional |SQLfactible,LCLotrosmeses/clockexplícito,sinzonafalsa |
|20mínimos/respaldos |Datos suficientes,recursos/restauraciónno probados |Alto:menos500klocales;únicos/versión/adquisición |Volumenamplio,index/QA/permisos aúnpendientes |
|23cierre técnico |Moderado siPG03/06yMG04/05resueltos,si noNO20/20 |Alto si proveedorDOT/adquisiciónen ruta crítica |Alto porTfL/permisos/clock/alcancedocente |
|28primeravance |Viablecondicionado,doc/revisión8–12hprevistas,nocertificación |Condicionadoconriesgoalto yposibleexceso118h |Condicionadoconriesgoalto/esperaexterna |

Después17evitar migrar núcleo completo;después20cambio solo porbloqueoirreversible decididoequipo/docente yplanrevisado. Si23faltanconsultas,documentarNO_CUMPLE/PARCIAL,no«listo»niresultadosficticios. **Noesquemas/cargas/remotos/Fase5implementados enestafase.**
''')
    write('04_team_decisions.md','''
# Fase 4 — Decisiones humanas pendientes

Lista corta según P pp.1–5. Los cuatro integrantes deben aprobar fuentes y claves; **no se atribuye una firma ni respuesta docente**. Fecha objetivo:12–14 de octubre de2026.

| Responsable | Decisión concreta | Evidencia de aprobación esperada |
|---|---|---|
| **José** |Ratificar Madrid condicionado y sus cinco fuentes; reutilizar snapshots y priorizar complementos acotados, sin descargas automáticas |Ficha de versiones, ventanas y QA; plan de unidades/cartografía/recursos, conteos y respaldo/restauración posteriores autorizados |
| **Daniel** |Acordar canal ≠ dispositivo, alta de sitio ≠ instalación, actividad ≠ estado y organismo ≠ publicador; catálogo independiente para PG07 |Contrato y modelo3FN propuesto; PG03/04/06/07 con ruta de fuente real o alcance docente; NULL visible, sin maestros inflados |
| **Kembly** |Acordar documento único por intervalo, variables juntas, IDs compartidos y reloj/BSON; eventos, alertas y expedientes separados |Plan de ≥500k documentos reales, CRUD sobre copias, pipelines nativos e índices; MG04/05 no cumplen por colección vacía |
| **Fernanda** |Obtener respuesta docente sobre fecha, rúbrica, entidades, alertas, KPIs,100MB y dos repositorios; consolidar acta |Matriz requisito–evidencia–estado–alcance aprobado, firmas, fechas, citas y privacidad/atribución; no solo diagrama |
| **Los cuatro** |Ratificar selección provisional, disponibilidad horaria y reserva Londres condicionada; fecha límite de cambio temprano:14oct |Acta con participantes, condiciones y disparadores; sin migración automática tardía ni Fase5 autorizada implícitamente |

## Confirmaciones cerradas para el profesor

1. ¿Fecha y rúbrica del avance del28oct, con los20casos? E fija25nov, no confirma P28oct;14/17/20/23 son hitos internos.
2. ¿Canal/sitio aceptado como sensor? ¿PG03 actividad en ventana y PG06 alta de sitio son alternativas explícitas, o se exigen atributos administrativos de dispositivos reales? Sin fuente/aceptación quedan NO_CUMPLE; primera observación no es instalación.
3. ¿Usuarios reales consentidos del equipo y organismo gestor/cargo documentado satisfacen los atributos? ¿Qué campos permiten NULL y qué evidencia de relación se espera? No inventar personas.
4. ¿Eventos derivados con regla válida y alertas actuales de replay con emitted_at real satisfacen MG04/05? Si exige mensajes históricos oficiales por zona, se necesita una fuente aún no acreditada.
5. ¿Todos los21KPIs estrictos o un caso IoT con ausencias visibles? Madrid tiene energía mensual, no horaria, y carece de CO2/recorridos; LCL aporta cohorte, no energía por borough. Mantener cuatro gráficos, incluido uno realmente generado por Spark.
6. ¿100k hechos relacionales y500k intervalos multivariables únicos cuentan para los mínimos? Dos fuentes municipales distintas(E6) frente a recomendación de dos repositorios(E23), ¿hay requisito adicional? ¿100MB globales, comprimidos o lógicos? Reutilizar hechos por roles de motor no crea fuentes ni registros físicos nuevos.

## Acta por completar, no respuesta simulada

- Estado: **RECOMENDACIÓN TÉCNICA / SELECCIÓN PROVISIONAL CONDICIONADA**.
- Preferido: **Madrid,63,665/100** según el método de Fase4, no una nota académica.
- Firmas y fechas de José,Daniel,Kembly,Fernanda: **pendientes**.
- Respuesta docente, fuentes, permisos y alcance de excepciones: **pendientes**.
- Autorización para Fase5: **no concedida en esta fase**.
- Si no cierran puertas: registrar rechazo/suspensión/revisión, no afirmar20/20.

No autoriza bases remotas, cambios Coolify/Tailscale, cargas de producción, commit/push/merge ni síntesis masiva.
''')
    # Numeric/code shorthand is normalized without touching paths, URLs or code blocks.
    for name in ['04_final_comparison.md','04_selected_dataset.md','04_decision_evidence.md',
                 '04_open_risks.md','04_implementation_feasibility.md','04_team_decisions.md']:
        text=(ROOT/name).read_text(); lines=[];code=False
        for line in text.splitlines():
            if line.startswith('```'):code=not code;lines.append(line);continue
            if not code:
                chunks=re.split(r'(`[^`]*`|https?://\S+)',line)
                for i in range(0,len(chunks),2): chunks[i]=prose(chunks[i])
                line=''.join(chunks)
            lines.append(line)
        (ROOT/name).write_text('\n'.join(lines)+'\n')
    print('Six Markdown deliverables generated; 04_scores.csv produced by phase4_evaluate.py.')


if __name__=='__main__':main()
