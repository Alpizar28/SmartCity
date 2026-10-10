"""Measured integrations with denominators; never a Cartesian sensor equivalence."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

from download import ROOT
from quality import dump

P=ROOT/'private_results';R=ROOT/'results'


def load(name):
    return pd.read_parquet(P/(name+'.parquet'))


def distance_m(lat1,lon1,lat2,lon2):
    a,b,c,d=np.radians([lat1,lon1,lat2,lon2])
    h=np.sin((c-a)/2)**2+np.cos(a)*np.cos(c)*np.sin((d-b)/2)**2
    return float(6371008.8*2*np.arcsin(np.sqrt(h)))


def unambiguous(df):
    keys=['entity','variable','time']
    distinct=df.drop_duplicates(keys+['value','quality'])
    ambiguous=distinct.duplicated(keys,keep=False)
    return distinct[~ambiguous & distinct['quality'].eq('valid') & distinct['value'].notna()].copy(), {
        'input_rows':len(df),'identical_extra_rows':len(df)-len(distinct),
        'ambiguous_rows_excluded_from_join_not_deleted':int(ambiguous.sum()),
        'eligible_rows':int((~ambiguous & distinct['quality'].eq('valid') & distinct['value'].notna()).sum())}


def join_coverage(left,right,keys,label):
    if left.duplicated(keys).any() or right.duplicated(keys).any():
        raise ValueError('Integration keys not unique after aggregation')
    outer=left.merge(right,on=keys,how='outer',indicator=True,validate='one_to_one')
    both=int(outer['_merge'].eq('both').sum());l=int(outer['_merge'].eq('left_only').sum());r=int(outer['_merge'].eq('right_only').sum())
    return outer[outer['_merge'].eq('both')].drop(columns='_merge'), {
        'label':label,'left_groups':len(left),'right_groups':len(right),'matched_groups':both,
        'left_unmatched':l,'right_unmatched':r,'left_match_pct':100*both/len(left) if len(left) else 0,
        'right_match_pct':100*both/len(right) if len(right) else 0,'keys':keys}


def madrid():
    a=load('MAD-AIR');m=load('MAD-METEO')
    ai=load('MAD-AIR-META');mi=load('MAD-METEO-META')
    coloc=[]
    for _,left in ai.iterrows():
        for _,right in mi.iterrows():
            # Exact published coordinate equality and same short code; not proximity inference.
            if left['entity'].split(':')[-1]==right['entity'].split(':')[-1] and distance_m(left['lat'],left['lon'],right['lat'],right['lon'])<1:
                coloc.append({'air_entity':left['entity'],'meteo_entity':right['entity'],
                              'name_air':left['ESTACION'],'name_meteo':right['ESTACION'],
                              'distance_m':distance_m(left['lat'],left['lon'],right['lat'],right['lon'])})
    mapping=pd.DataFrame(coloc)
    mapping.to_csv(R/'MAD-colocated_sites.csv',index=False)
    left,lr=unambiguous(a[a['variable'].eq('8')]);right,rr=unambiguous(m[m['variable'].eq('83')])
    mapped=left.merge(mapping[['air_entity','meteo_entity']],left_on='entity',right_on='air_entity',how='inner',validate='many_to_one')
    l=mapped[['meteo_entity','time','value']].rename(columns={'meteo_entity':'site','value':'NO2_ug_m3'})
    r=right[['entity','time','value']].rename(columns={'entity':'site','value':'temperature_degC'})
    joined,cover=join_coverage(l,r,['site','time'],'Madrid co-located site/hour NO2-temperature')
    joined.to_parquet(P/'Madrid-integrated.parquet',index=False)
    result={'co_located_sites':len(mapping),'air_inventory_sites':len(ai),'meteo_inventory_sites':len(mi),
            'air_sample_sites':a['entity'].nunique(),'geographic_air_site_match_pct':100*len(set(mapping.air_entity)&set(a.entity))/a.entity.nunique(),
            'eligible_air_NO2_rows':len(left),'spatially_mapped_air_NO2_rows':len(mapped),
            'air_row_spatial_pct':100*len(mapped)/len(left),'air_row_spatial_unmatched':len(left)-len(mapped),
            'air_row_spatiotemporal_matched':len(joined),'air_row_spatiotemporal_pct':100*len(joined)/len(left),
            'normalization_left':lr,'normalization_right':rr,'coverage':cover,
            'rule':'same published coordinates<1m plus same site short code; independent channels retained',
            'lost':'other variables, non-co-located sites, invalid flags; current inventory historical validity not fully documented',
            'timezone':'Madrid local hour endpoints; January and July2025 avoid DST transitions; no UTC ambiguity forced'}
    if (P/'MAD-TRAFFIC.parquet').exists():
        traffic,tr=unambiguous(load('MAD-TRAFFIC'))
        points=traffic[['entity','lat','lon']].drop_duplicates('entity')
        near=[]
        for _,pt in points.dropna().iterrows():
            candidates=[(distance_m(pt.lat,pt.lon,s.lat,s.lon),s.entity) for _,s in ai.iterrows() if pd.notna(s.lat) and pd.notna(s.lon)]
            dist,site=min(candidates)
            if dist<=1000:near.append({'traffic_entity':pt.entity,'air_entity':site,'distance_m':dist})
        mp=pd.DataFrame(near)
        mp.to_csv(R/'MAD-traffic_near_sites.csv',index=False)
        t=traffic.merge(mp,left_on='entity',right_on='traffic_entity',how='inner',validate='many_to_one')
        t['time']=t['time'].dt.floor('h')+pd.Timedelta(hours=1)
        # Mean signal, NOT total cars; variable integration duration differs in raw source.
        tg=t.groupby(['air_entity','time']).agg(traffic_mean_signal=('value','mean'),traffic_records=('value','size')).reset_index().rename(columns={'air_entity':'site'})
        ag=left[left['time'].between('2025-01-01','2025-02-01')][['entity','time','value']].rename(columns={'entity':'site','value':'NO2_ug_m3'})
        j,c=join_coverage(tg,ag,['site','time'],'Madrid traffic proximity<=1km site/hour, ecological mean signal')
        j.to_parquet(P/'Madrid-traffic_integrated.parquet',index=False)
        result['traffic']={'sample_points':len(points),'points_with_coordinates':len(points.dropna()),'points_within1km':len(mp),
            'point_geographic_match_pct':100*len(mp)/len(points),'eligible_rows':len(traffic),'spatially_mapped_rows':len(t),
            'spatial_row_match_pct':100*len(t)/len(traffic),'spatial_unmatched_rows':len(traffic)-len(t),
            'coverage':c,'normalization':tr,'assumptions':'1km exploratory context radius, not equivalence or causality; equally weighted report intensity, not vehicles sum; timestamps interpreted interval start',
            'historical_inventory':'published traffic inventory version must be confirmed forJan2025'}
    dump(R/'Madrid-integration.json',result)


def nyc():
    dot,dr=unambiguous(load('NYC-COUNTS'));req,rr=unambiguous(load('NYC-311'))
    dot['day']=dot['time'].dt.normalize();req['day']=req['time'].dt.normalize()
    dg=dot.groupby(['zone','day']).agg(vehicles_in_sample=('value','sum'),traffic_intervals=('value','size')).reset_index()
    rg=req.groupby(['zone','day']).agg(requests=('value','size')).reset_index()
    j,c=join_coverage(dg,rg,['zone','day'],'NYC DOT-311 borough/day; sampled days only')
    j.to_parquet(P/'NYC-DOT-311-integrated.parquet',index=False)
    result={'DOT_normalization':dr,'311_normalization':rr,'DOT_311':c,
            'geographic_rule':'official boro/borough strings standardized to title case; no coordinates required for borough-level join',
            '311_semantics':'citizen requests by created date, not occurrence time, sensor events or alerts',
            'sampling_loss':f'311 only{req.day.nunique()}sampled dates, including consecutiveJan6-12; DOT campaigns unequal exposure; sums are measured intervals not borough-wide traffic totals'}
    # Candidate transformation is audited separately; not accepted without official CRS declaration.
    raw=pd.read_parquet(P/'NYC-COUNTS-raw.parquet')
    transform=Transformer.from_crs(2263,4326,always_xy=True)
    lon,lat=transform.transform(raw.projected_x.to_numpy(dtype=float),raw.projected_y.to_numpy(dtype=float))
    result['CRS_candidate']={'candidate':'EPSG2263 -> EPSG4326; not confirmed official metadata',
          'transformed_bbox':[float(np.nanmin(lon)),float(np.nanmin(lat)),float(np.nanmax(lon)),float(np.nanmax(lat))],
          'rows_in_exploratory_NYC_bbox':int(((lon>-74.3)&(lon<-73.6)&(lat>40.45)&(lat<40.95)).sum()),
          'used_for_join':False,'bbox_consistency_does_not_prove_CRS':True}
    if (P/'NYC-AIR.parquet').exists():
        air,ar=unambiguous(load('NYC-AIR'))
        # Avoid method/POC multiplicity weighting: average per physicalsite first, then sites/borough.
        air['physicalsite']=air['entity'].str.split('-').str[:3].str.join('-')
        air['day']=air['time'].dt.tz_convert('America/New_York').dt.normalize().dt.tz_localize(None)
        site=air.groupby(['zone','day','physicalsite']).agg(PM25=('value','mean')).reset_index()
        ag=site.groupby(['zone','day']).agg(PM25_site_mean=('PM25','mean'),sites=('physicalsite','size')).reset_index()
        ja,ca=join_coverage(dg,ag,['zone','day'],'NYC DOT-EPA PM2.5 borough/day, full2023')
        ja.to_parquet(P/'NYC-DOT-EPA-integrated.parquet',index=False)
        three=ja.merge(rg,on=['zone','day'],how='inner',validate='one_to_one')
        three.to_parquet(P/'NYC-three_sources-integrated.parquet',index=False)
        result.update(EPA_normalization=ar,DOT_EPA=ca,three_source_groups=len(three),
                      three_source_pct_of_DOT_groups=100*len(three)/len(dg),
                      assumptions='county->borough official administrative equivalence; PM2.5 site mean over hours loses hourly peaks, POC/method detail; NYC local wall-clock from EPA GMT, not Date Local standard-time')
    else:result['DOT_EPA']={'status':'incomplete EPA archive; integration failed/not attempted with national prefix'}
    dump(R/'NYC-integration.json',result)


def london():
    air,ar=unambiguous(load('LON-AIR'));energy,er=unambiguous(load('LON-ENERGY'))
    energy['hour']=energy['time'].dt.floor('h')
    # Sum only exactly2 unique half-hour records per household/hour. Missing is not0.
    household=energy.groupby(['entity','hour']).agg(kWh=('value','sum'),intervals=('time','nunique')).reset_index()
    partial=int(household['intervals'].ne(2).sum())
    complete=household[household['intervals'].eq(2)]
    eg=complete.groupby('hour').agg(cohort_kWh=('kWh','sum'),households=('entity','nunique')).reset_index().rename(columns={'hour':'time'})
    ag=air.groupby('time').agg(NO2_site_mean=('value','mean'),sites=('entity','nunique')).reset_index()
    joined,c=join_coverage(eg,ag,['time'],'London energy cohort/hour vs NO2 site mean/hour')
    joined.to_parquet(P/'London-integrated.parquet',index=False)
    sites=load('LON-AIR-META');siteids=set(air.entity)
    selected=sites[sites['@SiteCode'].isin(siteids)]
    opened=pd.to_datetime(selected['@DateOpened'],errors='coerce')
    closed=pd.to_datetime(selected['@DateClosed'].replace('',pd.NA),errors='coerce')
    dump(R/'London-integration.json',{'air_normalization':ar,'energy_normalization':er,
        'coverage':c,'households_selected':energy.entity.nunique(),'partial_household_hours_excluded':partial,
        'cohort_households_per_matched_hour_min':int(joined.households.min()),'cohort_households_per_matched_hour_max':int(joined.households.max()),
        'sample_sites':len(selected),'sites_opened_beforeJan2013':int((opened<pd.Timestamp('2013-01-01')).sum()),
        'sites_closed_before2013':int((closed<pd.Timestamp('2013-01-01')).sum()),
        'geographic_granularity':'London city context only; no household coordinate or borough',
        'household_fine_zone_mapping_pct':0,'fine_zone_mapping_failure':True,
        'city_context_mapping_pct':100,'city_context_is_sampling_area_not_measured_household_location':True,
        'timezone_assumption':'Jan2013 UKGMT; July2013 LCLclock not declared timezone -> joining to LAQN GMT conditional. No UTC assertion forLCL',
        'lost':'individual half-hour values/households, site-level concentrations and geographic variation; cohort total not London total',
        'redistribution':'rawLAQN and integrated numeric data kept ignored locally; only aggregate audit metrics/report versioned'})


def main():
    for fn in [madrid,nyc,london]:fn()


if __name__=='__main__':main()
