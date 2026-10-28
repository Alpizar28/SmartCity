"""Offline regression tests for closure tooling; no private inputs or engines."""
import importlib.util
from pathlib import Path
import sys
import unittest
import zipfile
import io
import json
import re
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('pg_closure_audit', ROOT / 'scripts/auditar_cierre_postgresql.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ClosureTests(unittest.TestCase):
    def test_safe_archive_rejects_traversal_absolute_and_symlink(self):
        for name in ('../escape', '/absolute', 'bad\\path', 'symlink'):
            with self.subTest(name=name):
                stream = io.BytesIO()
                with zipfile.ZipFile(stream, 'w') as z:
                    info = zipfile.ZipInfo(name)
                    if name == 'symlink':
                        info.external_attr = 0o120777 << 16
                    z.writestr(info, 'x')
                stream.seek(0)
                with zipfile.ZipFile(stream) as z, self.assertRaises(ValueError):
                    audit.safe_members(z)

    def test_safe_archive_accepts_relative_regular_member(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('generation/catalogs.json', '{}')
        stream.seek(0)
        with zipfile.ZipFile(stream) as z:
            audit.safe_members(z)

    def test_observed_ranking_is_not_based_on_synthetic_sensors(self):
        sql = (ROOT / 'sprint1/postgres/sql_avanzado_observado.sql').read_text()
        self.assertIn('DENSE_RANK()', sql)
        self.assertIn('WITH channel_counts', sql)
        self.assertIn('smartcity.observations', sql)
        self.assertNotIn('smartcity.sensors', sql)

    def test_pg07_extra_fixture_keeps_rollback_owned_by_runner(self):
        text = (ROOT / 'tests/integration/postgres_pg07_cases.sql').read_text()
        self.assertIn('23:59:59.999999+01', text)
        self.assertIn('channel-active-empty', text)
        self.assertIn('channel-empty-2', text)
        self.assertNotIn('COMMIT;', text)

    def test_audit_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'test failure'):
            audit.require(False, 'test failure')

    def test_audit_rejects_failed_stale_or_unclean_historical_report(self):
        historical = json.loads(audit.HISTORICAL.read_text())
        preparation = {k: historical[k] for k in ('generation','contract','accepted','by_source')}
        audit.validate_historical(preparation, historical)
        for key, value in [('status','FAIL'), ('generation','expanded-2025'), ('shared_server_modified',True)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit.validate_historical(preparation, {**historical, key:value})
        for key in ('replay_verified','container_removed','anonymous_volumes_removed'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit.validate_historical(preparation, {**historical, 'postgresql':{**historical['postgresql'],key:False}})

    def test_persisted_closure_evidence_matches_current_code(self):
        for name in ('cierre_auditoria_v2.json', 'cierre_subconjunto_v2.json', 'cierre_pg07_controlado.json'):
            with self.subTest(report=name):
                report = json.loads((ROOT / 'sprint1/postgres/evidencias' / name).read_text())
                self.assertEqual(report['status'], 'PASS')
                self.assertTrue(report.get('container_removed', True))
                for path, expected in report['source_hashes'].items():
                    self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)

    def test_latex_structure_inputs_and_citations_without_compiler(self):
        # Static smoke test only: cannot validate pagination, TikZ rendering or PDF.
        base = ROOT / 'docs/avance_1'
        paths = [base / 'SmartCity_Sprint1_Entrega.tex']
        self.assertTrue((base / 'SmartCity_Sprint1_Entrega.pdf').read_bytes().startswith(b'%PDF-'))
        all_text = '\n'.join(p.read_text() for p in paths)
        self.assertNotIn(r'\input{', all_text)
        self.assertNotIn(r'\includegraphics', all_text)
        for path in paths:
            text = path.read_text()
            environments = []
            for kind, name in re.findall(r'\\(begin|end)\{([^}]+)\}', text):
                if kind == 'begin':
                    environments.append(name)
                else:
                    self.assertTrue(environments, str(path))
                    self.assertEqual(environments.pop(), name, str(path))
            self.assertEqual(environments, [], str(path))
            depth = 0
            for brace in re.findall(r'(?<!\\)[{}]', text):
                depth += 1 if brace == '{' else -1
                self.assertGreaterEqual(depth, 0, str(path))
            self.assertEqual(depth, 0, str(path))
        for target in re.findall(r'\\input\{([^}]+)\}', all_text):
            self.assertTrue((base / (target + '.tex')).is_file(), target)
        bibliography = set(re.findall(r'\\bibitem\{([^}]+)\}', all_text))
        for citation in re.findall(r'\\cite\{([^}]+)\}', all_text):
            self.assertTrue(set(citation.split(',')) <= bibliography, citation)
