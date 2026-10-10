"""Verify draft DDL + catalogs + <=10k sample with native LOCAL PostgreSQL, never remote."""
import json
import subprocess
import time
import uuid

from phase5_contract import ROOT, OUT, PRIVATE, stable_id
from phase5_prepare import AIR_UNITS, METEO_CANDIDATES, sources

DOCKER = ['docker','--host','unix:///var/run/docker.sock']


def sql_literal(value):
    return "'"+json.dumps(value,ensure_ascii=False,allow_nan=False).replace("'","''")+"'"


def main():
    catalogs = json.loads((PRIVATE/'catalogs.json').read_text())
    sample = json.loads((PRIVATE/'sample.extjson').read_text())
    assert 1000<=len(sample)<=10000
    resource = list(sources().values())
    name = 'smartcity-phase5-postgres-'+uuid.uuid4().hex[:12]
    result = {'native_executed':False,'engine':'PostgreSQL','image':'postgres:16-alpine',
              'network':'none','published_ports':[], 'local_socket':'unix:///var/run/docker.sock',
              'container':name, 'log':[]}
    created = False
    def docker(args,**kwargs):
        return subprocess.run(DOCKER+args,check=True,capture_output=True,text=True,timeout=180,**kwargs)
    def sql(query):
        output = docker(['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],input=query)
        return output.stdout.strip()
    def insert(table, rows, types):
        columns = ','.join(k.split()[0] for k in types.split(','))
        sql(f'SET search_path=draft5; INSERT INTO {table}({columns}) SELECT {columns} FROM json_to_recordset({sql_literal(rows)}) AS x({types});')
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
        types = []
        for typ in sorted({r['category_id'] for r in catalogs['channels'].values()}):
            source,code = typ.rsplit(':',1)
            unit = AIR_UNITS.get(code) if source=='MAD-AIR' else ('veh/h' if source=='MAD-TRAFFIC' else None)
            types.append({'measurement_type':typ,'category_id':typ,'name':typ,'source_id':source,'code':code,
                          'unit':unit,'candidate_unit':METEO_CANDIDATES.get(code) if source=='MAD-METEO' else None,
                          'unit_status':'verified_dictionary' if unit else 'pending_dictionary'})
        insert('sensor_categories',types,'category_id text,name text')
        insert('measurement_types',types,'measurement_type text,source_id text,code text,category_id text,unit text,candidate_unit text,unit_status text')
        channels = [{**r,'measurement_type':r['category_id']} for r in catalogs['channels'].values()]
        insert('channels',channels,'channel_id text,station_id text,sensor_id text,source_key jsonb,measurement_type text,catalog_basis text')
        observations = [{**d,'observed_at':d['observed_at']['$date'],
                         'interval_minutes':int(d['interval_minutes']) if d.get('interval_minutes') is not None else None} for d in sample]
        insert('observations',observations,'measurement_id text,channel_id text,observed_at timestamptz,original_time timestamp,original_timezone text,timestamp_role text,timestamp_status text,value double precision,quality_flag text,source_version text,data_origin text,raw_reference jsonb,interval_minutes integer,measurements jsonb,schema_version text')
        sql('ANALYZE draft5.observations;')
        result['preparation_and_insert_seconds'] = time.perf_counter()-t
        actual = json.loads(sql("SELECT json_build_object('observations',(SELECT count(*) FROM draft5.observations),'channels',(SELECT count(*) FROM draft5.channels),'stations',(SELECT count(*) FROM draft5.stations),'sensors',(SELECT count(*) FROM draft5.sensors),'users',(SELECT count(*) FROM draft5.users));"))
        assert actual['observations']==len(sample) and actual['sensors']==actual['users']==0
        result['counts'] = actual
        result['catalogs_match_document_catalogs'] = actual['channels']==len(catalogs['channels']) and actual['stations']==len(catalogs['stations'])
        assert result['catalogs_match_document_catalogs']
        result['source_aggregates'] = json.loads(sql("SELECT coalesce(json_agg(x),'[]') FROM (SELECT source_id,count(*) n,min(value),max(value),sum(value) FROM draft5.observation_contract GROUP BY source_id ORDER BY source_id) x;"))
        refs = json.loads((OUT/'sample_reference.json').read_text())['by_source']
        for r in result['source_aggregates']:
            ref = refs[r['source_id']]
            assert r['n']==ref['count'] and r['min']==ref['min'] and r['max']==ref['max']
            assert abs(r['sum']-ref['sum'])<=max(1e-6,abs(ref['sum'])*1e-10)
        result['sample_values_match_reference'] = True
        result['queries_output'] = sql((ROOT/'scripts/phase5_postgresql_queries.sql').read_text())
        result['queries_empty_physical_inventory_not_compliance'] = True
        result['constraints'] = {}
        for label,q in {
            'duplicate_rejected':'INSERT INTO draft5.observations SELECT * FROM draft5.observations LIMIT 1;',
            'orphan_channel_rejected':"UPDATE draft5.observations SET channel_id='not-in-catalog' WHERE measurement_id=(SELECT min(measurement_id) FROM draft5.observations);",
            'wrong_source_rejected':"UPDATE draft5.observations SET source_version=(SELECT source_version FROM draft5.source_versions WHERE source_id='MAD-METEO' LIMIT 1) WHERE measurement_id=(SELECT min(measurement_id) FROM draft5.observation_contract WHERE source_id='MAD-AIR');"
        }.items():
            rejected = subprocess.run(DOCKER+['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],
                                      input='BEGIN; '+q+' ROLLBACK;',capture_output=True,text=True,timeout=30)
            assert rejected.returncode!=0,label
            result['constraints'][label] = {'rejected':True,'stderr':rejected.stderr.strip()}
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
