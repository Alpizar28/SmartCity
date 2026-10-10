"""Offline audit of manifest-verified local sources. No database connections."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import resource
import sqlite3
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from download import ROOT
from quality import dump, number, profile, normalized_summary, temporal
from readers import complete_zip_members, madrid_long

RESULT=ROOT/'results'
PRIVATE=ROOT/'private_results'


def csv_encoding(path):
    try:
        Path(path).read_bytes().decode('utf-8-sig')
        return 'utf-8-sig'
    except UnicodeDecodeError:
        return 'cp1252'


def local(name):
    with (ROOT/'02_download_manifest.csv').open() as f:
        matches=[r for r in csv.DictReader(f) if r['id']==name and r['status'] in ('200','206') and not r['error']]
    return ROOT/matches[-1]['path'] if matches else None


def profiles(df, source, keys, declared=None):
    dump(RESULT/(source+'-schema_quality.json'),profile(df,source,keys,declared))


def save_normal(df, source, minutes=60):
    PRIVATE.mkdir(exist_ok=True)
    df.to_parquet(PRIVATE/(source+'.parquet'),index=False)
    dump(RESULT/(source+'-summary.json'),normalized_summary(df,source))
    if minutes is None:
        # Citizen requests are irregular events, not scheduled sensor channels.
        events=df.assign(day=df['time'].dt.normalize()).groupby(['zone','day'],dropna=False).agg(
            events=('entity','size'),unique_requests=('entity','nunique'),first=('time','min'),last=('time','max')).reset_index()
        events.to_csv(RESULT/(source+'-coverage.csv'),index=False)
    else:
        temporal(df,minutes).to_csv(RESULT/(source+'-coverage.csv'),index=False)


def madrid():
    inventories={}
    for source,name in [('MAD-AIR','212629-0-estaciones-control-aire-inventory'),
                        ('MAD-METEO','300360-0-meteorologicos-estaciones-inventory')]:
        inv=pd.read_csv(local(name),sep=';',dtype=str,encoding='utf-8-sig')
        code='CODIGO_CORTO' if 'CODIGO_CORTO' in inv else 'CÓDIGO_CORTO'
        profiles(inv,source+'-META',[code])
        inv['entity']=source+':'+inv[code].astype(str)
        inv['lat']=number(inv['LATITUD']);inv['lon']=number(inv['LONGITUD'])
        inventories[source]=inv
        inv.to_parquet(PRIVATE/(source+'-META.parquet'),index=False)
        path=local(source+'-file')
        raw=pd.read_csv(path,sep=';',dtype=str,encoding=csv_encoding(path))
        key=['PROVINCIA','MUNICIPIO','ESTACION','MAGNITUD','ANO','MES','DIA']
        profiles(raw,source,key,dict.fromkeys(raw.columns,'official CSV numeric/date-components or flag'))
        # Full annual raw structure audited; exact counts of all hourly slots and flags.
        flagcols=[f'V{h:02d}' for h in range(1,25)]
        flags=pd.Series(raw[flagcols].to_numpy().ravel()).value_counts(dropna=False).to_dict()
        full={'raw_rows':len(raw),'hourly_slots':len(raw)*24,'flags_full_year':{str(k):int(v) for k,v in flags.items()},
              'raw_duplicate_keys':int(raw.duplicated(key).sum()),'stations':int(raw['ESTACION'].nunique()),
              'channel_station_magnitude_pairs':len(raw[['ESTACION','MAGNITUD']].drop_duplicates()),
              'first_day':str(pd.to_datetime(dict(year=number(raw['ANO']),month=number(raw['MES']),day=number(raw['DIA']))).min()),
              'last_day':str(pd.to_datetime(dict(year=number(raw['ANO']),month=number(raw['MES']),day=number(raw['DIA']))).max()),
              'timezone':'Europe/Madrid; hourly endpoint H24 goes to next midnight; DST duplicated hour removed by publisher',
              'unknown_station_ids':sorted(set(source+':'+raw['ESTACION'].astype(str))-set(inv['entity']))}
        dump(RESULT/(source+'-annual_counts.json'),full)
        # Calendar January and July, all published sites and variables; not first lines.
        selected=raw[number(raw['ANO']).eq(2025) & number(raw['MES']).isin([1,7])]
        df=madrid_long(selected,source)
        geo=inv[['entity','lat','lon']].drop_duplicates('entity')
        df=df.drop(columns=['lat','lon']).merge(geo,on='entity',how='left',validate='many_to_one')
        save_normal(df,source)
    # Complements profiled completely but not falsely matched to2025 when resource is2026.
    for source,key in [('MAD-TRAFFIC-META',['id']),('MAD-ENERGY',['SENSOR','ID','AÑO','MES','CLASE','GRUPO','UNIDADES']),
                       ('MAD-CRASH',['num_expediente'])]:
        path=local(source+'-file')
        raw=pd.read_csv(path,sep=';',dtype=str,encoding=csv_encoding(path))
        profiles(raw,source,key)
        if source=='MAD-TRAFFIC-META':
            raw.to_parquet(PRIVATE/(source+'.parquet'),index=False)
        if source=='MAD-CRASH':
            dump(RESULT/'MAD-CRASH-incidents.json',{'rows_person_details':len(raw),'unique_expedientes':raw['num_expediente'].nunique(),
                 'dates':raw['fecha'].value_counts().to_dict(),'types':raw['tipo_accidente'].value_counts().to_dict()})
    dump(RESULT/'MAD-coordinate_correspondence.json', {
        'common_short_codes':sorted(set(inventories['MAD-AIR']['entity'].str.split(':').str[-1]) & set(inventories['MAD-METEO']['entity'].str.split(':').str[-1])),
        'rule':'same numeric code alone is not equivalence; coordinate match must also be verified; separate network entities retained'})


def traffic():
    path=local('MAD-TRAFFIC-Jan2025')
    if not path:
        dump(RESULT/'MAD-TRAFFIC-block.json',{'status':'not downloaded'});return
    try:
        z=zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        dump(RESULT/'MAD-TRAFFIC-block.json',{'status':'incomplete/invalid ZIP'});return
    infos=z.infolist();info=next(i for i in infos if i.filename.endswith('.csv'))
    total=0;selected=[];errors={};intervals={};days={};points=set();full_null={}
    # Uniform deterministic ID stratum over entire month (5%), not first-row truncation.
    with z.open(info) as f:
        for raw in pd.read_csv(f,sep=';',dtype=str,chunksize=100000,encoding='utf-8-sig'):
            total+=len(raw)
            points.update(raw['id'].dropna().unique())
            for c in raw:
                full_null[c]=full_null.get(c,0)+int(raw[c].isna().sum())
            for c,target in [('error',errors),('periodo_integracion',intervals)]:
                if c in raw:
                    for k,v in raw[c].value_counts(dropna=False).items():target[str(k)]=target.get(str(k),0)+int(v)
            dates=pd.to_datetime(raw['fecha'],errors='coerce')
            for k,v in dates.dt.date.value_counts().items():days[str(k)]=days.get(str(k),0)+int(v)
            mask=number(raw['id']).mod(20).eq(0)
            selected.append(raw[mask].copy())
    raw=pd.concat(selected,ignore_index=True)
    profiles(raw,'MAD-TRAFFIC',['id','fecha','tipo_elem'])
    dump(RESULT/'MAD-TRAFFIC-full_counts.json',{'raw_rows':total,'points':len(points),'errors':errors,
         'intervals':intervals,'rows_by_date':days,'full_null_count':full_null,'full_null_pct':{c:100*n/total for c,n in full_null.items()},
         'sample_rows':len(raw),'sampling':'id numeric modulo20=0, all timestamps inJan2025',
         'zip_members':[{'name':i.filename,'compressed':i.compress_size,'uncompressed':i.file_size,'CRC':i.CRC} for i in infos],
         'zip_member_crc_verified':'reading complete ZipExtFile to EOF checks CRC',
         'full_unique_key_count':'not measured outside deterministic sample; do not claim total equals unique'})
    inv=pd.read_parquet(PRIVATE/'MAD-TRAFFIC-META.parquet')
    geo=inv[['id','longitud','latitud','distrito']].drop_duplicates('id')
    raw=raw.merge(geo,on='id',how='left',validate='many_to_one')
    df=pd.DataFrame({'entity':'MAD-TRAFFIC:'+raw['id'],'variable':'intensidad',
        'time':pd.to_datetime(raw['fecha'],errors='coerce'),'value':number(raw['intensidad']),
        'quality':raw['error'].map({'N':'valid','S':'invalid'}).fillna('unknown'),
        'lat':number(raw['latitud']),'lon':number(raw['longitud']),
        'zone':raw['distrito'].fillna('unmapped'),'unit':'veh/h','source':'MAD-TRAFFIC'})
    save_normal(df,'MAD-TRAFFIC',15)


def epa():
    path=ROOT/'raw/EPA-2023-assembled.zip'
    if not path.exists():
        dump(RESULT/'NYC-AIR-block.json',{'status':'archive incomplete'});return
    rows=0;state_rows=0;selected=[];all_counts={}
    with zipfile.ZipFile(path) as z:
        info=next(i for i in z.infolist() if i.filename.endswith('.csv'))
        with z.open(info) as f:
            for raw in pd.read_csv(f,dtype=str,chunksize=100000):
                rows+=len(raw)
                ny=raw[raw['State Code'].eq('36')]
                state_rows+=len(ny)
                localny=ny[ny['County Code'].isin(['005','047','061','081','085'])]
                if len(localny):selected.append(localny.copy())
        archive={'national_rows':rows,'NY_state_rows':state_rows,'compressed':path.stat().st_size,
                 'uncompressed':info.file_size,'member':info.filename,'CRC':info.CRC,'CRC_validated_at_EOF':True}
    raw=pd.concat(selected,ignore_index=True)
    keys=['State Code','County Code','Site Num','Parameter Code','POC','Date GMT','Time GMT','Method Code']
    profiles(raw,'NYC-AIR',keys)
    raw.to_parquet(PRIVATE/'NYC-AIR-raw.parquet',index=False)
    archive.update(NYC_rows=len(raw),NYC_sites=len(raw[['County Code','Site Num']].drop_duplicates()),
                   counties=raw['County Code'].value_counts().to_dict(),units=raw['Units of Measure'].value_counts().to_dict(),
                   datums=raw['Datum'].value_counts().to_dict(),qualifiers=raw['Qualifier'].value_counts(dropna=False).rename(index=lambda x:str(x)).to_dict())
    dump(RESULT/'NYC-AIR-full_counts.json',archive)
    # Keep POC+method as distinct channels, not false duplicates.
    entity=raw['State Code']+'-'+raw['County Code']+'-'+raw['Site Num']+'-'+raw['POC']+'-'+raw['Method Code']
    date=pd.to_datetime(raw['Date GMT']+' '+raw['Time GMT'],errors='coerce',utc=True)
    df=pd.DataFrame({'entity':entity,'variable':raw['Parameter Code'],'time':date,
                     'value':number(raw['Sample Measurement']),'quality':np.where(raw['Qualifier'].isna(),'valid','qualified'),
                     'lat':number(raw['Latitude']),'lon':number(raw['Longitude']),
                     'zone':raw['County Code'].map({'005':'Bronx','047':'Brooklyn','061':'Manhattan','081':'Queens','085':'Staten Island'}),
                     'unit':raw['Units of Measure'],'source':'NYC-AIR'})
    # Keep UTC for identity; NYC local day is derived ONLY in integration.
    # Dropping timezone before key checks would invent fall-DST duplicates.
    save_normal(df,'NYC-AIR')


def nyc():
    records=list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    for prefix,source in [('DOT-2023-','NYC-COUNTS'),('311-2023-','NYC-311')]:
        paths={r['id']:ROOT/r['path'] for r in records if r['id'].startswith(prefix) and
               (r['id'][len(prefix):].isdigit() if source=='NYC-COUNTS' else True) and r['status']=='200' and r['complete_response']=='True' and not r['error']}
        raw=pd.DataFrame([row for path in paths.values() for row in json.loads(path.read_text())])
        if not len(raw):
            dump(RESULT/(source+'-block.json'),{'status':'no valid JSON pages'});continue
        if source=='NYC-COUNTS':
            keys=['requestid','segmentid','direction','yr','m','d','hh','mm']
            meta=json.loads(local('N01-refresh').read_text())
            declared={c['fieldName']:c['dataTypeName'] for c in meta['columns'] if c.get('fieldName')}
            profiles(raw,source,keys,declared)
            date=pd.to_datetime(dict(year=number(raw['yr']),month=number(raw['m']),day=number(raw['d'])),errors='coerce')
            date+=pd.to_timedelta(number(raw['hh']),unit='h')+pd.to_timedelta(number(raw['mm']),unit='m')
            point=raw['wktgeom'].str.extract(r'POINT\s*\(([\d.-]+)\s+([\d.-]+)\)')
            raw['projected_x']=number(point[0]);raw['projected_y']=number(point[1])
            # CRS only a candidate pending official declaration: no unverified transformation in accepted join.
            df=pd.DataFrame({'entity':raw['requestid']+':'+raw['segmentid']+':'+raw['direction'],
                  'variable':'volume','time':date,'value':number(raw['vol']),'quality':'valid',
                  'zone':raw['boro'],'lat':np.nan,'lon':np.nan,'unit':'vehicles/15min','source':source})
            raw.to_parquet(PRIVATE/(source+'-raw.parquet'),index=False)
            dump(RESULT/'NYC-COUNTS-campaigns.json',{'campaigns':raw['requestid'].nunique(),'segments':raw['segmentid'].nunique(),
                 'days':date.dt.date.nunique(),'rows_by_month':date.dt.month.value_counts().sort_index().to_dict(),
                 'projected_coordinates_available_rows':int(raw['projected_x'].notna().sum()),
                 'interval_bad_minute_rows':int((~number(raw['mm']).isin([0,15,30,45])).sum()),
                 'negative_volume_rows':int((number(raw['vol'])<0).sum())})
            save_normal(df,source,15)
        else:
            meta=json.loads(local('N03-refresh').read_text())
            declared={c['fieldName']:c['dataTypeName'] for c in meta['columns'] if c.get('fieldName')}
            profiles(raw,source,['unique_key'],declared)
            if 'latitude' not in raw:raw['latitude']=pd.NA
            if 'longitude' not in raw:raw['longitude']=pd.NA
            df=pd.DataFrame({'entity':raw['unique_key'],'variable':raw['complaint_type'],
                 'time':pd.to_datetime(raw['created_date'],errors='coerce'),'value':1.0,'quality':'valid',
                 'zone':raw['borough'].str.title(),'lat':number(raw['latitude']),'lon':number(raw['longitude']),
                 'unit':'citizen request','source':source})
            dump(RESULT/'NYC-311-categories.json',{'category_counts':raw['complaint_type'].value_counts().to_dict(),
                 'status_counts':raw['status'].value_counts().to_dict(),'agency_counts':raw['agency'].value_counts().to_dict(),
                 'sample_dates':sorted(df['time'].dt.date.astype(str).unique().tolist()),
                 'dates_impossible':int(df['time'].isna().sum()),
                 'closed_before_created':int((pd.to_datetime(raw['closed_date'],errors='coerce')<df['time']).sum()) if 'closed_date' in raw else None,
                 'note':'citizen requests, not accidents or automatic sensor alerts; value1 is event count not physical reading'})
            save_normal(df,source,None)


def complements():
    path=local('LL84-sample')
    if path:
        raw=pd.DataFrame(json.loads(path.read_text()))
        if len(raw):
            meta=json.loads(local('N12-refresh').read_text())
            declared={c['fieldName']:c['dataTypeName'] for c in meta['columns'] if c.get('fieldName')}
            profiles(raw,'NYC-ENERGY',['report_year','property_id'],declared)
    path=local('DfT2013')
    if path:
        raw=pd.DataFrame(json.loads(path.read_text())['data'])
        profiles(raw,'LON-COUNTS',['count_point_id','count_date','hour','direction_of_travel'])


def london():
    sites=pd.DataFrame(json.loads(local('L01-refresh').read_text())['Sites']['Site'])
    profiles(sites,'LON-AIR-META',['@SiteCode'])
    sites.to_parquet(PRIVATE/'LON-AIR-META.parquet',index=False)
    rows=[]
    records=list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    paths={r['id']:ROOT/r['path'] for r in records if r['id'].startswith('LAQN-') and r['status']=='200'}
    for name,path in paths.items():
        data=json.loads(path.read_text())['RawAQData'];site=name.split('-')[1]
        for row in data.get('Data',[]):rows.append({'site':site,**row})
    raw=pd.DataFrame(rows)
    profiles(raw,'LON-AIR',['site','@MeasurementDateGMT'])
    raw=raw.merge(sites[['@SiteCode','@Latitude','@Longitude','@LocalAuthorityName','@DateOpened','@DateClosed']],
                  left_on='site',right_on='@SiteCode',how='left',validate='many_to_one')
    value=number(raw['@Value'])
    df=pd.DataFrame({'entity':raw['site'],'variable':'NO2','time':pd.to_datetime(raw['@MeasurementDateGMT'],errors='coerce'),
          'value':value,'quality':np.where(value.notna(),'valid','missing'),
          'zone':raw['@LocalAuthorityName'],'lat':number(raw['@Latitude']),'lon':number(raw['@Longitude']),
          'unit':'ug/m3','source':'LON-AIR'})
    save_normal(df,'LON-AIR')
    members=complete_zip_members(local('LCL-prefix'),ROOT/'raw/lcl_members')
    dump(RESULT/'LCL-members.json',members)
    chunks=[];total=0;households=set();fullnull={};fullmissingvalue=0;fullnegative=0;fullmin=None;fullmax=None
    first=None;last=None;fullrowsbymonth={}
    # Exact global household/timestamp cardinality on disk, not a hash estimate or RAM set.
    db=sqlite3.connect(PRIVATE/'lcl_keys.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS audit_lcl_keys (household TEXT, timestamp TEXT, PRIMARY KEY(household,timestamp)) WITHOUT ROWID')
    db.execute('DELETE FROM audit_lcl_keys')
    db.execute('PRAGMA cache_size=-8192')
    for m in members:
        for c in pd.read_csv(m['path'],dtype=str,chunksize=100000):
            c.columns=c.columns.str.strip();total+=len(c)
            households.update(c['LCLid'].unique())
            date=pd.to_datetime(c['DateTime'],errors='coerce')
            db.executemany('INSERT OR IGNORE INTO audit_lcl_keys VALUES (?,?)',
                           zip(c['LCLid'].astype(str),date.dt.strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            first=date.min() if first is None else min(first,date.min());last=date.max() if last is None else max(last,date.max())
            v=number(c['KWH/hh (per half hour)'])
            fullmissingvalue+=int(v.isna().sum());fullnegative+=int((v<0).sum())
            if len(v.dropna()):
                fullmin=float(v.min()) if fullmin is None else min(fullmin,float(v.min()))
                fullmax=float(v.max()) if fullmax is None else max(fullmax,float(v.max()))
            for col in c:fullnull[col]=fullnull.get(col,0)+int(c[col].isna().sum())
            for month,n in date.dt.to_period('M').value_counts().items():fullrowsbymonth[str(month)]=fullrowsbymonth.get(str(month),0)+int(n)
            chosen=date.dt.year.eq(2013)&date.dt.month.isin([1,7])
            chunks.append(c[chosen].copy())
    raw=pd.concat(chunks,ignore_index=True)
    profiles(raw,'LON-ENERGY',['LCLid','DateTime'])
    value=number(raw['KWH/hh (per half hour)'])
    df=pd.DataFrame({'entity':raw['LCLid'],'variable':'electricity','time':pd.to_datetime(raw['DateTime'],errors='coerce'),
                     'value':value,'quality':np.where(value.notna(),'valid','missing'),'zone':'London',
                     'lat':np.nan,'lon':np.nan,'unit':'kWh/30min','source':'LON-ENERGY'})
    save_normal(df,'LON-ENERGY',30)
    unique_keys=int(db.execute('SELECT count(*) FROM audit_lcl_keys').fetchone()[0])
    db.close()
    dump(RESULT/'LCL-expanded_counts.json',{'rows_complete_members':total,'households':len(households),
        'unique_household_timestamp_keys':unique_keys,'duplicate_key_extra_rows':total-unique_keys,
        'members':len(members),'first':str(first),'last':str(last),'monthly_counts':fullrowsbymonth,
        'raw_nulls':fullnull,'nonnumeric_or_missing_energy':fullmissingvalue,'negative_energy':fullnegative,
        'min_energy':fullmin,'max_energy':fullmax,'geographic_columns':[],
        'selection_bias':'first complete ZIP members; household ordering nonrandom; all Jan+Jul2013 retained',
        'zip_whole_archive_integrity':'not tested; prefix only; each extracted member CRC/length verified'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('city',choices=['madrid','traffic','epa','nyc','london','complements','all'])
    args=parser.parse_args()
    RESULT.mkdir(exist_ok=True);PRIVATE.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO)
    stages={'madrid':madrid,'traffic':traffic,'epa':epa,'nyc':nyc,'london':london,'complements':complements}
    for name,fn in stages.items():
        if args.city in ('all',name):
            logging.info('Auditing %s',name)
            fn()
    profiles_out=[]
    for f in sorted(RESULT.glob('*-schema_quality.json')):
        profiles_out.extend(json.loads(f.read_text())['attributes'])
    pd.DataFrame(profiles_out).to_csv(ROOT/'02_quality_metrics.csv',index=False)
    dump(RESULT/'runtime.json',{'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                               'chunk_size':100000,'analysis_process':'offline; sources original bytes retained'})


if __name__=='__main__':main()
