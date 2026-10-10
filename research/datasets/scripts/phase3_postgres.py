"""Disposable native PostgreSQL proof. Fixed LOCAL socket, no network/published ports/pull."""
import json
import subprocess
import time
import uuid

from download import ROOT

OUT=ROOT/'results/phase3'
PRIVATE=ROOT/'private_results/phase3'
DOCKER=['docker','--host','unix:///var/run/docker.sock']
IMAGE='postgres:16-alpine'

DDL="""
CREATE SCHEMA proof;
SET search_path=proof;
CREATE TABLE categories(category_id text PRIMARY KEY, variable text NOT NULL, unit text NOT NULL);
CREATE TABLE locations(location_id text PRIMARY KEY, zone text, lat double precision, lon double precision,
 name text, district text, site_opened timestamp,
 CHECK(lat IS NULL OR lat BETWEEN -90 AND 90),CHECK(lon IS NULL OR lon BETWEEN -180 AND 180));
CREATE TABLE organizations(organization_id text PRIMARY KEY,name text NOT NULL,responsible text);
CREATE TABLE users(user_id text PRIMARY KEY,name text, email text UNIQUE);
CREATE TABLE channels(channel_id text PRIMARY KEY,entity text NOT NULL,
 category_id text NOT NULL REFERENCES categories,location_id text NOT NULL REFERENCES locations,
 source text NOT NULL,name text,installation_date date,administrative_status text,
 organization_id text REFERENCES organizations,entity_kind text NOT NULL);
CREATE TABLE readings(measurement_id text PRIMARY KEY,channel_id text NOT NULL REFERENCES channels,
 observed_at timestamp NOT NULL,value double precision,quality text NOT NULL,clock text NOT NULL,
 UNIQUE(channel_id,observed_at));
CREATE INDEX channel_location ON channels(location_id);
CREATE INDEX channel_category ON channels(category_id);
CREATE INDEX reading_channel_time ON readings(channel_id,observed_at);
CREATE VIEW sensor_scope AS SELECT * FROM channels
 WHERE entity_kind NOT IN ('campaign_segment_direction','anonymous_household_channel');
CREATE VIEW channel_by_type AS SELECT category_id,count(*) AS n FROM sensor_scope GROUP BY category_id;
CREATE FUNCTION channels_at_location(target text) RETURNS bigint LANGUAGE SQL STABLE
 AS $$ SELECT count(*) FROM proof.sensor_scope WHERE location_id=target $$;
"""

QUERIES={
 'PG01':"SELECT coalesce(json_object_agg(category_id,n),'{}') FROM (SELECT category_id,count(*) n FROM sensor_scope GROUP BY category_id) x",
 'PG02':"SELECT coalesce(json_object_agg(location_id,n),'{}') FROM (SELECT l.location_id,count(c.channel_id) n FROM locations l JOIN sensor_scope c USING(location_id) GROUP BY l.location_id) x",
 'PG03':"SELECT json_build_object('unknown_status',count(*) FILTER(WHERE administrative_status IS NULL),'known_status',count(administrative_status)) FROM sensor_scope",
 'PG04':"SELECT json_build_object('known_owner',count(organization_id),'unknown_owner',count(*) FILTER(WHERE organization_id IS NULL)) FROM sensor_scope LEFT JOIN organizations USING(organization_id)",
 'PG05':"SELECT coalesce(json_object_agg(location_id,n),'{}') FROM (SELECT location_id,count(*) n FROM sensor_scope GROUP BY location_id HAVING count(*)>0 ORDER BY n DESC,location_id) x",
 'PG06':"SELECT json_build_object('known_installation_date',count(installation_date)) FROM sensor_scope",
 'PG07':"SELECT json_build_object('without_activity_in_loaded_window',count(*),'independent_inventory_test_pending',true) FROM sensor_scope c WHERE NOT EXISTS(SELECT 1 FROM readings r WHERE r.channel_id=c.channel_id)",
 'PG08':"WITH counts AS (SELECT l.zone,count(*) n FROM sensor_scope c JOIN locations l USING(location_id) WHERE l.zone IS NOT NULL GROUP BY l.zone), ranked AS(SELECT zone,n,dense_rank() OVER(ORDER BY n DESC) AS rank FROM counts) SELECT json_build_object('counts',coalesce(json_object_agg(zone,n),'{}'),'ranks',coalesce(json_object_agg(zone,rank),'{}')) FROM ranked",
 'PG09':"SELECT coalesce(json_object_agg(category_id,n),'{}') FROM channel_by_type",
 'PG10':"SELECT coalesce(json_object_agg(location_id,channels_at_location(location_id)),'{}') FROM locations WHERE location_id IN(SELECT location_id FROM sensor_scope)",
 'readings':"SELECT to_json(count(*)) FROM readings",
 'sum_values':"SELECT to_json(sum(value)) FROM readings",
 'min_value':"SELECT to_json(min(value)) FROM readings",
 'max_value':"SELECT to_json(max(value)) FROM readings",
}


