#!/usr/bin/env python3
"""Run the ten canonical smartcity queries in an owned disposable PostgreSQL.

No private inputs, published ports, host mounts, downloads or remote endpoints.
Fixtures are deliberately fabricated tests, never evidence of real sensor activity.
"""
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
sys.path.insert(0, str(ROOT / 'tests/sprint1'))
from validate_real_postgres import read_queries

DOCKER = ['docker', '--host', 'unix:///var/run/docker.sock']
IMAGE = 'postgres:16.6-alpine'
QUERY_PATH = ROOT / 'sprint1/postgres/queries.sql'
SCHEMA_PATH = ROOT / 'research/datasets/scripts/phase5_postgresql.sql'
FIXTURE_PATH = ROOT / 'tests/integration/postgres_canonical_fixture.sql'


def docker(*args, stdin=None, timeout=120):
    result = subprocess.run([*DOCKER, *args], input=stdin, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'Docker command failed ({result.returncode}):\n'
                           + result.stdout + '\n' + result.stderr)
    return result.stdout


def check_results(results):
    expected = {
        'PG01': [{'category_id': 'category-air', 'category_name': 'Test air', 'sensor_count': 2},
                 {'category_id': 'category-other', 'category_name': 'Test other', 'sensor_count': 2}],
        'PG02': [{'station_id': f'station-{i}', 'location_id': f'location-{i}',
                  'location_name': f'Test location {i}', 'sensor_count': 2} for i in (1, 2)],
        'PG03': [{'administrative_status': 'active', 'sensor_count': 2},
                 {'administrative_status': 'inactive', 'sensor_count': 1},
                 {'administrative_status': None, 'sensor_count': 1}],
        'PG04': [{'organization_id': 'org-assigned', 'name': 'Test organization', 'sensor_count': 3},
                 {'organization_id': 'org-empty', 'name': 'Test empty organization', 'sensor_count': 0}],
        'PG05': [{'location_id': f'location-{i}', 'name': f'Test location {i}',
                  'sensor_count': 2} for i in (1, 2)],
        'PG06': [{'installation_year': 2024, 'sensor_count': 2},
                 {'installation_year': 2025, 'sensor_count': 1}],
        'PG07': [{'sensor_id': 'sensor-no-readings'}, {'sensor_id': 'sensor-outside'}],
        'PG08': [{'zone_id': f'zone-{i}', 'name': f'Test zone {i}',
                  'sensor_count': 2, 'zone_rank': 1} for i in (1, 2)],
        'PG10': [{'station_id': f'station-{i}', 'channel_count': 2} for i in (1, 2)],
    }
    if set(results) != {f'PG{i:02d}' for i in range(1, 11)}:
        raise ValueError('Missing canonical query outputs')
    for name, rows in expected.items():
        if results[name] != rows:
            raise ValueError(f'{name}: expected {rows!r}, got {results[name]!r}')
    activity = results['PG09']
    times = {'channel-active': '2024-12-31T23:00:00+00:00',
             'channel-outside': '2025-01-31T23:00:00+00:00',
             'channel-unassigned': '2025-01-01T00:00:00+00:00'}
    if len(activity) != 3 or [r['channel_id'] for r in activity] != list(times):
        raise ValueError('PG09: unexpected channel activity')
    for row in activity:
        if row['readings'] != 1 or any(
            datetime.fromisoformat(row[key]) != datetime.fromisoformat(times[row['channel_id']])
            for key in ('first_observed_at', 'last_observed_at')
        ):
            raise ValueError('PG09: counts or timestamps differ from fixture')


