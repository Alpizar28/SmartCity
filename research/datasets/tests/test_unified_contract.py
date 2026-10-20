"""Current contract tests: no saved evidence, services or private inputs required."""
import copy
from datetime import datetime

import pytest

from phase5_contract import (base_document, payload_hash, stable_id, validate_document,
                             VERSION, OUT, PRIVATE)
from unified_synthetic import generate


def observation():
    doc = base_document('MAD-AIR', 'a'*64, '4', ['4','8',None],
                        datetime(2025,1,1,1), 'hour_end')
    doc.update(value=1.5, measurement_type='MAD-AIR:8', unit='ug/m3',
               unit_status='verified_dictionary', quality_flag='V',
               raw_reference={'sha256':'a'*64, 'row':2, 'path':'fixture.csv','column':'H01'})
    doc['payload_hash'] = payload_hash(doc)
    catalogs = {
        'stations':{doc['station_id']:{'source_id':'MAD-AIR','source_key':'4','zone_id':None}},
        'channels':{doc['channel_id']:{'station_id':doc['station_id'], 'source_id':'MAD-AIR',
                                     'source_key':['4','8',None], 'measurement_type':'MAD-AIR:8'}},
        'measurement_types':{'MAD-AIR:8':{'source_id':'MAD-AIR','unit':'ug/m3','unit_status':'verified_dictionary'}},
        'source_versions':{'a'*64:{'source_id':'MAD-AIR'}}, 'zones':{}}
    return doc, catalogs


def test_current_output_is_separate_from_historical():
    assert OUT.name == PRIVATE.name == 'unified-v1'
    assert VERSION == 'madrid-draft-v1'


def test_valid_document_and_explicit_station_channel_identity():
    doc, catalogs = observation()
    assert validate_document(doc, catalogs)
    assert doc['channel_id'] == stable_id('channel', 'MAD-AIR', doc['station_id'], ['4','8',None])
    other = base_document('MAD-AIR', 'a'*64, '5', ['4','8',None], datetime(2025,1,1,1), 'hour_end')
    assert doc['channel_id'] != other['channel_id']


@pytest.mark.parametrize('local,status,reason', [
    (datetime(2025,3,30,2,30),'documented_local','nonexistent'),
    (datetime(2025,10,26,2,30),'documented_local','ambiguous'),
    (datetime(2025,1,1,1),'assumed_local','unconfirmed')])
def test_quarantine_never_exports_provisional_utc_or_identity(local,status,reason):
    doc = base_document('MAD-AIR','a'*64,'4', ['8'], local, 'hour_end', status)
    assert reason in doc['time_error']
    assert doc['observed_at'] is None and doc['measurement_id'] is None and doc['_id'] is None


@pytest.mark.parametrize('field,value', [
    ('schema_version','madrid-draft-v1-frozen'), ('catalog_version','other'),
    ('source_id','unknown'), ('source_version','bad'), ('timestamp_status','assumed_local'),
    ('transformation_version',''), ('timestamp_role','invented'), ('value',float('inf')),
    ('value',True), ('value','1.5'), ('sensor_id','fictional'), ('unit',None),
    ('data_origin','synthetic'), ('original_timezone','UTC')])
def test_rejects_invalid_contract(field,value):
    doc, catalogs = observation()
    doc[field] = value
    with pytest.raises(ValueError):
        doc['payload_hash'] = payload_hash(doc)
        validate_document(doc, catalogs)


def test_payload_hash_detects_change_but_not_physical_row():
    doc, catalogs = observation()
    moved = copy.deepcopy(doc)
    moved['raw_reference']['row'] = 99
    assert payload_hash(moved) == doc['payload_hash']
    assert validate_document(moved,catalogs)
    moved['value'] += 1
    with pytest.raises(ValueError, match='payload_hash'):
        validate_document(moved,catalogs)


@pytest.mark.parametrize('catalog,key,field,value', [
    ('stations','station_id','source_id','MAD-METEO'),
    ('channels','channel_id','station_id','other'),
    ('channels','channel_id','source_key',['other']),
    ('measurement_types','measurement_type','unit','wrong'),
    ('source_versions','source_version','source_id','MAD-METEO')])
def test_catalog_integrity(catalog,key,field,value):
    doc, catalogs = observation()
    catalogs[catalog][doc[key]][field] = value
    with pytest.raises(ValueError):
        validate_document(doc,catalogs)


def test_synthetic_administrative_entities_reproducible_and_separate():
    rows = generate()
    assert rows == generate() and rows != generate(seed=123)
    assert {r['entity_type'] for r in rows} == {'sensor','organization','user'}
    assert all(r['data_origin']=='synthetic' and 'measurement_id' not in r for r in rows)
    assert all(not r['provenance']['physical_inventory_evidence'] for r in rows)
    assert all(r['payload']['station_id'] is None for r in rows if r['entity_type']=='sensor')
