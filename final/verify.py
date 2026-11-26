"""Cruza Spark, PostgreSQL, MongoDB y el conteo de MapReduce. No inventa tiempos."""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

import pyarrow.parquet as pq
from final.manage import DEFAULT_BATCH_REPORT, DEFAULT_GENERATION, DEFAULT_SPARK_OUTPUT
from final.postgres import query as postgres_query, materialize
from final.mongo import query as mongo_query, primary


def normalized(rows):
    result = {}
    for row in rows:
        key = (str(row['source_day']), row['zone_id'], row['unit'])
        result[key] = {name: row[name] for name in ('count', 'total_value', 'min', 'max', 'demo_events')}
    return result


# Misma clave y mismos valores, con tolerancia en los decimales.
def equivalent(expected, actual):
    if expected.keys() != actual.keys():
        raise ValueError('Result group keys mismatch')
    for key in expected:
        for name, value in expected[key].items():
            if not math.isclose(float(value), float(actual[key][name]), rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError('Result values mismatch: ' + name)


def spark_materialized(output, measurement, start, end):
    frame = pq.read_table(output / 'SP03_daily').to_pandas()
    mask = (frame['measurement_type'] == measurement) & (frame['source_day'] >= str(start)) & (frame['source_day'] <= str(end))
    return frame[mask].to_dict('records')


def verify(generation, output, batch_report):
    manifest = json.loads((generation / 'manifest.json').read_text())
    summary = json.loads((output / 'summary.json').read_text())
    if summary['status'] != 'PASS' or summary['input_records'] != manifest['count']:
        raise ValueError('Unfinished or mismatched Spark generation')
    if hashlib.sha256(Path(__file__).with_name('spark_job.py').read_bytes()).hexdigest() != summary['code_sha256']:
        raise ValueError('Spark code changed since execution')
    if hashlib.sha256((generation / 'manifest.json').read_bytes()).hexdigest() != summary['input_manifest_sha256']:
        raise ValueError('Manifest changed since Spark execution')
    with primary() as connection:
        mongo_count = connection.smartcity_final.observations.count_documents({})
        if mongo_count != manifest['count']:
            raise ValueError('Mongo generation count mismatch')
        status = connection.admin.command('replSetGetStatus')
        roles = [row['stateStr'] for row in status['members']]
        if sorted(roles) != ['ARBITER', 'PRIMARY', 'SECONDARY']:
            raise ValueError('Expected primary, secondary and arbiter')
    batch = json.loads(batch_report.read_text())
    batch_counts = {}
    for line in batch['counts'].splitlines():
        key, value = line.split('\t')
        _, typ, _ = key.split('|')
        batch_counts[typ] = int(value)
    if batch_counts != {name: row['count'] for name, row in manifest['reference_by_measurement'].items()}:
        raise ValueError('MapReduce independent counts mismatch')
    benchmarks = []
    for measurement in ('MAD-AIR:8', 'MAD-TRAFFIC:intensidad'):
        start, end = date(2025, 1, 1), date(2025, 1, 31)
        expected = normalized(spark_materialized(output, measurement, start, end))
        for engine, function in (('PostgreSQL', postgres_query), ('MongoDB', mongo_query)):
            timings = []
            for _ in range(3):
                started = time.perf_counter()
                actual = normalized(function(measurement, start, end, None))
                timings.append(time.perf_counter() - started)
                equivalent(expected, actual)
            benchmarks.append({'engine': engine, 'measurement': measurement, 'groups': len(expected),
                'seconds': timings, 'median_seconds': statistics.median(timings),
                'scope': 'Daily filtered results; includes opening/authenticating connection; warm caches not controlled',
                'storage': 'PostgreSQL reads Spark hourly aggregates; MongoDB aggregates original analytics records'})
    replay = materialize(output)
    if not replay.get('idempotent_reuse'):
        raise ValueError('PostgreSQL replay was not idempotent')
    return {'status': 'PASS', 'input_records': manifest['count'], 'mongo_roles': roles,
        'mapreduce_counts_verified': True, 'postgres_replay_verified': True,
        'filtered_pg_mongo_spark_results_match': True, 'benchmarks': benchmarks,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'limits': ['Not an equal-storage performance competition',
                   'HDFS storage and full Spark ETL are different workloads from filtered database queries']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation', type=Path, default=DEFAULT_GENERATION)
    parser.add_argument('--spark-output', type=Path, default=DEFAULT_SPARK_OUTPUT)
    parser.add_argument('--batch-report', type=Path, default=DEFAULT_BATCH_REPORT)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Use a new report path')
    result = verify(args.generation, args.spark_output, args.batch_report)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
