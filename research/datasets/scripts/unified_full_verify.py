"""Read-only evidence verification for full local runs; never claims Spark or two sources."""
import argparse
import json
import sqlite3
from hashlib import sha256

from phase5_contract import ROOT, canonical, digest
from unified_expand import generation_paths, verify_generation


def verify(generation):
    preparation=verify_generation(generation)
    private,out=generation_paths(generation)
    reports={engine:json.loads((out/(engine+'_full.json')).read_text())
             for engine in ('postgresql','mongodb')}
    expected_hash=sha256()
    with sqlite3.connect(f'file:{private / "identities.sqlite"}?mode=ro',uri=True) as ledger:
        count=0
        for ident,payload in ledger.execute('SELECT id,signature FROM identities ORDER BY id'):
            expected_hash.update((canonical([ident,payload])+'\n').encode())
            count+=1
    if count!=preparation['accepted']:
        raise ValueError('Ledger count mismatch')
    for engine,report in reports.items():
        if report.get('error'):
            raise ValueError(engine+' failed: '+report['error'])
        for filename, expected in report['source_hashes'].items():
            if digest(ROOT/'scripts'/filename)!=expected:
                raise ValueError('Engine source changed since execution: '+filename)
        if report['accepted_input_sha256']!=preparation['output_hashes']['accepted.extjsonl']:
            raise ValueError('Engine consumed another generation')
        if report['count']!=count or report['metadata_verified']!=count:
            raise ValueError('Engine did not verify full dataset')
        if report['ids_payload_sha256']!=expected_hash.hexdigest():
            raise ValueError('Identity/payload fingerprint mismatch')
        for key in ('full_batch','native_executed','idempotent_reimport','conflicting_payload_rejected',
                    'ledger_reconciled','container_removed','anonymous_volumes_removed'):
            if not report.get(key):
                raise ValueError(engine+' missing '+key)
        if report['synthetic_measurements'] or report['shared_server_modified']:
            raise ValueError('Real-only/local-only invariant violated')
    if not reports['mongodb'].get('conflict_recorded') or not reports['mongodb'].get('unique_id_and_natural_key'):
        raise ValueError('MongoDB conflict record or uniqueness evidence missing')
    administrative = {engine: report.get('administrative_counts') for engine, report in reports.items()}
    if not all(isinstance(counts, dict) and all(isinstance(counts.get(name), int) and counts[name] > 0
               for name in ('organizations', 'users', 'sensors')) for counts in administrative.values()):
        raise ValueError('Administrative table evidence missing or empty')
    if administrative['postgresql'] != administrative['mongodb']:
        raise ValueError('Administrative counts differ between engines')
    for engine, report in reports.items():
        if report.get('channels_assigned_to_synthetic_sensors') != 0 or report.get('readings_with_sensor_link', 0) != 0:
            raise ValueError(engine+' links observed data to a synthetic sensor')
    rejections=reports['postgresql'].get('integrity_rejections',{})
    if not rejections or not all(value.get('rejected') for value in rejections.values()):
        raise ValueError('PostgreSQL rejection evidence missing or failed')
    return {'verified':True,'generation':generation,'accepted':count,
        'quarantined_air':preparation['quarantined'],'duplicates':preparation['duplicates'],
        'conflicts':preparation['conflicts'],'synthetic_measurements':0,
        'ids_payload_sha256':expected_hash.hexdigest(),
        'postgresql':{'count':reports['postgresql']['count'],'minimum':100000,'met':count>=100000},
        'mongodb':{'count':reports['mongodb']['count'],'minimum':500000,'met':count>=500000},
        'spark':{'executed':False,'status':'pending','eligible_input_records':count},
        'accepted_measurement_sources':['MAD-AIR'],'two_measurement_sources_met':False,
        'administrative_demo':{'verified':True,**administrative['postgresql'],
            'synthetic_measurements':0,'channels_assigned_to_synthetic_sensors':0,
            'readings_assigned_to_synthetic_sensors':0},
        'shared_server_modified':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation',default='expanded-2025')
    args=parser.parse_args()
    print(json.dumps(verify(args.generation),ensure_ascii=False,indent=2))
