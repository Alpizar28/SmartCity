"""Static proposal guards only: these tests do NOT execute PostgreSQL."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PostgresProposalTests(unittest.TestCase):
    def test_proposal_has_composite_references_and_original_key_uniqueness(self):
        sql = (ROOT / 'sprint1/postgres/schema_proposal.sql').read_text()
        self.assertIn('FOREIGN KEY (source_version, source_id)', sql)
        self.assertIn('FOREIGN KEY (channel_id, source_id)', sql)
        self.assertIn('UNIQUE (source_version, channel_id, source_key)', sql)
        self.assertIn('GENERATED ALWAYS AS IDENTITY', sql)
        self.assertNotIn('UNIQUE (channel_id, observed_at)', sql)

    def test_function_is_snapshot_and_evidence_scoped(self):
        sql = (ROOT / 'sprint1/postgres/queries.sql').read_text()
        self.assertIn('CREATE VIEW sprint1.quality_summary', sql)
        self.assertIn('CREATE FUNCTION sprint1.air_statistics', sql)
        self.assertIn('r.source_version = p_version', sql)
        self.assertIn("r.source_id = 'MAD-AIR'", sql)
        self.assertIn('r.observed_at < p_end', sql)
        self.assertIn('SET search_path = pg_catalog', sql)

    def test_init_directories_remain_empty(self):
        for engine in ('postgres', 'mongodb'):
            self.assertEqual([p.name for p in (ROOT / engine / 'init').iterdir()], ['.gitkeep'])
