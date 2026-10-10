"""Bounded sample export + exact identity validation of January only, no DB/network loads.

Large originals are immutable. Traffic extraction reuses audited ID%20 stratum and caches
all nine original fields (previous Parquet retained intensity only). Local SQLite is a
deduplication/checkpoint ledger, NOT PostgreSQL/MongoDB fulfillment.
"""
import argparse
from collections import Counter
import csv
import fcntl
from datetime import datetime
import json
import logging
import os
import sqlite3
import time
import zipfile

import pandas as pd

from phase5_contract import (ROOT, OUT, PRIVATE, VERSION, base_document, canonical,
                             digest, hourly_endpoint, numeric, stable_id, validate_document)

IDS = ['MAD-AIR-file', 'MAD-METEO-file', 'MAD-TRAFFIC-Jan2025',
       '212629-0-estaciones-control-aire-inventory',
       '300360-0-meteorologicos-estaciones-inventory', 'MAD-TRAFFIC-META-file']
AIR_UNITS = json.loads((ROOT/'results/phase3/madrid_dictionary_provenance.json').read_text())['unit_codes_extracted']
METEO_CANDIDATES = {'81':'m/s', '82':'degrees', '83':'degC', '86':'percent', '87':'hPa', '88':'W/m2', '89':'mm'}


def atomic_json(path, data):
    temp = path.with_suffix(path.suffix + '.partial')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    os.replace(temp, path)


def sources():
    rows = list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    selected = [next(r for r in reversed(rows) if r['id']==i and r['path'] and not r['error']) for i in IDS]
    for r in selected:
        assert digest(ROOT/r['path']) == r['sha256'], r['path']
    return {r['id']: r for r in selected}


def traffic_cache(source):
    path = PRIVATE/'traffic_selected.parquet'
    stamp = PRIVATE/'traffic_cache_manifest.json'
    fingerprint = {'original_sha256': source['sha256'], 'filter': 'int(id)%20==0', 'version': VERSION}
    if path.exists() and stamp.exists():
        meta = json.loads(stamp.read_text())
        if meta['fingerprint']==fingerprint and digest(path)==meta['sha256']:
            return path, meta
        raise ValueError('Existing Phase5 traffic cache differs; use a new version, do not overwrite')
    parts = []
    seen = 0
    with zipfile.ZipFile(ROOT/source['path']) as z:
        member = next(n for n in z.namelist() if n.endswith('.csv'))
        with z.open(member) as f:
            for chunk in pd.read_csv(f, sep=';', dtype=str, keep_default_na=False, chunksize=100000):
                chunk['raw_row'] = range(seen+2, seen+len(chunk)+2)  # physical CSV line; header=1
                seen += len(chunk)
                part = chunk[pd.to_numeric(chunk['id'], errors='coerce').mod(20).eq(0)]
                if len(part):
                    parts.append(part)
                logging.info('traffic extraction rows=%d selected=%d', seen, sum(len(p) for p in parts))
    data = pd.concat(parts, ignore_index=True)
    temp = path.with_suffix('.parquet.partial')
    data.to_parquet(temp, index=False)
    os.replace(temp, path)
    meta = {'fingerprint': fingerprint, 'sha256': digest(path), 'member': member,
            'csv_rows_traversed_for_missing_fields': seen, 'selected_rows': len(data),
            'crc_verified_at_eof': True}
    atomic_json(stamp, meta)
    return path, meta


def metadata(resource):
    result = {}
    for s in ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC'):
        d = pd.read_parquet(ROOT/'private_results'/f'{s}-META.parquet').fillna('')
        key = 'id' if s=='MAD-TRAFFIC' else ('CODIGO_CORTO' if s=='MAD-AIR' else 'CÓDIGO_CORTO')
        ident = {'MAD-AIR':IDS[3], 'MAD-METEO':IDS[4], 'MAD-TRAFFIC':IDS[5]}[s]
        reference = {'resource_id':ident, 'path':resource[ident]['path'], 'sha256':resource[ident]['sha256']}
        result[s] = {str(r[key]):{**r,'inventory_reference':reference} for r in d.to_dict('records')}
    return result


