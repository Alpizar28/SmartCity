"""Materializa salidas Spark en PostgreSQL local aislado. No migra el Sprint 1."""
import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import time

import psycopg
from psycopg import sql
import pyarrow.parquet as pq

from final.manage import DEFAULT_SPARK_OUTPUT

ROOT = Path(__file__).resolve().parents[1]


def connection(readonly=False, *, normalized=False, autocommit=False):
    db_credential = os.environ.get('SMARTCITY_FINAL_PASSWORD')
    if not db_credential:
        db_credential = (ROOT / '.cache/final-password').read_text().strip()
    options = {'host': '127.0.0.1', 'port': 55446, 'dbname': 'smartcity_final',
               'user': 'smartcity', 'password': db_credential.strip(), 'connect_timeout': 5}
    if normalized:
        options['dbname'] = 'smartcity_normalized'
    conn = psycopg.connect(**options, autocommit=autocommit)
    if readonly:
        conn.read_only = True
    return conn


def materialize(output):
    summary = json.loads((output / 'summary.json').read_text())
    if summary['status'] != 'PASS':
        raise ValueError('Spark must finish before PostgreSQL publication')
    fingerprint = hashlib.sha256((output / 'summary.json').read_bytes()).hexdigest()
    started = time.perf_counter()
    with connection() as conn:
        conn.execute('CREATE SCHEMA IF NOT EXISTS analytics')
        conn.execute('CREATE TABLE IF NOT EXISTS analytics.runs (fingerprint text PRIMARY KEY, input_records bigint NOT NULL)')
        old = conn.execute('SELECT fingerprint FROM analytics.runs').fetchall()
        if old:
            if old != [(fingerprint,)]:
                raise ValueError('Another published generation exists; never overwrite it')
            return {'status': 'PASS', 'idempotent_reuse': True, 'fingerprint': fingerprint}
        conn.execute('''CREATE TABLE analytics.hourly (
            source_id text NOT NULL, measurement_type text NOT NULL, unit text NOT NULL,
            source_day date NOT NULL, source_year int NOT NULL, source_month int NOT NULL,
            zone_id text, local_hour int NOT NULL CHECK(local_hour BETWEEN 0 AND 23),
            count bigint NOT NULL CHECK(count > 0), total_value double precision NOT NULL,
            min double precision NOT NULL, max double precision NOT NULL, demo_events bigint NOT NULL
        ) PARTITION BY RANGE(source_day)''')
        for year in (2025, 2026):
            for month in range(1, 13):
                first = date(year, month, 1)
                if month == 12:
                    last = date(year + 1, 1, 1)
                else:
                    last = date(year, month + 1, 1)
                conn.execute(sql.SQL('CREATE TABLE analytics.{} PARTITION OF analytics.hourly FOR VALUES FROM ({}) TO ({})').format(
                    sql.Identifier(f'hourly_{year}_{month:02d}'), sql.Literal(first), sql.Literal(last)))
        columns = ('source_id', 'measurement_type', 'unit', 'source_day', 'source_year',
                   'source_month', 'zone_id', 'local_hour', 'count', 'total_value', 'min', 'max', 'demo_events')
        table = pq.read_table(output / 'hourly')
        with conn.cursor().copy('COPY analytics.hourly (' + ','.join(columns) + ') FROM STDIN') as copy:
            for row in table.to_pylist():
                copy.write_row([row[name] for name in columns])
        conn.execute('CREATE INDEX hourly_type_day ON analytics.hourly(measurement_type,source_day)')
        conn.execute('CREATE INDEX hourly_zone_day ON analytics.hourly(zone_id,source_day)')
        conn.execute('''CREATE MATERIALIZED VIEW analytics.daily AS SELECT
            source_id,measurement_type,unit,source_day,zone_id,
            sum(count)::bigint AS count,sum(total_value) AS total_value,
            sum(total_value)/sum(count) AS mean,min(min) AS min,max(max) AS max,
            sum(demo_events)::bigint AS demo_events
            FROM analytics.hourly GROUP BY source_id,measurement_type,unit,source_day,zone_id''')
        conn.execute('CREATE INDEX daily_type_day ON analytics.daily(measurement_type,source_day)')
        total = conn.execute('SELECT sum(count) FROM analytics.hourly').fetchone()[0]
        if total != summary['input_records']:
            raise ValueError('PostgreSQL aggregate reconciliation failed')
        conn.execute('INSERT INTO analytics.runs VALUES (%s,%s)', (fingerprint, total))
        conn.execute('ANALYZE analytics.hourly')
        plan = conn.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM analytics.hourly WHERE measurement_type=%s AND source_day=%s",
                            ('MAD-AIR:8', date(2025, 1, 15))).fetchone()[0]
        return {'status': 'PASS', 'represented_input_records': int(total), 'hourly_rows': table.num_rows,
                'partitions': 24, 'materialized_view': 'analytics.daily',
                'elapsed_seconds': time.perf_counter() - started, 'fingerprint': fingerprint, 'plan': plan}


def query(measurement, start, end, zone, hour_start=0, hour_end=23):
    with connection(readonly=True) as conn:
        conn.execute("SET LOCAL statement_timeout='8000ms'")
        cursor = conn.execute('''SELECT source_day::text,zone_id,unit,sum(count)::bigint AS count,
            sum(total_value) AS total_value,min(min) AS min,max(max) AS max,
            sum(demo_events)::bigint AS demo_events FROM analytics.hourly
            WHERE measurement_type=%s AND source_day BETWEEN %s AND %s
            AND (%s::text IS NULL OR zone_id=%s) AND local_hour BETWEEN %s AND %s
            GROUP BY source_day,zone_id,unit ORDER BY source_day''',
            (measurement, start, end, zone, zone, hour_start, hour_end))
        names = [column.name for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spark-output', type=Path, default=DEFAULT_SPARK_OUTPUT)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.report is not None and args.report.exists():
        parser.error('Use a new report path')
    result = materialize(args.spark_output)
    if args.report is not None:
        with args.report.open('x') as stream:
            json.dump(result, stream, indent=2)
    print(json.dumps({key: value for key, value in result.items() if key != 'plan'}, indent=2))
