#!/usr/bin/env python3
"""Read-only SQL evidence from the private native validation instance."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests/sprint1'), str(ROOT / 'research/datasets/scripts')]
from benchmark_real_postgres import read_air_summary
from phase5_contract import digest


def run(data):
    data = data.resolve(strict=True)
    cache = (ROOT / '.cache').resolve()
    if data.parent.parent != cache or not data.parent.name.startswith('pg3nf-'):
        raise ValueError('Only a private cluster created by the 3NF validator is accepted')
    pid_lines = (data / 'postmaster.pid').read_text().splitlines()
    socket = Path(pid_lines[4])
    if (pid_lines[3] != '55439' or not str(socket).startswith('/tmp/sc3nf-')
        or socket.stat().st_uid != os.getuid() or socket.stat().st_mode & 0o077):
        raise ValueError('Not the owned private Unix socket')
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
    env.update(PGOPTIONS='-c default_transaction_read_only=on -c timezone=UTC -c statement_timeout=120000')

    def query(text):
        sql = 'BEGIN READ ONLY; SELECT to_jsonb(t) FROM (' + text.rstrip(';\n') + ') t; COMMIT;'
        r = subprocess.run(['/usr/lib/postgresql/16/bin/psql', '-X', '-Atq', '-h', str(socket),
            '-p', '55439', '-d', 'postgres', '-U', env.get('USER', 'kemgarro'), '-v', 'ON_ERROR_STOP=1'],
            input=sql, text=True, capture_output=True, env=env, timeout=150)
        if r.returncode:
            raise RuntimeError('Read-only SQL evidence failed')
        return [json.loads(line) for line in r.stdout.splitlines()]

    advanced = ROOT / 'sprint1/postgres/sql_avanzado_observado.sql'
    legacy_queries = ROOT / 'sprint1/postgres/queries.sql'
    source = ROOT / 'research/datasets/private_results/expanded-v2-2025-01/accepted.extjsonl'
    sums = defaultdict(list)
    channels = Counter()
    by_source = Counter()
    with source.open() as f:
        for line in f:
            d = json.loads(line)
            by_source[d['source_id']] += 1
            if '2024-12-31T23:00:00Z' <= d['observed_at']['$date'] < '2025-01-31T23:00:00Z':
                channels[d['channel_id']] += 1
            if (d['source_id'] == 'MAD-AIR' and
                '2025-01-01T00:00:00' <= d['original_time'] < '2025-01-02T00:00:00'):
                sums[(d['measurement_type'], d['unit'])].append(d['value'])
    air = query(read_air_summary(legacy_queries))
    assert len(air) == len(sums)
    for row in air:
        values = sums[(row['measurement_type'], row['unit'])]
        assert row['reading_count'] == len(values)
        assert row['minimum_value'] == min(values) and row['maximum_value'] == max(values)
        assert math.isclose(row['total_value'], sum(values), rel_tol=1e-12)
        assert math.isclose(row['average_value'], sum(values) / len(values), rel_tol=1e-12)
    ranking = query(advanced.read_text())
    ranks = {n: i for i, n in enumerate(sorted(set(channels.values()), reverse=True), 1)}
    expected = [{'channel_id': k, 'reading_count': n, 'activity_rank': ranks[n]}
        for k, n in sorted(channels.items(), key=lambda x: (-x[1], x[0]))[:5]]
    assert ranking == expected
    distinct = query('SELECT DISTINCT source_id FROM smartcity.observation_contract ORDER BY source_id')
    assert [r['source_id'] for r in distinct] == sorted(by_source)
    result = {'status': 'PASS', 'scope': 'read-only full normalized generation',
        'finished_at': datetime.now(timezone.utc).isoformat(), 'read_only': True,
        'tcp_enabled': False, 'shared_server_modified': False,
        'source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in [Path(__file__), advanced, legacy_queries]},
        'input_sha256': digest(source), 'independent_count': sum(by_source.values()),
        'air_summary': air, 'observed_channel_ranking': ranking, 'distinct_sources': distinct,
        'independent_full_result_match': True,
        'operations': ['SELECT DISTINCT', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT',
                       'WHERE', 'GROUP BY', 'HAVING', 'CTE', 'DENSE_RANK', 'ORDER BY']}
    parent = ROOT / 'sprint1/postgres/evidencias/3nf'
    target = parent / ('advanced-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + os.urandom(4).hex() + '.json')
    with target.open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write('\n')
    target.with_suffix('.sha256').write_text(digest(target) + '  ' + target.name + '\n')
    print(target, '\nSQL avanzado: PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    run(parser.parse_args().data)
