"""Multi-month real-air export. Reuse the frozen contract/catalog helpers, never rewrite v1.

No DB/network access. Output generations are isolated; interrupted generations replay
deterministically and cannot be consumed without a completed manifest.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import sqlite3
import time

import pandas as pd

from phase5_contract import (ROOT, VERSION, SOURCES, base_document, canonical, digest,
                             hourly_endpoint, numeric, payload_hash, validate_document)
from phase5_prepare import AIR_UNITS, add_channel, geographic, metadata, sources

EXPORTER = 'multi-month-air-v1'


def generation_paths(generation):
    if not re.fullmatch(r'expanded-[a-zA-Z0-9_-]{1,48}', generation):
        raise ValueError('Generation must start expanded- and contain only safe characters')
    return ROOT/'private_results'/generation, ROOT/'results'/generation


def atomic_json(path, content):
    temporary = path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(content,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    os.replace(temporary,path)


def hourly_documents(resource, year, months, meta, catalogs):
    """Preserve physical CSV row offsets, original codes and original source dates."""
    required = {'PROVINCIA','MUNICIPIO','ESTACION','MAGNITUD','PUNTO_MUESTREO','ANO','MES','DIA'}
    required.update(f'{prefix}{hour:02d}' for prefix in ('H','V') for hour in range(1,25))
    for chunk in pd.read_csv(ROOT/resource['path'],sep=';',dtype=str,keep_default_na=False,
                             encoding='utf-8-sig',chunksize=1000):
        if set(chunk.columns) != required:
            raise ValueError('Unexpected official hourly CSV schema')
        selected = chunk[chunk['ANO'].eq(str(year)) & pd.to_numeric(chunk['MES']).isin(months)]
        for position, row in selected.iterrows():
            code, variable = row['ESTACION'],row['MAGNITUD']
            key = [code,variable,row['PUNTO_MUESTREO'] or None]
            day = f"{year}-{int(row['MES']):02d}-{int(row['DIA']):02d}"
            # Invalid dates abort instead of silently changing calendar semantics.
            datetime.fromisoformat(day)
            for hour in range(1,25):
                flag, value = row[f'V{hour:02d}'],numeric(row[f'H{hour:02d}'])
                doc = base_document('MAD-AIR',resource['sha256'],code,key,
                                    hourly_endpoint(day,hour),'hour_end','documented_local')
                doc.update(measurement_type=f'MAD-AIR:{variable}',value=value,unit=AIR_UNITS.get(variable),
                    unit_status='verified_dictionary' if variable in AIR_UNITS else 'pending_dictionary',
                    candidate_unit=None,quality_flag=flag,source_key=[*key,day,f'H{hour:02d}'],
                    raw_reference={'path':resource['path'],'sha256':resource['sha256'],
                                   'row':int(position)+2,'column':f'H{hour:02d}'},
                    provenance={'value':'observed','observed_at':'derived','ids':'derived',
                                'unit':'derived','unit_availability':'available'})
                if doc['station_id'] not in catalogs['stations']:
                    geographic('MAD-AIR',code,meta,catalogs)
                doc['zone_id'] = catalogs['stations'][doc['station_id']]['zone_id']
                if doc['channel_id'] not in catalogs['channels']:
                    add_channel(doc,key,catalogs)
                reason = (doc['time_error'] or ('provider_flag' if flag!='V' else
                          'value_or_unit' if value is None or doc['unit'] is None else 'accepted'))
                doc['payload_hash'] = payload_hash(doc)
                yield doc, reason, day[:7]


def configuration(resource, year, months):
    code = ('unified_expand.py','phase5_contract.py','phase5_prepare.py')
    return {'exporter':EXPORTER,'contract':VERSION,'year':year,'months':sorted(set(months)),
        'snapshots':{k:r['sha256'] for k,r in resource.items()},
        'code_hashes':{f:digest(ROOT/'scripts'/f) for f in code}}


def verify_generation(generation):
    private, out = generation_paths(generation)
    report = json.loads((out/'preparation.json').read_text())
    for name, expected in report['configuration']['code_hashes'].items():
        if digest(ROOT/'scripts'/name) != expected:
            raise ValueError('Exporter source changed: '+name)
    for name, expected in report['output_hashes'].items():
        if digest(private/name) != expected:
            raise ValueError('Changed generation output: '+name)
    return report


def prepare(generation, year, months, dry_run=False, interrupt_after=None):
    if not months or any(m not in range(1,13) for m in months):
        raise ValueError('Months must be in 1..12')
    resource = sources()
    config = configuration(resource,year,months)
    private,out = generation_paths(generation)
    if dry_run:
        return {'dry_run':True,'configuration':config,'connects_to_engines':False,'writes':False}
    private.mkdir(parents=True,exist_ok=True)
    out.mkdir(parents=True,exist_ok=True)
    with (private/'prepare.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        completed = out/'preparation.json'
        if completed.exists():
            report = verify_generation(generation)
            if report['configuration'] != config:
                raise ValueError('Sealed generation differs; select another generation')
            return {'idempotent_reuse':True,'accepted':report['accepted'],'generation':generation}
        checkpoint = private/'checkpoint.json'
        resumed = checkpoint.exists()
        if resumed and json.loads(checkpoint.read_text()) != config:
            raise ValueError('Interrupted generation fingerprint differs; do not overwrite')
        atomic_json(checkpoint,config)
        meta = metadata(resource)
        catalogs = {'schema_version':VERSION,'implementation':EXPORTER,
            'stations':{},'channels':{},'zones':{},'measurement_types':{},
            'sources':{s:{'source_id':s,'name':s,'publisher':'Ayuntamiento de Madrid'} for s in SOURCES},
            'source_versions':{}}
        for key,source in zip(resource,(*SOURCES,*SOURCES)):
            row = resource[key]
            catalogs['source_versions'][row['sha256']] = {'source_version':row['sha256'],
                'source_id':source,'original_path':row['path']}
        for source, records in meta.items():
            for code in records:
                geographic(source,code,meta,catalogs)
        started = time.perf_counter()
        stats, categories, totals = {},Counter(),Counter()
        sample = []
        with ExitStack() as stack:
            db = sqlite3.connect(private/'identities.sqlite')
            stack.callback(db.close)
            db.execute('PRAGMA cache_size=-16384')
            db.execute('CREATE TABLE IF NOT EXISTS identities(id TEXT PRIMARY KEY, signature TEXT NOT NULL, natural_key TEXT UNIQUE NOT NULL)')
            # Only our unfinished generation's derived ledger is rebuilt; originals are immutable.
            db.execute('DELETE FROM identities')
            outputs = {name:stack.enter_context((private/(name+'.partial')).open('w'))
                       for name in ('accepted.extjsonl','quarantine.extjsonl','conflicts.extjsonl')}
            for doc,reason,month in hourly_documents(resource['MAD-AIR-file'],year,months,meta,catalogs):
                counter = stats.setdefault(month,Counter())
                counter['selected'] += 1
                totals['selected'] += 1
                if reason!='accepted':
                    outputs['quarantine.extjsonl'].write(canonical({'reason':reason,'source_id':doc['source_id'],
                        'source_month':month,'raw_reference':doc['raw_reference'],'original_time':doc['original_time'],
                        'original_timezone':doc['original_timezone'],'timestamp_role':doc['timestamp_role'],
                        'timestamp_status':doc['timestamp_status'],'observed_at':None,'value':doc['value'],
                        'quality_flag':doc['quality_flag'],'measurement_type':doc['measurement_type'],
                        'schema_version':VERSION,'payload_hash':doc['payload_hash']})+'\n')
                    counter[reason] += 1
                    totals['quarantined'] += 1
                else:
                    validate_document(doc,catalogs)
                    natural = canonical([doc['channel_id'],doc['observed_at'],doc['timestamp_role']])
                    previous = db.execute('SELECT signature FROM identities WHERE id=? OR natural_key=?',
                                          (doc['measurement_id'],natural)).fetchone()
                    if previous:
                        if previous[0] != doc['payload_hash']:
                            conflict = {'measurement_id':doc['measurement_id'],'previous_hash':previous[0],
                                'incoming_hash':doc['payload_hash'],'raw_reference':doc['raw_reference']}
                            outputs['conflicts.extjsonl'].write(canonical(conflict)+'\n')
                            outputs['conflicts.extjsonl'].flush()
                            raise ValueError('Identity/payload conflict; generation not published')
                        totals['duplicates'] += 1
                        counter['duplicates'] += 1
                    else:
                        db.execute('INSERT INTO identities VALUES (?,?,?)',(doc['measurement_id'],doc['payload_hash'],natural))
                        outputs['accepted.extjsonl'].write(canonical(doc)+'\n')
                        totals['accepted'] += 1
                        counter['accepted'] += 1
                        categories[doc['measurement_type']] += 1
                        if len(sample)<5000:
                            sample.append(doc)
                if totals['selected']%10000==0:
                    db.commit()
                if interrupt_after is not None and totals['selected']>=interrupt_after:
                    raise RuntimeError('Injected interruption for restart test')
            db.commit()
        if not totals['accepted']:
            raise ValueError('No accepted observations')
        for name in outputs:
            os.replace(private/(name+'.partial'),private/name)
        atomic_json(private/'catalogs.json',catalogs)
        atomic_json(private/'sample.extjson',sample)
        files = ('accepted.extjsonl','quarantine.extjsonl','conflicts.extjsonl','catalogs.json','sample.extjson','identities.sqlite')
        report = {'generation':generation,'configuration':config,'accepted':totals['accepted'],
            'quarantined':totals['quarantined'],'duplicates':totals['duplicates'],'conflicts':0,
            'selected':totals['selected'],'by_source':{'MAD-AIR':dict(totals)},
            'by_month':{k:dict(v) for k,v in sorted(stats.items())},'by_measurement_type':dict(sorted(categories.items())),
            'synthetic_measurements':0,'resumed_by_deterministic_replay':resumed,
            'elapsed_seconds':time.perf_counter()-started,'engine_loads':False,
            'source_snapshots':list(resource.values()),
            'output_bytes':{f:(private/f).stat().st_size for f in files},
            'output_hashes':{f:digest(private/f) for f in files}}
        if report['selected'] != report['accepted']+report['quarantined']+report['duplicates']:
            raise ValueError('Count reconciliation failed')
        atomic_json(completed,report)
        return {k:report[k] for k in ('generation','accepted','quarantined','duplicates','conflicts','elapsed_seconds')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation',default='expanded-2025')
    parser.add_argument('--year',type=int,default=2025)
    parser.add_argument('--months',type=int,nargs='+',default=list(range(1,13)))
    parser.add_argument('--dry-run',action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.generation,args.year,args.months,args.dry_run),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
