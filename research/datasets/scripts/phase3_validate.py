"""Offline Phase 3 validation. Original measurements and previous outputs are read-only."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from audit import csv_encoding, local
from download import ROOT
from integrate import join_coverage, unambiguous
from quality import number

OUT = ROOT / 'results/phase3'
PRIVATE = ROOT / 'private_results/phase3'
SOURCES = {'Madrid': ['MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC'],
           'NYC': ['NYC-AIR', 'NYC-COUNTS'], 'London': ['LON-AIR', 'LON-ENERGY']}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while b := f.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str, allow_nan=False))


def load(source):
    return pd.read_parquet(ROOT / 'private_results' / (source + '.parquet'))


def evidence_index():
    entries = []
    paths = set(ROOT.glob('0[012]_*')) | {ROOT / 'README.md', ROOT / '.gitignore'}
    for folder in ['scripts', 'tests', 'results', 'raw', 'private_results']:
        paths.update(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and 'phase3' not in p.parts and '__pycache__' not in p.parts
                     and not p.name.startswith(('phase3_', 'test_phase3')))
    for p in sorted(paths):
        if p.is_file():
            if p.suffix == '.json': json.loads(p.read_text())
            if p.suffix == '.csv' and p.parent == ROOT:
                with p.open() as f: list(csv.DictReader(f))
            if p.suffix in ['.md', '.py', '.log', '.txt', '.lock']: p.read_text()
            entries.append({'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    with (OUT / 'inputs_manifest.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'bytes', 'sha256'])
        writer.writeheader(); writer.writerows(entries)
    pdf = Path('/home/jp/Descargas/Proyectos_CE3101_Enunciado_Proyecto_II_Semestre_2026.pdf')
    text = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
    (OUT / 'academic_original.txt').write_text(text)
    pages = text.split('\f')
    dump('academic_evidence.json', {'path': str(pdf), 'sha256': sha(pdf), 'pages': len(pages)-1,
         'requirements': {str(i+1): p for i, p in enumerate(pages) if any(s in p for s in
             ['Consultas Obligatorias', 'Entidades mínimas', 'Escenario mínimo', 'Métricas Clave'])}})
    return entries


def raw_and_integration_checks():
    result = {}; main_counts = {}
    for city, sources in SOURCES.items():
        result[city] = {}
        for source in sources:
            raw = load(source); good, stats = unambiguous(raw)
            result[city][source] = {**stats, 'raw_keys': len(raw.drop_duplicates(['entity','variable','time'])),
                'null_dates': int(raw.time.isna().sum()), 'units': sorted(raw.unit.unique().tolist()),
                'entities': int(raw.entity.nunique()), 'months': sorted(raw.time.dt.strftime('%Y-%m').unique().tolist())}
    # Recount primary original files, not just phase2 prose.
    mad_counts = {}
    for source in ['MAD-AIR', 'MAD-METEO']:
        path = local(source + '-file')
        raw = pd.read_csv(path, sep=';', dtype=str, encoding=csv_encoding(path))
        mad_counts[source] = len(raw)
        dates = pd.to_datetime(dict(year=number(raw.ANO), month=number(raw.MES), day=number(raw.DIA)))
        result['Madrid'][source]['raw_period'] = [str(dates.min()), str(dates.max())]
        result['Madrid'][source]['raw_daily_duplicates'] = int(raw.duplicated(['ESTACION','MAGNITUD','ANO','MES','DIA']).sum())
        result['Madrid'][source]['raw_year_month_rows'] = raw.groupby(['ANO','MES']).size().rename('rows').reset_index().to_dict('records')
    traffic_rows = 0; sample = []
    with zipfile.ZipFile(local('MAD-TRAFFIC-Jan2025')) as archive:
        info = next(i for i in archive.infolist() if i.filename.endswith('.csv'))
        with archive.open(info) as f:
            for chunk in pd.read_csv(f, sep=';', dtype=str, chunksize=100000):
                traffic_rows += len(chunk)
                sample.append(chunk[number(chunk.id).mod(20).eq(0)].copy())
    traffic = pd.concat(sample, ignore_index=True)
    assert traffic_rows == json.loads((ROOT/'results/MAD-TRAFFIC-full_counts.json').read_text())['raw_rows']
    traffic.to_parquet(PRIVATE/'traffic_original_sample.parquet', index=False)
    assert len(traffic) == len(load('MAD-TRAFFIC'))
    assert np.array_equal(number(traffic.intensidad).to_numpy(), load('MAD-TRAFFIC').value.to_numpy())
    main_counts['Madrid'] = sum(mad_counts.values()) + traffic_rows
    main_counts['NYC'] = sum(len(load(s)) for s in ['NYC-AIR','NYC-COUNTS','NYC-311'])
    # DOT: test every candidate identifier available, excluding the measured value.
    dot = load('NYC-COUNTS-raw')
    base = ['requestid','segmentid','direction','yr','m','d','hh','mm']
    extra = ['boro','wktgeom','street','fromst','tost']
    bad = dot[dot.duplicated(base, keep=False)]
    candidate_counts = {','.join(base+x): int(dot.duplicated(base+x).sum()) for x in [[], ['wktgeom'], extra]}
    groups = bad.groupby(base).agg(records=('vol','size'), distinct_values=('vol','nunique')).reset_index()
    groups.to_parquet(PRIVATE/'dot_conflict_groups.parquet', index=False)
    dump('dot_conflicts.json', {'rows': len(dot), 'conflicting_rows': len(bad), 'groups': len(groups),
        'candidate_duplicate_extras': candidate_counts, 'distinct_values_distribution': groups.distinct_values.value_counts().to_dict(),
        'campaigns_with_conflicts': sorted(bad.requestid.unique().tolist()),
        'exact_raw_duplicates': int(dot.drop(columns=['projected_x','projected_y']).duplicated().sum()),
        'days_measured': int(load('NYC-COUNTS').time.dt.normalize().nunique()),
        'correct_physical_key_found': False, 'row_locator_is_provenance_not_sensor_identity': True})
    # Independently rebuild Madrid denominators and list each loss by entity/month.
    a,_ = unambiguous(load('MAD-AIR').query("variable == '8'"))
    m,_ = unambiguous(load('MAD-METEO').query("variable == '83'"))
    mapping = pd.read_csv(ROOT/'results/MAD-colocated_sites.csv')
    a = a.merge(mapping[['air_entity','meteo_entity']], left_on='entity', right_on='air_entity', how='left', validate='many_to_one')
    probe = a.merge(m[['entity','time','value']].rename(columns={'entity':'meteo_entity','value':'temperature'}),
                    on=['meteo_entity','time'], how='left', validate='many_to_one')
    probe['loss_reason'] = np.select([probe.meteo_entity.isna(), probe.temperature.isna()],
                                    ['no_colocated_site','no_eligible_temperature'], default='matched')
    probe['month'] = probe.time.dt.strftime('%Y-%m')
    losses = probe.groupby(['entity','month','loss_reason']).size().rename('rows').reset_index()
    losses.to_csv(OUT/'madrid_no2_losses.csv', index=False)
    matched = int(probe.loss_reason.eq('matched').sum())
    result['Madrid']['join'] = {'eligible_NO2': len(a), 'matched': matched, 'pct':100*matched/len(a),
         'spatially_mapped': int(a.meteo_entity.notna().sum()), 'losses': probe.loss_reason.value_counts().to_dict(),
         'unmatched_entities': sorted(probe.loc[probe.loss_reason!='matched','entity'].unique().tolist())}
    assert matched == len(pd.read_parquet(ROOT/'private_results/Madrid-integrated.parquet'))
    # Rebuild NYC borough/day key coverage without depending on saved integration assertions.
    d,_ = unambiguous(load('NYC-COUNTS')); q,_ = unambiguous(load('NYC-311')); e,_ = unambiguous(load('NYC-AIR'))
    d['day'] = d.time.dt.normalize(); q['day'] = q.time.dt.normalize()
    e['day'] = e.time.dt.tz_convert('America/New_York').dt.normalize().dt.tz_localize(None)
    dg=d[['zone','day']].drop_duplicates(); qg=q[['zone','day']].drop_duplicates(); eg=e[['zone','day']].drop_duplicates()
    _,qc=join_coverage(dg,qg,['zone','day'],'DOT-311'); _,ec=join_coverage(dg,eg,['zone','day'],'DOT-EPA')
    result['NYC']['joins'] = {'DOT_311':qc, 'DOT_EPA':ec, '311_dates':q.day.nunique(),
        'DOT_days':d.day.nunique(), 'DOT_date_groups_in_311_sample_dates':len(dg[dg.day.isin(q.day.unique())]),
        'EPA_UTC_duplicates':int(e.duplicated(['entity','variable','time']).sum())}
    dg.merge(qg,on=['zone','day'],how='outer',indicator=True).to_csv(OUT/'nyc_borough_day_matches.csv',index=False)
    # London: independently aggregate complete hours and examine timezone sensitivity.
    en,_=unambiguous(load('LON-ENERGY')); air,_=unambiguous(load('LON-AIR'))
    en['hour']=en.time.dt.floor('h')
    hh=en.groupby(['entity','hour']).agg(value=('value','sum'),intervals=('time','nunique')).reset_index()
    complete=hh[hh.intervals.eq(2)]
    left=complete.groupby('hour').agg(energy=('value','sum'),households=('entity','nunique')).reset_index().rename(columns={'hour':'time'})
    right=air.groupby('time').agg(NO2=('value','mean'),sites=('entity','nunique')).reset_index()
    joined,c=join_coverage(left,right,['time'],'London unshifted city/hour')
    variants=[]
    for shift in [-1,0,1]:
        moved=left.copy(); moved.loc[moved.time.dt.month.eq(7),'time'] += pd.Timedelta(hours=shift)
        j,cc=join_coverage(moved,right,['time'],f'July LCL clock shift {shift}h')
        variants.append({'July_shift_hours':shift,'matches':len(j),'left_match_pct':cc['left_match_pct'],
                         'pearson_exploratory_only':float(j.energy.corr(j.NO2))})
    result['London']['join']={'coverage':c,'partial_household_hours':int(hh.intervals.ne(2).sum()),
        'timezone_sensitivity':variants,'households_min':int(joined.households.min()),'households_max':int(joined.households.max()),
        'household_fine_location_columns':[], 'temporal_match_is_not_geographic_match':True}
    # Exact full LCL value conflicts: phase2 only measured key cardinality globally.
    db=sqlite3.connect(PRIVATE/'lcl_full_validation.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS keys(h TEXT,t TEXT,v TEXT,PRIMARY KEY(h,t)) WITHOUT ROWID')
    db.execute('DELETE FROM keys');db.execute('PRAGMA cache_size=-8192')
    total=0;conflicting_extras=0;months={}
    for member in json.loads((ROOT/'results/LCL-members.json').read_text()):
        for chunk in pd.read_csv(member['path'],dtype=str,chunksize=100000):
            chunk.columns=chunk.columns.str.strip(); total+=len(chunk)
            ts=pd.to_datetime(chunk.DateTime,errors='raise').dt.strftime('%Y-%m-%d %H:%M:%S')
            values=number(chunk['KWH/hh (per half hour)']).map(lambda x: 'null' if pd.isna(x) else format(float(x),'.15g'))
            for h,t,v in zip(chunk.LCLid,ts,values):
                cursor=db.execute('INSERT OR IGNORE INTO keys VALUES (?,?,?)',(h,t,v))
                if cursor.rowcount==0:
                    previous=db.execute('SELECT v FROM keys WHERE h=? AND t=?',(h,t)).fetchone()[0]
                    conflicting_extras+=previous!=v
            db.commit()
    unique=db.execute('SELECT count(*) FROM keys').fetchone()[0]
    for ym,count in db.execute('SELECT substr(t,1,7),count(*) FROM keys GROUP BY substr(t,1,7)'):months[ym]=count
    db.close()
    result['London']['expanded']={'rows':total,'unique_keys':unique,'duplicate_extras':total-unique,
         'conflicting_extra_values':conflicting_extras,'unique_by_month':months}
    main_counts['London']=total+len(load('LON-AIR'))
    result['recounted_primary_raw_rows']=main_counts
    reported=json.loads((ROOT/'results/phase2_summary.json').read_text())['primary_raw_rows_audited']
    assert main_counts==reported
    dump('validation.json',result)
    return result


def prepare_relational():
    """Small disposable 3NF proof, not final project schema; no physical devices invented."""
    stats={}
    for city, sources in SOURCES.items():
        frames=[]
        for source in sources:
            good,_=unambiguous(load(source));frames.append(good)
        readings=pd.concat(frames,ignore_index=True)
        readings['channel_id']=readings.source+':'+readings.entity+':'+readings.variable
        readings['category_id']=readings.source+':'+readings.variable+':'+readings.unit
        readings['location_id']=readings.source+':'+readings.entity
        epa_mask=readings.source.eq('NYC-AIR')
        readings.loc[epa_mask,'location_id']='NYC-AIR:'+readings.loc[epa_mask,'entity'].str.split('-').str[:3].str.join('-')
        dot_mask=readings.source.eq('NYC-COUNTS')
        readings.loc[dot_mask,'location_id']='NYC-COUNTS:segment:'+readings.loc[dot_mask,'entity'].str.split(':').str[1]
        readings.loc[readings.source.eq('LON-ENERGY'),'location_id']='LON-ENERGY:unknown'
        readings['measurement_id']=[hashlib.sha256(f'{s}|{c}|{t.isoformat()}'.encode()).hexdigest()
                                   for s,c,t in zip(readings.source,readings.channel_id,readings.time)]
        assert not readings.measurement_id.duplicated().any()
        channels=readings[['channel_id','entity','category_id','location_id','source']].drop_duplicates()
        channels['name']=channels.entity;channels['installation_date']=None;channels['administrative_status']=None
        channels['organization_id']=None
        channels['entity_kind']=channels.source.map({'MAD-AIR':'environmental_channel','MAD-METEO':'weather_channel',
            'MAD-TRAFFIC':'traffic_point_channel','NYC-AIR':'environmental_channel','NYC-COUNTS':'campaign_segment_direction',
            'LON-AIR':'environmental_channel','LON-ENERGY':'anonymous_household_channel'})
        locations=readings[['location_id','zone','lat','lon']].drop_duplicates('location_id')
        locations['name']=locations.location_id;locations['district']=locations.zone
        # No borough for anonymous households: city context retained separately, geographic zone NULL.
        locations.loc[locations.location_id.str.startswith('LON-ENERGY:'),'zone']=None
        locations.loc[locations.location_id.str.startswith('LON-ENERGY:'),'district']=None
        locations['site_opened']=None
        if city=='London':
            sites=load('LON-AIR-META').set_index('@SiteCode')
            for ix,row in channels.iterrows():
                if row.source=='LON-AIR':channels.at[ix,'organization_id']='LAQN-owner:'+sites.loc[row.entity,'@DataOwner']
            for ix,row in locations.iterrows():
                if row.location_id.startswith('LON-AIR:'):
                    entity=row.location_id.split(':',1)[1];locations.at[ix,'name']=sites.loc[entity,'@SiteName']
                    locations.at[ix,'site_opened']=sites.loc[entity,'@DateOpened'] or None
        elif city=='Madrid':
            for source in ['MAD-AIR','MAD-METEO']:
                inv=load(source+'-META').set_index('entity')
                mask=locations.location_id.str.startswith(source+':')
                for ix,row in locations[mask].iterrows():
                    entity=row.location_id[len(source)+1:];locations.at[ix,'name']=inv.loc[entity,'ESTACION']
                    if source=='MAD-AIR':locations.at[ix,'site_opened']=pd.to_datetime(inv.loc[entity,'Fecha alta'],dayfirst=True).isoformat()
        organizations=pd.DataFrame([{'organization_id':o,'name':o.split(':',1)[1],'responsible':None}
                                  for o in channels.organization_id.dropna().unique()],columns=['organization_id','name','responsible'])
        categories=readings[['category_id','variable','unit']].drop_duplicates()
        # Do not inflate masters: all dimensions derive from actual channels, not products.
        assert not channels.channel_id.duplicated().any()
        assert readings.channel_id.isin(channels.channel_id).all()
        assert channels.category_id.isin(categories.category_id).all()
        assert channels.location_id.isin(locations.location_id).all()
        pg_readings=readings[['measurement_id','channel_id','time','value','quality']].copy()
        # Explicit clock: UTC only for EPA; other clocks preserved with no false UTC assertion.
        pg_readings['time']=readings.time.map(lambda t:t.isoformat())
        pg_readings['clock']=readings.source.map({'NYC-AIR':'UTC','LON-AIR':'GMT','LON-ENERGY':'unverified',
            'MAD-AIR':'Madrid_wall_endpoint','MAD-METEO':'Madrid_wall_endpoint','MAD-TRAFFIC':'Madrid_wall_start',
            'NYC-COUNTS':'NYC_wall_campaign'})
        directory=PRIVATE/city;directory.mkdir(exist_ok=True)
        for name,df in [('channels',channels),('locations',locations),('categories',categories),('organizations',organizations),('readings',pg_readings)]:
            df.to_csv(directory/(name+'.csv'),index=False,na_rep='')
        # Expected query results independently computed using pandas.
        scoped=channels[~channels.entity_kind.isin(['campaign_segment_direction','anonymous_household_channel'])]
        zone_counts=scoped.merge(locations[['location_id','zone']],on='location_id').dropna(subset=['zone']).groupby('zone').size().sort_index()
        expected={
            'PG01':scoped.groupby('category_id').size().sort_index().to_dict(),
            'PG02':scoped.groupby('location_id').size().sort_index().to_dict(),
            'PG03':{'unknown_status':len(scoped),'known_status':0},
            'PG04':{'known_owner':int(scoped.organization_id.notna().sum()),'unknown_owner':int(scoped.organization_id.isna().sum())},
            'PG05':scoped.groupby('location_id').size().sort_index().to_dict(),
            'PG06':{'known_installation_date':0},
            'PG07':{'without_activity_in_loaded_window':0,'independent_inventory_test_pending':True},
            'PG08':{'counts':zone_counts.to_dict(),'ranks':zone_counts.rank(method='dense',ascending=False).astype(int).to_dict()},
            'PG09':scoped.groupby('category_id').size().sort_index().to_dict(),
            'PG10':scoped.groupby('location_id').size().sort_index().to_dict(),
            'readings':len(readings),'sum_values':float(readings.value.sum()),'min_value':float(readings.value.min()),'max_value':float(readings.value.max())}
        dump(city+'_expected_sql.json',expected)
        # Mongo prerequisites/fallback: IDs, inclusive/exclusive dates, finite values, unit-separated aggregates.
        one=readings.iloc[0]; subset=readings[readings.channel_id.eq(one.channel_id)]
        start=subset.time.min();stop=start+pd.Timedelta(days=1)
        sliced=subset[(subset.time>=start)&(subset.time<stop)]
        grouped=readings.groupby(['source','variable','unit']).value.agg(['count','min','max','mean']).reset_index()
        grouped.to_csv(OUT/(city+'_python_aggregates.csv'),index=False)
        docs=readings.head(500).copy()
        docs.loc[docs.source.eq('LON-ENERGY'),'zone']=None
        docs['clock']=pg_readings['clock'].head(500).to_numpy()
        docs['data_origin']='observed'
        docs[['measurement_id','channel_id','location_id','source','variable','unit','time','clock','value','quality','zone','data_origin']].to_json(directory/'documents_preview.json',orient='records',date_format='iso')
        stats[city]={'eligible_unique_readings':len(readings),'channels':len(channels),'locations':len(locations),
             'sensor_query_scope_channels':len(scoped),
             'users_created':0,'known_installation_dates':0,'known_admin_status':0,'first_channel_readings':len(subset),
             'first_channel_one_day_readings':len(sliced),'range_start':str(start),'range_end_exclusive':str(stop),
             'null_units':int(readings.unit.isna().sum()),'invalid_dates':int(readings.time.isna().sum()),
             'negative_values_retained':int(readings.value.lt(0).sum()),'measurement_ids_unique':True,
             'python_filters_executed':True,'native_mongodb_executed':False,
             'documents_one_per_reading_not_per_attribute':True,'sensor_count_is_logical_channel_count_not_physical_devices':True}
    dump('prepared_data.json',stats)
    return stats


def main():
    OUT.mkdir(exist_ok=True,parents=True);PRIVATE.mkdir(exist_ok=True,parents=True)
    evidence_index();raw_and_integration_checks();prepare_relational()
    print('Offline Phase3 validation finished; original files not modified.')


if __name__=='__main__':main()
