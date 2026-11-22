"""Generación analítica nueva: aire 2025–ago2026 + tráfico v2, sin duplicar enero.

Lee el ZIP y el v2 extraído sin modificarlos. Solo escribe una carpeta NUEVA.
No importa datos administrativos ni originales personales de accidentes.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/datasets/scripts')]
from phase5_contract import (base_document, canonical, digest, hourly_endpoint,
                             numeric, payload_hash, stable_id, validate_document)

CONTRACT = 'smartcity-analytics-v1'


# Qué hace: escribe un JSON nuevo. Si el archivo ya existe, se cae a propósito para no pisarlo.
def seal(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


# Qué hace: aplana el documento al contrato analítico y le pone el hash. En tráfico copia velocidad, ocupación y carga si vienen válidas.
def flatten(doc, catalogs, source_day):
    station = catalogs['stations'][doc['station_id']]
    row = {'_id': doc['measurement_id'], 'channel_id': doc['channel_id'],
           'station_id': doc['station_id'], 'station_name': station.get('name'),
           'sensor_id': None, 'source_id': doc['source_id'],
           'source_version': doc['source_version'], 'measurement_type': doc['measurement_type'],
           'unit': doc['unit'], 'value': doc['value'],
           'observed_at': doc['observed_at']['$date'], 'original_time': doc['original_time'],
           'source_day': source_day, 'source_year': int(source_day[:4]),
           'source_month': int(source_day[5:7]), 'zone_id': doc['zone_id'],
           'latitude': station.get('latitude'), 'longitude': station.get('longitude'),
           'coordinate_crs': station.get('coordinate_crs'),
           'historical_location_verified': False, 'data_origin': 'observed',
           'input_contract': doc['schema_version'], 'input_payload_hash': doc['payload_hash'],
           'schema_version': CONTRACT, 'raw_reference': doc['raw_reference'],
           'element_type': doc.get('element_type'), 'speed_kmh': None,
           'occupancy_percent': None, 'load_index': None, 'demo_event': False}
    if doc['source_id'] == 'MAD-TRAFFIC':
        measurements = doc['measurements']
        for original, target in (('vmed', 'speed_kmh'), ('ocupacion', 'occupancy_percent'),
                                 ('carga', 'load_index')):
            if measurements[original]['status'] == 'valid':
                row[target] = measurements[original]['value']
        row['demo_event'] = doc['value'] > 2000
    row['record_hash'] = hashlib.sha256(canonical(row).encode()).hexdigest()
    return row


# Qué hace: recorre el CSV horario de aire y dice si cada hora se acepta o se va a cuarentena.
def air_documents(stream, sha, catalogs, units):
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'), delimiter=';')
    required = {'PROVINCIA', 'MUNICIPIO', 'ESTACION', 'MAGNITUD', 'PUNTO_MUESTREO', 'ANO', 'MES', 'DIA'}
    required.update(f'{prefix}{hour:02d}' for prefix in ('H', 'V') for hour in range(1, 25))
    if set(reader.fieldnames or []) != required:
        raise ValueError('Unexpected raw air schema')
    for position, row in enumerate(reader, 2):
        day = datetime(int(row['ANO']), int(row['MES']), int(row['DIA'])).date().isoformat()
        key = [row['ESTACION'], row['MAGNITUD'], row['PUNTO_MUESTREO'] or None]
        for hour in range(1, 25):
            doc = base_document('MAD-AIR', sha, row['ESTACION'], key,
                                hourly_endpoint(day, hour), 'hour_end', 'documented_local')
            doc.update(measurement_type='MAD-AIR:' + row['MAGNITUD'],
                       value=numeric(row[f'H{hour:02d}']), unit=units.get(row['MAGNITUD']),
                       unit_status='verified_dictionary', candidate_unit=None,
                       quality_flag=row[f'V{hour:02d}'], source_key=[*key, day, f'H{hour:02d}'],
                       raw_reference={'path': 'raw/MAD-AIR-file.attempt1.bin', 'sha256': sha,
                                      'row': position, 'column': f'H{hour:02d}'},
                       provenance={'value': 'observed', 'observed_at': 'derived', 'ids': 'derived',
                                   'unit': 'derived', 'unit_availability': 'available'})
            if doc['station_id'] not in catalogs['stations']:
                raise ValueError('Air station missing from verified catalog')
            doc['zone_id'] = catalogs['stations'][doc['station_id']]['zone_id']
            reason = 'accepted'
            if doc['time_error']:
                reason = doc['time_error']
            elif doc['quality_flag'] != 'V':
                reason = 'provider_flag'
            elif doc['value'] is None or doc['unit'] is None:
                reason = 'value_or_unit'
            doc['payload_hash'] = payload_hash(doc)
            if reason == 'accepted':
                if doc['channel_id'] not in catalogs['channels']:
                    catalogs['channels'][doc['channel_id']] = {
                        'channel_id': doc['channel_id'], 'station_id': doc['station_id'],
                        'sensor_id': None, 'source_id': 'MAD-AIR', 'source_key': key,
                        'measurement_type': doc['measurement_type'], 'catalog_basis': 'observations'}
                typ = doc['measurement_type']
                if typ not in catalogs['measurement_types']:
                    catalogs['measurement_types'][typ] = {'source_id': 'MAD-AIR',
                        'unit': doc['unit'], 'unit_status': 'verified_dictionary'}
                validate_document(doc, catalogs)
            yield doc, reason, day


# Qué hace: arma la generación nueva (aire del ZIP más tráfico v2, sin repetir el aire de enero) y deja el manifiesto con conteos y hashes.
def prepare(archive_path, v2, output):
    if output.exists():
        raise ValueError('Output must be NEW: existing generations are never overwritten')
    preparation = json.loads((v2 / 'preparation.json').read_text())
    for name in ('accepted.extjsonl', 'catalogs.json'):
        if digest(v2 / name) != preparation['output_hashes'][name]:
            raise ValueError('Changed v2 input: ' + name)
    catalogs = json.loads((v2 / 'catalogs.json').read_text())
    dictionary = ROOT / 'research/datasets/results/phase3/madrid_dictionary_provenance.json'
    units = json.loads(dictionary.read_text())['unit_codes_extracted']
    raw_name = 'raw/MAD-AIR-file.attempt1.bin'
    raw_sha = preparation['source_hashes'][raw_name]
    member = 'research/datasets/' + raw_name
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open(member) as stream:
            h = hashlib.sha256()
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
            if h.hexdigest() != raw_sha:
                raise ValueError('Changed raw air source')
        output.mkdir(parents=True)
        output.chmod(0o700)
        counts, rejects, references = Counter(), Counter(), {}
        with sqlite3.connect(output / 'identities.sqlite') as ledger, \
                (output / 'observations.jsonl.partial').open('x') as accepted, \
                (output / 'quarantine.jsonl').open('x') as quarantine:
            ledger.execute('CREATE TABLE records (id TEXT PRIMARY KEY, channel TEXT NOT NULL, '
                           'time TEXT NOT NULL, hash TEXT NOT NULL, UNIQUE(channel,time))')

            # Qué hace: mete una fila aceptada en el JSONL, en el libro de identidades y en los totales de referencia.
            def emit(doc, day):
                row = flatten(doc, catalogs, day)
                ledger.execute('INSERT INTO records VALUES (?,?,?,?)',
                               (row['_id'], row['channel_id'], row['observed_at'], row['record_hash']))
                accepted.write(canonical(row) + '\n')
                counts[row['source_id'] + ':' + str(row['source_year'])] += 1
                ref = references.setdefault(row['measurement_type'], {'count': 0, 'sum': 0.0,
                    'min': row['value'], 'max': row['value'], 'unit': row['unit']})
                if ref['unit'] != row['unit']:
                    raise ValueError('Inconsistent measurement units')
                ref['count'] += 1
                ref['sum'] += row['value']
                ref['min'] = min(ref['min'], row['value'])
                ref['max'] = max(ref['max'], row['value'])
                if sum(counts.values()) % 100000 == 0:
                    ledger.commit()
                    print('Accepted:', sum(counts.values()), flush=True)

            with archive.open(member) as stream:
                for doc, reason, day in air_documents(stream, raw_sha, catalogs, units):
                    if reason != 'accepted':
                        rejects[str(day[:4]) + ':' + reason] += 1
                        quarantine.write(canonical({'reason': reason, 'raw_reference': doc['raw_reference']}) + '\n')
                        continue
                    emit(doc, day)
            skipped_air = 0
            with (v2 / 'accepted.extjsonl').open() as stream:
                for line in stream:
                    doc = json.loads(line)
                    if doc['source_id'] == 'MAD-AIR':
                        skipped_air += 1
                        continue
                    if doc['source_id'] != 'MAD-TRAFFIC' or doc['schema_version'] != 'madrid-draft-v2':
                        raise ValueError('Unexpected v2 source/contract')
                    if doc['payload_hash'] != payload_hash(doc):
                        raise ValueError('Changed traffic payload')
                    if doc['_id'] != stable_id('measurement', doc['channel_id'],
                                              doc['observed_at']['$date'], doc['timestamp_role']):
                        raise ValueError('Changed traffic identity')
                    emit(doc, doc['original_time'][:10])
            if skipped_air != preparation['by_source']['MAD-AIR']['accepted']:
                raise ValueError('Unexpected excluded January air count')
            if counts['MAD-TRAFFIC:2025'] != preparation['by_source']['MAD-TRAFFIC']['accepted']:
                raise ValueError('Traffic count mismatch')
            ledger.commit()
        (output / 'observations.jsonl.partial').rename(output / 'observations.jsonl')
    seal(output / 'catalogs.json', catalogs)
    manifest = {'status': 'PREPARED', 'contract': CONTRACT,
        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'count': sum(counts.values()),
        'counts': dict(counts), 'rejections': dict(rejects), 'excluded_v2_air_overlap': skipped_air,
        'reference_by_measurement': references, 'synthetic_measurements': 0,
        'physical_sensor_links': 0, 'spark_executed': False,
        'input_hashes': {'raw_air': raw_sha, 'v2_accepted': preparation['output_hashes']['accepted.extjsonl'],
                         'v2_catalogs': preparation['output_hashes']['catalogs.json'], 'dictionary': digest(dictionary)},
        'code_hashes': {str(p.relative_to(ROOT)): digest(p) for p in
                        (Path(__file__), ROOT / 'research/datasets/scripts/phase5_contract.py')},
        'output_hashes': {name: digest(output / name) for name in
                          ('observations.jsonl', 'catalogs.json', 'quarantine.jsonl', 'identities.sqlite')},
        'limits': ['Current inventory, historical geography unverified',
                   'Air has no district mapping', 'Traffic only January 2025 id%20==0',
                   'Events intensity >2000 veh/h are demo, not official alerts',
                   'Analytics projection is not the full madrid-draft-v2 DTO']}
    seal(output / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--v2', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.archive, args.v2, args.output), indent=2))
