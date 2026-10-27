-- SYNTHETIC TEST FIXTURE ONLY. Never import into shared or observed datasets.
-- This transaction belongs exclusively to test_sprint1_sql.py and is rolled back.
-- Observation rows use the schema-required origin label, but their provenance
-- explicitly identifies a fabricated SQL test, not a public-source measurement.
BEGIN;
INSERT INTO smartcity.sources VALUES ('MAD-AIR', 'SQL test source', 'Test only');
INSERT INTO smartcity.source_versions(source_version, source_id, original_path)
VALUES (repeat('a', 64), 'MAD-AIR', 'sql-test-only');
INSERT INTO smartcity.zones VALUES
    ('zone-1', 'Test zone 1', 'district'), ('zone-2', 'Test zone 2', 'district');
INSERT INTO smartcity.locations(location_id, zone_id, name, coordinate_crs) VALUES
    ('location-1', 'zone-1', 'Test location 1', 'unverified'),
    ('location-2', 'zone-2', 'Test location 2', 'unverified');
INSERT INTO smartcity.stations(station_id, source_id, source_key, name,
    location_id, inventory_present) VALUES
    ('station-1', 'MAD-AIR', '1', 'Test station 1', 'location-1', false),
    ('station-2', 'MAD-AIR', '2', 'Test station 2', 'location-2', false);
INSERT INTO smartcity.sensor_categories VALUES
    ('category-air', 'Test air'), ('category-other', 'Test other');
INSERT INTO smartcity.measurement_types(measurement_type, source_id, code,
    category_id, unit, unit_status) VALUES
    ('MAD-AIR:8', 'MAD-AIR', '8', 'category-air', 'ug/m3', 'verified_dictionary');
INSERT INTO smartcity.organizations(organization_id, name, data_origin, provenance) VALUES
    ('org-assigned', 'Test organization', 'synthetic', '{"purpose":"sql_test"}'),
    ('org-empty', 'Test empty organization', 'synthetic', '{"purpose":"sql_test"}');
INSERT INTO smartcity.sensors(sensor_id, name, category_id, station_id,
    installation_date, administrative_status, organization_id,
    identity_evidence_reference, data_origin, provenance) VALUES
    ('sensor-active', 'Test active', 'category-air', 'station-1', '2024-01-01',
     'active', 'org-assigned', 'sql-test-only', 'synthetic', '{"purpose":"sql_test"}'),
    ('sensor-no-readings', 'Test no readings', 'category-air', 'station-1', '2025-01-01',
     'inactive', 'org-assigned', 'sql-test-only', 'synthetic', '{"purpose":"sql_test"}'),
    ('sensor-outside', 'Test outside window', 'category-other', 'station-2', '2024-02-01',
     'active', 'org-assigned', 'sql-test-only', 'synthetic', '{"purpose":"sql_test"}'),
    ('sensor-unlinked', 'Test unknown relationship', 'category-other', 'station-2', NULL,
     NULL, NULL, 'sql-test-only', 'synthetic', '{"purpose":"sql_test"}');
INSERT INTO smartcity.channels(channel_id, station_id, source_id, sensor_id,
    source_key, measurement_type, catalog_basis) VALUES
    ('channel-active', 'station-1', 'MAD-AIR', 'sensor-active', '["1","active"]', 'MAD-AIR:8', 'observations'),
    ('channel-empty', 'station-1', 'MAD-AIR', 'sensor-no-readings', '["1","empty"]', 'MAD-AIR:8', 'observations'),
    ('channel-outside', 'station-2', 'MAD-AIR', 'sensor-outside', '["2","outside"]', 'MAD-AIR:8', 'observations'),
    ('channel-unassigned', 'station-2', 'MAD-AIR', NULL, '["2","unassigned"]', 'MAD-AIR:8', 'observations');
INSERT INTO smartcity.observations(measurement_id, channel_id, source_id,
    observed_at, original_time, original_timezone, timestamp_role, timestamp_status,
    value, quality_flag, source_version, data_origin, payload_hash,
    transformation_method, transformation_version, catalog_version, raw_reference,
    source_key, provenance, schema_version)
SELECT 'test-measurement-' || row_number() OVER (), channel_id, 'MAD-AIR',
    observed_at, observed_at AT TIME ZONE 'Europe/Madrid', 'Europe/Madrid',
    'hour_end', 'documented_local', 10, 'V', repeat('a', 64), 'observed',
    'payload:' || repeat('b', 64), 'sql-test-only', 'sql-test-only', 'madrid-draft-v1',
    jsonb_build_object('path', 'sql-test-only', 'sha256', repeat('a', 64)),
    jsonb_build_array(channel_id, observed_at::text),
    '{"purpose":"fabricated_sql_test_only","real_measurement":false}'::jsonb,
    'madrid-draft-v1'
FROM (VALUES
    -- Exactly at the inclusive Madrid lower bound: this sensor IS active in January.
    ('channel-active', TIMESTAMPTZ '2025-01-01 00:00:00+01'),
    -- Exactly at the exclusive upper bound: no January reading for this sensor.
    ('channel-outside', TIMESTAMPTZ '2025-02-01 00:00:00+01'),
    -- A reading without a sensor link must not be attributed to sensor-unlinked.
    ('channel-unassigned', TIMESTAMPTZ '2025-01-01 01:00:00+01')
) AS fixture(channel_id, observed_at);
