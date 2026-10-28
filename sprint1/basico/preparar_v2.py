"""Prepara aire y tráfico de enero de 2025 sin tocar los paquetes anteriores.

Ejecutar con el Python de research/datasets/.venv. No conecta a bases.
Los accidentes son de 2026: se mantienen separados y sin datos de personas.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
import fcntl
import json
from pathlib import Path
import re
import sqlite3
import sys

PROYECTO = Path(__file__).resolve().parents[2]
DATOS = PROYECTO / 'research/datasets'
sys.path.insert(0, str(DATOS / 'scripts'))
from phase5_contract import base_document, canonical, digest, numeric, payload_hash, stable_id

VERSION = 'madrid-draft-v2'
UMBRAL_DEMO = 2000  # veh/h: ejercicio académico, NO umbral legal ni alarma oficial.
PDF_TRAFICO_SHA = '17562978ce1b7930c6c720db37f055cb3459e30b8cec50d2a671682b215b9de9'


def valor_opcional(texto, unidad, aplicable=True, maximo=None):
    numero = numeric(texto)
    estado = 'valid'
    if not aplicable:
        numero, estado = None, 'not_applicable'
    elif numero is None or numero < 0:
        numero, estado = None, 'missing_or_negative'
    elif maximo is not None and numero > maximo:
        numero, estado = None, 'out_of_range'
    return {'value': numero, 'unit': unidad, 'status': estado,
            'raw_value': texto, 'data_origin': 'observed'}


def documento_trafico(fila, fuente, miembro):
    """Una fila es un intervalo: nunca multiplicar muestras por documentos."""
    if fila['error'] != 'N':
        return None, 'provider_flag'
    if fila['tipo_elem'] not in ('URB', 'M30'):
        return None, 'undocumented_element_type'
    intensidad = numeric(fila['intensidad'])
    muestras = numeric(fila['periodo_integracion'])
    if intensidad is None or intensidad < 0:
        return None, 'invalid_intensity'
    if muestras is None or muestras <= 0 or not muestras.is_integer():
        return None, 'invalid_sample_count'
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', fila['fecha']):
        return None, 'invalid_date_format'
    try:
        fecha = datetime.strptime(fila['fecha'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None, 'invalid_date'
    documento = base_document('MAD-TRAFFIC', fuente['sha256'], fila['id'],
        [fila['id'], fila['tipo_elem']], fecha, 'publisher_label', 'publisher_confirmed_local')
    if documento['time_error']:
        return None, documento['time_error']
    if (fecha.year, fecha.month) != (2025, 1):
        return None, 'outside_january_2025'
    documento.update(measurement_type='MAD-TRAFFIC:intensidad', value=intensidad,
        unit='veh/h', unit_status='verified_dictionary', candidate_unit=None,
        quality_flag='N', interval_minutes=15, integration_sample_count=int(muestras),
        element_type=fila['tipo_elem'], source_key=[fila['id'], fila['fecha'], fila['tipo_elem']],
        measurements={
            'ocupacion': valor_opcional(fila['ocupacion'], 'percent', maximo=100),
            'carga': valor_opcional(fila['carga'], 'index', maximo=100),
            'vmed': valor_opcional(fila['vmed'], 'km/h', fila['tipo_elem'] == 'M30'),
        },
        raw_reference={'path': fuente['path'], 'sha256': fuente['sha256'],
            'member': miembro, 'row': int(fila['raw_row']), 'column': 'intensidad'},
        provenance={'value': 'observed', 'ids': 'derived', 'observed_at': 'derived',
            'traffic_dictionary_sha256': PDF_TRAFICO_SHA})
    return documento, 'accepted'


def cambiar_version(documento):
    """Conservar identidad y valor; registrar cambio de contrato en otro paquete."""
    documento = dict(documento)
    documento.update(schema_version=VERSION, catalog_version=VERSION,
        transformation_version='madrid-normalize-v3')
    documento.setdefault('integration_sample_count', None)
    documento['zone_scope'] = ('current_inventory_not_historically_verified'
                              if documento['zone_id'] is not None else 'unknown')
    documento['payload_hash'] = payload_hash(documento)
    return documento


def leer_incidentes(ruta, fuente):
    """Deduplicar expedientes; nunca exportar sexo, edad, lesiones o dirección."""
    expedientes = {}
    filas = 0
    with ruta.open(encoding='utf-8-sig', newline='') as archivo:
        for numero, fila in enumerate(csv.DictReader(archivo, delimiter=';'), 2):
            filas += 1
            clave = fila['num_expediente'].strip()
            if not clave:
                raise ValueError('Accidente sin expediente: no se puede deduplicar.')
            fecha = datetime.strptime(fila['fecha'], '%d/%m/%Y').date().isoformat()
            codigo = fila['cod_distrito'].strip()
            zona = 'madrid:district:' + str(int(codigo)) if codigo.isdigit() and 1 <= int(codigo) <= 21 else None
            actual = expedientes.setdefault(clave, {'dates': set(), 'zones': set(),
                'categories': set(), 'first_row': numero, 'rows': 0})
            actual['dates'].add(fecha)
            actual['zones'].add(zona)
            actual['categories'].add(fila['tipo_accidente'].strip() or 'sin_categoria')
            actual['rows'] += 1
    salida = []
    for clave, datos in sorted(expedientes.items()):
        if len(datos['dates']) != 1 or len(datos['zones']) != 1 or len(datos['categories']) != 1:
            raise ValueError('Expediente con fecha, zona o categoría contradictoria; revisar original.')
        fecha = next(iter(datos['dates']))
        if not fecha.startswith('2026-'):
            raise ValueError('El snapshot de incidentes no corresponde a 2026.')
        salida.append({'_id': stable_id('incident', 'MAD-CRASH', clave),
            'category': next(iter(datos['categories'])), 'reported_date': fecha,
            'zone_id': next(iter(datos['zones'])), 'source_id': 'MAD-CRASH',
            'source_version': fuente['sha256'], 'data_origin': 'observed',
            'person_fields_removed': True,
            'raw_reference': {'path': fuente['path'], 'sha256': fuente['sha256'],
                'row': datos['first_row'], 'person_rows_deduplicated': datos['rows']}})
    return salida, filas


def verificar_paquete(carpeta):
    informe = json.loads((carpeta / 'preparation.json').read_text())
    for nombre, esperado in informe['code_hashes'].items():
        if digest(PROYECTO / nombre) != esperado:
            raise ValueError('Código de preparación cambiado: usar otra generación: ' + nombre)
    for nombre, esperado in informe['output_hashes'].items():
        if digest(carpeta / nombre) != esperado:
            raise ValueError('Paquete alterado: ' + nombre)
    return informe


def preparar(generacion):
    if not re.fullmatch(r'expanded-v2-[a-zA-Z0-9_-]{1,40}', generacion):
        raise ValueError('La generación debe comenzar con expanded-v2-.')
    # Dependencias de datos solo al preparar, no al importar las funciones simples.
    import pyarrow.parquet as parquet
    from phase5_prepare import sources, metadata, geographic, add_channel, traffic_cache
    from phase5_contract import validate_document
    from unified_expand import hourly_documents, atomic_json
    from unified_synthetic import build_administrative_seed

    carpeta = DATOS / 'private_results' / generacion
    carpeta.mkdir(parents=True, exist_ok=True)
    with (carpeta / 'prepare.lock').open('a') as bloqueo:
        fcntl.flock(bloqueo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (carpeta / 'preparation.json').exists():
            return verificar_paquete(carpeta)
        fuentes = sources()  # Verifica hashes de los seis originales, sin descargarlos.
        # Los catálogos Parquet también deben ser los snapshots históricos exactos.
        for fila in csv.DictReader((DATOS / 'results/phase3/inputs_manifest.csv').open()):
            if fila['path'] in [f'private_results/{s}-META.parquet' for s in ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC')]:
                if digest(DATOS / fila['path']) != fila['sha256']:
                    raise ValueError('Inventario modificado: ' + fila['path'])
        if digest(DATOS / 'raw/sprint1-v2/traffic_dictionary.pdf') != PDF_TRAFICO_SHA:
            raise ValueError('Falta el intérprete de tráfico oficial verificado.')
        filas_fuentes = list(csv.DictReader((DATOS / '02_download_manifest.csv').open()))
        accidente = next(f for f in reversed(filas_fuentes) if f['id'] == 'MAD-CRASH-file' and f['path'] and not f['error'])
        if digest(DATOS / accidente['path']) != accidente['sha256']:
            raise ValueError('Snapshot de accidentes modificado.')
        meta = metadata(fuentes)
        catalogos = {'schema_version': VERSION, 'stations': {}, 'channels': {},
            'zones': {}, 'measurement_types': {}, 'source_versions': {},
            'sources': {s: {'source_id': s, 'name': s, 'publisher': 'Ayuntamiento de Madrid'}
                        for s in ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC')}}
        for clave, fuente in zip(fuentes, ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC') * 2):
            f = fuentes[clave]
            catalogos['source_versions'][f['sha256']] = {'source_version': f['sha256'],
                'source_id': fuente, 'original_path': f['path']}
        for fuente, estaciones in meta.items():
            for codigo in estaciones:
                geographic(fuente, codigo, meta, catalogos)
        cache, sello = traffic_cache(fuentes['MAD-TRAFFIC-Jan2025'])
        conteos = {'MAD-AIR': Counter(), 'MAD-TRAFFIC': Counter()}
        rechazos = Counter()
        eventos = alertas = 0
        ledger = sqlite3.connect(carpeta / 'identities.sqlite')
        try:
            ledger.execute('CREATE TABLE IF NOT EXISTS identities(id TEXT PRIMARY KEY, signature TEXT, natural_key TEXT UNIQUE)')
            ledger.execute('DELETE FROM identities')  # Solo derivados de esta generación sin sellar.
            def documentos():
                for doc, motivo, mes in hourly_documents(fuentes['MAD-AIR-file'], 2025, [1], meta, catalogos):
                    yield doc, motivo, 'MAD-AIR', doc['raw_reference']
                for bloque in parquet.ParquetFile(cache).iter_batches(batch_size=10000):
                    for fila in bloque.to_pylist():
                        doc, motivo = documento_trafico(fila, fuentes['MAD-TRAFFIC-Jan2025'], sello['member'])
                        referencia = {'path': fuentes['MAD-TRAFFIC-Jan2025']['path'],
                            'sha256': fuentes['MAD-TRAFFIC-Jan2025']['sha256'],
                            'member': sello['member'], 'row': int(fila['raw_row'])}
                        if doc:
                            geographic('MAD-TRAFFIC', fila['id'], meta, catalogos)
                            doc['zone_id'] = catalogos['stations'][doc['station_id']]['zone_id']
                            add_channel(doc, [fila['id'], fila['tipo_elem']], catalogos)
                            doc['payload_hash'] = payload_hash(doc)
                        yield doc, motivo, 'MAD-TRAFFIC', referencia
            with (carpeta / 'accepted.extjsonl.partial').open('w') as aceptados, \
                 (carpeta / 'quarantine.extjsonl.partial').open('w') as cuarentena:
                for doc, motivo, fuente, referencia in documentos():
                    conteos[fuente]['selected'] += 1
                    if motivo != 'accepted':
                        conteos[fuente]['quarantined'] += 1
                        rechazos[fuente + ':' + motivo] += 1
                        cuarentena.write(canonical({'source_id': fuente, 'reason': motivo,
                            'raw_reference': referencia}) + '\n')
                        continue
                    validate_document(doc, catalogos)
                    doc = cambiar_version(doc)
                    natural = canonical([doc['channel_id'], doc['observed_at'], doc['timestamp_role']])
                    previo = ledger.execute('SELECT signature FROM identities WHERE id=? OR natural_key=?',
                        (doc['_id'], natural)).fetchone()
                    if previo:
                        if previo[0] != doc['payload_hash']:
                            raise ValueError('Conflicto de identidad: no se publica la generación.')
                        conteos[fuente]['duplicates'] += 1
                        continue
                    ledger.execute('INSERT INTO identities VALUES(?,?,?)', (doc['_id'], doc['payload_hash'], natural))
                    aceptados.write(canonical(doc) + '\n')
                    conteos[fuente]['accepted'] += 1
                    if fuente == 'MAD-TRAFFIC' and doc['value'] > UMBRAL_DEMO:
                        eventos += 1
                        alertas += doc['zone_id'] is not None
                    if sum(c['selected'] for c in conteos.values()) % 100000 == 0:
                        ledger.commit()
                        print('Filas revisadas:', sum(c['selected'] for c in conteos.values()), flush=True)
            ledger.commit()
        finally:
            ledger.close()
        for nombre in ('accepted.extjsonl', 'quarantine.extjsonl'):
            (carpeta / (nombre + '.partial')).replace(carpeta / nombre)
        incidentes, filas_personas = leer_incidentes(DATOS / accidente['path'], accidente)
        with (carpeta / 'incidents.extjsonl').open('w') as archivo:
            for incidente in incidentes:
                archivo.write(canonical(incidente) + '\n')
        atomic_json(carpeta / 'catalogs.json', catalogos)
        admin = build_administrative_seed(catalogos, digest(carpeta / 'catalogs.json'))
        admin['schema_version'] = VERSION
        atomic_json(carpeta / 'administrative_seed.json', admin)
        for c in conteos.values():
            if c['selected'] != c['accepted'] + c['quarantined'] + c['duplicates']:
                raise ValueError('Los conteos no concilian.')
        archivos = ['accepted.extjsonl', 'quarantine.extjsonl', 'incidents.extjsonl',
                    'catalogs.json', 'administrative_seed.json', 'identities.sqlite']
        codigo = ['sprint1/basico/preparar_v2.py', 'research/datasets/scripts/phase5_contract.py',
            'research/datasets/scripts/phase5_prepare.py', 'research/datasets/scripts/unified_expand.py',
            'research/datasets/scripts/unified_synthetic.py']
        informe = {'generation': generacion, 'contract': VERSION, 'scope': 'January 2025; traffic id%20==0',
            'accepted': sum(c['accepted'] for c in conteos.values()),
            'by_source': {s: dict(c) for s, c in conteos.items()}, 'rejection_reasons': dict(rechazos),
            'synthetic_measurements': 0, 'observed_sensor_links': 0,
            'incident_year': 2026, 'incidents': len(incidentes), 'incident_person_rows': filas_personas,
            'incident_categories': dict(Counter(i['category'] for i in incidentes)),
            'demo_rule': {'field': 'intensidad', 'operator': 'gt', 'threshold': UMBRAL_DEMO,
                'unit': 'veh/h', 'official_rule': False, 'version': 'traffic-intensity-demo-v1'},
            'expected_events': eventos, 'expected_alerts_with_zone': alertas,
            'zone_scope': 'current_inventory_not_historically_verified',
            'code_hashes': {n: digest(PROYECTO / n) for n in codigo},
            'source_hashes': {f['path']: f['sha256'] for f in [*fuentes.values(), accidente]},
            'output_hashes': {n: digest(carpeta / n) for n in archivos}}
        atomic_json(carpeta / 'preparation.json', informe)
        return informe


if __name__ == '__main__':
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--generacion', default='expanded-v2-2025-01')
    opciones = argumentos.parse_args()
    informe = preparar(opciones.generacion)
    print(json.dumps({k: informe[k] for k in ('generation', 'accepted', 'by_source', 'incidents')}, indent=2))
