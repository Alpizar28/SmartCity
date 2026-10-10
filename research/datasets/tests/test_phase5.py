"""Draft contract regressions + actual saved native evidence; no network or engine startup."""
import copy
import csv
from datetime import datetime, timedelta
import json
import sqlite3
import subprocess
import sys

import pytest

from phase5_contract import (ROOT, OUT, PRIVATE, base_document, digest, hourly_endpoint,
                             local_to_utc, numeric, stable_id, validate_document)


def result(name):
    return json.loads((OUT/name).read_text())


@pytest.fixture(scope='module')
def sample():
    return json.loads((PRIVATE/'sample.extjson').read_text())


@pytest.fixture(scope='module')
def catalogs():
    return json.loads((PRIVATE/'catalogs.json').read_text())


def test_ids_stable_length_safe_and_snapshot_independent():
    assert stable_id('channel','ab','c')!=stable_id('channel','a','bc')
    assert stable_id('station','MAD-AIR','4')!=stable_id('station','MAD-METEO','4')
    a = base_document('MAD-AIR','a'*64,'4',['4','8','technique'],datetime(2025,1,1,1),'hour_end')
    b = base_document('MAD-AIR','b'*64,'4',['4','8','technique'],datetime(2025,1,1,1),'hour_end')
    assert a['_id']==b['_id'] and a['sensor_id'] is None


@pytest.mark.parametrize('local,utc',[
    (datetime(2025,1,1,1),'2025-01-01T00:00:00+00:00'),
    (datetime(2025,7,1,1),'2025-06-30T23:00:00+00:00'),
    (hourly_endpoint('2025-01-31',24),'2025-01-31T23:00:00+00:00')])
def test_madrid_offsets_and_H24(local,utc):
    assert local_to_utc(local).isoformat()==utc


@pytest.mark.parametrize('local,message',[
    (datetime(2025,3,30,2,30),'nonexistent'),
    (datetime(2025,10,26,2,30),'ambiguous')])
def test_DST_rejects_without_publisher_evidence(local,message):
    with pytest.raises(ValueError,match=message):
        local_to_utc(local)


def test_explicit_publisher_fold_is_distinct_not_guessed():
    first = local_to_utc(datetime(2025,10,26,2,30),fold=0)
    second = local_to_utc(datetime(2025,10,26,2,30),fold=1)
    assert second-first==timedelta(hours=1)


@pytest.mark.parametrize('hour',[0,25])
def test_invalid_hour_rejected(hour):
    with pytest.raises(ValueError):
        hourly_endpoint('2025-01-31',hour)


@pytest.mark.parametrize('value,expected',[('0',0),('1,25',1.25),('NaN',None),('Infinity',None),('',None),(None,None)])
def test_numeric_zero_decimal_null_and_finite(value,expected):
    assert numeric(value)==expected


def test_all_exported_observations_have_traceability_and_refs(sample,catalogs):
    assert len(sample)==5000 and len({d['_id'] for d in sample})==5000
    for d in sample:
        assert validate_document(d,catalogs)
        assert d['data_origin']=='observed' and d['sensor_id'] is None
        assert d['raw_reference']['row']>=2
        content = {k:v for k,v in d.items() if k not in ('raw_reference','payload_hash')}
        assert stable_id('payload',content)==d['payload_hash']
        assert all(v is None or v in ('observed','derived','synthetic') for k,v in d['provenance'].items() if k!='unit_availability')


@pytest.mark.parametrize('field,value',[
    ('sensor_id','invented-device'),('channel_id','orphan-channel'),
    ('zone_id','invented-zone'),('measurement_type','not-real-variable'),
    ('source_id','other-city'),('value',None),('observed_at',{'$date':'2025-01-01T00:00:01Z'})])
def test_bad_references_or_contract_rejected(sample,catalogs,field,value):
    d = copy.deepcopy(sample[0]); d[field]=value
    with pytest.raises(ValueError):
        validate_document(d,catalogs)


def test_meteo_unknown_units_and_no_fabricated_geography(sample,catalogs):
    meteo = [d for d in sample if d['source_id']=='MAD-METEO']
    assert len(meteo)==1000 and all(d['unit'] is None and d['unit_status']=='pending_dictionary' for d in meteo)
    assert all(d['zone_id'] is None for d in sample if d['source_id']!='MAD-TRAFFIC')
    assert all(not s['historical_location_verified'] for s in catalogs['stations'].values())
    assert any(s['original_coordinates'] for s in catalogs['stations'].values())
    assert not any('geometry' in s for s in catalogs['stations'].values())


def test_January_source_selection_includes_H24_February_endpoint(sample):
    endpoint = [d for d in sample if d['timestamp_role']=='hour_end' and d['original_time']=='2025-02-01T00:00:00']
    assert endpoint and all(d['observed_at']=={'$date':'2025-01-31T23:00:00Z'} for d in endpoint)
    assert all(d['original_time'][:7]=='2025-01' or d['original_time']=='2025-02-01T00:00:00' for d in sample)


