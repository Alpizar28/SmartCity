"""Phase3 tests over real saved data and actual native SQL execution (no fake volume)."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from audit import csv_encoding, local
from download import ROOT
from readers import madrid_long
from phase3_validate import OUT, PRIVATE, SOURCES, load, sha


def result(name):
    path=OUT/name
    assert path.exists(),f'Run phase3_validate.py and phase3_postgres.py before tests: {path}'
    return json.loads(path.read_text())


@pytest.mark.parametrize('city',list(SOURCES))
def test_native_postgresql_results_and_volume(city):
    execution=result('postgres_execution.json')
    assert execution['native_executed'] and execution['container_removed']
    city_result=execution['cities'][city]
    assert city_result['threshold_100k_loaded']
    for query in ['PG01','PG02','PG03','PG04','PG05','PG06','PG07','PG08','PG09','PG10']:
        assert city_result['queries'][query]['equals_python_reference']
    for check in city_result['constraints'].values():assert check['rejected']


@pytest.mark.parametrize('city',list(SOURCES))
def test_shared_identifiers_integrity_and_unknown_attributes(city):
    d=PRIVATE/city
    readings=pd.read_csv(d/'readings.csv',dtype={'measurement_id':str,'channel_id':str})
    channels=pd.read_csv(d/'channels.csv')
    categories=pd.read_csv(d/'categories.csv');locations=pd.read_csv(d/'locations.csv')
    assert readings.measurement_id.is_unique
    assert channels.channel_id.is_unique
    assert readings.channel_id.isin(channels.channel_id).all()
    assert channels.category_id.isin(categories.category_id).all()
    assert channels.location_id.isin(locations.location_id).all()
    assert channels.installation_date.isna().all() and channels.administrative_status.isna().all()
    assert readings.time.notna().all() and np.isfinite(readings.value).all()


@pytest.mark.parametrize('source',['MAD-AIR','MAD-METEO'])
def test_original_madrid_normalization_exact(source):
    path=local(source+'-file')
    raw=pd.read_csv(path,sep=';',dtype=str,encoding=csv_encoding(path))
    selected=raw[raw.ANO.eq('2025') & raw.MES.astype(int).isin([1,7])]
    reference=madrid_long(selected,source)
    saved=load(source)
    for c in ['entity','variable','time','value','quality','unit']:
        pd.testing.assert_series_equal(reference[c].reset_index(drop=True),saved[c].reset_index(drop=True),check_dtype=False)
    catalog=load(source+'-META')
    assert saved.entity.isin(catalog.entity).all()


def test_epa_utc_identity_and_values_match_raw():
    original=load('NYC-AIR-raw');normalized=load('NYC-AIR')
    reference=pd.to_datetime(original['Date GMT']+' '+original['Time GMT'],utc=True)
    pd.testing.assert_series_equal(reference.reset_index(drop=True),normalized.time.reset_index(drop=True),check_names=False)
    np.testing.assert_allclose(pd.to_numeric(original['Sample Measurement']),normalized.value)
    assert not normalized.duplicated(['entity','variable','time']).any()
    assert set(normalized.unit)=={'Micrograms/cubic meter (LC)'}


def test_dot_no_published_metadata_key_resolves_conflicts():
    r=result('dot_conflicts.json')
    assert r['groups']==4767 and r['conflicting_rows']==9534
    assert all(n==4767 for n in r['candidate_duplicate_extras'].values())
    assert not r['correct_physical_key_found']
    assert r['exact_raw_duplicates']==0


def test_madrid_coverage_denominator_and_losses():
    d=result('validation.json')['Madrid']['join']
    assert d['eligible_NO2']==33821 and d['matched']==19087
    assert sum(d['losses'].values())==d['eligible_NO2']
    assert d['losses']['no_colocated_site']==14722
    assert d['losses']['no_eligible_temperature']==12
    assert 56.43<d['pct']<56.44


def test_nyc_coverage_is_sample_groups_not_observations():
    d=result('validation.json')['NYC']['joins']
    assert d['DOT_311']['matched_groups']==11 and d['DOT_311']['left_groups']==322
    assert d['DOT_EPA']['matched_groups']==146
    assert d['311_dates']==16
    assert d['EPA_UTC_duplicates']==0


def test_london_temporal_match_not_household_geography():
    d=result('validation.json')['London']['join']
    assert d['coverage']['matched_groups']==1488
    assert d['household_fine_location_columns']==[]
    assert d['partial_household_hours']==44
    df=pd.read_csv(PRIVATE/'London/locations.csv')
    homes=df[df.location_id.str.startswith('LON-ENERGY:')]
    assert homes[['zone','district','lat','lon']].isna().all().all()
    variants=d['timezone_sensitivity']
    assert len(variants)==3 and variants[0]['matches']<variants[1]['matches']


def test_full_lcl_unique_document_count_not_attribute_multiplication():
    d=result('validation.json')['London']['expanded']
    assert d['rows']==4000000 and d['unique_keys']==3997252
    assert d['conflicting_extra_values']==0
    assert d['duplicate_extras']==2748
    assert d['unique_keys']>1000000


def test_incident_details_not_counted_as_accidents_and_null_categories_preserved():
    d=result('incident_checks.json')['Madrid']
    assert d['detail_rows']==33322 and d['incident_ids']==14388
    assert d['conflicting_categories']==0
    assert sum(d['category_counts'].values())+d['missing_category_incidents']==d['incident_ids']
    assert d['missing_category_incidents']==2


def test_units_documented_separately_from_unverified_units():
    d=result('unit_history_checks.json')['Madrid']
    assert d['air_unit_mapping_consistent_with_dictionary']
    assert not d['meteo_units_dictionary_full_verification']
    provenance=result('madrid_dictionary_provenance.json')
    assert provenance['unit_codes_extracted']['8']=='ug/m3'
    assert provenance['unit_codes_extracted']['6']=='mg/m3'


@pytest.mark.parametrize('city',list(SOURCES))
def test_python_aggregation_separates_units_and_matches_samples(city):
    observed=pd.concat([load(s) for s in SOURCES[city]],ignore_index=True)
    from integrate import unambiguous
    observed,_=unambiguous(observed)
    # Cross-source entity namespaces remain distinct; retained input is same as validator.
    actual=pd.read_csv(OUT/(city+'_python_aggregates.csv'),dtype={'variable':str})
    reference=observed.groupby(['source','variable','unit']).value.agg(['count','min','max','mean']).reset_index()
    pd.testing.assert_frame_equal(actual,reference,check_dtype=False,rtol=1e-10)


def test_prior_inputs_unchanged_after_phase3():
    entries=pd.read_csv(OUT/'inputs_manifest.csv')
    for _,r in entries.iterrows():
        p=ROOT/r.path
        assert p.stat().st_size==r.bytes and sha(p)==r.sha256,r.path
