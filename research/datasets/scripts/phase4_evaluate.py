"""Read-only evidence review and reproducible decision rubric, not a dataset loader."""
import csv
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/phase4'
CITIES = ['Madrid', 'NYC', 'London']
LABELS = ['Compatibilidad con consultas obligatorias', 'Integración con las cuatro tecnologías',
          'Cobertura de indicadores del dashboard', 'Calidad, procedencia y trazabilidad',
          'Volumen y escalabilidad', 'Compatibilidad espacial y temporal',
          'Facilidad de descarga y preparación', 'Riesgo y esfuerzo de implementación']
WEIGHTS = [20, 15, 15, 10, 10, 10, 10, 10]
CREDIT = {'CUMPLE_VERIFICADO': 1, 'FACTIBLE_NO_EJECUTADO': .75,
          'PARCIAL': .25, 'NO_CUMPLE': 0, 'NO_VERIFICADO': 0}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(1 << 20): h.update(chunk)
    return h.hexdigest()


def get(name): return json.loads((ROOT / name).read_text())
def csvrows(name): return list(csv.DictReader((ROOT / name).open()))
def save(name, obj): (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def verify():
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    for manifest in ['results/phase3/inputs_manifest.csv', 'results/phase3/outputs_manifest.csv']:
        rows = csvrows(manifest)
        for row in rows:
            p = ROOT / row['path']
            assert p.stat().st_size == int(row['bytes']) and sha(p) == row['sha256'], row['path']
        checks.append({'manifest': manifest, 'verified_files': len(rows)})
    pdfs = [('E', 'Proyectos_CE3101_Enunciado_Proyecto_II_Semestre_2026.pdf'),
            ('P', 'Plan_de_trabajo.pdf'), ('I', 'Informe_Datasets_SmartCity_Jose.pdf')]
    for code, name in pdfs:
        p = Path('/home/jp/Descargas') / name
        text = subprocess.check_output(['pdftotext', '-layout', str(p), '-'], text=True)
        (OUT / (code + '_original.txt')).write_text(text)
        checks.append({'document': code, 'path': str(p), 'sha256': sha(p),
                       'pages': len(text.split('\f')) - 1})
    sources = csvrows('02_download_manifest.csv')
    review=[]
    for path in sorted(ROOT.glob('0[0123]_*.csv')):
        rows=csvrows(path.name)
        review.append({'path':path.name,'rows':len(rows),'sha256':sha(path)})
    save('reviewed_csv_artifacts.json',review)
    api_counts=[]
    for ident, expected in [('311-count-2023-01-01',242173),('311-count-2023-07-01',289330)]:
        r=next(r for r in sources if r['id']==ident and r['path'])
        assert sha(ROOT/r['path'])==r['sha256']
        body=json.loads((ROOT/r['path']).read_text())[0]
        assert int(body['n'])==int(body['unique_ids'])==expected
        api_counts.append({'id':ident,'path':r['path'],'unique_ids':expected,'sha256':r['sha256']})
    assert sum(r['unique_ids'] for r in api_counts)==531503
    save('nyc_311_api_count_evidence.json',api_counts)
    selected = [r for r in sources if r['source'].startswith('MAD-') and r['path'] and
                r['id'] in ['MAD-AIR-file', 'MAD-METEO-file', 'MAD-TRAFFIC-Jan2025',
                            'MAD-ENERGY-file', 'MAD-CRASH-file']]
    for row in selected: assert sha(ROOT / row['path']) == row['sha256']
    with (OUT / 'selected_source_snapshots.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(sources[0])); w.writeheader(); w.writerows(selected)
    save('selected_storage_evidence.json',{'original_data_files':len(selected),
        'original_snapshot_bytes':sum(int(r['bytes_downloaded']) for r in selected),
        'basis':'five complete original data responses, each counted once; ZIP traffic compressed',
        'not_database_storage_or_network_budget':True,'100MB_academic_interpretation_pending':True})
    prepared = get('results/phase3/prepared_data.json')
    execution = get('results/phase3/postgres_execution.json')
    summary = get('results/phase3/summary.json')
    validation = get('results/phase3/validation.json')
    matrix = csvrows('03_compliance_matrix.csv')
    assert execution['native_executed'] and execution['container_removed']
    assert execution['anonymous_volumes_removed']
    for city, rows in zip(CITIES, [993374, 112070, 354637]):
        assert prepared[city]['eligible_unique_readings'] == execution['cities'][city]['loaded_readings'] == rows
        for technology in ['PostgreSQL', 'MongoDB', 'Spark', 'Dashboard']:
            counts = {}
            for r in matrix:
                if r['alternative'] == city and r['technology'] == technology:
                    k = r['compliance_status']; counts[k] = counts.get(k, 0) + 1
            assert counts == summary['coverage'][city][technology]
        assert not prepared[city]['native_mongodb_executed']
        for k in ['PG09', 'PG10']: assert execution['cities'][city]['queries'][k]['equals_python_reference']
    assert validation['recounted_primary_raw_rows'] == {'Madrid': 13351700, 'NYC': 247526, 'London': 4007440}
    madrid = get('results/Madrid-integration.json')
    assert madrid['eligible_air_NO2_rows'] == 33821 and madrid['air_row_spatiotemporal_matched'] == 19087
    assert validation['Madrid']['join']['matched'] == 19087
    nyc = get('results/NYC-integration.json')
    assert nyc['DOT_EPA']['matched_groups'] == 146 and nyc['DOT_311']['matched_groups'] == 11
    assert nyc['DOT_EPA']['left_groups'] == nyc['DOT_311']['left_groups'] == 322
    dot = get('results/phase3/dot_conflicts.json')
    assert dot['groups'] == 4767 and dot['conflicting_rows'] == 9534 and not dot['correct_physical_key_found']
    assert validation['London']['expanded']['unique_keys'] == 3997252
    assert validation['London']['expanded']['conflicting_extra_values'] == 0
    assert validation['London']['join']['coverage']['matched_groups'] == 1488
    tests = []
    for path in ['results/phase3/legacy_tests.xml', 'results/phase3/tests.xml']:
        for suite in ET.parse(ROOT / path).getroot().iter('testsuite'):
            assert all(int(suite.attrib.get(k, 0)) == 0 for k in ['failures', 'errors', 'skipped'])
            tests.append({'path': path, 'tests': int(suite.attrib['tests'])})
    assert sum(t['tests'] for t in tests) == 42
    save('evidence_checks.json', {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'hash_checks': checks, 'previous_tests': tests, 'counts_and_matrix_agree': True,
        'originals_unchanged': True, 'native_mongodb_executed': False, 'audit_or_load_repeated': False,
        'network_requests': 0, 'all_checks_passed': True})
    return matrix, summary


def score(matrix, summary):
    details = []

    def add(criterion, name, weight, ratings, rationale, evidence, missing, condition):
        for city, rating, reason in zip(CITIES, ratings, rationale):
            assert 0 <= rating <= 4
            details.append({'alternative': city, 'criterion_id': criterion, 'subcriterion': name,
                'subweight': weight, 'rating_0_4': round(rating, 8), 'points': round(weight * rating / 4, 8),
                'rationale': reason, 'evidence': evidence, 'missing_evidence': missing,
                'rescore_condition': condition})

    same = lambda text: [text] * 3
    matrix_ref = '03_compliance_matrix.csv; results/phase3/summary.json'
    add(1, 'SQL estricto ejecutado (4 × verificadas/10)', 4, [.8]*3,
        same('2/10 verificadas: PG09/10; diagnóstico NULL no cumplimiento'), matrix_ref,
        'Inventario físico, estado, instalación, organismos completos', 'Reejecución semántica nativa tras cerrar fuente/aceptación')
    add(1, 'SQL funcional en alcance lógico (4 × funcionales/10)', 4, [2.4]*3,
        same('6/10 funcionales condicionadas, no seis estrictamente cumplidas'), matrix_ref,
        'Aceptación docente del canal como unidad y catálogos independientes', 'Aceptar alcance y comprobar PG03/04/06/07 sin inventar atributos')
    add(1, 'MongoDB soporte de datos (4 × media de créditos)', 8,
        [4*sum(CREDIT[r['compliance_status']] for r in matrix if r['alternative']==c and r['technology']=='MongoDB')/10 for c in CITIES],
        ['8 factibles +1 parcial +1 no cumple', '7 factibles +2 parciales +1 no cumple', '7 factibles +1 parcial +1 no cumple +1 no verificado'],
        matrix_ref, 'Política de críticos, emisiones reales, incidentes según ciudad', 'Fuente y semántica acreditadas; no puntuar una alerta vacía')
    add(1, 'MongoDB nativo ejecutado (4 × verificadas/10)', 4, [0]*3,
        same('0/10 nativas; Python no Aggregation Framework'), '03_tests_report.md; scripts/phase3_mongo_queries.js',
        'BSON/pipelines/CRUD/índices nativos', 'Evidencia de diez ejecuciones y referencias, en fase autorizada posterior')
    add(2, 'Relacional, IDs e integridad', 4, [4]*3, same('Carga nativa >100k con PK/FK y referencias compartidas de prueba'),
        'results/phase3/postgres_execution.json; tests/test_phase3.py', 'Contrato final no aprobado', 'Revisar si contrato invalida identidades existentes')
    add(2, 'Documentos variables y contrato reutilizable', 4, [2]*3,
        same('JSON preliminar y tipos variables auditados; BSON/ingestión entre motores no probados'),
        'private_results/phase3/*/documents_preview.json; 03_mongodb_matrix.md', 'Ejecución integrada nativa', 'Carga documental e IDs cruzados validados')
    add(2, 'Archivos históricos exportables a HDFS', 3, [3,3,2],
        ['CSV/ZIP/Parquet con hashes locales, sin HDFS ejecutado', 'CSV/JSON/Parquet locales; ampliar ventanas para historia', 'Miembros LCL válidos; LAQN redistribución pendiente'],
        '02_artifact_manifest.csv; 03_spark_future_matrix.md', 'HDFS/batch/distribución y permisos efectivos', 'Ejecutar HDFS y cerrar alcance de exportación')
    spark_credit={'FACTIBLE_NO_EJECUTADO':.6,'PARCIAL':.3,'NO_VERIFICADO':0,'NO_CUMPLE':0,'CUMPLE_VERIFICADO':1}
    add(2, 'Soporte de los diez productos Spark', 4,
        [4*sum(spark_credit[r['compliance_status']] for r in matrix if r['alternative']==c and r['technology']=='Spark')/10 for c in CITIES],
        ['8 factibles,2 parciales; no Spark', '6 factibles,3 parciales,1 no verificado; no Spark', '7 factibles,2 parciales,1 no verificado; no Spark'],
        matrix_ref, 'Join aceptado, panel anual, evento y reporte reales', 'Evidencia distribuida; no confundir potencial con ejecución')
    dashboard_credit={**CREDIT, 'FACTIBLE_NO_EJECUTADO':.75, 'PARCIAL':.4}
    for domain, count, weight in [('Movilidad',5,4),('Ambiente',5,4),('Energía',5,4),('IoT',6,3)]:
        # Dashboard rows preserve original order: five mobility, five environment, five energy, six IoT.
        start={'Movilidad':0,'Ambiente':5,'Energía':10,'IoT':15}[domain]
        ratings=[]; reasons=[]
        for city in CITIES:
            rows=[r for r in matrix if r['alternative']==city and r['technology']=='Dashboard'][start:start+count]
            assert len(rows)==count
            ratings.append(4*sum(dashboard_credit[r['compliance_status']] for r in rows)/count)
            reasons.append('; '.join(r['requirement']+':'+r['compliance_status'] for r in rows))
        add(3, domain+' (media de créditos de KPIs)', weight, ratings, reasons,
            '03_dashboard_coverage.md; 03_compliance_matrix.csv', 'UI y KPI faltantes; proxy no indicador observado',
            'Fuente real/definición aprobada cambia solo KPIs afectados, no UI imaginaria')
    add(4, 'Derechos y procedencia institucional', 2, [4,2,1],
        ['CC BY4.0 municipal comprobada, atribución requerida', 'Términos NYC/EPA conservados, derechos terceros pendientes', 'LCL CC BY, LAQN educativo/restrictivo sin redistribución acreditada'],
        '01_source_risks.md; 02_blockers.md; 02_download_manifest.csv', 'Alcance de publicación NYC/LAQN', 'Permiso/cláusulas compatibles con despliegue previsto')
    add(4, 'Snapshots, hashes y pruebas reproducibles', 2, [4]*3, same('Hash/manifiestos y42 pruebas previas, referencias nativas y Python'),
        'results/phase3/inputs_manifest.csv; outputs_manifest.csv; tests.xml', 'Reproducción sin datos privados distribuibles', 'Fallos de hashes o resultados reducirían crédito')
    add(4, 'Identidad natural y duplicados', 2, [3,1,3],
        ['Sin duplicados en muestra; ZIP tráfico completo no cardinalizado', '4767 conflictos DOT sin clave física; cuarentena9534filas', 'LCL3997252claves,2748extras idénticos y0conflictos; hogares no medidor'],
        'results/phase3/dot_conflicts.json; validation.json; 02_volume_analysis.md', 'Unicidad global tráfico, identidades físicas', 'Claves correctas documentadas y prueba global, no incluir valor en PK')
    add(4, 'Unidades, relojes y diccionarios', 2, [2,3,2],
        ['Aire confirmado; meteo provisional y DST fuera de muestra', 'EPA unidades/UTC confirmados; CRS/clock DOT pendientes', 'NO2 GMT y kWh; LCLGMT/BST sin resolver'],
        'results/phase3/unit_history_checks.json; 03_integration_gaps.md', 'Diccionario meteo/timezone y CRS DOT/LCLclock', 'Fuente técnica oficial y pruebas de bordes')
    add(4, 'QA, nulos, extremos y sesgo declarados', 2, [3]*3,
        same('Flags/nulos/extremos y muestreo cuantificados; no extremos borrados ni representatividad urbana acreditada'),
        '02_quality_metrics.csv; results/*-summary.json; 02_audit_report.md', 'Ratificación, panel estable y representatividad', 'QA fuente/ventana específica, no afirmar calidad de ciudad entera')
    add(5, '100k hechos SQL efectivamente cargados', 3, [4]*3,
        ['993374 conPK/FK', '112070 conPK/FK', '354637 conPK/FK'], 'results/phase3/postgres_execution.json',
        'Carga final y recursos de infraestructura no probados', 'Nuevo contrato reduce válidos bajo100k')
    add(5, '500k documentos reales disponibles localmente', 3, [4,1,4],
        ['674704 intervalos tráfico solos;993374 hechos locales', '236200 locales;531503unique_key311 API no descargados', '3997252claves LCLlocales, ampliar ventana de347314'],
        'results/phase3/prepared_data.json; validation.json; 02_volume_analysis.md', 'Mongo nativo para todas; adquisición extra NYC', 'Contar documentos únicos cargados, no campos ni raw más derivado')
    add(5, '1M registros y crecimiento histórico sin síntesis', 4, [3,1,4],
        ['1795279slotsVaire, ampliación local/DST pendiente; no Spark', '1875154DOTglobalrawpotencial, QA/únicos sin comprobar', '3997252claves locales verificadas; no Spark'],
        'results/MAD-AIR-annual_counts.json; results/phase3/validation.json; 02_volume_analysis.md',
        'Ejecución Spark, panel comparable y recursos', 'Cardinalidad QA y ejecución real >=1M')
    add(6, 'Geografía compartida defendible (no ranking de porcentajes)', 4, [3,2,1],
        ['13sitios co-localizados <1m; radios tráfico solo exploratorios', 'Borough compartido; EPA3boroughs, CRS DOTpendiente', 'Energía sinubicación fina0%; solo contexto ciudad'],
        'results/*-integration.json; 03_integration_gaps.md', 'Vigencia/cartografía/CRS/geografía hogar', 'No casas ficticias; fuente geográfica compatible o alcance aprobado')
    add(6, 'Períodos y relojes comunes', 3, [3,2,1],
        ['Jan/Jul2025 sinDST, aire/meteo2025-2026local; accidente2026nojoinJan2025', 'Campañas2023, UTC EPA;31116días; interanualidad local pendiente', '2013Jan/Julcomún peroGMT/BSTjulio pendiente, cohorte variable'],
        'results/phase3/validation.json; 02_integration_results.md', 'DST/horas endpoint, exposición y años', 'Definición oficial del clock y períodos equivalentes')
    add(6, 'Join medido con denominadores y pérdidas', 3, [3,2,1],
        ['19087/33821 NO2, pérdidas explícitas; no causalidad', '146/322DOT-EPA y11/322DOT-311; muestra y campañas', '1488/1488horas condicionales, no geografía ni sincronía demostradas'],
        'results/*-integration.json; results/phase3/validation.json', 'Ponderación/exposición/cobertura aceptada', 'Revalidar semántica de joins, nunca comparar56%contra100%como nota')
    add(7, 'Datos suficientes ya locales para Sprint1', 3, [4,2,4],
        ['Datos y normalización suficientes, ZIP oficial ya descargado', 'MínimoMongo exige adquisición extra pese aAPIfuncional', 'LCLhistórico suficiente en4miembros locales'],
        '02_download_manifest.csv; results/phase3/prepared_data.json', 'MínimoMongoNYC y catálogos semánticos todas', 'Nueva descarga solo con autorización/presupuesto')
    add(7, 'Adquisición oficial acotada y robustez', 2, [3,2,1],
        ['CSV/ZIP accesibles;403pasado no vigente enrecurso auditado', 'SODA+paginación+EPA rangos; desconexiones/adjuntos404', 'LCLRangeignorado yprefijo, LAQNpor sitio/período'],
        '02_reproduction.md; results/download.log', 'Continuidad de endpoints no garantizada', 'Recurso oficial estable/reproducción desde snapshot')
    add(7, 'Complejidad de formatos y limpieza', 2, [3,2,3],
        ['CSVsemicolon/HV/decimal, scripts disponibles; meteo unidades', 'Campañas/SODA/UTC/métodos/qualifier yLL84padres', 'CSVenergía simple yJSONLAQN; clock/duplicados conocidos'],
        'scripts/readers.py; audit.py; phase3_validate.py', 'QA final y claves específicas', 'Costo de transformación se confirma en implementación, no horas medidas aquí')
    add(7, 'Pipeline offline existente y evidencia de preparación', 3, [4,3,3],
        ['Normalización, joins ypruebaSQL completa, sin descargar más núcleo', 'Pipeline reproduce solo alcance2023/16fechas, no mínimosMongo/Spark', 'Pipeline4CSV/5sitios, no zona niTfL completo'],
        'scripts/phase3_run.py; results/phase3/run.log', 'Carga finalMongo ycontrato', 'Fallo de reproducción invalida crédito correspondiente')
    add(8, 'Dependencias externas bloqueantes (mayor = menor riesgo)', 4, [2,1,1],
        ['Metadatos administrativos/docente ydiccionario, sin cambiar núcleo si acepta límites', 'ClaveDOT requiere proveedor yvolumen extra; retraso no acotado', 'PermisoLAQN/geografíaLCL son bloqueos no solucionables conlimpieza'],
        '03_integration_gaps.md; 03_feasibility_report.md', 'Respuesta de proveedor/docente no obtenida', 'Cerrar bloqueos antes14oct; sin respuesta no garantizar10/10')
    add(8, 'Viabilidad de calendario (juicio de ingeniería)', 4, [3,1,2],
        ['54-84h-persona estimadas Sprint1 bajo aceptación, reutiliza artefactos', '72-118h-persona estimadas más esperaDOT/adquisición', '64-104h-persona estimadas más licencia/timezone/TfL'],
        '04_implementation_feasibility.md (estimación, no benchmark)', 'Disponibilidad horaria real del equipo', 'Medir avance al17oct; si ruta crítica no cabe, replanificar')
    add(8, 'Gobernanza y publicación', 2, [3,2,1],
        ['CC BY núcleo; accidentes minimizar datos personales, faltantes docentes', '311privacidad y términosNYC/EPA sincierre publicación', 'LAQNsinredistribución ysinzonasLCL limita despliegue'],
        '01_source_risks.md; 02_blockers.md', 'Aprobación de equipo yalcance publicación', 'Revisar permisos ydatos personales antesdeexportar')

    with (OUT/'subscores.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(details[0]));writer.writeheader();writer.writerows(details)
    scores=[]; totals={}
    for city in CITIES:
        total=0
        for ident,label,weight in zip(range(1,9),LABELS,WEIGHTS):
            rows=[r for r in details if r['alternative']==city and r['criterion_id']==ident]
            assert sum(r['subweight'] for r in rows)==weight
            points=sum(r['points'] for r in rows);total+=points
            scores.append({'alternative':city,'criterion_id':ident,'criterion':label,'weight':weight,
                'score_points':round(points,4),'subcriteria':'; '.join(f"{r['subcriterion']} [{r['subweight']}]:{r['points']:.4f}" for r in rows),
                'rationale':'; '.join(r['rationale'] for r in rows),'evidence':'; '.join(sorted(set(r['evidence'] for r in rows))),
                'missing_evidence':'; '.join(r['missing_evidence'] for r in rows),
                'rescore_conditions':'; '.join(r['rescore_condition'] for r in rows),
                'score_nature':'judgment_based_on_evidence_not_academic_grade'})
        totals[city]=round(total,4)
        scores.append({'alternative':city,'criterion_id':'TOTAL','criterion':'Total','weight':100,
            'score_points':round(total,4),'subcriteria':'sum(C1..C8)','rationale':'Mismos pesos, criterios y penalizaciones para todas',
            'evidence':'results/phase4/subscores.csv','missing_evidence':'Aprobaciones/ejecuciones pendientes no se presumen',
            'rescore_conditions':'Nueva evidencia y revisión de condiciones excluyentes','score_nature':'judgment_based_on_evidence_not_academic_grade'})
    with (ROOT/'04_scores.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(scores[0]));writer.writeheader();writer.writerows(scores)
    save('scores_summary.json',{'weights':WEIGHTS,'totals':totals,'rubric_source':'I p1; not E grading rubric',
        'query_credits':CREDIT,'dashboard_partial_credit':.4,'spark_feasible_credit':.6,
        'decision':'Madrid preferred conditional core','team_approval':False,'phase5_started':False})
    print(json.dumps(totals,indent=2))


if __name__=='__main__':
    matrix,summary=verify();score(matrix,summary)
