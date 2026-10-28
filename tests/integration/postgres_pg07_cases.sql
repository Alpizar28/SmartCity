-- SYNTHETIC TEST ONLY. Appended inside postgres_canonical_fixture.sql transaction.
-- test_sprint1_sql.py runs the EXACT parsed PG07 and then ROLLBACK.
INSERT INTO smartcity.sensors(sensor_id,name,category_id,station_id,
    administrative_status,identity_evidence_reference,data_origin,provenance)
VALUES
 ('sensor-before','Before lower bound','category-air','station-1','active',
  'sql-test-only','synthetic','{"purpose":"fabricated_sql_test_only"}'),
 ('sensor-last','Just before upper bound','category-air','station-1','inactive',
  'sql-test-only','synthetic','{"purpose":"fabricated_sql_test_only"}');
INSERT INTO smartcity.channels(channel_id,station_id,source_id,sensor_id,
    source_key,measurement_type,catalog_basis)
VALUES
 ('channel-active-empty','station-1','MAD-AIR','sensor-active','["active-empty"]','MAD-AIR:8','observations'),
 ('channel-empty-2','station-1','MAD-AIR','sensor-no-readings','["empty-2"]','MAD-AIR:8','observations'),
 ('channel-before','station-1','MAD-AIR','sensor-before','["before"]','MAD-AIR:8','observations'),
 ('channel-last','station-1','MAD-AIR','sensor-last','["last"]','MAD-AIR:8','observations');
-- Administrative status deliberately contradicts reading activity.
UPDATE smartcity.sensors SET administrative_status='active' WHERE sensor_id='sensor-no-readings';
UPDATE smartcity.sensors SET administrative_status='inactive' WHERE sensor_id='sensor-active';
INSERT INTO smartcity.observations
SELECT (jsonb_populate_record(NULL::smartcity.observations,
    to_jsonb(template) || jsonb_build_object(
      'measurement_id','test-' || v.channel_id,'channel_id',v.channel_id,
      'observed_at',v.ts,'original_time',v.ts AT TIME ZONE 'Europe/Madrid',
      'source_key',jsonb_build_array(v.channel_id,v.ts::text)))).*
FROM smartcity.observations template
CROSS JOIN (VALUES
 ('channel-before',TIMESTAMPTZ '2024-12-31 23:59:59.999999+01'),
 ('channel-last',TIMESTAMPTZ '2025-01-31 23:59:59.999999+01')
) v(channel_id,ts)
WHERE template.channel_id='channel-active';
