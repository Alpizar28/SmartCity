"""Full accepted-generation validation on owned, isolated local Docker containers only."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
import sqlite3
import subprocess
import time
import uuid

from phase5_contract import ROOT, canonical, digest, stable_id
from phase5_postgres_sample import sql_literal
from unified_expand import generation_paths, verify_generation, atomic_json
from unified_synthetic import build_administrative_seed

DOCKER = ['docker','--host','unix:///var/run/docker.sock']


def command(args, **kwargs):
    return subprocess.run(DOCKER+args,check=True,capture_output=True,text=True,timeout=1800,**kwargs)


@contextmanager
def container(engine, image, private, report):
    name = 'smartcity-full-'+engine+'-'+uuid.uuid4().hex[:12]
    image_info = json.loads(command(['image','inspect',image]).stdout)[0]
    report.update(engine=engine,image=image,image_id=image_info['Id'],network='none',published_ports=[],
                  local_socket='unix:///var/run/docker.sock',memory_limit_bytes=2*1024**3,cpus=2,
                  container=name,container_removed=False,anonymous_volumes_removed=False)
    created = False
    try:
        args=['run','--detach','--pull=never','--name',name,'--network','none','--memory=2g','--cpus=2',
              '--mount',f'type=bind,src={private},dst=/inputs,readonly',
              '--mount',f'type=bind,src={ROOT / "scripts"},dst=/scripts,readonly']
        if engine=='postgresql':
            args += ['-e','POSTGRES_HOST_AUTH_METHOD=trust',image]
        else:
            args += [image,'mongod','--bind_ip','127.0.0.1','--wiredTigerCacheSizeGB','0.5']
        command(args)
        created = True
        mounts=json.loads(command(['inspect',name,'--format','{{json .Mounts}}']).stdout)
        volumes=[m['Name'] for m in mounts if m['Type']=='volume']
        for _ in range(120):
            ready=(['exec',name,'pg_isready','-U','postgres'] if engine=='postgresql' else
                   ['exec',name,'mongosh','--quiet','--eval','db.adminCommand({ping:1}).ok'])
            result=subprocess.run(DOCKER+ready,capture_output=True,text=True,timeout=10)
            if result.returncode==0:
                if engine!='postgresql' or 'init process complete' in command(['logs',name]).stdout:
                    break
            time.sleep(.25)
        else:
            raise RuntimeError('Owned local container failed readiness')
        yield name
        peak=command(['exec',name,'cat','/sys/fs/cgroup/memory.peak']).stdout.strip()
        report['peak_cgroup_memory_bytes']=int(peak)
    finally:
        if created:
            # Only this randomly named owned container and its anonymous volumes.
            subprocess.run(DOCKER+['stop',name],capture_output=True,timeout=90)
            subprocess.run(DOCKER+['rm','--volumes',name],capture_output=True,timeout=60)
            report['container_removed']=subprocess.run(DOCKER+['inspect',name],capture_output=True).returncode!=0
            report['anonymous_volumes_removed']=all(subprocess.run(DOCKER+['volume','inspect',v],capture_output=True).returncode!=0 for v in volumes)


def administrative_seed(private, out):
    """Read a sealed deterministic demo package tied to current catalogs."""
    manifest = json.loads((out/'administrative_manifest.json').read_text())
    path = private / manifest['administrative_seed_file']
    catalogs_path = private / 'catalogs.json'
    if digest(path) != manifest['administrative_seed_sha256'] or digest(catalogs_path) != manifest['catalogs_sha256']:
        raise ValueError('Administrative seed or catalogs changed')
    seed = json.loads(path.read_text())
    expected = build_administrative_seed(json.loads(catalogs_path.read_text()), manifest['catalogs_sha256'], manifest['seed'])
    if seed != expected:
        raise ValueError('Administrative seed is not deterministic')
    counts = {key: len(seed[key]) for key in ('organizations', 'users', 'sensors')}
    if counts != manifest['counts'] or not all(counts.values()) or seed.get('synthetic_measurements') != 0:
        raise ValueError('Administrative seed counts or provenance invalid')
    if any(row.get('data_origin') != 'synthetic' for rows in (seed[k] for k in counts) for row in rows):
        raise ValueError('Administrative data must be synthetic')
    return seed


def catalog_sql(catalogs):
    statements=['SET search_path=smartcity,pg_temp;']
    def insert(table,rows,types):
        columns=','.join(t.split()[0] for t in types.split(','))
        statements.append(f'INSERT INTO {table}({columns}) SELECT {columns} FROM json_to_recordset({sql_literal(rows)}) AS x({types});')
    insert('sources',list(catalogs['sources'].values()),'source_id text,name text,publisher text')
    insert('source_versions',list(catalogs['source_versions'].values()),'source_version text,source_id text,original_path text')
    insert('zones',list(catalogs['zones'].values()),'zone_id text,name text,level text')
    locations,stations=[],[]
    for row in catalogs['stations'].values():
        location=stable_id('location',row['station_id'],'current-inventory')
        locations.append({**row,'location_id':location,'inventory_version':
                          row['inventory_reference']['sha256'] if row.get('inventory_reference') else None})
        stations.append({**row,'location_id':location})
    insert('locations',locations,'location_id text,zone_id text,name text,latitude double precision,longitude double precision,coordinate_crs text,historical_location_verified boolean,inventory_version text')
    insert('stations',stations,'station_id text,source_id text,source_key text,name text,location_id text,inventory_present boolean')
    types=list(catalogs['measurement_types'].values())
    insert('sensor_categories',types,'category_id text,name text')
    insert('measurement_types',types,'measurement_type text,source_id text,code text,category_id text,unit text,candidate_unit text,unit_status text')
    insert('channels',list(catalogs['channels'].values()),'channel_id text,station_id text,source_id text,sensor_id text,source_key jsonb,measurement_type text,catalog_basis text')
    return '\n'.join(statements)


def administrative_sql(seed):
    statements = ['SET search_path=smartcity,pg_temp;']
    def insert(table, rows, types):
        columns = ','.join(field.split()[0] for field in types.split(','))
        statements.append(f'INSERT INTO {table}({columns}) SELECT {columns} FROM json_to_recordset({sql_literal(rows)}) AS x({types});')
    insert('organizations', seed['organizations'], 'organization_id text,name text,responsible_person_or_role text,evidence_reference text,data_origin text,provenance jsonb')
    insert('users', seed['users'], 'user_id text,name text,email text,consent_reference text,demo_only boolean,data_origin text')
    insert('sensors', seed['sensors'], 'sensor_id text,name text,category_id text,station_id text,installation_date date,administrative_status text,status_effective_at timestamptz,organization_id text,identity_evidence_reference text,data_origin text,provenance jsonb')
    return '\n'.join(statements)


def postgres(private, out, report):
    with container('postgresql','postgres:16-alpine',private,report) as name:
        def sql(query):
            return command(['exec','-i',name,'psql','-X','-U','postgres','-Atq','-v','ON_ERROR_STOP=1'],
                           input="SET statement_timeout='25min'; SET timezone='UTC'; "+query).stdout.strip()
        report['version']=sql('SELECT version();')
        sql((ROOT/'scripts/phase5_postgresql.sql').read_text())
        sql(catalog_sql(json.loads((private/'catalogs.json').read_text())))
        seed = administrative_seed(private, out)
        sql(administrative_sql(seed))
        report['administrative_counts'] = json.loads(sql("""SELECT json_object_agg(name,count) FROM (
          SELECT 'organizations' AS name,count(*)::bigint AS count FROM smartcity.organizations
          UNION ALL SELECT 'users',count(*)::bigint FROM smartcity.users
          UNION ALL SELECT 'sensors',count(*)::bigint FROM smartcity.sensors
        ) AS counts"""))
        report['channels_assigned_to_synthetic_sensors'] = int(sql("SELECT count(*) FROM smartcity.channels WHERE sensor_id IS NOT NULL"))
        if report['channels_assigned_to_synthetic_sensors']:
            raise ValueError('Observed channels must not use synthetic sensors')
        started=time.perf_counter()
        sql("CREATE UNLOGGED TABLE smartcity.import_stage(doc jsonb NOT NULL);")
        # CSV control separators cannot occur literally in canonical JSON strings.
        copy="\\copy smartcity.import_stage FROM '/inputs/accepted.extjsonl' WITH (FORMAT csv, DELIMITER E'\\x02', QUOTE E'\\x01');"
        command(['exec','-i',name,'psql','-X','-U','postgres','-Atq','-v','ON_ERROR_STOP=1'],input=copy+'\n')
        report['stage_copy_seconds']=time.perf_counter()-started
        load="""INSERT INTO smartcity.observations SELECT
          (jsonb_populate_record(NULL::smartcity.observations,
            doc||jsonb_build_object('observed_at',doc->'observed_at'->>'$date'))).*
          FROM smartcity.import_stage"""
        started=time.perf_counter()
        sql(load+'; ANALYZE smartcity.observations;')
        report['initial_import_seconds']=time.perf_counter()-started
        report['count']=int(sql('SELECT count(*) FROM smartcity.observations;'))
        started=time.perf_counter()
        sql(load+' ON CONFLICT(measurement_id) DO UPDATE SET payload_hash=excluded.payload_hash,value=excluded.value;')
        if int(sql('SELECT count(*) FROM smartcity.observations;'))!=report['count']:
            raise ValueError('PostgreSQL replay duplicated data')
        report['idempotent_reimport']=True
        report['full_reimport_seconds']=time.perf_counter()-started
        started=time.perf_counter()
        errors=int(sql("""SELECT count(*) FROM smartcity.import_stage d
          JOIN smartcity.observation_contract v ON v.measurement_id=d.doc->>'measurement_id'
          WHERE NOT ((d.doc-'observed_at'-'time_error') <@ (to_jsonb(v)-'observed_at'-'time_error'))
          OR v.observed_at<>(d.doc->'observed_at'->>'$date')::timestamptz;"""))
        if errors:
            raise ValueError(f'PostgreSQL full metadata mismatches: {errors}')
        report['metadata_verified']=report['count']
        report['full_metadata_comparison_seconds']=time.perf_counter()-started
        report['count_by_source']=json.loads(sql("SELECT json_agg(x) FROM (SELECT source_id,count(*) FROM smartcity.observations GROUP BY source_id) x;"))
        report['integrity_rejections']={}
        invalid={
            'payload_conflict':"UPDATE smartcity.observations SET value=value+1 WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations);",
            'duplicate_id':"INSERT INTO smartcity.observations SELECT * FROM smartcity.observations LIMIT 1;",
            'natural_key':"INSERT INTO smartcity.observations SELECT (jsonb_populate_record(NULL::smartcity.observations,to_jsonb(o)||jsonb_build_object('measurement_id','duplicate-natural'))).* FROM smartcity.observations o LIMIT 1;",
            'catalog_source':"UPDATE smartcity.channels SET source_id='MAD-METEO' WHERE channel_id=(SELECT min(channel_id) FROM smartcity.channels);",
        }
        for label,query in invalid.items():
            try:
                sql('BEGIN; '+query+' ROLLBACK;')
            except subprocess.CalledProcessError as exc:
                report['integrity_rejections'][label]={'rejected':True,'error':exc.stderr.strip()[:600]}
            else:
                raise ValueError('PostgreSQL accepted invalid '+label)
        report['conflicting_payload_rejected']=True
        target=next(iter(json.loads((private/'catalogs.json').read_text())['channels']))
        report['explain']=json.loads(sql("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM smartcity.observations WHERE channel_id='"+target+"' ORDER BY observed_at;"))
        report['database_bytes']=int(sql("SELECT pg_database_size(current_database());"))
        report['observations_total_bytes']=int(sql("SELECT pg_total_relation_size('smartcity.observations');"))
        command(['exec','-i',name,'psql','-X','-U','postgres','-Atq','-v','ON_ERROR_STOP=1'],
                input=(ROOT/'scripts/phase5_postgresql_queries.sql').read_text())
        report['queries_executed']=[f'PG{n:02d}' for n in range(1,11)]
        def query_evidence(status, data_scope, scope_notice, assertions, synthetic_input_count=0):
            return {'status':status,'data_scope':data_scope,'scope_notice':scope_notice,
                    'assertions':assertions,'synthetic_input_count':synthetic_input_count}
        synthetic_scope='Synthetic administrative demo; it does not identify the producer of an observed reading.'
        observed_scope='Observed MAD-AIR data; channels and readings are not linked to synthetic sensors.'
        blocked_scope='No defensible observed sensor-to-channel relationship exists; the query is not presented as physical inventory evidence.'
        report['query_evidence']={
            'PG01':query_evidence('executed','synthetic_demo',synthetic_scope,{'categorized_sensors':int(sql('SELECT count(*) FROM smartcity.sensors;'))>0},len(seed['sensors'])),
            'PG02':query_evidence('executed','synthetic_demo',synthetic_scope,{'sensors_with_location':int(sql('SELECT count(*) FROM smartcity.sensors s JOIN smartcity.stations t USING(station_id) WHERE t.location_id IS NOT NULL;'))>0},len(seed['sensors'])),
            'PG03':query_evidence('executed','synthetic_demo',synthetic_scope,{'administrative_statuses':int(sql('SELECT count(*) FROM smartcity.sensors WHERE administrative_status IS NOT NULL;'))>0},len(seed['sensors'])),
            'PG04':query_evidence('executed','synthetic_demo',synthetic_scope,{'organizations_assigned':int(sql('SELECT count(*) FROM smartcity.sensors WHERE organization_id IS NOT NULL;'))>0},len(seed['sensors'])),
            'PG05':query_evidence('executed','synthetic_demo',synthetic_scope,{'locations_ranked':int(sql('SELECT count(DISTINCT location_id) FROM smartcity.stations;'))>0},len(seed['sensors'])),
            'PG06':query_evidence('executed','synthetic_demo',synthetic_scope,{'installation_dates':int(sql('SELECT count(*) FROM smartcity.sensors WHERE installation_date IS NOT NULL;'))>0},len(seed['sensors'])),
            'PG07':query_evidence('blocked','synthetic_demo',blocked_scope,{'observed_sensor_links':False},len(seed['sensors'])),
            'PG08':query_evidence('executed','synthetic_demo',synthetic_scope,{'zones_ranked':int(sql('SELECT count(DISTINCT zone_id) FROM smartcity.locations WHERE zone_id IS NOT NULL;'))>0},len(seed['sensors'])),
            'PG09':query_evidence('executed','observed',observed_scope,{'channel_activity_rows':int(sql('SELECT count(*) FROM smartcity.channel_activity;'))>0}),
            'PG10':query_evidence('executed','observed',observed_scope,{'stations_available':int(sql('SELECT count(*) FROM smartcity.stations WHERE inventory_present;'))>0}),
        }
        report['physical_inventory_functional_compliance']=False
        report['synthetic_measurements']=int(sql("SELECT count(*) FROM smartcity.observations WHERE data_origin='synthetic';"))
        args=DOCKER+['exec',name,'psql','-X','-U','postgres','-Atq','-v','ON_ERROR_STOP=1','-c',
            "COPY (SELECT json_build_array(measurement_id,payload_hash) FROM smartcity.observations ORDER BY measurement_id) TO STDOUT;"]
        checksum=sha256()
        with subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) as proc:
            for line in proc.stdout:
                checksum.update((canonical(json.loads(line))+'\n').encode())
            error=proc.stderr.read()
            if proc.wait(timeout=1800):
                raise RuntimeError(error)
        report['ids_payload_sha256']=checksum.hexdigest()
        report['native_executed']=True


def mongo(private, out, report):
    administrative_seed(private, out)
    with container('mongodb','mongo:7.0.16',private,report) as name:
        database='smartcity_full_'+uuid.uuid4().hex[:12]
        output=command(['exec',name,'mongosh','--quiet',f'mongodb://127.0.0.1:27017/{database}',
                        '/scripts/unified_full_mongo.js']).stdout
        line=next(line for line in output.splitlines() if line.startswith('FULL_RESULT='))
        report.update(json.loads(line.split('=',1)[1]))


def run(generation,engine):
    preparation=verify_generation(generation)
    private,out=generation_paths(generation)
    report={'generation':generation,'native_executed':False,'full_batch':True,
            'accepted_input_sha256':digest(private/'accepted.extjsonl'),
            'source_hashes':{f:digest(ROOT/'scripts'/f) for f in
                ('unified_full_load.py','unified_full_mongo.js','phase5_postgresql.sql','phase5_contract.py')},
            'shared_server_modified':False}
    started=time.perf_counter()
    try:
        (postgres if engine=='postgresql' else mongo)(private,out,report)
        if report['count']!=preparation['accepted'] or report['metadata_verified']!=preparation['accepted']:
            raise ValueError('Incomplete engine count or metadata verification')
        db=sqlite3.connect(f'file:{private / "identities.sqlite"}?mode=ro',uri=True)
        expected=sha256()
        for ident,signature in db.execute('SELECT id,signature FROM identities ORDER BY id'):
            expected.update((canonical([ident,signature])+'\n').encode())
        db.close()
        if expected.hexdigest()!=report['ids_payload_sha256']:
            raise ValueError('Engine IDs/payloads differ from accepted ledger')
        report['ledger_reconciled']=True
    except Exception as exc:
        report['error']=str(exc)
        if isinstance(exc,subprocess.CalledProcessError):
            report['engine_stderr']=exc.stderr[-4000:]
        raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started
        atomic_json(out/(engine+'_full.json'),report)
    print(json.dumps({k:report[k] for k in ('engine','count','elapsed_seconds','ledger_reconciled','container_removed')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation',default='expanded-2025')
    parser.add_argument('--engine',choices=['postgresql','mongodb'],required=True)
    args=parser.parse_args()
    run(args.generation,args.engine)
