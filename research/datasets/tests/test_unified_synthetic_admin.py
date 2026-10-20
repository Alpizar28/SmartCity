"""Deterministic administrative seed must never contaminate observed data."""

import json

from phase5_contract import digest
from unified_synthetic import build_administrative_seed, write_administrative_seed


def catalogs():
    return {
        'stations': {
            'station:a': {'station_id': 'station:a'},
            'station:b': {'station_id': 'station:b'},
        },
        'sensor_categories': {
            'category:x': {'category_id': 'category:x'},
            'category:y': {'category_id': 'category:y'},
        },
    }


def test_administrative_seed_is_deterministic_and_covers_each_station():
    first = build_administrative_seed(catalogs(), 'a' * 64)
    second = build_administrative_seed(catalogs(), 'a' * 64)

    assert first == second
    assert {row['station_id'] for row in first['sensors']} == {'station:a', 'station:b'}
    assert {row['category_id'] for row in first['sensors']} <= {'category:x', 'category:y'}


def test_administrative_seed_rows_are_safe_and_explicitly_synthetic():
    seed = build_administrative_seed(catalogs(), 'b' * 64)

    for table in ('organizations', 'users', 'sensors'):
        assert seed[table]
        for row in seed[table]:
            assert row['data_origin'] == 'synthetic'
            assert row['provenance']['physical_inventory_evidence'] is False
    assert all(row['demo_only'] is True for row in seed['users'])
    assert all(row['email'].endswith('@example.invalid') for row in seed['users'])
    assert all('channel_id' not in row and 'measurement_id' not in row for row in seed['sensors'])
    assert seed['synthetic_measurements'] == 0


def test_seed_writer_seals_hashes_and_refuses_different_overwrite(tmp_path):
    private, results = tmp_path / 'private', tmp_path / 'results'
    private.mkdir()
    results.mkdir()
    catalog_path = private / 'catalogs.json'
    catalog_path.write_text(json.dumps(catalogs()))

    manifest = write_administrative_seed(private, results, catalog_path)

    seed_path = private / 'administrative_seed.json'
    assert manifest['administrative_seed_sha256'] == digest(seed_path)
    assert manifest['catalogs_sha256'] == digest(catalog_path)
    assert manifest['counts'] == {'organizations': 1, 'users': 2, 'sensors': 2}
    assert (results / 'administrative_manifest.json').is_file()
    assert write_administrative_seed(private, results, catalog_path) == manifest

    catalog_path.write_text(json.dumps({**catalogs(), 'stations': {'station:changed': {}}}))
    try:
        write_administrative_seed(private, results, catalog_path)
    except ValueError as error:
        assert 'differs' in str(error)
    else:
        raise AssertionError('different catalog must not overwrite the sealed seed')
