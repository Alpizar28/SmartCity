"""Regression guards for the canonical SQL route; no Docker or private data."""
from pathlib import Path
import tempfile
import unittest

from benchmark_real_postgres import read_air_summary
from validate_real_postgres import PROJECT, read_queries


class SQLRouteTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'queries.sql'
            path.write_text(text)
            return read_queries(path)

    def test_canonical_file_has_all_ten_smartcity_queries(self):
        queries = read_queries()
        self.assertEqual(list(queries), [f'PG{i:02d}' for i in range(1, 11)])
        for statement in queries.values():
            self.assertIn('smartcity.', statement)
            self.assertNotIn('sprint1.', statement)
        self.assertIn('smartcity.channel_activity', queries['PG09'])
        self.assertIn('smartcity.channels_at_station', queries['PG10'])

    def test_staging_demo_is_not_accepted_as_canonical_queries(self):
        with self.assertRaisesRegex(ValueError, 'Falta alguna consulta'):
            read_queries(PROJECT / 'sprint1/postgres/staging_queries.sql')

    def test_rejects_missing_duplicate_and_unterminated_queries(self):
        text = (PROJECT / 'sprint1/postgres/queries.sql').read_text()
        with self.assertRaisesRegex(ValueError, 'Falta alguna consulta'):
            self.parse(text.replace('-- PG03:', '-- Example03:'))
        with self.assertRaisesRegex(ValueError, 'duplicada'):
            self.parse(text + '\n-- PG01: repeated\nSELECT 1;\n')
        with self.assertRaisesRegex(ValueError, 'sin punto y coma'):
            self.parse('-- PG01: incomplete\nSELECT 1\n-- PG02: next\nSELECT 2;')

    def test_rejects_numbered_ddl(self):
        with self.assertRaisesRegex(ValueError, 'SELECT/CTE'):
            self.parse('-- PG01: invalid\nCREATE TABLE wrong(id int);')

    def test_benchmark_keeps_documented_air_and_valid_quality(self):
        sql = read_air_summary(PROJECT / 'sprint1/postgres/queries.sql')
        self.assertIn("quality_flag = 'V'", sql)
        self.assertIn("unit_status = 'verified_dictionary'", sql)
        self.assertIn('smartcity.observation_contract', sql)

    def test_pg07_requires_known_link_and_half_open_madrid_window(self):
        sql = read_queries()['PG07']
        self.assertIn('WHERE EXISTS (', sql)
        self.assertIn('AND NOT EXISTS (', sql)
        self.assertIn("observed_at >= TIMESTAMPTZ '2025-01-01 00:00:00+01'", sql)
        self.assertIn("observed_at < TIMESTAMPTZ '2025-02-01 00:00:00+01'", sql)
