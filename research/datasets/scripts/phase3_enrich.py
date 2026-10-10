"""Additional source-semantic checks, no remote calls or changes to originals."""
import csv
import json
import re
from pathlib import Path

import pandas as pd

from audit import csv_encoding, local
from phase3_validate import OUT, ROOT, dump, load, sha


def main():
    activity=[]
    for source in ['MAD-AIR','MAD-METEO']:
        inv=load(source+'-META');reads=load(source)
        present=set(reads.entity)
        for _,r in inv.iterrows():
            activity.append({'source':source,'site_id':r.entity,'site_name':r.ESTACION,
                'sample_readings':int(reads.entity.eq(r.entity).sum()),
                'window':'2025 January/July; published hour endpoints',
                'inventory_independent':True,'historical_validity_complete':False,
                'absence_interpretation':'not in sample, not administrative inactivity' if r.entity not in present else 'observations present'})
    inv=load('LON-AIR-META');reads=load('LON-AIR')
    for _,r in inv.iterrows():
        activity.append({'source':'LON-AIR','site_id':r['@SiteCode'],'site_name':r['@SiteName'],
            'sample_readings':int(reads.entity.eq(r['@SiteCode']).sum()),
            'window':'2013 January/July; only five sites requested',
            'inventory_independent':True,'historical_validity_complete':False,
            'absence_interpretation':'not requested or outside observed window, not inactive' if r['@SiteCode'] not in set(reads.entity) else 'observations present'})
    pd.DataFrame(activity).to_csv(OUT/'catalog_activity.csv',index=False)
    # Accident details must collapse to incident ID without majority-vote category invention.
    p=local('MAD-CRASH-file');crash=pd.read_csv(p,sep=';',dtype=str,encoding=csv_encoding(p))
    group=crash.groupby('num_expediente').agg(category_count=('tipo_accidente','nunique'),
        day_count=('fecha','nunique'),district_count=('cod_distrito','nunique')).reset_index()
    eligible=group[group.category_count.eq(1)]
    incidents=crash[crash.num_expediente.isin(eligible.num_expediente)].drop_duplicates('num_expediente')
    categories=incidents.tipo_accidente.value_counts().to_dict()
    dump('incident_checks.json',{'Madrid':{'detail_rows':len(crash),'incident_ids':len(group),
        'conflicting_categories':int(group.category_count.gt(1).sum()),
        'conflicting_dates':int(group.day_count.gt(1).sum()),'conflicting_districts':int(group.district_count.gt(1).sum()),
        'unambiguous_category_incidents':len(incidents),'missing_category_incidents':int(group.category_count.eq(0).sum()),'category_counts':categories},
        'NYC':{'unique_requests':len(load('NYC-311')),'kind':'citizen_service_request','confirmed_incident':False},
        'London':{'TfL_incidents_complete_sample_audited':False,'status':'unverified complement in Phase1'}})
    # Preserve the verified historical dictionary evidence as small text, not a live URL assertion.
    path=Path('/tmp/opencode/smartcity-phase1/M13.txt')
    if not path.exists():path=OUT/'madrid_air_dictionary.txt'
    if path.exists():
        text=path.read_text();(OUT/'madrid_air_dictionary.txt').write_text(text)
        site_changes=[line.strip() for line in text.splitlines() if re.search(r'28079\d{3}',line) and ('Alta' in line or 'Baja' in line)]
        dictionary={}
        for line in text.splitlines():
            match=re.match(r'^\s*(\d+)\s+.*?\s+(µg/m\s*3|mg/m\s*3)\b',line)
            if match:dictionary[str(int(match[1]))]='ug/m3' if match[2].startswith('µ') else 'mg/m3'
        used=load('MAD-AIR')[['variable','unit']].drop_duplicates()
        air_units_valid=all(dictionary.get(row.variable)==row.unit for row in used.itertuples())
        source=next(r for r in csv.DictReader((ROOT/'01_http_evidence.csv').open()) if r['probe_id']=='M13')
        dump('madrid_dictionary_provenance.json',{'original_source':source,'retained_text_sha256':sha(OUT/'madrid_air_dictionary.txt'),
              'unit_codes_extracted':dictionary,'all_used_air_units_match':air_units_valid})
    else:site_changes=[];air_units_valid=False
    dump('unit_history_checks.json',{'Madrid':{
        'air_units_evidence':'madrid_air_dictionary.txt AnexoII:8NO2 ug/m3,9PM25 ug/m3,6CO mg/m3',
        'air_unit_mapping_consistent_with_dictionary':air_units_valid,
        'meteo_units_dictionary_full_verification':False,
        'meteo_provisional_units':{'83':'degC','86':'percent','81':'m/s','82':'degrees','87':'hPa','88':'W/m2','89':'mm'},
        'historical_site_rows':site_changes,'history_scope':'site code/alta/baja, NOT installation per analyzer',
        'meteo_historical_inventory_complete':False,'traffic_historical_inventory_Jan2025_complete':False},
        'NYC':{'EPA_datum':sorted(load('NYC-AIR-raw').Datum.unique().tolist()),
            'EPA_units':sorted(load('NYC-AIR').unit.unique().tolist()),'DOT_CRS_verified':False},
        'London':{'LAQN_GMT_field':True,'LCL_timezone_verified':False,'household_coordinates_available':False}})
    print('Semantic catalog, units/history and incident checks completed.')


if __name__=='__main__':main()
