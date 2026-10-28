#!/usr/bin/env python3
"""Demostración sintética en una instancia MongoDB standalone propia y efímera.

No acepta URI, host, base existente ni directorio de datos externo. Conserva
resultados nuevos por ejecución y contrasta documentos y consultas con Python.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'sprint1/mongodb/academico'
COLLECTIONS = ('sensor_types', 'sensors', 'readings', 'dynamic_information')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def normalize(value):
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {'$date'}:
            return normalize(value['$date'])
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, str) and value.endswith('Z') and 'T' in value:
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).isoformat()
        except ValueError:
            pass
    return value


def compare_independent(fixture, native):
    """Calculate joins, groups and narrative selections without MongoDB code."""
    f = normalize(fixture)
    actual = normalize(native)
    for name in COLLECTIONS:
        assert sorted(f[name], key=lambda d: d['_id']) == actual['documents'][name], name
    sensors = {s['_id']: s for s in f['sensors']}
    types = {t['_id']: t for t in f['sensor_types']}
    expected_sensor = sorted((r for r in f['readings'] if r['sensor_id'] == f['mg01_sensor_id']),
                             key=lambda r: (r['observed_at'], r['_id']))
    assert actual['results']['MG01'] == expected_sensor
    assert actual['results']['MG01_unknown'] == []
    values = defaultdict(list)
    for r in f['readings']:
        sensor = sensors[r['sensor_id']]
        kind = types[sensor['sensor_type']]['_id']
        values[kind, r['measurement_type'], r['unit']].append(r['value'])
    rows = actual['results']['MG07']
    assert len(rows) == len(values)
    seen = set()
    expected_groups = []
    for row in rows:
        k = tuple(row['_id'][name] for name in ('sensor_type', 'measurement_type', 'unit'))
        assert k not in seen
        seen.add(k)
        sample = values[k]
        average = math.fsum(sample) / len(sample)
        assert row['cantidad'] == len(sample)
        assert math.isclose(row['promedio'], average, rel_tol=1e-12, abs_tol=1e-12)
        expected_groups.append({'key': list(k), 'count': len(sample), 'sum': math.fsum(sample), 'mean': average})
    assert seen == set(values)
    notes = f['dynamic_information']
    expected_dynamic = {
        'texto': sorted((n for n in notes if 'vibración' in n['body'].casefold()), key=lambda n: n['_id']),
        'atributo': sorted((n for n in notes if 'maintenance' in n['attributes']), key=lambda n: n['_id']),
        'revisiones': sorted((n for n in notes if n['subject_sensor_id'] == f['mg01_sensor_id']), key=lambda n: n['revision']),
    }
    assert actual['results']['dynamic'] == expected_dynamic
    assert all(case['rejected'] for case in actual['negatives'].values())
    assert len(actual['negatives']) == 13 and actual['replay_verified']
    # Closed-form checks prevent changes to fixtures from silently changing the exercise.
    a, b = (t['_id'] for t in f['sensor_types'])
    expected = {(a, 'demo:temperature', 'degC'): (4, 17),
                (b, 'demo:temperature', 'degC'): (3, 100 / 3),
                (b, 'demo:humidity', '%'): (2, 50)}
    assert len(expected_sensor) == 2 and len(notes) == 3
    assert {k: (len(v), math.fsum(v) / len(v)) for k, v in values.items()} == expected
    return {'status': 'PASS', 'method': 'Python joins, full document comparison, sums/counts and text selection',
            'MG01_count': len(expected_sensor), 'MG07': expected_groups,
            'dynamic_counts': {k: len(v) for k, v in expected_dynamic.items()},
            'full_documents_verified': sum(len(f[n]) for n in COLLECTIONS),
            'negative_cases_verified': len(actual['negatives'])}


def verify_admin_origin(fixture):
    private = ROOT / 'research/datasets/private_results/expanded-v2-2025-01'
    paths = [private / 'administrative_seed.json', private / 'catalogs.json']
    assert digest(paths[0]) == fixture['administrative_seed_sha256']
    assert digest(paths[1]) == fixture['catalogs_sha256']
    admin, catalog = (json.loads(p.read_text()) for p in paths)
    by_id = {s['sensor_id']: s for s in admin['sensors']}
    categories = sorted({v['category_id'] for v in catalog['measurement_types'].values()})
    for t in fixture['sensor_types']:
        assert t['_id'] == 'demo-type:' + t['category_id']
        assert t['name'] == f"Tipo de dispositivo sintético {categories.index(t['category_id']) + 1:02d}"
    for s in fixture['sensors']:
        original = by_id[s['sensor_id']]
        assert original['data_origin'] == s['data_origin'] == 'synthetic'
        assert s['name'] == original['name'] and s['sensor_type'] == 'demo-type:' + original['category_id']
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def run(mongod, mongosh):
    mongod, mongosh = str(Path(mongod).resolve()), str(Path(mongosh).resolve())
    fixture = json.loads((DEMO / 'fixtures.json').read_text())
    inputs = verify_admin_origin(fixture)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
    output = ROOT / 'sprint1/mongodb/evidencias/academico' / run_id
    output.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), *DEMO.glob('*.js'), DEMO / 'fixtures.json',
               ROOT / 'tests/sprint1/test_mongodb.js']
    report = {'status': 'FAIL', 'run_id': run_id, 'scope': 'synthetic_academic_only',
              'topology': 'standalone', 'distributed_storage_demonstrated': False,
              'public_data_loaded': False, 'shared_server_modified': False,
              'source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in sources},
              'input_hashes': inputs, 'executables': {p: digest(p) for p in (mongod, mongosh)},
              'instance_stopped': False, 'temporary_data_removed': False}
    process = None
    work = None
    try:
        with tempfile.TemporaryDirectory(prefix='smartcity-academic-') as temporary:
            work = Path(temporary)
            (work / 'data').mkdir()
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            report.update(bind_ip='127.0.0.1', port=port, database='smartcity_academic_' + uuid.uuid4().hex[:16])
            process = subprocess.Popen([mongod, '--dbpath', str(work / 'data'), '--port', str(port),
                '--bind_ip', '127.0.0.1', '--unixSocketPrefix', temporary, '--wiredTigerCacheSizeGB', '0.25',
                '--setParameter', 'diagnosticDataCollectionEnabled=false', '--logpath', str(work / 'mongod.log')],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                socket_path = work / f'mongodb-{port}.sock'
                for _ in range(200):
                    if process.poll() is not None:
                        raise RuntimeError('mongod no pudo iniciar: ' + (work / 'mongod.log').read_text()[-2500:])
                    if socket_path.exists():
                        break
                    time.sleep(.1)
                else:
                    raise TimeoutError('La instancia no creó su socket privado')
                from urllib.parse import quote
                uri = 'mongodb://' + quote(str(socket_path), safe='') + '/' + report['database']
                expression = 'globalThis.ACADEMIC_DIR=' + json.dumps(str(DEMO)) + ';globalThis.EXPECTED_PID=' + str(process.pid) + ';load(' + json.dumps(str(DEMO / 'ejecutar_demo.js')) + ');'
                execution = subprocess.run([mongosh, '--norc', '--quiet', uri, '--eval', expression],
                                           capture_output=True, text=True, timeout=120)
                (output / 'mongosh.stdout.txt').write_text(execution.stdout)
                (output / 'mongosh.stderr.txt').write_text(execution.stderr)
                if execution.returncode:
                    raise RuntimeError('mongosh falló; consultar evidencia de ejecución')
                line = next(s for s in execution.stdout.splitlines() if s.startswith('ACADEMIC_RESULT='))
                native = json.loads(line.split('=', 1)[1])
                assert native['version'] == '7.0.16'
                (output / 'native.json').write_text(json.dumps(native, ensure_ascii=False, indent=2) + '\n')
                independent = compare_independent(fixture, native)
                (output / 'independent.json').write_text(json.dumps(independent, ensure_ascii=False, indent=2) + '\n')
                assert inputs == verify_admin_origin(fixture)
                report.update(status='PASS', version=native['version'], independent=independent,
                              counts={n: native['metadata'][n]['count'] for n in COLLECTIONS})
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=30)
                report['instance_stopped'] = process.poll() is not None
        report['temporary_data_removed'] = not work.exists()
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        report['temporary_data_removed'] = work is not None and not work.exists()
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        (output / 'execution.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        files = sorted(p for p in output.iterdir() if p.is_file())
        (output / 'SHA256SUMS').write_text(''.join(digest(p) + '  ' + p.name + '\n' for p in files))
        print(output.relative_to(ROOT))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mongod', default=shutil.which('mongod'))
    parser.add_argument('--mongosh', default=shutil.which('mongosh'))
    args = parser.parse_args()
    if not args.mongod or not args.mongosh:
        parser.error('Se requieren mongod 7.0.16 y mongosh locales')
    run(args.mongod, args.mongosh)
