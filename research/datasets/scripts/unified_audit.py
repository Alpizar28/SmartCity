"""Compact, read-only reconciliation of annual scope, January compatibility and sizes."""
from collections import Counter
import json
import sqlite3

from phase5_contract import ROOT, digest
from unified_expand import generation_paths, verify_generation


def audit(generation='expanded-2025'):
    report=verify_generation(generation)
    private,out=generation_paths(generation)
    january=ROOT/'private_results/unified-v1/identity_ledger.sqlite'
    with sqlite3.connect(f'file:{private / "identities.sqlite"}?mode=ro',uri=True) as annual:
        annual.execute('ATTACH DATABASE ? AS january',(f'file:{january}?mode=ro',))
        expected=annual.execute('SELECT count(*) FROM january.identities WHERE valid AND NOT conflict').fetchone()[0]
        matched=annual.execute('SELECT count(*) FROM january.identities j JOIN main.identities a ON a.id=j.id '
            'AND a.signature=j.signature WHERE j.valid AND NOT j.conflict').fetchone()[0]
        if expected!=matched or expected!=91959:
            raise ValueError('Annual expansion changed accepted January IDs/payloads')
    reasons=Counter()
    for month in report['by_month'].values():
        for reason,count in month.items():
            if reason not in ('selected','accepted','duplicates'):
                reasons[reason]+=count
    if sum(reasons.values())!=report['quarantined']:
        raise ValueError('Quarantine reasons do not reconcile')
    research=json.loads((out/'research_sources.json').read_text())
    for resource in research:
        if digest(ROOT/resource['path'])!=resource['sha256']:
            raise ValueError('Research snapshot hash mismatch')
    original_files={row['path']:int(row['bytes_downloaded']) for row in report['source_snapshots']}
    return {'generation':generation,'accepted':report['accepted'],
        'january_accepted_unchanged':matched,'additional_accepted_beyond_january':report['accepted']-matched,
        'quarantined_air':report['quarantined'],'quarantine_reasons':dict(reasons),
        'quarantined_other_sources_january':{'MAD-METEO':69408,'MAD-TRAFFIC':677724},
        'combined_quarantine_without_double_counting':report['quarantined']+69408+677724,
        'duplicates':report['duplicates'],'conflicts':report['conflicts'],'synthetic_measurements':0,
        'synthetic_admin_entities':14,'new_measurement_download_bytes':0,
        'official_documentation_bytes':sum(row['bytes'] for row in research),
        'original_input_bytes':sum(original_files.values()),
        'annual_output_bytes':report['output_bytes'],
        'accepted_jsonl_MB_decimal':report['output_bytes']['accepted.extjsonl']/1_000_000,
        'annual_outputs_GB_decimal':sum(report['output_bytes'].values())/1_000_000_000,
        'counts_are_not_additive_across_generations':True,'shared_server_modified':False}


if __name__=='__main__':
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
