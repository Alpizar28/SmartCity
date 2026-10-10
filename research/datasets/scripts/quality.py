"""Exact sample metrics. Extremes are flagged, never removed or relabeled as errors."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def number(s):
    return pd.to_numeric(s.astype('string').str.replace(',', '.', regex=False), errors='coerce')


def valid_coordinates(lat, lon):
    return lat.notna() & lon.notna() & lat.between(-90,90) & lon.between(-180,180)


def profile(df, source, keys=None, declared=None):
    """Strings and absent JSON attributes count as null; no zero-as-null rule."""
    clean=df.astype('string').replace(r'^\s*$',pd.NA,regex=True)
    schema=[]
    for col in clean.columns:
        s=clean[col]
        numeric=number(s)
        nonempty=int(s.notna().sum())
        infer='numeric' if nonempty and int(numeric.notna().sum())==nonempty else str(s.dtype)
        row={'source':source,'attribute':str(col),'rows':len(df),'null_count':int(s.isna().sum()),
             'null_pct':float(s.isna().mean()*100),'unique_nonnull':int(s.nunique()),
             'inferred_type':infer,'declared_type':(declared or {}).get(col,'not documented/checked'),
             'minimum':None,'maximum':None,'mean':None,'median':None,'iqr_outliers':None}
        if infer=='numeric':
            row.update(minimum=float(numeric.min()),maximum=float(numeric.max()),
                       mean=float(numeric.mean()),median=float(numeric.median()))
            q1,q3=numeric.quantile([.25,.75]);iqr=q3-q1
            row['iqr_outliers']=int(((numeric<q1-1.5*iqr)|(numeric>q3+1.5*iqr)).sum())
        schema.append(row)
    duplicates=int(df.duplicated(keys).sum()) if keys and all(k in df for k in keys) else None
    return {'source':source,'rows':len(df),'columns':len(df.columns),'keys':keys,
            'duplicate_key_rows':duplicates,'exact_duplicate_rows':int(df.duplicated().sum()),
            'required_missing_rows':int(clean[keys].isna().any(axis=1).sum()) if keys and all(k in clean for k in keys) else None,
            'attributes':schema}


def temporal(df, minutes):
    rows=[]
    work=df.copy()
    work['time']=pd.to_datetime(work['time'],errors='coerce')
    grouping_time=work['time'].dt.tz_localize(None) if work['time'].dt.tz is not None else work['time']
    work['month']=grouping_time.dt.to_period('M').astype(str)
    for (entity,var,month),g in work.groupby(['entity','variable','month'],dropna=False):
        ts=g['time'].dropna().drop_duplicates().sort_values()
        delta=ts.diff().dt.total_seconds().div(60)
        expected=int((ts.max()-ts.min()).total_seconds()/60/minutes)+1 if len(ts) else 0
        valid=g[g['quality'].eq('valid') & g['value'].notna()]['time'].nunique()
        rows.append({'entity':str(entity),'variable':str(var),'month':month,'rows':len(g),
                     'first':str(ts.min()),'last':str(ts.max()),'unique_timestamps':len(ts),
                     'duplicate_time_rows':len(g)-len(ts),'expected_between_observed_endpoints':expected,
                     'missing_slots_between_endpoints':max(0,expected-len(ts)),
                     'coverage_between_endpoints_pct':100*len(ts)/expected if expected else None,
                     'valid_unique_timestamps':valid,'gaps_gt_expected':int((delta>minutes).sum()),
                     'max_gap_minutes':float(delta.max()) if len(ts)>1 else None,
                     'median_interval_minutes':float(delta.median()) if len(ts)>1 else None,
                     'null_value_rows':int(g['value'].isna().sum()),
                     'invalid_flag_rows':int(g['quality'].ne('valid').sum())})
    return pd.DataFrame(rows)


def normalized_summary(df, source):
    keys=['entity','variable','time']
    out={'source':source,'observations':len(df),'entities':int(df['entity'].nunique()),
         'variables':sorted(df['variable'].dropna().astype(str).unique().tolist()),
         'date_min':str(df['time'].min()),'date_max':str(df['time'].max()),
         'invalid_dates':int(df['time'].isna().sum()),'missing_values':int(df['value'].isna().sum()),
         'unique_keys':int(len(df.drop_duplicates(keys))),
         'duplicate_keys':int(df.duplicated(keys).sum()),
         'valid_observations':int((df['quality'].eq('valid') & df['value'].notna() & df['time'].notna()).sum()),
         'quality_counts':df['quality'].value_counts(dropna=False).astype(int).to_dict(),
         'zone_counts':df['zone'].value_counts(dropna=False).astype(int).to_dict(),
         'coordinate_valid_rows':int(valid_coordinates(df['lat'],df['lon']).sum()),
         'coordinate_missing_rows':int((df['lat'].isna()|df['lon'].isna()).sum()),
         'coordinate_invalid_nonmissing':int(((df['lat'].notna() & df['lon'].notna()) & ~valid_coordinates(df['lat'],df['lon'])).sum()),
         'unique_coordinates':int(df[['lat','lon']].dropna().drop_duplicates().shape[0])}
    stats=[]
    for (var,unit),g in df.groupby(['variable','unit'],dropna=False):
        v=g['value'].dropna()
        q1,q3=v.quantile([.25,.75]) if len(v) else (np.nan,np.nan)
        stats.append({'variable':str(var),'unit':str(unit),'n':len(g),'nonnull':len(v),
                      'min':float(v.min()) if len(v) else None,'max':float(v.max()) if len(v) else None,
                      'mean':float(v.mean()) if len(v) else None,'median':float(v.median()) if len(v) else None,
                      'p01':float(v.quantile(.01)) if len(v) else None,'p99':float(v.quantile(.99)) if len(v) else None,
                      'negative_values':int((v<0).sum()),
                      'iqr_candidate_outliers':int(((v<q1-1.5*(q3-q1))|(v>q3+1.5*(q3-q1))).sum())})
    out['statistics_all_values_no_auto_deletion']=stats
    physical=[]
    # Mathematical domain constraints, not invented upper limits on pollution or traffic.
    # Negative pollution readings can reflect instrument baseline/QC, not automatic errors.
    for var,g in df.groupby('variable'):
        unit=set(g['unit'].dropna().astype(str))
        v=g['value']
        rule=None;bad=pd.Series(False,index=g.index)
        if unit=={'percent'}:
            rule='relative humidity domain0..100%; source magnitude86'
            bad=v.notna() & ~v.between(0,100)
        elif unit=={'degrees'}:
            rule='wind direction0..360degrees; 360retained'
            bad=v.notna() & ~v.between(0,360)
        elif unit=={'degC'}:
            rule='absolute zero lower bound -273.15C; no arbitrary upper bound'
            bad=v.lt(-273.15)
        elif unit in ({'m/s'},{'kWh/30min'},{'vehicles/15min'},{'veh/h'}):
            rule='nonnegative measured speed/consumption/count/intensity expected; investigate negatives without deletion'
            bad=v.lt(0)
        if rule:physical.append({'variable':str(var),'rule':rule,'candidate_violations':int(bad.sum()),'automatically_deleted':0})
    out['physical_domain_checks']=physical
    return out


def dump(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf-8')
