"""Run official SmartCity validation and collect native evidence outside source code.

Run as the repository owner with a temporary docker primary group via sudo.
No server credentials, shared endpoint, system installation, or group edits.
"""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / 'config.json').read_text())
ROOT = Path(CONFIG['repository'])
DOCKER = ['docker', '--host', 'unix:///var/run/docker.sock']
GENERATION = CONFIG['generation']


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def command(args, log, timeout=1800):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    (OUTPUT / log).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{log}: exit={result.returncode}; see {OUTPUT / log}')
    return result.stdout


def save(name, data):
    (OUTPUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main(status):
    os.chdir(ROOT)
    if os.getuid() == 0:
        raise RuntimeError('Run as kemgarro with temporary docker group, not as root')
    if git('branch', '--show-current') != 'main':
        raise RuntimeError('main is required')
    head = git('rev-parse', 'HEAD')
    if head != CONFIG['expected_commit'] or head != git('rev-parse', 'origin/main'):
        raise RuntimeError('Repository revision differs from the reviewed official main')
    if git('diff', '--name-only') or git('diff', '--cached', '--name-only'):
        raise RuntimeError('Tracked source modifications detected')
    tracked_paths = git('ls-files').splitlines()
    source_hashes = {p: digest(ROOT / p) for p in tracked_paths if (ROOT / p).is_file()}
    status['head'] = head
    save('evidence-helper-hashes.json', {p.name: digest(p) for p in [
        Path(__file__), HERE / 'capture_metadata.js', HERE / 'config.json']})
    versions = {}
    for line in (ROOT / 'research/datasets/scripts/requirements.lock').read_text().splitlines():
        if not line.strip():
            continue
        name, expected = line.split('==')
        actual = version(name)
        if actual != expected:
            raise RuntimeError(f'Dependency version mismatch: {name}')
        versions[name] = actual
    save('python-environment.json', {'python': sys.version, 'versions': versions})
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'research/datasets/scripts'))
    from sprint1.basico.preparar_v2 import verificar_paquete
    prepared = ROOT / 'research/datasets/private_results' / GENERATION
    prep = verificar_paquete(prepared)
    if prep['accepted'] != 748889 or prep['contract'] != 'madrid-draft-v2':
        raise RuntimeError('Unexpected prepared package')
    private_hashes = {name: digest(prepared / name) for name in [*prep['output_hashes'], 'preparation.json']}
    save('package-before.json', {'accepted': prep['accepted'], 'hashes': private_hashes})
    status['package'] = 'PASS'
    info = command(DOCKER + ['info', '--format', '{{json .ServerVersion}}'], 'docker-info.log', 30)
    status['docker_version'] = json.loads(info.strip())
    image = subprocess.run(DOCKER + ['image', 'inspect', 'mongo:7.0.16'], cwd=ROOT,
                           text=True, capture_output=True, timeout=30)
    if image.returncode:
        print('Downloading mongo:7.0.16 on local Docker...', flush=True)
        command(DOCKER + ['pull', 'mongo:7.0.16'], 'image-pull.log')
    save('image-inspection.json', json.loads(command(
        DOCKER + ['image', 'inspect', 'mongo:7.0.16'], 'image-inspection.log', 30)))
    Path('/tmp/opencode').mkdir(exist_ok=True)
    print('Running OFFICIAL native sample...', flush=True)
    status['native_sample'] = 'RUNNING'
    sample = command([sys.executable, '-B', 'scripts/test_mongo_v2_sample.py'], 'native-sample.log')
    if 'Mongo v2 native sample: PASS' not in sample:
        raise RuntimeError('Native sample completion marker absent')
    status['native_sample'] = 'PASS'
    print('Native sample PASS. Running OFFICIAL massive MongoDB validation...', flush=True)
    status['massive_mongodb'] = 'RUNNING'

    import unified_full_load as native
    if native.DOCKER != DOCKER:
        raise RuntimeError('Official runner Docker endpoint differs from local fixed socket')
    original_container = native.container

    @contextmanager
    def evidence_container(engine, image, private, report):
        # Delegate all creation, limits, lifecycle and cleanup to the official code.
        with original_container(engine, image, private, report) as name:
            yield name
            if engine != 'mongodb':
                raise RuntimeError('This evidence runner allows only MongoDB')
            names_output = native.command(['exec', name, 'mongosh', '--quiet',
                'mongodb://127.0.0.1:27017/admin', '--eval',
                "print('OWNED_DATABASES='+JSON.stringify(db.adminCommand({listDatabases:1,nameOnly:true}).databases.map(d=>d.name).filter(n=>/^smartcity_v2_[a-f0-9]{12}$/.test(n))));"]).stdout
            names = json.loads(next(line.split('=', 1)[1] for line in names_output.splitlines()
                                    if line.startswith('OWNED_DATABASES=')))
            if len(names) != 1:
                raise RuntimeError('Exactly one owned v2 database required')
            uri = 'mongodb://127.0.0.1:27017/' + names[0]
            status['indexes_validators_plans'] = 'RUNNING'
            native.command(['cp', str(HERE / 'capture_metadata.js'), name + ':/tmp/capture_metadata.js'])
            metadata_output = native.command(['exec', name, 'mongosh', '--quiet', uri,
                                              '/tmp/capture_metadata.js']).stdout
            (OUTPUT / 'native-metadata.log').write_text(metadata_output)
            metadata = json.loads(next(line.split('=', 1)[1] for line in metadata_output.splitlines()
                                       if line.startswith('NATIVE_METADATA=')))
            save('native-metadata.json', metadata)
            status['indexes_validators_plans'] = 'PASS'
            # Reuse the official CRUD script, affecting only practica_crud.
            status['seven_crud_operations'] = 'RUNNING'
            crud_source = ROOT / 'sprint1/basico/crud_mongodb.js'
            native.command(['cp', str(crud_source), name + ':/tmp/crud_official.js'])
            crud_output = native.command(['exec', name, 'mongosh', '--quiet', uri,
                '--eval', 'var GUARDAR=true; load("/tmp/crud_official.js");']).stdout
            (OUTPUT / 'native-crud.log').write_text(crud_output)
            if 'CRUD_BASICO_PASS' not in crud_output:
                raise RuntimeError('Official CRUD completion marker absent')
            post_output = native.command(['exec', name, 'mongosh', '--quiet', uri, '--eval',
                "if(db.readings.countDocuments({})!==748889 || db.getCollectionNames().includes('practica_crud')) throw new Error('CRUD isolation failed'); print('CRUD_ISOLATION_PASS');"]).stdout
            if 'CRUD_ISOLATION_PASS' not in post_output:
                raise RuntimeError('CRUD isolation completion marker absent')
            save('native-crud.json', {'status': 'PASS', 'script': str(crud_source.relative_to(ROOT)),
                'script_sha256': digest(crud_source), 'collection': 'practica_crud',
                'operations': ['insertOne', 'insertMany', 'findOne', 'find', 'updateOne', 'updateMany', 'deleteOne'],
                'readings_before_and_after': 748889, 'practice_collection_removed': True})
            status['seven_crud_operations'] = 'PASS'

    before_reports = set((ROOT / 'research/datasets/results' / GENERATION).glob('execution-*.json'))
    native.container = evidence_container
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(ROOT / 'scripts/validar_v2.py'), '--generacion', GENERATION, '--motor', 'mongodb']
        with (OUTPUT / 'massive-validation.log').open('w') as log, redirect_stdout(log), redirect_stderr(log):
            namespace = runpy.run_path(str(ROOT / 'scripts/validar_v2.py'), run_name='__main__')
        result = namespace['informe']
    finally:
        native.container = original_container
        sys.argv = old_argv
        new_reports = set((ROOT / 'research/datasets/results' / GENERATION).glob('execution-*.json')) - before_reports
        status['new_official_reports'] = [str(p.relative_to(ROOT)) for p in sorted(new_reports)]
        for report_path in new_reports:
            (OUTPUT / report_path.name).write_bytes(report_path.read_bytes())
    mongo = result.get('mongodb', {})
    if (result.get('status') != 'PASS' or mongo.get('count') != 748889 or
            not mongo.get('replay_verified') or not mongo.get('container_removed') or
            not mongo.get('anonymous_volumes_removed') or
            set(mongo.get('results', {})) != {f'MG{i:02d}' for i in range(1, 11)}):
        raise RuntimeError('Official massive validation requirements not met')
    status['massive_mongodb'] = 'PASS'
    print('Massive validation PASS. Running OFFICIAL cross-engine evidence verifier...', flush=True)
    status['reconciliation'] = 'RUNNING'
    reconciliation = command([sys.executable, '-B', 'scripts/verificar_v2.py',
                              '--generacion', GENERATION], 'reconciliation.log')
    reconciled = json.loads(reconciliation)
    if reconciled.get('verified') is not True or reconciled.get('accepted') != 748889:
        raise RuntimeError('Reconciliation not verified')
    save('reconciliation.json', reconciled)
    status['reconciliation'] = 'PASS'
    for path, expected in private_hashes.items():
        if digest(prepared / path) != expected:
            raise RuntimeError('Private package changed: ' + path)
    for path, expected in source_hashes.items():
        if digest(ROOT / path) != expected:
            raise RuntimeError('Tracked official file changed: ' + path)
    status.update(private_files_unchanged=True, tracked_files_unchanged=True,
                  readings=mongo['count'], results=mongo['results'],
                  ids_payload_sha256=mongo['ids_payload_sha256'],
                  cleanup_verified=True, overall_status='PASS')


