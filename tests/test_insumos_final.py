"""Pruebas pequeñas del auditor: sin datos privados ni motores."""
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location(
    'insumos_final', Path(__file__).resolve().parents[1] / 'scripts/auditar_insumos_final.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def source(rows):
    text = io.StringIO()
    writer = csv.DictWriter(text, fieldnames=list(rows[0]), delimiter=';')
    writer.writeheader()
    writer.writerows(rows)
    return io.BytesIO(text.getvalue().encode('utf-8-sig'))


def row(month='1', day='1'):
    result = dict(PROVINCIA='28', MUNICIPIO='079', ESTACION='1', MAGNITUD='8',
                  PUNTO_MUESTREO='sample', ANO='2025', MES=month, DIA=day)
    for hour in range(1, 25):
        result[f'H{hour:02d}'] = '12,5'
        result[f'V{hour:02d}'] = 'V'
    return result


class InputAuditTests(unittest.TestCase):
    def test_hash(self):
        self.assertEqual(MODULE.sha256_stream(io.BytesIO(b'abc')),
                         hashlib.sha256(b'abc').hexdigest())

    def test_quality_and_nonfinite(self):
        data = row()
        data['V01'] = 'N'
        data['H02'] = 'nan'
        data['H03'] = ''
        counts = MODULE.profile_air(source([data]))['2025']['counts']
        self.assertEqual(counts['candidate_slots'], 21)
        outcomes = sum(value for key, value in counts.items() if key != 'selected_slots')
        self.assertEqual(outcomes, counts['selected_slots'])

    def test_dst(self):
        counts = MODULE.profile_air(source([row('3', '30'), row('10', '26')]))['2025']['counts']
        self.assertEqual(counts['candidate_slots'], 46)
        self.assertEqual(counts['nonexistent_local_time'], 1)
        self.assertEqual(counts['ambiguous_local_time_requires_publisher_fold'], 1)

    def test_duplicate_daily_key_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicada'):
            MODULE.profile_air(source([row(), row()]))

    def test_unknown_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Esquema'):
            MODULE.profile_air(io.BytesIO(b'wrong;columns\n1;2\n'))

    def test_audit_verifies_files_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            generation = root / 'private_results/expanded-v2-2025-01'
            generation.mkdir(parents=True)
            data = source([row()]).getvalue()
            expected = hashlib.sha256(data).hexdigest()
            archive_path = root / 'input.zip'
            with zipfile.ZipFile(archive_path, 'w') as archive:
                archive.writestr('research/datasets/raw/MAD-AIR-file.attempt1.bin', data)
            (generation / 'accepted.extjsonl').write_bytes(b'fixture')
            preparation = {'accepted': 1,
                           'output_hashes': {'accepted.extjsonl': hashlib.sha256(b'fixture').hexdigest()},
                           'source_hashes': {'raw/MAD-AIR-file.attempt1.bin': expected}}
            (generation / 'preparation.json').write_text(json.dumps(preparation))
            result = MODULE.audit(archive_path, root)
            self.assertTrue(result['input_hashes_verified'])
            self.assertFalse(result['spark_executed'])
            self.assertEqual(result['air_raw_profile']['2025']['counts']['candidate_slots'], 24)
            (generation / 'accepted.extjsonl').write_bytes(b'changed')
            self.assertFalse(MODULE.audit(archive_path, root)['input_hashes_verified'])
            (generation / 'accepted.extjsonl').unlink()
            result = MODULE.audit(archive_path, root)
            self.assertFalse(result['input_hashes_verified'])
            self.assertFalse(result['v2_outputs']['accepted.extjsonl']['present'])

    def test_bad_raw_hash_never_produces_candidate_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            generation = root / 'private_results/expanded-v2-2025-01'
            generation.mkdir(parents=True)
            archive_path = root / 'input.zip'
            with zipfile.ZipFile(archive_path, 'w') as archive:
                archive.writestr('research/datasets/raw/MAD-AIR-file.attempt1.bin', b'changed')
            preparation = {'accepted': 0, 'output_hashes': {},
                           'source_hashes': {'raw/MAD-AIR-file.attempt1.bin': '0' * 64}}
            (generation / 'preparation.json').write_text(json.dumps(preparation))
            result = MODULE.audit(archive_path, root)
            self.assertFalse(result['input_hashes_verified'])
            self.assertNotIn('air_raw_profile', result)


if __name__ == '__main__':
    unittest.main()