@pytest.mark.parametrize('source,selected,valid',[
    ('MAD-AIR',93720,91959),('MAD-METEO',69408,66005),('MAD-TRAFFIC',677724,674704)])
def test_exact_January_cardinality_in_saved_ledger(source,selected,valid):
    prep = result('preparation.json')['counts'][source]
    db = sqlite3.connect('file:'+str(PRIVATE/'identity_ledger.sqlite')+'?mode=ro',uri=True)
    actual = db.execute('SELECT count(*),sum(valid AND NOT conflict),sum(conflict) FROM identities WHERE source=?',(source,)).fetchone()
    db.close()
    assert actual==(selected,valid,0)
    assert prep['effective_documents']==valid and prep['duplicate_extras']==prep['conflicting_keys']==0


def test_traffic_document_has_one_bundle_not_split_and_URB_QA(sample):
    traffic = [d for d in sample if d['source_id']=='MAD-TRAFFIC']
    assert len(traffic)==3000
    for d in traffic:
        assert set(d['measurements'])=={'ocupacion','carga','vmed'}
        assert 1<=d['interval_minutes']<=30 and d['value']>=0
        if d['element_type']=='URB':
            assert d['measurements']['vmed']['value'] is None
    assert result('preparation.json')['counts']['MAD-TRAFFIC']['effective_documents']==674704


def test_dry_run_no_mutation_and_complete_run_idempotent():
    before = digest(PRIVATE/'sample.extjson')
    command = [sys.executable,str(ROOT/'scripts/phase5_prepare.py')]
    dry = subprocess.run(command+['--dry-run'],check=True,capture_output=True,text=True)
    assert json.loads(dry.stdout)['connects_to_engines'] is False
    replay = subprocess.run(command,check=True,capture_output=True,text=True)
    assert json.loads(replay.stdout)['idempotent_reuse'] is True
    assert digest(PRIVATE/'sample.extjson')==before


def test_native_Mongo_bson_framework_indexes_and_local_only():
    mongo = result('mongodb_execution.json')
    assert mongo['native_executed'] and mongo['sample_size']==5000
    assert mongo['network']=='none' and mongo['published_ports']==[]
    assert mongo['local_socket']=='unix:///var/run/docker.sock'
    assert mongo['container_removed'] and mongo['anonymous_volumes_removed']
    assert mongo['catalog_reference_errors']==0
    assert mongo['queries']['MG09']['native_framework'] and mongo['queries']['MG09']['reference_equal']
    assert mongo['rejected']['duplicate'] and mongo['rejected']['string_date']
    assert mongo['idempotent_reimport']['count']==5000 and mongo['idempotent_reimport']['upserted']==0
    assert mongo['crud']['original_measurements_mutated']==0
    assert mongo['crud']['synthetic_nonmeasurement_fixtures']==3
    assert len(mongo['indexes'])>=4 and mongo['explain']['executionStats']['nReturned']>0
    assert all(not mongo['queries'][q]['executed'] for q in ('MG04','MG05','MG08'))


def test_native_SQL_catalogs_and_actual_constraint_errors():
    pg = result('postgresql_sample.json')
    assert pg['native_executed'] and pg['counts']['observations']==5000
    assert pg['counts']['sensors']==pg['counts']['users']==0
    assert pg['catalogs_match_document_catalogs'] and pg['sample_values_match_reference']
    assert pg['container_removed'] and pg['anonymous_volumes_removed']
    assert all(r['rejected'] for r in pg['constraints'].values())
    assert 'channel/station/type/source version mismatch' in pg['constraints']['wrong_source_rejected']['stderr']


def test_dictionary_required_attributes_and_explicit_missing():
    rows = list(csv.DictReader((ROOT/'05_data_dictionary.csv').open()))
    required = {'sensor_id','station_id','zone_id','measurement_id','observed_at','measurement_type','value','unit','source_id','data_origin'}
    assert required.issubset({r['attribute'] for r in rows})
    assert len(rows)>=50
    assert all(r['meaning'] and r['postgresql_type'] and r['bson_type'] and r['availability'] and
               r['source_id'] and r['source_version'] and r['transformation'] for r in rows)
    sensor = next(r for r in rows if r['attribute']=='sensor_id')
    assert sensor['nullable']=='true' and sensor['availability']=='unavailable' and sensor['data_origin']==''


def test_eleven_deliverables_and_no_approval_inferred():
    paths = list(ROOT.glob('05_*.md'))+[ROOT/'05_data_dictionary.csv']
    assert len(paths)==11 and all(p.stat().st_size>100 for p in paths)
    assert result('preparation.json')['synthetic_measurements']==0
    assert not result('mongodb_execution.json')['physical_sensor_semantics_approved']
    assert all(d['source_id'] in ('MAD-AIR','MAD-METEO','MAD-TRAFFIC') for d in result('examples.extjson'))
    assert 'no ratifica' in (ROOT/'05_dataset_manifest.md').read_text()
