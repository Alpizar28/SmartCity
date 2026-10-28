#!/usr/bin/env python3
"""Validate normalized v2 in an owned native PostgreSQL 16, Unix socket only.

No host/DSN arguments, sudo, Docker, shared servers or private-input writes.
The complete sealed dataset is loaded unless --sample is explicitly selected.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/datasets/scripts'), str(ROOT / 'tests/sprint1')]
from phase5_contract import canonical, digest, stable_id
from validate_real_postgres import read_queries
from sprint1.basico.preparar_v2 import verificar_paquete
from auditar_cierre_postgresql import administrative_results

BIN = Path('/usr/lib/postgresql/16/bin')
PRIVATE = ROOT / 'research/datasets/private_results/expanded-v2-2025-01'
DDL = ROOT / 'sprint1/postgres/schema_v2_3nf.sql'
QUERIES = ROOT / 'sprint1/postgres/queries_v2_3nf.sql'
DISTRICTS = ROOT / 'sprint1/postgres/distritos_madrid.json'


def literal(value):
    return "'" + json.dumps(value, ensure_ascii=False, allow_nan=False).replace("'", "''") + "'"


def catalogs_sql(catalogs, admin):
    statements = ['SET search_path=smartcity,pg_temp;']

    def insert(table, rows, types):
        columns = ','.join(t.split()[0] for t in types.split(','))
        statements.append(f'INSERT INTO {table}({columns}) SELECT {columns} FROM '
                          f'json_to_recordset({literal(rows)}) x({types});')

    insert('sources', list(catalogs['sources'].values()), 'source_id text,name text,publisher text')
    insert('source_versions', list(catalogs['source_versions'].values()),
           'source_version text,source_id text,original_path text')
    names = json.loads(DISTRICTS.read_text())['names']
    insert('zones', [{**r, 'name': names.get(r['zone_id'], r['name'])}
           for r in catalogs['zones'].values()], 'zone_id text,name text,level text')
    locations, stations = [], []
    for row in catalogs['stations'].values():
        loc = stable_id('location', row['station_id'], 'current-inventory')
        locations.append({**row, 'location_id': loc, 'inventory_version':
            row['inventory_reference']['sha256'] if row.get('inventory_reference') else None})
        stations.append({**row, 'location_id': loc})
    insert('locations', locations, 'location_id text,zone_id text,name text,latitude double precision,'
           'longitude double precision,coordinate_crs text,historical_location_verified boolean,inventory_version text')
    insert('stations', stations, 'station_id text,source_id text,source_key text,name text,location_id text,inventory_present boolean')
    types = list(catalogs['measurement_types'].values())
    categories = sorted({r['category_id'] for r in types})
    insert('sensor_categories', [{'category_id': k, 'name': f'Categoría administrativa sintética {n:02d}'}
           for n, k in enumerate(categories, 1)], 'category_id text,name text')
    insert('measurement_types', types, 'measurement_type text,source_id text,code text,unit text,candidate_unit text,unit_status text')
    insert('organizations', admin['organizations'], 'organization_id text,name text,responsible_person_or_role text,'
           'evidence_reference text,data_origin text,provenance jsonb')
    insert('users', admin['users'], 'user_id text,name text,email text,consent_reference text,demo_only boolean,data_origin text')
    insert('sensor_types', [{'sensor_type': 'demo-type:' + k,
           'name': f'Tipo de dispositivo sintético {n:02d}', 'category_id': k,
           'data_origin': 'synthetic', 'evidence_reference': 'synthetic://sprint1-3nf/types/' + str(n)}
           for n, k in enumerate(categories, 1)],
           'sensor_type text,name text,category_id text,data_origin text,evidence_reference text')
    insert('sensors', [{**r, 'sensor_type': 'demo-type:' + r['category_id']} for r in admin['sensors']],
           'sensor_id text,name text,sensor_type text,station_id text,installation_date date,administrative_status text,'
           'status_effective_at timestamptz,organization_id text,identity_evidence_reference text,data_origin text,provenance jsonb')
    insert('channels', list(catalogs['channels'].values()),
           'channel_id text,station_id text,source_key jsonb,measurement_type text,catalog_basis text')
    if any(c.get('sensor_id') is not None for c in catalogs['channels'].values()):
        raise ValueError('Unexpected physical assignments in sealed dataset')
    return '\n'.join(statements)


def run(sample=None):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    report = {'status': 'FAIL', 'started_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'sample' if sample else 'full', 'sample_limit': sample,
        'contract': 'madrid-draft-v2', 'shared_server_modified': False,
        'tcp_enabled': False, 'postgresql_stopped': False, 'private_files_unchanged': False,
        'source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in [Path(__file__), DDL, QUERIES,
            ROOT / 'sprint1/postgres/dependencias_3nf.json', DISTRICTS,
            ROOT / 'scripts/auditar_cierre_postgresql.py',
            ROOT / 'tests/sprint1/validate_real_postgres.py']}}
    output_root = ROOT / 'sprint1/postgres/evidencias/3nf'
    output_root.mkdir(parents=True, exist_ok=True)
    output = output_root / (stamp + '-' + os.urandom(4).hex() + '.json')
    # Database files remain outside Git in a private, owned cache directory.
    cache = ROOT / '.cache'
    cache.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='pg3nf-', dir=cache))
    workspace.chmod(0o700)
    socket = Path(tempfile.mkdtemp(prefix='sc3nf-', dir='/tmp'))
    socket.chmod(0o700)
    data = workspace / 'database'
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
    env.update(PGHOST=str(socket), PGPORT='55439', PGDATABASE='postgres', PGUSER=env.get('USER', 'kemgarro'),
               PGCONNECT_TIMEOUT='5', PGOPTIONS="-c timezone=UTC -c statement_timeout=1500000")
    started = False

    def sql(text):
        r = subprocess.run([str(BIN / 'psql'), '-X', '-Atq', '-v', 'ON_ERROR_STOP=1'],
                           input=text, capture_output=True, text=True, env=env, timeout=1800)
        if r.returncode:
            # Details remain in protected local diagnostics, not deliverable evidence.
            with (workspace / 'sql-error.txt').open('a') as errors:
                errors.write(r.stderr)
            raise RuntimeError('SQL validation failed; protected diagnostics: ' + str(workspace / 'sql-error.txt'))
        return r.stdout.strip()

    def scalar(text):
        return json.loads(sql('SELECT to_jsonb(t) FROM (' + text + ') t;'))

    def rows(text):
        return [json.loads(line) for line in sql('SELECT to_jsonb(t) FROM (' + text + ') t;').splitlines()]

    try:
        print('Verificando hashes del paquete privado...', flush=True)
        preparation = verificar_paquete(PRIVATE)
        sealed = {name: digest(PRIVATE / name) for name in preparation['output_hashes']}
        report['input_hashes'] = sealed
        historical_pg_path = ROOT / 'research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json'
        historical_mg_path = ROOT / 'research/datasets/results/expanded-v2-2025-01/execution-d26e40706dcd.json'
        historical_pg = json.loads(historical_pg_path.read_text())
        historical_mg = json.loads(historical_mg_path.read_text())
        report['historical_report_hashes'] = {str(p.relative_to(ROOT)): digest(p) for p in [historical_pg_path, historical_mg_path]}
        catalogs = json.loads((PRIVATE / 'catalogs.json').read_text())
        admin = json.loads((PRIVATE / 'administrative_seed.json').read_text())
        init = subprocess.run([str(BIN / 'initdb'), '-D', str(data), '--auth-local=trust',
                               '--auth-host=reject', '--no-locale', '--encoding=UTF8'],
                              capture_output=True, text=True, env=env)
        if init.returncode:
            raise RuntimeError('initdb failed: ' + init.stderr[-500:])
        with (data / 'postgresql.conf').open('a') as conf:
            conf.write(f"\nlisten_addresses=''\nport=55439\nunix_socket_directories='{socket}'\n"
                       "unix_socket_permissions=0700\nshared_buffers='128MB'\nwork_mem='8MB'\n")
        startup = subprocess.run([str(BIN / 'pg_ctl'), '-D', str(data), '-l', str(workspace / 'server.log'),
                                  '-w', 'start'], capture_output=True, text=True, env=env)
        if startup.returncode:
            raise RuntimeError('Private PostgreSQL startup failed: ' + startup.stderr[-500:])
        started = True
        report['version'] = sql('SELECT version();')
        report['listen_addresses'] = sql('SHOW listen_addresses;')
        assert report['listen_addresses'] == ''
        sql(DDL.read_text())
        sql(catalogs_sql(catalogs, admin))
        print('Cargando lecturas en PostgreSQL nativo normalizado...', flush=True)
        sql('CREATE SCHEMA validation; CREATE UNLOGGED TABLE validation.input(doc jsonb NOT NULL);')
        path = PRIVATE / 'accepted.extjsonl'
        if sample:
            path = workspace / 'sample.extjsonl'
            with (PRIVATE / 'accepted.extjsonl').open() as source, path.open('w') as target:
                for n, line in enumerate(source):
                    if n >= sample:
                        break
                    target.write(line)
        escaped = str(path).replace("'", "''")
        sql(f"\\copy validation.input FROM '{escaped}' WITH (FORMAT csv, DELIMITER E'\\x02', QUOTE E'\\x01');")
        projection = "doc || jsonb_build_object('observed_at',doc->'observed_at'->>'$date','raw_locator',(doc->'raw_reference')-'sha256')"
        load = f'INSERT INTO smartcity.observations SELECT (jsonb_populate_record(NULL::smartcity.observations,{projection})).* FROM validation.input'
        before = time.monotonic()
        sql('ANALYZE; ' + load + ';')
        report['load_seconds'] = time.monotonic() - before
        expected_count = min(sample, preparation['accepted']) if sample else preparation['accepted']
        report['counts'] = scalar('SELECT (SELECT count(*) FROM smartcity.observations) AS observations,'
            '(SELECT count(*) FROM smartcity.channels) AS channels,(SELECT count(*) FROM smartcity.sensors) AS sensors,'
            '(SELECT count(*) FROM smartcity.users) AS users,(SELECT count(*) FROM smartcity.organizations) AS organizations,'
            '(SELECT count(*) FROM smartcity.channel_sensors) AS physical_assignments')
        assert report['counts']['observations'] == expected_count
        assert report['counts']['physical_assignments'] == 0
        mismatches = scalar("SELECT count(*) AS n FROM validation.input i LEFT JOIN smartcity.observation_contract v "
            "ON v.measurement_id=i.doc->>'measurement_id' WHERE v.measurement_id IS NULL OR "
            "NOT ((i.doc-'observed_at'-'time_error') <@ (to_jsonb(v)-'observed_at'-'time_error')) "
            "OR v.observed_at<>(i.doc->'observed_at'->>'$date')::timestamptz")['n']
        report['dto_mismatches'] = mismatches
        assert mismatches == 0
        print('DTO completo conservado; verificando replay, consultas e integridad...', flush=True)
        sql(load + ' ON CONFLICT(measurement_id) DO UPDATE SET value=excluded.value,payload_hash=excluded.payload_hash;')
        report['replay_verified'] = scalar('SELECT count(*) AS n FROM smartcity.observations')['n'] == expected_count
        assert report['replay_verified']
        sql('ANALYZE smartcity.observations;')
        queries = read_queries(QUERIES)
        independent = administrative_results(catalogs, admin)
        district_names = json.loads(DISTRICTS.read_text())['names']
        for row in independent['PG08']:
            row['name'] = district_names.get(row['zone_id'], row['name'])
        independent['PG01'] = [{'sensor_type': 'demo-type:' + r['category_id'],
            'sensor_type_name': f'Tipo de dispositivo sintético {n:02d}', 'sensor_count': r['sensor_count']}
            for n, r in enumerate(independent['PG01'], 1)]
        activity = {}
        with path.open() as source:
            for line in source:
                d = json.loads(line)
                t = datetime.fromisoformat(d['observed_at']['$date'].replace('Z', '+00:00'))
                g = activity.setdefault(d['channel_id'], {'n': 0, 'first': t, 'last': t})
                g['n'] += 1
                g['first'] = min(g['first'], t)
                g['last'] = max(g['last'], t)
        independent['PG09'] = [{'channel_id': k, 'readings': g['n'],
            'first_observed_at': g['first'].isoformat(), 'last_observed_at': g['last'].isoformat()}
            for k, g in sorted(activity.items(), key=lambda item: (-item[1]['n'], item[0]))]
        report['queries'] = {}
        results = {}
        for key, query in queries.items():
            data_rows = rows(query)
            results[key] = data_rows
            report['queries'][key] = {'rows': len(data_rows),
                'sha256': sha256(canonical(data_rows).encode()).hexdigest()}
            assert data_rows == independent[key], key + ': independent full result mismatch'
            report['queries'][key]['independent_full_result_match'] = True
            if not sample and key != 'PG01':
                prior = historical_pg['postgresql']['results'][key]
                assert len(data_rows) == prior['total'], key
                # Compare every recorded historical sample, independently of PostgreSQL JSON key ordering.
                current = data_rows[:len(prior['sample'])]
                previous = prior['sample']
                if key == 'PG08':
                    current = [{k:v for k,v in r.items() if k!='name'} for r in current]
                    previous = [{k:v for k,v in r.items() if k!='name'} for r in previous]
                    report['queries'][key]['semantic_change'] = 'published district names; IDs/counts/ranking preserved'
                assert current == previous, key
                report['queries'][key]['historical_metrics_and_sample_match'] = True
        expected_types = Counter('demo-type:' + s['category_id'] for s in admin['sensors'])
        assert {r['sensor_type']: r['sensor_count'] for r in results['PG01']} == dict(expected_types)
        report['queries']['PG01']['independent_type_counts_match'] = True
        report['queries']['PG01']['semantic_change'] = 'device type, formerly measurement-derived category'
        report['by_source'] = {r['source_id']: r['n'] for r in rows(
            'SELECT source_id,count(*) AS n FROM smartcity.observation_contract GROUP BY source_id')}
        if not sample:
            assert report['by_source'] == {s: c['accepted'] for s, c in preparation['by_source'].items()}
        fingerprint = sha256()
        # Same canonical JSON and ordering used in the historical reconciliation.
        for row in rows('SELECT measurement_id,payload_hash FROM smartcity.observations ORDER BY measurement_id'):
            fingerprint.update((canonical([row['measurement_id'], row['payload_hash']]) + '\n').encode())
        report['ids_payload_sha256'] = fingerprint.hexdigest()
        if not sample:
            for old in (historical_pg['postgresql'], historical_mg['mongodb']):
                assert old['ids_payload_sha256'] == report['ids_payload_sha256']
            report['mongodb_v2_reconciliation'] = True
        report['indexes'] = rows("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='smartcity' ORDER BY tablename,indexname")
        report['constraints'] = rows("SELECT c.relname AS table_name,p.conname,p.contype,pg_get_constraintdef(p.oid) AS definition "
            "FROM pg_constraint p JOIN pg_class c ON c.oid=p.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='smartcity' ORDER BY c.relname,p.conname")
        report['tables'] = [r['table_name'] for r in rows("SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='smartcity' AND table_type='BASE TABLE' ORDER BY table_name")]
        assert len(report['tables']) == 14
        model = json.loads((ROOT / 'sprint1/postgres/dependencias_3nf.json').read_text())
        actual_columns = rows("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='smartcity' ORDER BY ordinal_position")
        for table, definition in model['relations'].items():
            assert [r['column_name'] for r in actual_columns if r['table_name'] == table] == definition['attributes'], table
        report['negative_tests'] = negative_tests(sql)
        report['positive_tests'] = positive_tests(sql)
        controlled = ROOT / 'tests/integration/postgres_3nf.sql'
        report['source_hashes'][str(controlled.relative_to(ROOT))] = digest(controlled)
        report['pg07_controlled'] = json.loads(sql(controlled.read_text() +
            "\nSELECT COALESCE(jsonb_agg(t),'[]') FROM (" + queries['PG07'] + ') t; ROLLBACK;'))
        assert report['pg07_controlled'] == [{'sensor_id': s} for s in
            ('test-sensor-before', 'test-sensor-empty', 'test-sensor-outside')]
        assert scalar('SELECT count(*) AS n FROM smartcity.channel_sensors')['n'] == 0
        report['fd_check'] = check_dependencies()
        report['plan'] = json.loads(sql('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT measurement_id FROM smartcity.observations '
            "WHERE channel_id=(SELECT min(channel_id) FROM smartcity.channels) ORDER BY observed_at LIMIT 5;"))
        report['private_files_unchanged'] = all(digest(PRIVATE / name) == h for name, h in sealed.items())
        assert report['private_files_unchanged']
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = str(error)
        print('Validación interrumpida:', error, flush=True)
    finally:
        if started:
            stop = subprocess.run([str(BIN / 'pg_ctl'), '-D', str(data), '-m', 'fast', '-w', 'stop'],
                                  capture_output=True, text=True, env=env)
            report['postgresql_stopped'] = stop.returncode == 0
            if stop.returncode:
                report['status'] = 'FAIL'
        if report['status'] == 'PASS' and report['postgresql_stopped']:
            shutil.rmtree(workspace)
            shutil.rmtree(socket)
            report['temporary_database_removed'] = True
        else:
            report['protected_diagnostics'] = str(workspace)
            report['temporary_database_removed'] = False
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        with output.open('x') as target:
            json.dump(report, target, ensure_ascii=False, indent=2)
            target.write('\n')
        with output.with_suffix('.sha256').open('x') as target:
            target.write(digest(output) + '  ' + output.name + '\n')
        print('Report:', output, '\nStatus:', report['status'], flush=True)
    return 0 if report['status'] == 'PASS' else 1


def negative_tests(sql):
    statements = {
        'channel_source': "INSERT INTO smartcity.channels SELECT 'bad-channel',s.station_id,'[\"invalid\"]'::jsonb,t.measurement_type,'observations' FROM smartcity.stations s CROSS JOIN smartcity.measurement_types t WHERE s.source_id<>t.source_id LIMIT 1",
        'sensor_station': "INSERT INTO smartcity.channel_sensors SELECT c.channel_id,s.sensor_id FROM smartcity.channels c CROSS JOIN smartcity.sensors s WHERE c.station_id<>s.station_id LIMIT 1",
        'parent_source_update': "UPDATE smartcity.stations SET source_id=CASE source_id WHEN 'MAD-AIR' THEN 'MAD-TRAFFIC' ELSE 'MAD-AIR' END WHERE station_id=(SELECT min(station_id) FROM smartcity.stations)",
        'payload_conflict': "UPDATE smartcity.observations SET value=value+1 WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations)",
        'raw_locator_sha': "UPDATE smartcity.observations SET raw_locator=raw_locator||'{\"sha256\":\"x\"}'::jsonb WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations)",
        'observation_version': "UPDATE smartcity.observations SET source_version=repeat('0',64) WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations)",
        'zone_parent': "INSERT INTO smartcity.zones VALUES ('test-bad-zone','Invalid','local','missing-parent')",
        'duplicate_natural': "INSERT INTO smartcity.observations SELECT 'bad-identity',channel_id,observed_at,value,source_version,payload_hash,transformation_method,transformation_version,raw_locator,source_key,provenance,element_type,measurements,integration_sample_count,zone_scope FROM smartcity.observations LIMIT 1",
    }
    for name, statement in statements.items():
        # The sentinel is thrown OUTSIDE the caught block: accepting invalid data fails the test.
        sql("DO $test$ DECLARE rejected boolean:=false; BEGIN BEGIN " + statement +
            "; EXCEPTION WHEN OTHERS THEN rejected:=true; END; "
            "IF NOT rejected THEN RAISE EXCEPTION 'invalid operation accepted'; END IF; END $test$;")
    return {name: 'rejected' for name in statements}


def positive_tests(sql):
    sql("BEGIN; INSERT INTO smartcity.zones VALUES ('test-local','Zona de prueba','local',"
        "(SELECT min(zone_id) FROM smartcity.zones WHERE level='district')); "
        "INSERT INTO smartcity.locations(location_id,zone_id,name,coordinate_crs) VALUES "
        "('test-location','test-local','Ubicación de prueba','unknown'); "
        "DO $test$ BEGIN IF (SELECT district_id FROM smartcity.location_geography WHERE location_id='test-location') "
        "IS DISTINCT FROM (SELECT min(zone_id) FROM smartcity.zones WHERE level='district') "
        "THEN RAISE EXCEPTION 'district not reconstructed'; END IF; END $test$; ROLLBACK;")
    sql("BEGIN; INSERT INTO smartcity.channel_sensors SELECT c.channel_id,s.sensor_id FROM smartcity.channels c "
        "JOIN smartcity.sensors s USING(station_id) LIMIT 1; "
        "DO $test$ BEGIN IF (SELECT count(*) FROM smartcity.channel_sensors)<>1 "
        "THEN RAISE EXCEPTION 'assignment absent'; END IF; END $test$; ROLLBACK;")
    return {'local_zone_district': 'PASS with rollback', 'same_station_assignment': 'PASS with rollback'}


def check_dependencies():
    """Exhaustively check every determinant on the documented FD cover.

    This proves 3NF relative to that cover; SQL/data tests do not establish an FD.
    """
    model = json.loads((ROOT / 'sprint1/postgres/dependencias_3nf.json').read_text())
    from itertools import combinations
    checked = {}
    for name, relation in model['relations'].items():
        attrs = set(relation['attributes'])
        fds = [(set(x), set(y)) for x, y in relation['dependencies']]

        def closure(x):
            result = set(x)
            while True:
                expanded = result | set().union(*(y for a, y in fds if a <= result), set())
                if expanded == result:
                    return result
                result = expanded

        keys = []
        for size in range(len(attrs) + 1):
            for candidate in combinations(sorted(attrs), size):
                candidate = set(candidate)
                if not any(k <= candidate for k in keys) and closure(candidate) == attrs:
                    keys.append(candidate)
        prime = set().union(*keys)
        for size in range(len(attrs) + 1):
            for determinant in combinations(sorted(attrs), size):
                x = set(determinant)
                expanded = closure(x)
                if expanded != attrs and not (expanded - x) <= prime:
                    raise ValueError('3NF violation: ' + name + ' ' + str(determinant))
        assert {frozenset(k) for k in keys} == {frozenset(k) for k in relation['candidate_keys']}, name
        checked[name] = {'third_normal_form': True, 'candidate_keys': [sorted(k) for k in keys]}
    return {'method': 'all determinant closures over explicit FD cover', 'relations': checked,
            'structured_domains': 'SQL JSONB treated as atomic typed domains; not recursive scalar normalization'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=int, help='explicit non-massive sample; never evidence of 748889 loaded')
    args = parser.parse_args()
    if args.sample is not None and args.sample < 1:
        parser.error('--sample must be positive')
    sys.exit(run(args.sample))
