"""Run MongoDB bounded native test ONLY on local Docker Unix socket; cleanup our container.

Requires explicit --engine mongodb; never reads .env, remote URI, or Docker context.
No image pulled by this script; install the image separately with authorization.
"""
import argparse
from hashlib import sha256
import json
import subprocess
import time
import uuid

from phase5_contract import ROOT, OUT, PRIVATE, digest, validate_document, validate_bundle, canonical

DOCKER = ['docker','--host','unix:///var/run/docker.sock']
IMAGE = 'mongo:7.0.16'


def command(args, **kwargs):
    return subprocess.run(DOCKER+args, capture_output=True, text=True, check=True, timeout=180, **kwargs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', choices=['mongodb'], required=True)
    args = p.parse_args()
    validate_bundle()
    sample = json.loads((PRIVATE/'sample.extjson').read_text())
    assert 1000<=len(sample)<=10000
    catalogs = json.loads((PRIVATE/'catalogs.json').read_text())
    for document in sample:
        validate_document(document, catalogs)
    image = json.loads(command(['image','inspect',IMAGE]).stdout)[0]
    token = uuid.uuid4().hex[:12]
    name = 'smartcity-phase5-mongo-'+token
    database = 'smartcity_phase5_'+token
    result = {'engine':'MongoDB','native_executed':False, 'local_socket':'unix:///var/run/docker.sock',
              'image':IMAGE,'image_id':image['Id'],'repo_digests':image.get('RepoDigests',[]),
              'network':'none','published_ports':[], 'database':database, 'container':name,
               'input_sha256':digest(PRIVATE/'sample.extjson')}
    result['source_hashes'] = {filename:digest(ROOT/'scripts'/filename) for filename in
        ('phase5_contract.py','phase5_prepare.py','phase5_native.py','phase5_mongo_test.js')}
    created = False
    try:
        started = command(['run','--detach','--pull=never','--name',name,'--network','none',
            '--memory=1g','--cpus=1','--mount',f'type=bind,src={PRIVATE},dst=/inputs,readonly',
            '--mount',f'type=bind,src={ROOT / "scripts"},dst=/scripts,readonly',
            '--mount',f'type=bind,src={OUT},dst=/evidence,readonly',IMAGE,
            'mongod','--bind_ip','127.0.0.1','--wiredTigerCacheSizeGB','0.25'])
        created = True
        result['container_id'] = started.stdout.strip()
        mounts = json.loads(command(['inspect',name,'--format','{{json .Mounts}}']).stdout)
        volumes = [m['Name'] for m in mounts if m['Type']=='volume']
        result['owned_anonymous_volumes'] = volumes
        for _ in range(100):
            test = subprocess.run(DOCKER+['exec',name,'mongosh','--quiet','mongodb://127.0.0.1:27017/admin','--eval','db.adminCommand({ping:1}).ok'],
                                  capture_output=True,text=True,timeout=10)
            if test.returncode==0:
                break
            running = command(['inspect',name,'--format','{{.State.Running}}']).stdout.strip()
            if running=='false':
                result['last_readiness_stderr'] = test.stderr
                raise RuntimeError('Disposable MongoDB exited during startup; see mongodb_server.log')
            time.sleep(.25)
        else:
            result['last_readiness_stderr'] = test.stderr
            raise RuntimeError('Disposable MongoDB readiness timeout')
        t = time.perf_counter()
        native = command(['exec',name,'mongosh','--quiet',f'mongodb://127.0.0.1:27017/{database}',
                          '/scripts/phase5_mongo_test.js'])
        (OUT/'mongodb_execution.log').write_text(native.stdout+'\n'+native.stderr)
        line = next(s for s in native.stdout.splitlines() if s.startswith('PHASE5_RESULT='))
        result.update(json.loads(line.split('=',1)[1]))
        exported = result.pop('ids_values')
        expected = sorted([{'measurement_id':d['measurement_id'], 'value':d['value']} for d in sample], key=lambda d:d['measurement_id'])
        if exported != expected:
            raise ValueError('Mongo IDs/values differ from common export')
        result['ids_values_sha256'] = sha256(canonical(exported).encode()).hexdigest()
        pg = json.loads((OUT/'postgresql_sample.json').read_text())
        if (pg['input_sha256'] != result['input_sha256']
                or pg['ids_values_sha256'] != result['ids_values_sha256']):
            raise ValueError('PostgreSQL/Mongo reconciliation mismatch')
        result['postgresql_reconciled'] = True
        result['native_script_elapsed_seconds'] = time.perf_counter()-t
    except Exception as exc:
        result['error'] = str(exc)
        if isinstance(exc,subprocess.CalledProcessError):
            (OUT/'mongodb_execution.log').write_text((exc.stdout or '')+'\n'+(exc.stderr or ''))
        raise
    finally:
        if created:
            logs = subprocess.run(DOCKER+['logs',name],capture_output=True,text=True,timeout=20)
            (OUT/'mongodb_server.log').write_text(logs.stdout+'\n'+logs.stderr)
            stopped = subprocess.run(DOCKER+['stop',name],capture_output=True,text=True,timeout=60)
            result['cleanup_returncode'] = stopped.returncode
            removed = subprocess.run(DOCKER+['rm','--volumes',name],capture_output=True,text=True,timeout=30)
            result['remove_returncode'] = removed.returncode
            result['container_removed'] = subprocess.run(DOCKER+['inspect',name],capture_output=True,timeout=10).returncode!=0
            result['anonymous_volumes_removed'] = all(subprocess.run(DOCKER+['volume','inspect',v],capture_output=True,timeout=10).returncode!=0 for v in result.get('owned_anonymous_volumes',[]))
        (OUT/'mongodb_execution.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'native_executed':result['native_executed'],'sample_size':result['sample_size'],
                     'queries':result['local_native_query_designs_executed'],
                     'container_removed':result['container_removed'],'volumes_removed':result['anonymous_volumes_removed']},indent=2))


if __name__=='__main__':
    main()
