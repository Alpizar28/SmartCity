-- Datos fabricados de prueba; la transacción siempre termina en ROLLBACK.
BEGIN;
INSERT INTO smartcity.sensors
SELECT (jsonb_populate_record(NULL::smartcity.sensors,to_jsonb(s)||jsonb_build_object(
 'sensor_id','test-sensor-'||v.label,'name','Dispositivo ficticio de prueba',
 'data_origin','synthetic','identity_evidence_reference','synthetic://3nf-test',
 'provenance','{"purpose":"rollback_sql_test"}'::jsonb))).*
FROM (SELECT s.* FROM smartcity.sensors s JOIN smartcity.stations st USING(station_id)
 WHERE st.source_id='MAD-AIR' AND s.station_id=(SELECT c.station_id FROM smartcity.channels c JOIN smartcity.stations st USING(station_id) WHERE st.source_id='MAD-AIR' ORDER BY c.channel_id LIMIT 1) ORDER BY s.sensor_id LIMIT 1) s
CROSS JOIN (VALUES ('start'),('before'),('outside'),('empty'),('unlinked'),('multi')) v(label);
INSERT INTO smartcity.channels
SELECT (jsonb_populate_record(NULL::smartcity.channels,to_jsonb(c)||jsonb_build_object(
 'channel_id','test-channel-'||v.label,'source_key',jsonb_build_array('rollback-test',v.label)))).*
FROM (SELECT c.* FROM smartcity.channels c JOIN smartcity.stations s USING(station_id)
 WHERE s.source_id='MAD-AIR' ORDER BY c.channel_id LIMIT 1) c
CROSS JOIN (VALUES ('start'),('before'),('outside'),('empty'),('multi'),('multi-empty')) v(label);
INSERT INTO smartcity.channel_sensors SELECT 'test-channel-'||label,'test-sensor-'||label
FROM (VALUES ('start'),('before'),('outside'),('empty'),('multi')) v(label);
INSERT INTO smartcity.channel_sensors VALUES ('test-channel-multi-empty','test-sensor-multi');
INSERT INTO smartcity.observations
SELECT (jsonb_populate_record(NULL::smartcity.observations,to_jsonb(o)||jsonb_build_object(
 'measurement_id','test-measurement-'||v.label,'channel_id','test-channel-'||v.label,
 'observed_at',v.t,'provenance','{"purpose":"rollback_sql_test","real_measurement":false}'::jsonb))).*
FROM (SELECT o.* FROM smartcity.observations o JOIN smartcity.observation_contract v USING(measurement_id)
 WHERE v.source_id='MAD-AIR' ORDER BY o.measurement_id LIMIT 1) o
CROSS JOIN (VALUES
 ('start',TIMESTAMPTZ '2025-01-01 00:00:00+01'),
 ('before',TIMESTAMPTZ '2024-12-31 23:59:59.999999+01'),
 ('outside',TIMESTAMPTZ '2025-02-01 00:00:00+01'),
 ('multi',TIMESTAMPTZ '2025-01-31 23:59:59.999999+01')) v(label,t);