def geographic(source, code, meta, catalogs):
    sid = stable_id('station', source, str(code))
    r = meta[source].get(str(code))
    zone = None
    if r and source=='MAD-TRAFFIC' and str(r['distrito']).isdigit() and 1<=int(r['distrito'])<=21:
        zone = 'madrid:district:'+str(int(r['distrito']))
        catalogs['zones'][zone] = {'zone_id':zone, 'name':zone, 'level':'district', 'data_origin':'observed'}
    catalogs['stations'][sid] = {'station_id':sid, 'source_id':source, 'source_key':str(code),
        'name': (r.get('nombre') if source=='MAD-TRAFFIC' else r.get('ESTACION')) if r else None,
        'zone_id':zone, 'latitude':numeric(r.get('latitud' if source=='MAD-TRAFFIC' else 'LATITUD')) if r else None,
        'longitude':numeric(r.get('longitud' if source=='MAD-TRAFFIC' else 'LONGITUD')) if r else None,
        'coordinate_crs':'unverified_decimal_geographic', 'historical_location_verified':False,
        'inventory_reference':r['inventory_reference'] if r else None,
        'original_coordinates':{k:v for k,v in r.items() if any(x in k.lower() for x in ('longitud','latitud','utm_','coordenada_'))} if r else None,
        'inventory_present': bool(r), 'data_origin':'observed'}
    return zone


def add_channel(doc, key, catalogs):
    catalogs['channels'][doc['channel_id']] = {'channel_id':doc['channel_id'],
        'station_id':doc['station_id'], 'sensor_id':None, 'source_id':doc['source_id'],
        'source_key':key, 'category_id':doc['measurement_type'], 'catalog_basis':'observations',
        'installation_date':None, 'administrative_status':None, 'organization_id':None,
        'data_origin':'derived'}


def air_documents(source, resource, meta, catalogs, counters):
    # Read small existing CSV; select source date, NOT UTC month (H24 Jan31 is retained).
    raw = pd.read_csv(ROOT/resource['path'], sep=';', dtype=str, keep_default_na=False, encoding='utf-8-sig')
    selected = raw[raw['ANO'].eq('2025') & pd.to_numeric(raw['MES']).eq(1)]
    counters['daily_rows'] = len(selected)
    counters['raw_slots'] = len(selected)*24
    for pos, r in selected.iterrows():
        code, variable = r['ESTACION'], r['MAGNITUD']
        key = [str(code), variable, r['PUNTO_MUESTREO'] or None]
        date = f"2025-01-{int(r['DIA']):02d}"
        for h in range(1,25):
            flag, value = r[f'V{h:02d}'], numeric(r[f'H{h:02d}'])
            local = hourly_endpoint(date, h)
            doc = base_document(source, resource['sha256'], code, key, local, 'hour_end')
            doc.update(measurement_type=f'{source}:{variable}', value=value,
                unit=AIR_UNITS.get(variable) if source=='MAD-AIR' else None,
                unit_status='verified_dictionary' if source=='MAD-AIR' and variable in AIR_UNITS else 'pending_dictionary',
                candidate_unit=METEO_CANDIDATES.get(variable) if source=='MAD-METEO' else None,
                quality_flag=flag, timestamp_status='documented_local' if source=='MAD-AIR' else 'assumed_same_H_format_pending_dictionary',
                source_key=[*key, date, f'H{h:02d}'],
                raw_reference={'path':resource['path'], 'sha256':resource['sha256'], 'row':int(pos)+2, 'column':f'H{h:02d}'},
                provenance={'value':'observed', 'observed_at':'derived', 'ids':'derived',
                            'unit':'derived' if source=='MAD-AIR' else None,
                            'unit_availability':'available' if source=='MAD-AIR' else 'pending'})
            doc['zone_id'] = geographic(source, code, meta, catalogs)
            add_channel(doc, key, catalogs)
            valid = flag=='V' and value is not None and (source!='MAD-AIR' or doc['unit'] is not None)
            reason = 'valid' if valid else ('provider_flag' if flag!='V' else 'value_or_unit')
            yield doc, valid, reason


