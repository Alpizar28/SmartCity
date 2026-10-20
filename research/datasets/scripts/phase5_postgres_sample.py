"""Verify draft DDL + catalogs + <=10k sample with native LOCAL PostgreSQL, never remote."""
import json
from hashlib import sha256
import subprocess
import time
import uuid

from phase5_contract import ROOT, OUT, PRIVATE, stable_id, validate_document, validate_bundle, digest, canonical
from phase5_prepare import AIR_UNITS, METEO_CANDIDATES, sources

DOCKER = ['docker','--host','unix:///var/run/docker.sock']


def sql_literal(value):
    return "'"+json.dumps(value,ensure_ascii=False,allow_nan=False).replace("'","''")+"'"


def main():
    validate_bundle()
    catalogs = json.loads((PRIVATE/'catalogs.json').read_text())
    sample = json.loads((PRIVATE/'sample.extjson').read_text())
    assert 1000<=len(sample)<=10000
    for document in sample:
        validate_document(document, catalogs)
    resource = list(sources().values())
    name = 'smartcity-phase5-postgres-'+uuid.uuid4().hex[:12]
    result = {'native_executed':False,'engine':'PostgreSQL','image':'postgres:16-alpine',
              'network':'none','published_ports':[], 'local_socket':'unix:///var/run/docker.sock',
              'container':name, 'log':[]}
    result['source_hashes'] = {filename:digest(ROOT/'scripts'/filename) for filename in
        ('phase5_contract.py','phase5_prepare.py','phase5_postgres_sample.py',
         'phase5_postgresql.sql','phase5_postgresql_queries.sql','unified_synthetic.py')}
    created = False
    def docker(args,**kwargs):
        return subprocess.run(DOCKER+args,check=True,capture_output=True,text=True,timeout=180,**kwargs)
    def sql(query):
        output = docker(['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],input=query)
        return output.stdout.strip()
    def insert(table, rows, types, replay=False):
        columns = ','.join(k.split()[0] for k in types.split(','))
        conflict = (' ON CONFLICT(measurement_id) DO UPDATE SET payload_hash=excluded.payload_hash, '
                    'value=excluded.value, raw_reference=observations.raw_reference' if replay else '')
        sql(f'SET search_path=smartcity,pg_temp; INSERT INTO {table}({columns}) SELECT {columns} FROM json_to_recordset({sql_literal(rows)}) AS x({types}){conflict};')
    try:
        docker(['image','inspect',result['image']])
        docker(['run','--detach','--rm','--pull=never','--name',name,'--network','none','--memory=1g','--cpus=1',
                '-e','POSTGRES_HOST_AUTH_METHOD=trust',result['image']])
        created = True
        mounts = json.loads(docker(['inspect',name,'--format','{{json .Mounts}}']).stdout)
        result['owned_anonymous_volumes'] = [m['Name'] for m in mounts if m['Type']=='volume']
        for _ in range(100):
            test = subprocess.run(DOCKER+['exec',name,'pg_isready','-U','postgres'],capture_output=True,timeout=10)
            log = docker(['logs',name])
            if test.returncode==0 and 'init process complete' in log.stdout+log.stderr:
                break
            time.sleep(.25)
        else:
            raise RuntimeError('Local PostgreSQL readiness timeout')
        t = time.perf_counter()
        result['version'] = sql('SELECT version();')
        result['image_id'] = json.loads(docker(['image','inspect',result['image']]).stdout)[0]['Id']
        result['input_sha256'] = digest(PRIVATE/'sample.extjson')
        sql((ROOT/'scripts/phase5_postgresql.sql').read_text())
        insert('sources',[{'source_id':s,'name':s,'publisher':'Ayuntamiento de Madrid'} for s in ['MAD-AIR','MAD-METEO','MAD-TRAFFIC']],
               'source_id text,name text,publisher text')
        versions = []
        for i,r in enumerate(resource):
            s = ['MAD-AIR','MAD-METEO','MAD-TRAFFIC','MAD-AIR','MAD-METEO','MAD-TRAFFIC'][i]
            versions.append({'source_version':r['sha256'],'source_id':s,'original_path':r['path']})
        insert('source_versions',versions,'source_version text,source_id text,original_path text')
        insert('zones',list(catalogs['zones'].values()),'zone_id text,name text,level text')
        locations = []
        stations = []
        for r in catalogs['stations'].values():
            loc = stable_id('location',r['station_id'], 'current-inventory')
            locations.append({**r,'location_id':loc,
                              'inventory_version':r['inventory_reference']['sha256'] if r.get('inventory_reference') else None})
            stations.append({**r,'location_id':loc})
        insert('locations',locations,'location_id text,zone_id text,name text,latitude double precision,longitude double precision,coordinate_crs text,historical_location_verified boolean,inventory_version text')
        insert('stations',stations,'station_id text,source_id text,source_key text,name text,location_id text,inventory_present boolean')
        types = list(catalogs['measurement_types'].values())
        insert('sensor_categories',types,'category_id text,name text')
        insert('measurement_types',types,'measurement_type text,source_id text,code text,category_id text,unit text,candidate_unit text,unit_status text')
        channels = list(catalogs['channels'].values())
        insert('channels',channels,'channel_id text,station_id text,source_id text,sensor_id text,source_key jsonb,measurement_type text,catalog_basis text')
        observations = [{**d,'observed_at':d['observed_at']['$date'],
                         'interval_minutes':int(d['interval_minutes']) if d.get('interval_minutes') is not None else None} for d in sample]
        observation_types = 'measurement_id text,channel_id text,source_id text,observed_at timestamptz,original_time timestamp,original_timezone text,timestamp_role text,timestamp_status text,value double precision,quality_flag text,source_version text,data_origin text,raw_reference jsonb,interval_minutes integer,measurements jsonb,schema_version text,payload_hash text,transformation_method text,transformation_version text,catalog_version text,source_key jsonb,provenance jsonb,element_type text'
        insert('observations',observations,observation_types)
        insert('observations',observations,observation_types,replay=True)
        result['idempotent_reimport'] = True
        sql('ANALYZE smartcity.observations;')
        result['preparation_and_insert_seconds'] = time.perf_counter()-t
        actual = json.loads(sql("SELECT json_build_object('observations',(SELECT count(*) FROM smartcity.observations),'channels',(SELECT count(*) FROM smartcity.channels),'stations',(SELECT count(*) FROM smartcity.stations),'sensors',(SELECT count(*) FROM smartcity.sensors),'users',(SELECT count(*) FROM smartcity.users));"))
        assert actual['observations']==len(sample) and actual['sensors']==actual['users']==0
        result['counts'] = actual
        result['catalogs_match_document_catalogs'] = actual['channels']==len(catalogs['channels']) and actual['stations']==len(catalogs['stations'])
        assert result['catalogs_match_document_catalogs']
        result['source_aggregates'] = json.loads(sql("SELECT coalesce(json_agg(x),'[]') FROM (SELECT source_id,count(*) n,min(value),max(value),sum(value) FROM smartcity.observation_contract GROUP BY source_id ORDER BY source_id) x;"))
        exported = json.loads(sql("SELECT json_agg(x) FROM (SELECT measurement_id,value FROM smartcity.observations ORDER BY measurement_id) x;"))
        expected = sorted([{'measurement_id':d['measurement_id'], 'value':d['value']} for d in sample], key=lambda d:d['measurement_id'])
        assert exported == expected
        result['ids_values_sha256'] = sha256(canonical(exported).encode()).hexdigest()
        result['explain'] = json.loads(sql("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM smartcity.observations WHERE channel_id=" + "'" + sample[0]['channel_id'] + "' ORDER BY observed_at;"))
        refs = json.loads((OUT/'sample_reference.json').read_text())['by_source']
        for r in result['source_aggregates']:
            ref = refs[r['source_id']]
            assert r['n']==ref['count'] and r['min']==ref['min'] and r['max']==ref['max']
            assert abs(r['sum']-ref['sum'])<=max(1e-6,abs(ref['sum'])*1e-10)
        result['sample_values_match_reference'] = True
        queries_output = sql((ROOT/'scripts/phase5_postgresql_queries.sql').read_text())
        result['queries_output_preview'] = queries_output[:1500]
        result['queries_output_sha256'] = sha256(queries_output.encode()).hexdigest()
        result['queries_executed'] = [f'PG{n:02d}' for n in range(1,11)]
        result['queries_empty_physical_inventory_not_compliance'] = True
        result['constraints'] = {}
        for label,q in {
            'duplicate_rejected':'INSERT INTO smartcity.observations SELECT * FROM smartcity.observations LIMIT 1;',
            'orphan_channel_rejected':"UPDATE smartcity.observations SET channel_id='not-in-catalog' WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations);",
            'wrong_source_rejected':"UPDATE smartcity.observations SET source_version=(SELECT source_version FROM smartcity.source_versions WHERE source_id='MAD-METEO' LIMIT 1) WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations);",
            'payload_conflict_rejected':"UPDATE smartcity.observations SET value=value+1 WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations);",
            'raw_hash_rejected':"UPDATE smartcity.observations SET raw_reference=jsonb_build_object('sha256','bad') WHERE measurement_id=(SELECT min(measurement_id) FROM smartcity.observations);"
        }.items():
            rejected = subprocess.run(DOCKER+['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],
                                      input='BEGIN; '+q+' ROLLBACK;',capture_output=True,text=True,timeout=30)
            assert rejected.returncode!=0,label
            result['constraints'][label] = {'rejected':True,'stderr':rejected.stderr.strip()}
        invalid_inserts = {
            'insert_raw_hash': "'measurement_id','bad-hash','raw_reference',jsonb_build_object('sha256','bad')",
            'insert_wrong_source': "'measurement_id','bad-source','source_id','MAD-METEO'",
            'insert_unconfirmed_time': "'measurement_id','bad-status','timestamp_status','assumed_local'",
            'insert_dst_gap': "'measurement_id','bad-dst','original_time','2025-03-30T02:30:00','observed_at','2025-03-30T01:30:00Z'",
            'insert_dst_ambiguous': "'measurement_id','ambiguous-dst','original_time','2025-10-26T02:30:00','observed_at','2025-10-26T00:30:00Z'",
            'insert_nonfinite': "'measurement_id','bad-finite','value','NaN'",
        }
        for label, overrides in invalid_inserts.items():
            query = ('INSERT INTO smartcity.observations SELECT '
                '(jsonb_populate_record(NULL::smartcity.observations, to_jsonb(o)||jsonb_build_object('
                +overrides+'))).* FROM smartcity.observations o LIMIT 1;')
            rejected = subprocess.run(DOCKER+['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],
                input=query, capture_output=True, text=True, timeout=30)
            assert rejected.returncode != 0, label
            result['constraints'][label] = {'rejected':True, 'stderr':rejected.stderr.strip()}
        for label, query in {
            'channel_source_fk':"UPDATE smartcity.channels SET source_id='MAD-METEO' WHERE channel_id=(SELECT min(channel_id) FROM smartcity.channels);",
            'sensor_station_fk':"INSERT INTO smartcity.sensors(sensor_id,name,category_id,station_id,identity_evidence_reference,provenance) SELECT 'test-only','rollback fixture',measurement_type,station_id,'test-only','{}' FROM smartcity.channels LIMIT 1; UPDATE smartcity.channels SET sensor_id='test-only' WHERE station_id<>(SELECT station_id FROM smartcity.sensors WHERE sensor_id='test-only');",
        }.items():
            rejected = subprocess.run(DOCKER+['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],
                input='BEGIN; '+query+' ROLLBACK;', capture_output=True, text=True, timeout=30)
            assert rejected.returncode != 0, label
            result['constraints'][label] = {'rejected':True, 'stderr':rejected.stderr.strip()}
        # Run the actual replay path with conflicting content, not just an UPDATE.
        conflicting = [{**observations[0], 'value':observations[0]['value']+1}]
        try:
            insert('observations', conflicting, observation_types, replay=True)
        except subprocess.CalledProcessError as exc:
            result['conflicting_reimport'] = {'rejected':True, 'error':exc.stderr.strip()}
        else:
            raise AssertionError('Conflicting replay accepted')
        demo = json.loads((PRIVATE/'synthetic_admin.json').read_text())
        result['demo_input_sha256'] = digest(PRIVATE/'synthetic_admin.json')
        insert('smartcity_demo.entities',demo,'entity_id text,entity_type text,data_origin text,seed bigint,generator_version text,payload jsonb,provenance jsonb')
        result['demo_entities'] = int(sql('SELECT count(*) FROM smartcity_demo.entities;'))
        result['native_executed'] = True
        result['sample_not_100k_fulfillment'] = True
    except subprocess.CalledProcessError as exc:
        result['error'] = exc.stderr
        raise
    finally:
        if created:
            subprocess.run(DOCKER+['stop',name],capture_output=True,timeout=60)
            result['container_removed'] = subprocess.run(DOCKER+['inspect',name],capture_output=True,timeout=10).returncode!=0
            result['anonymous_volumes_removed'] = all(subprocess.run(DOCKER+['volume','inspect',v],capture_output=True,timeout=10).returncode!=0 for v in result.get('owned_anonymous_volumes',[]))
        (OUT/'postgresql_sample.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'native_executed':True,'counts':actual,'container_removed':result['container_removed']},indent=2))


if __name__=='__main__':
    main()
