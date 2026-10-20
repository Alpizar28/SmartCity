"""Evidence verifier must not accept a sample, missing replay or failed engine run."""
from hashlib import sha256
import json
import sqlite3

import pytest

from phase5_contract import canonical, digest
import unified_full_verify as verifier


@pytest.fixture
def evidence(tmp_path,monkeypatch):
    private,out=tmp_path/'private',tmp_path/'out'
    private.mkdir()
    out.mkdir()
    (private/'accepted.extjsonl').write_text('fixture-only\n')
    with sqlite3.connect(private/'identities.sqlite') as db:
        db.execute('CREATE TABLE identities(id TEXT PRIMARY KEY,signature TEXT)')
        db.execute('INSERT INTO identities VALUES (?,?)',('measurement:fixture','payload:fixture'))
    fingerprint=sha256((canonical(['measurement:fixture','payload:fixture'])+'\n').encode()).hexdigest()
    preparation={'accepted':1,'quarantined':2,'duplicates':0,'conflicts':0,
        'output_hashes':{'accepted.extjsonl':digest(private/'accepted.extjsonl')}}
    report={'source_hashes':{},'accepted_input_sha256':preparation['output_hashes']['accepted.extjsonl'],
        'count':1,'metadata_verified':1,'ids_payload_sha256':fingerprint,'full_batch':True,
        'native_executed':True,'idempotent_reimport':True,'conflicting_payload_rejected':True,
        'ledger_reconciled':True,'container_removed':True,'anonymous_volumes_removed':True,
        'synthetic_measurements':0,'shared_server_modified':False,'conflict_recorded':True,
        'unique_id_and_natural_key':True,'integrity_rejections':{'fixture':{'rejected':True}},
        'administrative_counts':{'organizations':1,'users':1,'sensors':1},
        'channels_assigned_to_synthetic_sensors':0,'readings_with_sensor_link':0}
    for engine in ('postgresql','mongodb'):
        (out/(engine+'_full.json')).write_text(json.dumps(report))
    monkeypatch.setattr(verifier,'generation_paths',lambda g:(private,out))
    monkeypatch.setattr(verifier,'verify_generation',lambda g:preparation)
    return out,report


def test_verified_small_input_does_not_claim_minimums_or_spark_or_two_sources(evidence):
    result=verifier.verify('fixture')
    assert result['verified']
    assert not result['postgresql']['met'] and not result['mongodb']['met']
    assert not result['spark']['executed'] and not result['two_measurement_sources_met']
    assert result['administrative_demo']['verified']
    assert result['administrative_demo']['sensors'] == 1


@pytest.mark.parametrize('field,value',[
    ('count',5000),('metadata_verified',0),('full_batch',False),('idempotent_reimport',False),
    ('conflicting_payload_rejected',False),('native_executed',False),('container_removed',False),
    ('ids_payload_sha256','bad'),('accepted_input_sha256','bad'),('error','engine failed'),
    ('shared_server_modified',True),('synthetic_measurements',1),('conflict_recorded',False),
    ('unique_id_and_natural_key',False)])
def test_incomplete_or_invalid_evidence_is_rejected(evidence,field,value):
    out,report=evidence
    (out/'mongodb_full.json').write_text(json.dumps({**report,field:value}))
    with pytest.raises(ValueError):
        verifier.verify('fixture')


def test_administrative_evidence_must_match_and_preserve_observed_data(evidence):
    out,report=evidence
    invalid = {**report, 'administrative_counts': {'organizations': 1, 'users': 1, 'sensors': 0}}
    (out/'mongodb_full.json').write_text(json.dumps(invalid))
    with pytest.raises(ValueError):
        verifier.verify('fixture')

    invalid = {**report, 'readings_with_sensor_link': 1}
    (out/'mongodb_full.json').write_text(json.dumps(invalid))
    with pytest.raises(ValueError):
        verifier.verify('fixture')