def traffic_documents(path, resource, cache, meta, catalogs, counters):
    raw = pd.read_parquet(path)
    counters['raw_rows'] = len(raw)
    for r in raw.to_dict('records'):
        code, typ = r['id'], r['tipo_elem']
        local = datetime.fromisoformat(r['fecha'])
        key = [code, typ]
        doc = base_document('MAD-TRAFFIC', resource['sha256'], code, key, local, 'publisher_label')
        duration, intensity = numeric(r['periodo_integracion']), numeric(r['intensidad'])
        optional = {}
        for field, unit in [('ocupacion','percent'), ('carga','percent'), ('vmed','km/h')]:
            optional[field] = {'value':numeric(r[field]), 'unit':unit, 'data_origin':'observed',
                               'applicability':'requires_type_specific_QA', 'raw_value':r[field]}
            if field=='vmed' and typ=='URB':
                optional[field]['value'] = None
                optional[field]['applicability'] = 'URB_zero_not_accepted_as_measured_speed'
        doc.update(measurement_type='MAD-TRAFFIC:intensidad', value=intensity, unit='veh/h',
            unit_status='documented_phase1_dictionary', candidate_unit=None, quality_flag=r['error'],
            timestamp_status='assumed_local_label_pending_provider_confirmation',
            source_key=[code, r['fecha'], typ], interval_minutes=duration, measurements=optional,
            element_type=typ, raw_reference={'path':resource['path'], 'sha256':resource['sha256'],
                'member':cache['member'], 'row':int(r['raw_row']), 'column':'intensidad'},
            provenance={'value':'observed', 'observed_at':'derived', 'ids':'derived', 'unit':'derived'})
        doc['zone_id'] = geographic('MAD-TRAFFIC', code, meta, catalogs)
        add_channel(doc, key, catalogs)
        valid = (r['error']=='N' and intensity is not None and intensity>=0 and typ in ('URB','M30','C30')
                 and duration is not None and duration.is_integer() and 1<=duration<=30
                 and local.year==2025 and local.month==1)
        reason = 'valid' if valid else ('provider_flag' if r['error']!='N' else 'mandatory_field')
        yield doc, valid, reason


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Verify inputs/plan only; do not write/export/connect')
    parser.add_argument('--sample-size', type=int, default=5000)
    args = parser.parse_args()
    if not 1000<=args.sample_size<=10000:
        parser.error('Local sample capped to 1000..10000; no mass export or engine load')
    resource = sources()
    if args.dry_run:
        print(json.dumps({'mode':'dry-run', 'source_hashes_verified':len(resource), 'scope':'January2025; traffic ID%20',
                          'sample_cap':args.sample_size, 'connects_to_engines':False}, indent=2))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    # A single preparation writer; OS releases lock on crash, persistent lockfile is harmless.
    lock = (PRIVATE/'prepare.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    logging.basicConfig(filename=OUT/'prepare.log', level=logging.INFO, format='%(asctime)s %(message)s')
    configuration = {'version':VERSION, 'sources':{k:r['sha256'] for k,r in resource.items()}, 'sample_size':args.sample_size,
                     'script_sha256':digest(__file__), 'contract_sha256':digest(ROOT/'scripts/phase5_contract.py')}
    completed = OUT/'preparation.json'
    if completed.exists():
        prior = json.loads(completed.read_text())
        if prior['configuration'] != configuration:
            raise ValueError('Completed run configuration differs; use new draft version/output, not overwrite')
        for f,h in prior['private_output_hashes'].items():
            assert digest(PRIVATE/f)==h, f
        print(json.dumps({'idempotent_reuse':True, 'counts':prior['counts'], 'sample_size':prior['sample_size']}, indent=2))
        return
    cache_path, cache = traffic_cache(resource['MAD-TRAFFIC-Jan2025'])
    meta = metadata(resource)
    catalogs = {'stations':{}, 'channels':{}, 'zones':{}}
    # Independent site inventory, not guessed channels formed by cross product of variables.
    for source, records in meta.items():
        for code in records:
            geographic(source, code, meta, catalogs)
    ledger = PRIVATE/'identity_ledger.sqlite'
    db = sqlite3.connect(ledger)
    db.execute('PRAGMA cache_size=-8192')
    db.execute('CREATE TABLE IF NOT EXISTS identities (id TEXT PRIMARY KEY, source TEXT, signature TEXT, valid INT, conflict INT DEFAULT 0)')
    # Interrupted run is replayed deterministically; schema/cache hash fixed. No partial output is accepted.
    db.execute('DELETE FROM identities')
    counters, candidates, stats = {}, [], {}
    t = time.perf_counter()
    for source in ('MAD-AIR','MAD-METEO','MAD-TRAFFIC'):
        counters[source] = {}
        totals = Counter()
        stream = (traffic_documents(cache_path, resource['MAD-TRAFFIC-Jan2025'], cache, meta, catalogs, counters[source])
                  if source=='MAD-TRAFFIC' else air_documents(source, resource[source+'-file'], meta, catalogs, counters[source]))
        quota = args.sample_size - 2*(args.sample_size//5) if source=='MAD-TRAFFIC' else args.sample_size//5
        n = 0
        for doc, valid, reason in stream:
            totals['selected_records'] += 1
            totals[reason] += 1
            if doc['zone_id'] is None:
                totals['zone_null'] += 1
            if valid:
                validate_document(doc, catalogs)
            # Raw reference row must not make repeated identical measurement look conflicting.
            identity_content = {k:v for k,v in doc.items() if k not in ('raw_reference',)}
            sig = stable_id('payload', identity_content)
            doc['payload_hash'] = sig
            db.execute('INSERT INTO identities(id,source,signature,valid) VALUES (?,?,?,?) '
                       'ON CONFLICT(id) DO UPDATE SET conflict=CASE WHEN signature!=excluded.signature THEN 1 ELSE conflict END',
                       (doc['_id'], source, sig, int(valid)))
            if valid and n<quota:
                candidates.append(doc)
                n += 1
            if totals['selected_records']%10000==0:
                db.commit()
        db.commit()
        unique, effective, conflicts = db.execute('SELECT count(*),sum(valid AND NOT conflict),sum(conflict) FROM identities WHERE source=?',(source,)).fetchone()
        stats[source] = {**counters[source], **dict(totals), 'unique_natural_keys':unique,
            'duplicate_extras':totals['selected_records']-unique, 'conflicting_keys':conflicts or 0,
            'effective_documents':effective or 0, 'strict_physical_sensor_documents':0}
    sample = [d for d in candidates if db.execute('SELECT conflict FROM identities WHERE id=?',(d['_id'],)).fetchone()[0]==0]
    if len(sample)!=args.sample_size:
        raise ValueError('Not enough valid nonconflicting candidates; review quota/QA, do not fabricate')
    assert len({d['_id'] for d in sample})==len(sample)
    db.close()
    atomic_json(PRIVATE/'catalogs.json', catalogs)
    atomic_json(PRIVATE/'sample.extjson', sample)
    sample_sources = Counter(d['source_id'] for d in sample)
    reference = {}
    for source in sample_sources:
        selected = [d for d in sample if d['source_id']==source]
        values = [d['value'] for d in selected]
        reference[source] = {'count':len(selected), 'min':min(values), 'max':max(values), 'sum':sum(values)}
    atomic_json(OUT/'sample_reference.json', {'by_source':reference, 'ids':len(sample), 'first_channel':sample[0]['channel_id'],
        'channel_count':sum(d['channel_id']==sample[0]['channel_id'] for d in sample)})
    # Bounded future HDFS/Spark route; no Spark/HDFS call and no bulk output.
    flat = [{k:(v['$date'] if k=='observed_at' else v) for k,v in d.items()
             if k in ('measurement_id','channel_id','station_id','zone_id','source_id','source_version','measurement_type','value','unit','observed_at','data_origin')} for d in sample]
    pd.DataFrame(flat).to_parquet(PRIVATE/'sample.parquet', index=False)
    pd.DataFrame(flat).to_csv(PRIVATE/'sample.csv', index=False)
    report = {'configuration':configuration, 'counts':stats, 'sample_size':len(sample), 'sample_by_source':dict(sample_sources),
        'synthetic_measurements':0, 'elapsed_seconds':time.perf_counter()-t, 'source_snapshots':list(resource.values()),
        'cache':cache, 'source_rows_only_January':True, 'engines_loaded':False,
        'private_output_hashes':{f:digest(PRIVATE/f) for f in ['catalogs.json','sample.extjson','sample.parquet','sample.csv','identity_ledger.sqlite']}}
    atomic_json(completed, report)
    print(json.dumps({'counts':stats, 'sample_size':len(sample), 'sample_by_source':dict(sample_sources)}, indent=2))


if __name__=='__main__':
    main()