def main():
    report = {'status': 'FAIL', 'started_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'canonical smartcity SQL with fabricated rollback-only fixtures; not a real-data load',
              'image': IMAGE, 'schema': 'smartcity', 'contract': 'madrid-draft-v1',
              'container_removed': False, 'query_results': {}}
    name = 'smartcity-s1-canonical-pg-' + uuid.uuid4().hex[:12]
    created = False
    try:
        queries = read_queries()
        inputs = [Path(__file__).resolve(), QUERY_PATH, SCHEMA_PATH, FIXTURE_PATH,
                  ROOT / 'tests/sprint1/validate_real_postgres.py',
                  ROOT / 'tests/sprint1/test_schema.sql', ROOT / 'tests/sprint1/test_queries.sql']
        report['source_hashes'] = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                                   for p in inputs}
        report['image_id'] = docker('image', 'inspect', '--format', '{{.Id}}', IMAGE).strip()
        docker('run', '--detach', '--rm', '--pull', 'never', '--name', name,
               '--network', 'none', '--cpus', '1', '--memory', '384m', '--pids-limit', '256',
               '--label', 'smartcity.scope=sprint1-canonical-sql',
               '--tmpfs', '/var/lib/postgresql/data:rw,size=134217728',
               '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', IMAGE)
        created = True
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            ready = subprocess.run([*DOCKER, 'exec', name, 'psql', '-X', '-h', '127.0.0.1',
                                    '-U', 'postgres', '-tAc', 'SELECT 1'],
                                   capture_output=True, timeout=10)
            if ready.returncode == 0:
                break
            if docker('inspect', '--format', '{{.State.Running}}', name).strip() != 'true':
                raise RuntimeError('Disposable PostgreSQL stopped during initialization')
            time.sleep(0.5)
        else:
            raise TimeoutError('Disposable PostgreSQL not ready in 60 seconds')

        sql = "SET timezone='UTC'; SET statement_timeout='15s';\n" + SCHEMA_PATH.read_text()
        for path in inputs[-2:]:
            sql += '\n' + path.read_text()
        sql += '\n' + FIXTURE_PATH.read_text() + '\n' + QUERY_PATH.read_text()
        for key, statement in queries.items():
            sql += (f"\nSELECT 'SQL_QUERY_RESULT=' || json_build_object('{key}', "
                    f"COALESCE(json_agg(row_to_json(result)), '[]'::json))::text "
                    f"FROM ({statement}) AS result;\n")
        sql += """
ROLLBACK;
SELECT 'FIXTURE_REMAINING=' || (
    (SELECT count(*) FROM smartcity.sources) +
    (SELECT count(*) FROM smartcity.zones) +
    (SELECT count(*) FROM smartcity.sensor_categories) +
    (SELECT count(*) FROM smartcity.organizations) +
    (SELECT count(*) FROM smartcity.sensors) +
    (SELECT count(*) FROM smartcity.observations)
)::text;
"""
        output = docker('exec', '-i', name, 'psql', '-X', '-Atq', '-U', 'postgres',
                        '-v', 'ON_ERROR_STOP=1', stdin=sql)
        report['output'] = output
        for line in output.splitlines():
            if line.startswith('SQL_QUERY_RESULT='):
                report['query_results'].update(json.loads(line.split('=', 1)[1]))
        check_results(report['query_results'])
        if 'FIXTURE_REMAINING=0' not in output.splitlines():
            raise ValueError('Controlled fixtures were not rolled back')
        report.update(status='PASS', queries_checked=10, fixtures_rolled_back=True,
                      pg07_unlinked_sensor_excluded=True, pg07_half_open_bounds_checked=True)
    except Exception as exc:
        report['error'] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        if created:
            try:
                docker('stop', '--time', '5', name, timeout=30)
                inspect = subprocess.run([*DOCKER, 'inspect', name], capture_output=True, timeout=10)
                if inspect.returncode == 0:
                    raise RuntimeError('Disposable container still exists')
                report['container_removed'] = True
            except Exception as exc:
                report.update(status='FAIL', cleanup_error=str(exc))
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        with tempfile.NamedTemporaryFile(mode='w', prefix='smartcity-s1-sql-', suffix='.json',
                                         dir='/tmp/opencode', delete=False) as target:
            json.dump(report, target, ensure_ascii=False, indent=2)
            print('SQL report: ' + target.name)
        print('Sprint 1 canonical SQL: ' + report['status'])
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
