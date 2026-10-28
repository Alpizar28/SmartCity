#!/usr/bin/env python3
"""Explicit local integration harness; no persistent services or private inputs.

Uses existing Docker images, a fixed LOCAL socket, no network/ports/host mounts,
RAM-backed database paths and random names. Stops only containers it created.
"""
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests/sprint1'))
from sprint1.core.adapters import ReadingDTO
from sprint1.core.contract import payload_hash
from test_contract import examples

DOCKER = ['docker', '--host', 'unix:///var/run/docker.sock']
IMAGES = {'postgres': 'postgres:16.6-alpine', 'mongodb': 'mongo:7.0.16'}
EVIDENCE = ROOT / 'research/datasets/results/phase5/examples.extjson'


def command(args, stdin=None, timeout=120):
    result = subprocess.run(args, input=stdin, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}')
    return result.stdout


def docker(*args, **kwargs):
    return command([*DOCKER, *args], **kwargs)


def wait_ready(name, args):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        result = subprocess.run([*DOCKER, 'exec', name, *args], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return
        if docker('inspect', '--format', '{{.State.Running}}', name).strip() != 'true':
            raise RuntimeError('Test container stopped:\n' + docker('logs', name))
        time.sleep(0.5)
    raise TimeoutError('Test engine not ready after 60 seconds: ' + name)


def pg_snapshot(name, database):
    sql = (ROOT / 'tests/integration/postgres_backup.sql').read_text()
    output = docker('exec', '-i', name, 'psql', '--no-psqlrc', '-U', 'postgres',
                    '-d', database, '-v', 'ON_ERROR_STOP=1', '-v', 'snapshot=true', '-tA', stdin=sql)
    return json.dumps(json.loads(output), sort_keys=True, separators=(',', ':'))


def postgres_backup_restore(name):
    """Backup/restore only databases in this harness-owned disposable container."""
    original = pg_snapshot(name, 'sprint1_test')
    archive = '/tmp/sprint1-test.pgdump'
    docker('exec', name, 'pg_dump', '-U', 'postgres', '-d', 'sprint1_test',
           '--format=custom', '--file=' + archive)
    archive_hash = docker('exec', name, 'sha256sum', archive).split()[0]
    docker('exec', name, 'createdb', '-U', 'postgres', 'sprint1_restore')
    docker('exec', name, 'pg_restore', '-U', 'postgres', '-d', 'sprint1_restore',
           '--exit-on-error', archive)
    restored = pg_snapshot(name, 'sprint1_restore')
    if restored != original:
        raise RuntimeError('PostgreSQL logical snapshot differs after restore')
    sql = (ROOT / 'tests/integration/postgres_backup.sql').read_text()
    output = docker('exec', '-i', name, 'psql', '--no-psqlrc', '-U', 'postgres',
                    '-d', 'sprint1_restore', '-v', 'ON_ERROR_STOP=1', '-v', 'snapshot=false', stdin=sql)
    if 'POSTGRES_RESTORE_PASS' not in output:
        raise RuntimeError('PostgreSQL restore completion marker absent')
    if pg_snapshot(name, 'sprint1_test') != original:
        raise RuntimeError('PostgreSQL source changed during restore checks')
    return {'status': 'PASS', 'archive_sha256': archive_hash,
            'logical_sha256': sha256(original.encode()).hexdigest(),
            'all_tables_schema_sequences_equal': True, 'output': output}


def mongodb_backup_restore(name):
    archive = '/tmp/sprint1-test.mongoarchive'
    docker('exec', name, 'mongodump', '--db=sprint1_test', '--archive=' + archive, '--gzip')
    archive_hash = docker('exec', name, 'sha256sum', archive).split()[0]
    # Target is new. Never --drop, never overwrite a source/shared database.
    docker('exec', name, 'mongorestore', '--archive=' + archive, '--gzip', '--stopOnError',
           '--nsInclude=sprint1_test.*', '--nsFrom=sprint1_test.*', '--nsTo=sprint1_restore.*')
    output = docker('exec', '--env', 'SMARTCITY_TEST_PHASE=restore', name,
                    'mongosh', '--quiet', '/tmp/integration.js')
    if 'MONGODB_RESTORE_PASS' not in output:
        raise RuntimeError('MongoDB restore completion marker absent')
    return {'status': 'PASS', 'archive_sha256': archive_hash, 'output': output}


def postgres_concurrency(name, records):
    """Eight independent connections, two conflicting candidates for one key.

    Uses ONLY the disposable restored database, after restore verification. The
    source database is never truncated or changed by this probe.
    """
    def sql(statement):
        return docker('exec', '-i', name, 'psql', '--no-psqlrc', '-U', 'postgres',
                      '-d', 'sprint1_restore', '-v', 'ON_ERROR_STOP=1', '-tA', stdin=statement)
    sql('TRUNCATE sprint1.readings, sprint1.quarantine RESTART IDENTITY;')
    def stage(record):
        encoded = base64.b64encode(json.dumps(record,
            default=lambda value: value.isoformat(), allow_nan=False).encode()).decode('ascii')
        return sql("SELECT sprint1.stage_reading(convert_from(decode('" + encoded
                   + "', 'base64'), 'UTF8')::jsonb);").strip()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(stage, records * 4))
    expected = {'accepted': 1, 'duplicate': 3, 'quarantined': 4}
    actual = {state: results.count(state) for state in set(results)}
    if actual != expected:
        raise RuntimeError('Unexpected concurrent staging outcomes: ' + repr(actual))
    state = json.loads(sql("""
        SELECT jsonb_build_object(
            'readings', (SELECT count(*) FROM sprint1.readings),
            'quarantine', (SELECT count(*) FROM sprint1.quarantine),
            'accepted_hash', (SELECT payload_hash FROM sprint1.readings),
            'quarantine_hashes', (SELECT jsonb_agg(document->>'payload_hash') FROM sprint1.quarantine));
    """))
    hashes = {record['payload_hash'] for record in records}
    if state['readings'] != 1 or state['quarantine'] != 4 or state['accepted_hash'] not in hashes:
        raise RuntimeError('Concurrent database counts/fingerprint invalid')
    if set(state['quarantine_hashes']) != hashes - {state['accepted_hash']}:
        raise RuntimeError('Conflicting payload was overwritten or wrongly quarantined')
    return {'status': 'PASS', 'connections': 8, 'outcomes': actual,
            'accepted_payload_unchanged': True, 'scope': 'READ COMMITTED, one original key, two payloads'}