def run(args, **kw):
    return subprocess.run(args,check=True,text=True,capture_output=True,timeout=180,**kw)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    name='smartcity-phase3-proof-'+uuid.uuid4().hex[:10]
    log=[];result={'engine':'PostgreSQL','image':IMAGE,'local_socket':'unix:///var/run/docker.sock',
                   'network':'none','published_ports':[],'cities':{},'native_executed':False}
    (OUT/'proof_queries.sql').write_text(DDL+'\n'+ '\n'.join(f'-- {k}\n{q};' for k,q in QUERIES.items()))
    try:
        run(DOCKER+['image','inspect',IMAGE])  # Never pull an image implicitly.
        created=run(DOCKER+['run','--detach','--rm','--pull=never','--name',name,'--network','none',
            '--memory=1g','--cpus=1',
            '--mount',f'type=bind,src={PRIVATE},dst=/inputs,readonly',
            '-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE])
        result['container_id']=created.stdout.strip()
        mounts=json.loads(run(DOCKER+['inspect',name,'--format','{{json .Mounts}}']).stdout)
        volumes=[m['Name'] for m in mounts if m['Type']=='volume']
        result['disposable_anonymous_volumes']=volumes
        for attempt in range(80):
            startup=subprocess.run(DOCKER+['logs',name],capture_output=True,text=True,timeout=10)
            p=subprocess.run(DOCKER+['exec',name,'pg_isready','-U','postgres'],capture_output=True,text=True,timeout=10)
            if p.returncode==0 and 'init process complete' in startup.stdout+startup.stderr:break
            time.sleep(.5)
        else:raise RuntimeError('Disposable PostgreSQL readiness timed out')
        def sql(query):
            r=subprocess.run(DOCKER+['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],
                             input=query,text=True,capture_output=True,timeout=180)
            if r.returncode:
                log.append({'sql':query,'stdout':r.stdout,'stderr':r.stderr,'error':True})
                raise RuntimeError(r.stderr)
            log.append({'sql':query,'stdout':r.stdout,'stderr':r.stderr});return r.stdout.strip()
        result['version']=sql('SELECT version();')
        for city in ['Madrid','NYC','London']:
            sql(DDL)
            for table in ['categories','locations','organizations','channels','readings']:
                sql(f"SET search_path=proof; COPY {table} FROM '/inputs/{city}/{table}.csv' WITH(FORMAT csv,HEADER true,NULL '');")
            sql('ANALYZE proof.readings;')
            expected=json.loads((OUT/(city+'_expected_sql.json')).read_text());results={}
            for ident,query in QUERIES.items():
                actual=json.loads(sql('SET search_path=proof; '+query+';'))
                target=expected[ident]
                if isinstance(target,float):assert abs(actual-target)<=max(1e-6,abs(target)*1e-10),(city,ident,actual,target)
                else:assert actual==target,(city,ident,actual,target)
                results[ident]={'result':actual,'equals_python_reference':True,
                    'required_semantics_covered':ident not in ['PG03','PG04','PG06','PG07'],
                    'scope':'logical source channels/locations; not complete physical sensor inventory'}
            # Actual constraints tested using real existing rows; no original data changed.
            validations={}
            for label,statement in {
                'duplicate_pk_rejected':'INSERT INTO readings SELECT * FROM readings LIMIT 1;',
                'orphan_fk_rejected':"INSERT INTO readings VALUES ('proof-orphan','not-a-real-channel',now(),NULL,'test','unverified');",
                'null_timestamp_rejected':"INSERT INTO readings SELECT 'proof-null',channel_id,NULL,value,quality,clock FROM readings LIMIT 1;"
            }.items():
                r=subprocess.run(DOCKER+['exec','-i',name,'psql','-X','-U','postgres','-v','ON_ERROR_STOP=1','-Atq'],
                    input='SET search_path=proof; BEGIN; '+statement+' ROLLBACK;',capture_output=True,text=True,timeout=30)
                assert r.returncode!=0,(city,label)
                validations[label]={'rejected':True,'stderr':r.stderr.strip()}
            results['null_semantics']={'installation_date_known':json.loads(sql('SELECT to_json(count(installation_date)) FROM proof.channels;')),
                                      'users':json.loads(sql('SELECT to_json(count(*)) FROM proof.users;'))}
            plan=sql("SET search_path=proof; EXPLAIN(FORMAT JSON) SELECT * FROM readings WHERE channel_id=(SELECT min(channel_id) FROM channels) AND observed_at>='2010-01-01' AND observed_at<'2030-01-01';")
            result['cities'][city]={'queries':results,'constraints':validations,'query_plan':json.loads(plan),
                'loaded_readings':expected['readings'],'threshold_100k_loaded':expected['readings']>=100000}
            sql('DROP SCHEMA proof CASCADE;')
        result['native_executed']=True
    finally:
        # Only the uniquely named container created by THIS script; no existing service touched.
        stopped=subprocess.run(DOCKER+['stop',name],capture_output=True,text=True,timeout=30)
        result['cleanup_returncode']=stopped.returncode
        result['container_removed']=subprocess.run(DOCKER+['inspect',name],capture_output=True,text=True,timeout=10).returncode!=0
        result['anonymous_volumes_removed']=all(subprocess.run(DOCKER+['volume','inspect',v],capture_output=True,text=True,timeout=10).returncode!=0 for v in result.get('disposable_anonymous_volumes',[]))
        dump_path=OUT/'postgres_execution.json';dump_path.write_text(json.dumps(result,indent=2))
        (OUT/'postgres_execution.log').write_text(json.dumps(log,indent=2))
        (OUT/(name+'.json')).write_text(json.dumps(result,indent=2))
        (OUT/(name+'.log')).write_text(json.dumps(log,indent=2))
    print(json.dumps({'native_executed':result['native_executed'],'container_removed':result['container_removed'],
                      'loaded_rows':{c:r['loaded_readings'] for c,r in result['cities'].items()}},indent=2))


if __name__=='__main__':main()
