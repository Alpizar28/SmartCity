#!/usr/bin/env python3
"""Additional local v2 evidence, NOT a second massive load.

Reads catalogs/demo administration plus all accepted air readings on Jan 1 and
the first 64 accepted traffic readings from the JP ZIP. Compares exact canonical
SQL to independent Python results. No ports, network or host mounts. Only an
aggregate report is written; temporary DB and its own volumes are removed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests/sprint1'))
sys.path.insert(0, str(ROOT / 'research/datasets/scripts'))
from auditar_cierre_postgresql import PREFIX, administrative_results, safe_members, require
from test_sprint1_sql import docker, DOCKER, IMAGE
from validate_real_postgres import read_queries, load_catalogs
from benchmark_real_postgres import read_air_summary, index_catalog, explain


def run(package, report):
    with zipfile.ZipFile(package) as z:
        safe_members(z)
        prep = json.loads(z.read(PREFIX + 'preparation.json'))
        inputs = {}
        for name in ('catalogs.json', 'administrative_seed.json'):
            data = z.read(PREFIX + name)
            require(sha256(data).hexdigest() == prep['output_hashes'][name], 'Input hash')
            inputs[name] = json.loads(data)
        catalogs, admin = inputs['catalogs.json'], inputs['administrative_seed.json']
        documents = []
        traffic = 0
        with z.open(PREFIX + 'accepted.extjsonl') as f:
            for line in f:
                d = json.loads(line)
                if d['source_id'] == 'MAD-AIR' and '2025-01-01T00:00:00' <= d['original_time'] < '2025-01-02T00:00:00':
                    documents.append(d)
                elif d['source_id'] == 'MAD-TRAFFIC':
                    documents.append(d)
                    traffic += 1
                    if traffic == 64:
                        break
    report['subset'] = {'selection': 'All accepted MAD-AIR original_time Jan 1 + first 64 MAD-TRAFFIC in accepted file',
        'count': len(documents), 'by_source': dict(Counter(d['source_id'] for d in documents)),
        'not_full_generation': True}
    name = 'smartcity-pg-close-' + uuid.uuid4().hex[:12]
    created = False
    try:
        report['image_id'] = docker('image', 'inspect', '--format', '{{.Id}}', IMAGE).strip()
        docker('run', '--detach', '--rm', '--pull', 'never', '--name', name,
               '--network', 'none', '--cpus', '1', '--memory', '512m', '--pids-limit', '256',
               '--label', 'smartcity.scope=postgres-close',
               '--tmpfs', '/var/lib/postgresql/data:rw,size=268435456',
               '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', IMAGE)
        created = True
        for attempt in range(120):
            ready = subprocess.run([*DOCKER, 'exec', name, 'pg_isready', '-U', 'postgres'], capture_output=True)
            if ready.returncode == 0 and 'init process complete' in docker('logs', name):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError('Local PostgreSQL not ready')

        def sql(text):
            return docker('exec', '-i', name, 'psql', '-X', '-Atq', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1',
                          stdin="SET timezone='UTC'; SET statement_timeout='60s';\n" + text).strip()

        def rows(query):
            return json.loads(sql("BEGIN READ ONLY; SELECT COALESCE(jsonb_agg(t),'[]') FROM (" + query.rstrip(';\n') + ') t; COMMIT;'))

        report['postgresql_version'] = sql('SELECT version();')
        ddl = ROOT / 'research/datasets/scripts/phase5_postgresql.sql'
        v2 = ROOT / 'sprint1/postgres/contract_v2.sql'
        advanced = ROOT / 'sprint1/postgres/sql_avanzado_observado.sql'
        limitations = ROOT / 'tests/integration/postgres_v2_limitations.sql'
        paths = [Path(__file__), limitations, ROOT / 'scripts/auditar_cierre_postgresql.py',
                 ROOT / 'scripts/test_sprint1_sql.py', ddl, v2, advanced,
                 ROOT / 'sprint1/postgres/queries.sql',
                 ROOT / 'tests/sprint1/benchmark_real_postgres.py', ROOT / 'tests/sprint1/validate_real_postgres.py']
        report['source_hashes'] = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in paths}
        report['input_hashes'] = prep['output_hashes']
        sql(ddl.read_text())
        sql(v2.read_text())
        load_catalogs(sql, catalogs)
        for table in ('organizations', 'users', 'sensors'):
            literal = json.dumps(admin[table], ensure_ascii=False).replace("'", "''")
            sql(f"INSERT INTO smartcity.{table} SELECT (jsonb_populate_record(NULL::smartcity.{table},d)).* "
                + "FROM jsonb_array_elements('" + literal + "'::jsonb) d;")
        # jsonb_populate_record converts the exact selected DTOs to v2 columns.
        for start in range(0, len(documents), 500):
            batch = []
            for d in documents[start:start + 500]:
                batch.append({**d, 'observed_at': d['observed_at']['$date']})
            literal = json.dumps(batch, ensure_ascii=False).replace("'", "''")
            sql("INSERT INTO smartcity.observations SELECT (jsonb_populate_record(NULL::smartcity.observations,d)).* "
                + "FROM jsonb_array_elements('" + literal + "'::jsonb) d;")
        sql('ANALYZE;')
        limitation_output = sql(limitations.read_text())
        limitation_checks = ['V2_NULL_CHECK_ACCEPTED=1', 'V2_DELETE_ALLOWED=1', 'V2_REFERENCE_ARRAY_ACCEPTED=1']
        require(all(marker in limitation_output.splitlines() for marker in limitation_checks), 'DDL limitation reproduction changed')
        report['ddl_limitations_reproduced'] = {'markers': limitation_checks, 'rolled_back': True,
            'notice': 'These are open integrity limitations, NOT academic or physical PASS claims'}
        expected = administrative_results(catalogs, admin)
        activity = {}
        for d in documents:
            a = activity.setdefault(d['channel_id'], [0, d['observed_at']['$date'], d['observed_at']['$date']])
            a[0] += 1
            a[1] = min(a[1], d['observed_at']['$date'])
            a[2] = max(a[2], d['observed_at']['$date'])
        expected['PG09'] = [dict(channel_id=k, readings=a[0], first_observed_at=a[1].replace('Z','+00:00'),
                                 last_observed_at=a[2].replace('Z','+00:00'))
                            for k,a in sorted(activity.items(),key=lambda x:(-x[1][0],x[0]))]
        report['canonical_subset'] = {}
        for key, query in read_queries().items():
            actual = rows(query)
            require(actual == expected[key], key + ' independent Python comparison')
            report['canonical_subset'][key] = {'rows': len(actual), 'sample': actual[:2], 'python_match': True}
        # Exact existing supplemental canonical aggregate, with independent arithmetic.
        aggregate = rows(read_air_summary(ROOT / 'sprint1/postgres/queries.sql'))
        for row in aggregate:
            values = [d['value'] for d in documents if d['source_id']=='MAD-AIR'
                      and d['measurement_type']==row['measurement_type'] and d['unit']==row['unit']]
            require(row['reading_count']==len(values) and row['minimum_value']==min(values)
                    and row['maximum_value']==max(values)
                    and math.isclose(row['total_value'],sum(values),rel_tol=1e-12)
                    and math.isclose(row['average_value'],sum(values)/len(values),rel_tol=1e-12), 'Air aggregate')
        require(len(aggregate) == len({d['measurement_type'] for d in documents if d['source_id']=='MAD-AIR'}), 'Missing aggregate groups')
        report['canonical_air_aggregate'] = aggregate
        ranking = rows(advanced.read_text())
        january = Counter(d['channel_id'] for d in documents
                          if '2024-12-31T23:00:00Z' <= d['observed_at']['$date'] < '2025-01-31T23:00:00Z')
        ranks = {c:r for r,c in enumerate(sorted(set(january.values()),reverse=True),1)}
        require(ranking == [dict(channel_id=k, reading_count=v, activity_rank=ranks[v])
                            for k,v in sorted(january.items(),key=lambda x:(-x[1],x[0]))][:5], 'Observed ranking')
        report['observed_cte_dense_rank'] = ranking
        report['constraints'] = rows("SELECT c.relname AS table_name, conname, contype, pg_get_constraintdef(k.oid) AS definition "
             "FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
             "WHERE n.nspname='smartcity' ORDER BY c.relname,conname")
        report['not_null'] = rows("SELECT table_name,column_name FROM information_schema.columns "
                                 "WHERE table_schema='smartcity' AND is_nullable='NO' ORDER BY table_name,ordinal_position")
        report['triggers'] = rows("SELECT pg_get_triggerdef(t.oid) AS definition FROM pg_trigger t "
                                  "JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                                  "WHERE n.nspname='smartcity' AND NOT t.tgisinternal")
        report['indexes'] = index_catalog(sql)
        channel = sorted(activity)[0].replace("'", "''")
        report['explain_analyze'] = {
            'channel_time': explain(sql, "SELECT measurement_id, observed_at FROM smartcity.observations "
                f"WHERE channel_id='{channel}' ORDER BY observed_at LIMIT 20", True),
            'observed_ranking': explain(sql, '\n'.join(line for line in advanced.read_text().splitlines()
                if not line.lstrip().startswith('--')).rstrip(';\n'), True)}
        report['count_after_read_only_evidence'] = int(sql('SELECT count(*) FROM smartcity.observations'))
        require(report['count_after_read_only_evidence'] == len(documents), 'Read-only evidence changed data')
        report['status'] = 'PASS'
    finally:
        if created:
            docker('stop', '--time', '5', name, timeout=30)
            require(subprocess.run([*DOCKER,'inspect',name],capture_output=True).returncode != 0, 'Cleanup')
            report['container_removed'] = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paquete', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    if args.salida.exists():
        parser.error('--salida ya existe: elegir otro nombre, no reemplazar evidencia')
    report = {'status':'FAIL','generation':'expanded-v2-2025-01','contract':'madrid-draft-v2',
              'image': IMAGE, 'started_at':datetime.now(timezone.utc).isoformat(),
              'shared_server_modified':False,'container_removed':False,
              'scope':'Live v2 SQL on a real subset plus synthetic administration, not full-generation query counts'}
    try:
        run(args.paquete, report)
    except Exception as error:
        report.update(status='FAIL',error=str(error))
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    with args.salida.open('x') as out:
        json.dump(report,out,ensure_ascii=False,indent=2)
        out.write('\n')
    print('PostgreSQL close:',report['status'],args.salida)
    if 'error' in report:
        print(report['error'])
    sys.exit(0 if report['status']=='PASS' else 1)