def main():
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'FAIL',
              'scope': 'three published examples, explicitly adapted in test copies; not volume or raw-source verification',
              'docker_endpoint': 'unix:///var/run/docker.sock', 'engines': {}, 'cleanup': {}}
    started = []
    before = sha256(EVIDENCE.read_bytes()).hexdigest()
    report['historical_examples_sha256'] = before
    inputs = [Path(__file__).resolve(),
              *sorted((ROOT / 'sprint1').rglob('*.py')),
              *sorted((ROOT / 'sprint1').rglob('*.sql')),
              *sorted((ROOT / 'sprint1').rglob('*.js')),
              ROOT / 'sprint1/basico/requirements.txt',
              *sorted((ROOT / 'tests/integration').glob('*')),
              ROOT / 'tests/sprint1/test_contract.py']
    report['code_sha256'] = {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                             for path in inputs if path.is_file()}
    exit_code = 1
    try:
        # inspect fails rather than pulling a missing image or contacting a registry.
        for engine, image in IMAGES.items():
            report['engines'][engine] = {'image': image,
                'image_id': docker('image', 'inspect', '--format', '{{.Id}}', image).strip()}
        docs, catalogs = examples()  # Test-only mapping; NEVER an ingestion API.
        dtos = [ReadingDTO(doc, catalogs) for doc in docs]
        # Deliberately contradictory test mutation, never accepted as real data.
        conflict = dtos[0].document()
        conflict['value'] += 1
        conflict['payload_hash'] = payload_hash(conflict)
        conflict_dto = ReadingDTO(conflict, catalogs)
        suffix = uuid.uuid4().hex[:12]
        pg = 'smartcity-s1-test-pg-' + suffix
        mongo = 'smartcity-s1-test-mongo-' + suffix
        common = ['--detach', '--rm', '--pull', 'never', '--network', 'none',
                  '--cpus', '1', '--pids-limit', '256', '--label', 'smartcity.scope=sprint1-integration']
        docker('run', *common, '--name', pg, '--memory', '384m',
               '--tmpfs', '/var/lib/postgresql/data:rw,size=134217728',
               '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', '--env', 'POSTGRES_DB=sprint1_test', IMAGES['postgres'])
        started.append(pg)
        # TCP readiness skips the temporary Unix-socket initialization server.
        # pg_isready alone can report ready before POSTGRES_DB has been created.
        wait_ready(pg, ['psql', '--no-psqlrc', '-h', '127.0.0.1', '-U', 'postgres',
                        '-d', 'sprint1_test', '-tAc', 'SELECT 1'])

        records = json.dumps([dto.postgres_record() for dto in dtos],
                             default=lambda value: value.isoformat(), allow_nan=False)
        encoded = base64.b64encode(records.encode()).decode('ascii')
        sql = (ROOT / 'sprint1/postgres/schema_proposal.sql').read_text() + '\n'
        sql += (ROOT / 'sprint1/postgres/staging_queries.sql').read_text() + '\n'
        sql += (ROOT / 'sprint1/postgres/staging.sql').read_text() + '\n'
        sql += 'CREATE TEMP TABLE fixture(record jsonb);\n'
        # The only interpolated SQL value is our base64 alphabet, not raw input.
        sql += ("INSERT INTO fixture SELECT jsonb_array_elements(convert_from(decode('"
                + encoded + "', 'base64'), 'UTF8')::jsonb);\n")
        encoded_conflict = base64.b64encode(json.dumps(conflict_dto.postgres_record(),
            default=lambda value: value.isoformat(), allow_nan=False).encode()).decode('ascii')
        sql += 'CREATE TEMP TABLE conflict_fixture(record jsonb);\n'
        sql += ("INSERT INTO conflict_fixture SELECT convert_from(decode('"
                + encoded_conflict + "', 'base64'), 'UTF8')::jsonb;\n")
        sql += (ROOT / 'tests/integration/postgres.sql').read_text()
        sql += '\n' + (ROOT / 'sprint1/basico/consultas_postgres.sql').read_text()
        output = docker('exec', '-i', pg, 'psql', '--no-psqlrc', '-U', 'postgres',
                        '-d', 'sprint1_test', '-v', 'ON_ERROR_STOP=1', stdin=sql)
        if 'POSTGRES_INTEGRATION_PASS' not in output:
            raise RuntimeError('PostgreSQL completion marker absent')
        report['engines']['postgres'].update(status='PASS', output=output, readings=3)
        report['engines']['postgres']['backup_restore'] = postgres_backup_restore(pg)
        before_race = pg_snapshot(pg, 'sprint1_test')
        report['engines']['postgres']['concurrency'] = postgres_concurrency(pg,
            [dtos[0].postgres_record(), conflict_dto.postgres_record()])
        if pg_snapshot(pg, 'sprint1_test') != before_race:
            raise RuntimeError('Concurrency checks changed the source database')

        docker('run', *common, '--name', mongo, '--memory', '768m',
               '--tmpfs', '/data/db:rw,size=536870912', '--tmpfs', '/data/configdb:rw,size=16777216',
               IMAGES['mongodb'], '--bind_ip', '127.0.0.1', '--wiredTigerCacheSizeGB', '0.25')
        started.append(mongo)
        wait_ready(mongo, ['mongosh', '--quiet', '--eval',
                          'if (db.adminCommand({ping:1}).ok !== 1) quit(1)'])
        for filename in ('validator.js', 'indexes.js', 'queries.js', 'staging.js'):
            docker('cp', str(ROOT / 'sprint1/mongodb' / filename), mongo + ':/tmp/' + filename)
        docker('cp', str(ROOT / 'tests/integration/mongodb.js'), mongo + ':/tmp/integration.js')
        with tempfile.TemporaryDirectory(prefix='smartcity-s1-', dir='/tmp/opencode') as directory:
            fixture = Path(directory) / 'fixture.json'
            # Extended JSON encodes BSON Date; staging_key is the canonical original tuple.
            mongo_docs = []
            for dto in [*dtos, conflict_dto]:
                document = dto.mongo_document()
                if document.get('observed_at') is not None:
                    document['observed_at'] = {'$date': document['observed_at'].isoformat()}
                mongo_docs.append(document)
            fixture.write_text(json.dumps(mongo_docs[:3], allow_nan=False))
            docker('cp', str(fixture), mongo + ':/tmp/fixture.json')
            conflict_file = Path(directory) / 'conflict.json'
            conflict_file.write_text(json.dumps(mongo_docs[3], allow_nan=False))
            docker('cp', str(conflict_file), mongo + ':/tmp/conflict.json')
        output = docker('exec', mongo, 'mongosh', '--quiet', '/tmp/integration.js')
        if 'MONGODB_INTEGRATION_PASS' not in output:
            raise RuntimeError('MongoDB completion marker absent')
        report['engines']['mongodb'].update(status='PASS', output=output, readings=3)
        docker('cp', str(ROOT / 'sprint1/basico/consultas_mongodb.js'), mongo + ':/tmp/consultas_basicas.js')
        basic_output = docker('exec', mongo, 'mongosh', '--quiet',
            'mongodb://127.0.0.1/sprint1_test', '/tmp/consultas_basicas.js')
        report['engines']['mongodb']['basic_queries'] = {'status': 'PASS', 'output': basic_output}
        docker('cp', str(ROOT / 'sprint1/basico/crud_mongodb.js'), mongo + ':/tmp/crud_basico.js')
        crud_output = docker('exec', mongo, 'mongosh', '--quiet',
            'mongodb://127.0.0.1/sprint1_test', '--eval',
            'var GUARDAR = true; load("/tmp/crud_basico.js");')
        if 'CRUD_BASICO_PASS' not in crud_output:
            raise RuntimeError('Basic CRUD completion marker absent')
        report['engines']['mongodb']['basic_crud'] = {'status': 'PASS', 'output': crud_output}
        report['engines']['mongodb']['backup_restore'] = mongodb_backup_restore(mongo)
        report['status'] = 'PASS'
        exit_code = 0
    except Exception as exc:
        report['error'] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        for name in reversed(started):
            try:
                docker('stop', '--time', '5', name, timeout=30)
                report['cleanup'][name] = 'stopped (--rm)'
            except Exception as exc:
                report['cleanup'][name] = str(exc)
                report['status'] = 'FAIL'
                exit_code = 1
        report['historical_examples_unchanged'] = sha256(EVIDENCE.read_bytes()).hexdigest() == before
        if not report['historical_examples_unchanged']:
            report['status'] = 'FAIL'
            exit_code = 1
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        with tempfile.NamedTemporaryFile(mode='w', prefix='smartcity-s1-integration-', suffix='.json',
                                         dir='/tmp/opencode', delete=False) as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            print('Integration report: ' + output.name)
        print('Sprint 1 disposable engines: ' + report['status'])
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
