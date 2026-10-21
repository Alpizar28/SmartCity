"""Offline unit tests using published historical examples, not generated datasets.

Only test-local copies are explicitly mapped to the new staging format. This is
not an importer, reclassification of evidence, or a new real-data validation.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from sprint1.core.contract import METHOD, VERSION, hourly_endpoint, local_to_utc, payload_hash, stable_id, staging_key
from sprint1.core.validation import StagingLedger, validate_document
from sprint1.core.adapters import ReadingDTO

ROOT = Path(__file__).resolve().parents[2]


def examples():
    historical = json.loads((ROOT / 'research/datasets/results/phase5/examples.extjson').read_text())
    docs = []
    catalogs = {'sources': {}, 'versions': {}, 'stations': {}, 'channels': {}, 'zones': {}}
    for original in historical:
        doc = deepcopy(original)
        del doc['_id'], doc['measurement_id']
        doc['schema_version'] = VERSION
        doc['transformation_method'] = METHOD
        if doc['source_id'] == 'MAD-TRAFFIC':
            doc['interval_minutes'] = int(doc['interval_minutes'])
        doc['payload_hash'] = payload_hash(doc)
        docs.append(doc)
        source = doc['source_id']
        catalogs['sources'][source] = {'source_id': source}
        catalogs['versions'][doc['source_version']] = {'source_id': source}
        catalogs['stations'][doc['station_id']] = {
            'source_id': source, 'source_key': doc['source_key'][0], 'zone_id': doc['zone_id']}
        catalogs['channels'][doc['channel_id']] = {
            k: doc[k] for k in ('source_id', 'station_id', 'measurement_type', 'unit', 'unit_status')}
        if doc['zone_id']:
            catalogs['zones'][doc['zone_id']] = {'level': 'district'}
    return docs, catalogs


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.docs, self.catalogs = examples()

    def invalid(self, doc, code):
        doc['payload_hash'] = payload_hash(doc)
        with self.assertRaisesRegex(ValueError, code):
            validate_document(doc, self.catalogs)

    def test_explicit_test_copies_validate_for_all_sources(self):
        for doc in self.docs:
            with self.subTest(source=doc['source_id']):
                self.assertTrue(validate_document(doc, self.catalogs))

    def test_historical_documents_not_automatically_retagged(self):
        original = json.loads((ROOT / 'research/datasets/results/phase5/examples.extjson').read_text())[0]
        with self.assertRaisesRegex(ValueError, 'schema_version'):
            validate_document(original, self.catalogs)

    def test_identity_matches_published_station(self):
        doc = self.docs[0]
        self.assertEqual(stable_id('station', doc['source_id'], doc['source_key'][0]), doc['station_id'])
        self.assertNotEqual(stable_id('station', 'ab', 'c'), stable_id('station', 'a', 'bc'))

    def test_h24_and_utc(self):
        self.assertEqual(hourly_endpoint('2025-01-31', 24), datetime(2025, 2, 1))
        self.assertEqual(local_to_utc(datetime(2025, 1, 1, 1)), datetime(2025, 1, 1, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            hourly_endpoint('2025-01-01', 0)

    def test_dst_fails_closed(self):
        for time in (datetime(2025, 3, 30, 2, 30), datetime(2025, 10, 26, 2, 30)):
            with self.subTest(time=time), self.assertRaises(ValueError):
                local_to_utc(time)
        self.assertNotEqual(local_to_utc(datetime(2025, 10, 26, 2, 30), 0),
                            local_to_utc(datetime(2025, 10, 26, 2, 30), 1))
        with self.assertRaises(ValueError):
            local_to_utc(datetime(2025, 1, 1), True)

    def test_null_is_not_zero_and_booleans_are_not_numbers(self):
        for value in (None, True, '0'):
            doc = deepcopy(self.docs[0])
            doc['value'] = value
            self.invalid(doc, 'finite_numeric')
        doc['value'] = 0
        doc['payload_hash'] = payload_hash(doc)
        self.assertTrue(validate_document(doc, self.catalogs))
        for value in (float('nan'), float('inf')):
            doc['value'] = value
            with self.assertRaises(ValueError):
                validate_document(doc, self.catalogs)

    def test_no_invented_physical_identity(self):
        for field in ('sensor_id', 'organization_id', 'user_id', 'installation_date', 'administrative_status'):
            doc = deepcopy(self.docs[0])
            doc[field] = 'unsupported'
            self.invalid(doc, 'unsupported_' + field)

    def test_provenance_and_catalog_mismatch_rejected(self):
        doc = deepcopy(self.docs[0])
        doc['raw_reference']['sha256'] = '0' * 64
        self.invalid(doc, 'provenance_hash')
        doc = deepcopy(self.docs[0])
        self.catalogs['channels'][doc['channel_id']]['source_id'] = 'MAD-METEO'
        self.invalid(doc, 'catalog_channel_source_id')

    def test_pending_units_and_clock_cannot_be_promoted(self):
        doc = deepcopy(self.docs[1])
        doc['unit'] = 'm/s'
        self.invalid(doc, 'meteo_unit_unverified')
        doc = deepcopy(self.docs[2])
        doc['timestamp_status'] = 'documented_local'
        self.invalid(doc, 'timestamp_evidence')

    def test_utc_and_source_key_must_match(self):
        doc = deepcopy(self.docs[0])
        doc['observed_at'] = {'$date': '2025-01-01T01:00:00Z'}
        self.invalid(doc, 'utc_roundtrip')
        doc = deepcopy(self.docs[0])
        doc['source_key'][-1] = 'H02'
        self.invalid(doc, 'source_clock')

    def test_traffic_raw_payload_and_qa_preserved(self):
        doc = deepcopy(self.docs[2])
        del doc['measurements']['vmed']['raw_value']
        self.invalid(doc, 'traffic_raw_value')
        doc = deepcopy(self.docs[2])
        doc['measurements']['carga']['value'] = None
        doc['payload_hash'] = payload_hash(doc)
        self.assertTrue(validate_document(doc, self.catalogs))
        self.assertEqual(self.docs[2]['measurements']['carga']['value'], 0)

    def test_content_fingerprint_is_verified(self):
        doc = deepcopy(self.docs[0])
        doc['value'] += 1
        with self.assertRaisesRegex(ValueError, 'payload_hash'):
            validate_document(doc, self.catalogs)

    def test_duplicate_and_conflict_never_overwrite(self):
        ledger = StagingLedger()
        doc = self.docs[0]
        self.assertEqual(ledger.accept(doc, self.catalogs), 'accepted')
        self.assertEqual(ledger.accept(doc, self.catalogs), 'duplicate')
        conflicting = deepcopy(doc)
        conflicting['value'] += 1  # Deliberately invalid content mutation, not a dataset.
        conflicting['payload_hash'] = payload_hash(conflicting)
        self.assertEqual(ledger.accept(conflicting, self.catalogs), 'quarantined')
        self.assertEqual(next(iter(ledger.records.values()))['value'], doc['value'])
        self.assertEqual(len(ledger.quarantine), 1)

    def test_snapshot_version_cannot_change_source(self):
        doc = self.docs[0]
        self.catalogs['versions'][doc['source_version']]['source_id'] = 'MAD-METEO'
        self.invalid(doc, 'catalog_version_source')

    def test_catalog_unit_cannot_be_changed_by_incoming_reading(self):
        doc = deepcopy(self.docs[0])
        doc['unit'] = 'unsupported'
        self.invalid(doc, 'catalog_channel_unit')

    def test_dto_copies_and_projects_without_assigning_final_identity(self):
        original = deepcopy(self.docs[0])
        dto = ReadingDTO(original, self.catalogs)
        original['value'] += 1
        exported = dto.document()
        exported['value'] += 2
        self.assertEqual(dto.document(), self.docs[0])
        mongo = dto.mongo_document()
        self.assertIsInstance(mongo['observed_at'], datetime)
        self.assertEqual(mongo['observed_at'].utcoffset().total_seconds(), 0)
        self.assertNotIn('_id', mongo)
        self.assertEqual(mongo['staging_key'], staging_key(dto.document()))
        postgres = dto.postgres_record()
        self.assertIsNone(postgres['original_time'].tzinfo)
        self.assertEqual(postgres['payload_hash'], self.docs[0]['payload_hash'])
        self.assertEqual(postgres['document'], self.docs[0])

    def test_dto_rejects_invalid_document_and_preserves_optional_null_time(self):
        doc = deepcopy(self.docs[1])
        doc['observed_at'] = None
        doc['payload_hash'] = payload_hash(doc)
        dto = ReadingDTO(doc, self.catalogs)
        self.assertIsNone(dto.mongo_document()['observed_at'])
        self.assertIsNone(dto.postgres_record()['unit'])
        doc['sensor_id'] = 'unsupported'
        with self.assertRaisesRegex(ValueError, 'unsupported_sensor_id'):
            ReadingDTO(doc, self.catalogs)

    def test_storage_key_is_derived_not_trusted_from_incoming_payload(self):
        doc = deepcopy(self.docs[0])
        doc['staging_key'] = 'untrusted'
        self.invalid(doc, 'storage_or_final_identity')

    def test_staging_identity_uses_original_key_not_utc_or_value(self):
        doc = deepcopy(self.docs[0])
        key = staging_key(doc)
        doc['value'] += 1
        doc['observed_at'] = None
        self.assertEqual(staging_key(doc), key)
        doc['source_version'] = '0' * 64
        self.assertNotEqual(staging_key(doc), key)


if __name__ == '__main__':
    unittest.main()
