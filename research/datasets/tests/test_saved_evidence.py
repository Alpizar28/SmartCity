"""Assertions over actual saved pipeline results; skipped on installations without data."""
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def evidence(name):
    path=ROOT/'results'/name
    if not path.exists():pytest.skip('Acquire and audit real sources first')
    return json.loads(path.read_text())


def test_actual_budget_and_integrity():
    d=evidence('verification.json')
    assert d['all_checks_passed'] and d['downloaded_entity_bytes']<=d['budget_bytes']


def test_actual_madrid_no_cartesian_growth():
    d=evidence('Madrid-integration.json');c=d['coverage']
    assert 0<c['matched_groups']<=min(c['left_groups'],c['right_groups'])
    assert c['matched_groups']+c['left_unmatched']==c['left_groups']
    assert d['air_row_spatiotemporal_matched']<=d['spatially_mapped_air_NO2_rows']<=d['eligible_air_NO2_rows']


def test_actual_epa_local_filter_not_national_count():
    d=evidence('NYC-AIR-full_counts.json')
    assert 0<d['NYC_rows']<d['NY_state_rows']<d['national_rows']
    assert set(d['counties'])<=set(['005','047','061','081','085'])
    assert sum(d['counties'].values())==d['NYC_rows']
    assert d['CRC_validated_at_EOF']
    summary=evidence('NYC-AIR-summary.json')
    assert summary['duplicate_keys']==0 and summary['unique_keys']==d['NYC_rows']


def test_actual_lcl_unique_real_capacity():
    d=evidence('LCL-expanded_counts.json')
    assert d['unique_household_timestamp_keys']>1_000_000
    assert d['unique_household_timestamp_keys']+d['duplicate_key_extra_rows']==d['rows_complete_members']
    assert d['geographic_columns']==[]


def test_actual_london_not_fake_household_map():
    d=evidence('London-integration.json')
    assert d['household_fine_zone_mapping_pct']==0 and d['fine_zone_mapping_failure']
    assert d['coverage']['matched_groups']>0
