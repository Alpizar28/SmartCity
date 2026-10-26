"""Read-only reconciliation of the new local evidence; no historical report rewrites."""
import json

from phase5_contract import ROOT, OUT, PRIVATE, digest, validate_bundle


def verify():
    preparation = validate_bundle()
    pg = json.loads((OUT/'postgresql_sample.json').read_text())
    mongo = json.loads((OUT/'mongodb_execution.json').read_text())
    for engine in (pg,mongo):
        for filename, expected in engine['source_hashes'].items():
            if digest(ROOT/'scripts'/filename) != expected:
                raise ValueError('Native evidence source changed: '+filename)
    for filename, expected in preparation['private_output_hashes'].items():
        if digest(PRIVATE/filename) != expected:
            raise ValueError('Altered output: '+filename)
    if not (pg['native_executed'] and mongo['native_executed'] and mongo['postgresql_reconciled']):
        raise ValueError('Missing native reconciliation')
    if pg['input_sha256'] != mongo['input_sha256'] or pg['input_sha256'] != digest(PRIVATE/'sample.extjson'):
        raise ValueError('Input generation mismatch')
    if pg['ids_values_sha256'] != mongo['ids_values_sha256']:
        raise ValueError('IDs/values differ')
    if pg['demo_input_sha256'] != digest(PRIVATE/'synthetic_admin.json'):
        raise ValueError('Demo changed after native validation')
    if pg['counts']['observations'] != preparation['sample_size'] or mongo['sample_size'] != preparation['sample_size']:
        raise ValueError('Sample count mismatch')
    if not (pg['idempotent_reimport'] and pg['conflicting_reimport']['rejected']
            and mongo['conflicting_reimport']['rejected'] and mongo['conflicting_reimport']['recorded']):
        raise ValueError('Replay/conflict checks missing')
    if not all(pg['constraints'][key]['rejected'] for key in pg['constraints']):
        raise ValueError('Integrity check failed')
    if not all(e['container_removed'] and e['anonymous_volumes_removed'] for e in (pg,mongo)):
        raise ValueError('Disposable resource cleanup incomplete')
    return {'verified':True, 'sample_size':preparation['sample_size'],
            'ids_values_sha256':pg['ids_values_sha256'], 'counts':preparation['counts'],
            'shared_server_modified':False, 'full_batch_loaded':False}


if __name__ == '__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