if __name__ == '__main__':
    os.umask(0o077)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    OUTPUT = HERE / ('execution-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + os.urandom(4).hex())
    OUTPUT.mkdir(mode=0o700)
    status = {'overall_status': 'FAIL', 'started_at': datetime.now(timezone.utc).isoformat(),
              'native_sample': 'NOT_EXECUTED', 'massive_mongodb': 'NOT_EXECUTED',
              'reconciliation': 'NOT_EXECUTED', 'seven_crud_operations': 'NOT_EXECUTED',
              'indexes_validators_plans': 'NOT_CAPTURED', 'shared_server_used': False,
              'persistent_group_or_socket_permissions_changed': False}
    exit_code = 1
    try:
        print('Evidence directory: ' + str(OUTPUT), flush=True)
        main(status)
        exit_code = 0
    except BaseException as exc:
        for key in ['native_sample', 'massive_mongodb', 'reconciliation',
                    'seven_crud_operations', 'indexes_validators_plans']:
            if status[key] == 'RUNNING':
                status[key] = 'FAIL'
        status['error'] = str(exc)
        (OUTPUT / 'error.log').write_text(traceback.format_exc())
        print('Validation stopped: ' + str(exc), file=sys.stderr, flush=True)
    finally:
        status['finished_at'] = datetime.now(timezone.utc).isoformat()
        save('status.json', status)
        (OUTPUT / 'INFORME.md').write_text(
            '# MongoDB native validation\n\nOverall: **' + status['overall_status'] + '**\n\n' +
            '\n'.join('- ' + key + ': ' + str(status.get(key)) for key in [
                'native_sample', 'massive_mongodb', 'reconciliation', 'seven_crud_operations',
                'indexes_validators_plans', 'cleanup_verified', 'tracked_files_unchanged',
                'private_files_unchanged', 'error']) +
            '\n\nSee status.json, official execution report, native-metadata.json and native-crud.log.\n')
        with (OUTPUT / 'SHA256SUMS').open('w') as sums:
            for file in sorted(OUTPUT.iterdir()):
                if file.is_file() and file.name != 'SHA256SUMS':
                    sums.write(digest(file) + '  ' + file.name + '\n')
        print('Overall: ' + status['overall_status'], flush=True)
        print('Evidence directory: ' + str(OUTPUT), flush=True)
    raise SystemExit(exit_code)
