"""Operaciones explícitas sobre el proyecto Compose propio smartcity-final.

No ejecuta down -v, limpiezas globales ni comandos sobre bases compartidas.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SAFE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$')

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENERATION = ROOT / 'data/final'
DEFAULT_SPARK_OUTPUT = ROOT / 'data/spark-cluster'
DEFAULT_BATCH_REPORT = ROOT / 'data/reportes-local/batch.json'
DEFAULT_ACTIVITY_REPORT = ROOT / 'data/reportes-local/batch-activity.json'


def generation_mount_name(generation, root=ROOT):
    resolved = Path(generation).resolve()
    data_root = (Path(root) / 'data').resolve()
    if resolved.parent != data_root:
        raise ValueError('Generation must be a directory directly under data/')
    if not SAFE_NAME.match(resolved.name):
        raise ValueError('Unsafe generation directory name')
    return resolved.name


def compose(*args, capture=True, timeout=1800, extra_env=None):
    credential_path = ROOT / '.cache/final-password'
    credential_path.parent.mkdir(exist_ok=True)
    if not credential_path.exists():
        import secrets
        with credential_path.open('x') as stream:
            stream.write(secrets.token_urlsafe(32))
        credential_path.chmod(0o600)
    key = ROOT / '.cache/final-repl-key'
    if not key.exists():
        import base64
        with key.open('x') as stream:
            stream.write(base64.b64encode(os.urandom(48)).decode())
        key.chmod(0o600)
    env = dict(os.environ)
    env.update({'SMARTCITY_FINAL_PASSWORD': credential_path.read_text(), 'SMARTCITY_REPL_KEY': key.read_text(),
                'SMARTCITY_UID': str(os.getuid()), 'SMARTCITY_GID': str(os.getgid())})
    if extra_env:
        env.update(extra_env)
    return subprocess.run(['docker', 'compose', '-f', str(ROOT / 'final/compose.yaml'), *args],
                          cwd=ROOT, env=env, text=True, capture_output=capture,
                          check=True, timeout=timeout)


def hdfs(*args):
    return compose('exec', '-T', 'namenode', 'hdfs', *args).stdout


def upload(generation):
    manifest = json.loads((generation / 'manifest.json').read_text())
    path = generation / 'observations.jsonl'
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    if digest.hexdigest() != manifest['output_hashes']['observations.jsonl']:
        raise ValueError('Changed generation')
    name = generation_mount_name(generation)
    report = hdfs('dfsadmin', '-report')
    if 'Live datanodes (2)' not in report:
        raise ValueError('Both DataNodes must be live')
    hdfs('dfs', '-mkdir', '-p', '/smartcity/final')
    # Sin -f, HDFS no sobrescribe la carga existente.
    hdfs('dfs', '-put', f'/inputs/{name}/observations.jsonl', '/smartcity/final/observations.jsonl')
    hdfs('dfs', '-put', f'/inputs/{name}/manifest.json', '/smartcity/final/manifest.json')
    hdfs('dfs', '-setrep', '-w', '2', '/smartcity/final/observations.jsonl')
    return {'status': 'PASS', 'datanodes': report,
            'files': hdfs('dfs', '-ls', '/smartcity/final'),
            'blocks': hdfs('fsck', '/smartcity/final/observations.jsonl', '-files', '-blocks', '-locations'),
            'input_sha256': digest.hexdigest(),
            'limits': 'Two containers on one host, permissions disabled only in isolated network'}


def batch(activity=False):
    job = 'activity' if activity else 'counts'
    mapper = 'map-activity' if activity else 'map'
    destination = f'/smartcity/batch-{job}-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    result = compose('exec', '-T', '-e', 'HADOOP_HEAPSIZE_MAX=256', 'namenode', 'hadoop', 'jar',
        '/opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar',
        '-D', 'mapreduce.framework.name=local', '-D', 'mapreduce.job.reduces=1',
        '-D', 'mapreduce.map.java.opts=-Xmx128m', '-D', 'mapreduce.reduce.java.opts=-Xmx128m',
        '-D', 'mapreduce.local.map.tasks.maximum=1',
        '-D', 'mapreduce.task.io.sort.mb=16',
        '-files', '/jobs/batch.py', '-input', '/smartcity/final/observations.jsonl',
        '-output', destination, '-mapper', f'/usr/bin/python batch.py {mapper}',
        '-reducer', '/usr/bin/python batch.py reduce')
    return {'status': 'EXECUTED', 'mode': 'Hadoop MapReduce local framework, HDFS distributed storage',
            'stdout': result.stdout, 'stderr': result.stderr,
             'destination': destination, 'counts': hdfs('dfs', '-cat', destination + '/part-*')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['up', 'upload', 'batch', 'batch-activity', 'spark', 'status', 'stop'])
    parser.add_argument('--generation', type=Path, default=DEFAULT_GENERATION)
    parser.add_argument('--spark-output', type=Path, default=DEFAULT_SPARK_OUTPUT)
    parser.add_argument('--min-records', type=int, default=1_000_000)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.action == 'up':
        compose('up', '-d', 'namenode', 'datanode1', 'datanode2', 'spark-master',
                'spark-worker1', 'spark-worker2', 'postgres', 'mongo1', 'mongo2',
                'mongo-arbiter', capture=False)
        return
    if args.action == 'stop':
        compose('stop', capture=False)
        return
    if args.action == 'status':
        print(compose('ps').stdout)
        return
    if args.report is None or args.report.exists():
        parser.error('A new --report path is required before executing this action')
    if args.action == 'upload':
        result = upload(args.generation)
    elif args.action in ('batch', 'batch-activity'):
        result = batch(activity=args.action == 'batch-activity')
    else:
        if args.min_records < 1:
            parser.error('--min-records must be at least 1')
        process = compose('run', '--rm', '--use-aliases', 'spark-driver', timeout=2400, extra_env={
            'SMARTCITY_GENERATION_NAME': generation_mount_name(args.generation),
            'SMARTCITY_SPARK_OUTPUT_NAME': generation_mount_name(args.spark_output),
            'SMARTCITY_MIN_RECORDS': str(args.min_records)})
        result = {'status': 'EXECUTED', 'stdout': process.stdout, 'stderr': process.stderr}
    result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
    print('Evidence:', args.report)


if __name__ == '__main__':
    main()
