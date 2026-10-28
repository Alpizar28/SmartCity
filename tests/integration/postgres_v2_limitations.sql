-- Regression evidence of CURRENT DDL limitations, NOT desired acceptance rules.
-- Run only in the owned subset DB. All derived test rows are rolled back.
BEGIN;
INSERT INTO smartcity.observations
SELECT (jsonb_populate_record(NULL::smartcity.observations,
    to_jsonb(o) || jsonb_build_object(
      'measurement_id','test-v2-null-check',
      'observed_at',o.observed_at + INTERVAL '10 years',
      'original_time',o.original_time + INTERVAL '10 years',
      'element_type',NULL,'interval_minutes',NULL,
      'provenance','{"purpose":"fabricated_ddl_limitation_test","real_measurement":false}'::jsonb))).*
FROM smartcity.observations o WHERE source_id='MAD-TRAFFIC' LIMIT 1;
SELECT 'V2_NULL_CHECK_ACCEPTED=' || count(*) FROM smartcity.observations
WHERE measurement_id='test-v2-null-check' AND element_type IS NULL AND interval_minutes IS NULL;
-- The immutability trigger does not fire for DELETE. Delete ONLY our test row.
WITH deleted AS (DELETE FROM smartcity.observations WHERE measurement_id='test-v2-null-check' RETURNING 1)
SELECT 'V2_DELETE_ALLOWED=' || count(*) FROM deleted;
INSERT INTO smartcity.observations
SELECT (jsonb_populate_record(NULL::smartcity.observations,
    to_jsonb(o) || jsonb_build_object(
      'measurement_id','test-v2-reference-shape',
      'observed_at',o.observed_at + INTERVAL '10 years',
      'original_time',o.original_time + INTERVAL '10 years',
      'raw_reference','["sha256"]'::jsonb,
      'provenance','{"purpose":"fabricated_ddl_limitation_test","real_measurement":false}'::jsonb))).*
FROM smartcity.observations o WHERE source_id='MAD-TRAFFIC' LIMIT 1;
SELECT 'V2_REFERENCE_ARRAY_ACCEPTED=' || count(*) FROM smartcity.observations
WHERE measurement_id='test-v2-reference-shape' AND jsonb_typeof(raw_reference)='array';
ROLLBACK;
