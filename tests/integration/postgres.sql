-- Runs only inside the disposable integration container. fixture(record) was
-- populated with ReadingDTO.postgres_record(), not synthetic sensor records.
INSERT INTO sprint1.sources
SELECT DISTINCT record->>'source_id', record->>'source_id', 'Ayuntamiento de Madrid'
FROM fixture;
INSERT INTO sprint1.source_versions (source_version, source_id, original_path)
SELECT DISTINCT record->>'source_version', record->>'source_id', record->'raw_reference'->>'path'
FROM fixture;
INSERT INTO sprint1.stations (station_id, source_id, source_key, inventory_present)
SELECT DISTINCT record->'document'->>'station_id', record->>'source_id',
       record->'source_key'->>0, NULL::boolean
FROM fixture;
INSERT INTO sprint1.channels (channel_id, station_id, source_id, measurement_type, source_key, catalog_basis)
SELECT record->>'channel_id', record->'document'->>'station_id', record->>'source_id',
       record->'document'->>'measurement_type',
       CASE WHEN record->>'source_id' = 'MAD-TRAFFIC'
            THEN jsonb_build_array(record->'source_key'->0, record->'source_key'->2)
            ELSE (record->'source_key') - 4 - 3 END,
       'observations'
FROM fixture;

CREATE FUNCTION pg_temp.insert_record(record jsonb) RETURNS void
LANGUAGE sql AS $$
    INSERT INTO sprint1.readings (
        source_id, source_version, channel_id, source_key, original_time,
        original_timezone, timestamp_role, timestamp_status, observed_at, value,
        unit, unit_status, quality_flag, payload_hash, raw_reference, schema_version, document
    ) VALUES (
        record->>'source_id', record->>'source_version', record->>'channel_id', record->'source_key',
        (record->>'original_time')::timestamp, record->>'original_timezone', record->>'timestamp_role',
        record->>'timestamp_status', (record->>'observed_at')::timestamptz,
        (record->>'value')::double precision, record->>'unit', record->>'unit_status',
        record->>'quality_flag', record->>'payload_hash', record->'raw_reference',
        record->>'schema_version', record->'document'
    );
$$;
DO $load$
DECLARE item jsonb;
BEGIN
    FOR item IN SELECT record FROM fixture LOOP
        IF sprint1.stage_reading(item) <> 'accepted' THEN RAISE EXCEPTION 'First insert must be accepted'; END IF;
        IF sprint1.stage_reading(item) <> 'duplicate' THEN RAISE EXCEPTION 'Replay must be idempotent'; END IF;
    END LOOP;
END;
$load$;

CREATE FUNCTION pg_temp.expect_rejection(candidate jsonb, expected_state text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE actual_state text;
BEGIN
    BEGIN
        PERFORM pg_temp.insert_record(candidate);
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE;
        IF actual_state = expected_state THEN RETURN; END IF;
        RAISE EXCEPTION 'Expected SQLSTATE %, got %', expected_state, actual_state;
    END;
    RAISE EXCEPTION 'Invalid record was accepted';
END;
$$;

DO $tests$
DECLARE air jsonb; meteo jsonb; traffic jsonb; changed jsonb; n bigint; result record;
BEGIN
    SELECT record INTO STRICT air FROM fixture WHERE record->>'source_id' = 'MAD-AIR';
    SELECT record INTO STRICT meteo FROM fixture WHERE record->>'source_id' = 'MAD-METEO';
    SELECT record INTO STRICT traffic FROM fixture WHERE record->>'source_id' = 'MAD-TRAFFIC';
    SELECT record INTO STRICT changed FROM conflict_fixture;
    IF sprint1.stage_reading(changed) <> 'quarantined' THEN RAISE EXCEPTION 'Conflict must be quarantined'; END IF;
    SELECT count(*) INTO n FROM sprint1.quarantine;
    IF n <> 1 THEN RAISE EXCEPTION 'Expected one quarantine record'; END IF;
    SELECT count(*) INTO n FROM sprint1.readings;
    IF n <> 3 THEN RAISE EXCEPTION 'Expected 3 readings, got %', n; END IF;
    -- PG01/02/05/07 alternatives against populated staging, not only syntax.
    SELECT count(*) INTO n FROM (
        SELECT source_id, measurement_type, count(*) FROM sprint1.channels
        GROUP BY source_id, measurement_type
    ) AS grouped;
    IF n <> 3 THEN RAISE EXCEPTION 'Expected three source-variable groups'; END IF;
    SELECT count(*) INTO n FROM sprint1.stations AS s
    INNER JOIN sprint1.channels AS c USING (station_id, source_id);
    IF n <> 3 THEN RAISE EXCEPTION 'Expected three site-channel joins'; END IF;
    SELECT count(*) INTO n FROM sprint1.channels AS c WHERE NOT EXISTS (
        SELECT 1 FROM sprint1.readings AS r WHERE r.channel_id = c.channel_id);
    IF n <> 0 THEN RAISE EXCEPTION 'Every test channel has one reading'; END IF;
    SELECT max(rank) INTO n FROM (
        SELECT dense_rank() OVER (ORDER BY count(*) DESC) AS rank
        FROM sprint1.channels GROUP BY station_id HAVING count(*) > 0
    ) AS ranked;
    IF n <> 1 THEN RAISE EXCEPTION 'One-channel sites must tie'; END IF;

    PERFORM pg_temp.expect_rejection(air, '23505'); -- duplicate original key
    -- Change column and document together so the FK, not projection check, fails.
    changed := jsonb_set(air, '{channel_id}', to_jsonb(traffic->>'channel_id'));
    changed := jsonb_set(changed, '{document,channel_id}', to_jsonb(traffic->>'channel_id'));
    PERFORM pg_temp.expect_rejection(changed, '23503'); -- cross-source channel
    changed := jsonb_set(air, '{source_version}', to_jsonb(meteo->>'source_version'));
    changed := jsonb_set(changed, '{document,source_version}', to_jsonb(meteo->>'source_version'));
    changed := jsonb_set(changed, '{raw_reference,sha256}', to_jsonb(meteo->>'source_version'));
    changed := jsonb_set(changed, '{document,raw_reference,sha256}', to_jsonb(meteo->>'source_version'));
    PERFORM pg_temp.expect_rejection(changed, '23503'); -- cross-source version
    PERFORM pg_temp.expect_rejection(jsonb_set(air, '{value}', 'null'), '23502');
    PERFORM pg_temp.expect_rejection(jsonb_set(air, '{value}', '"NaN"'), '23514');
    PERFORM pg_temp.expect_rejection(jsonb_set(air, '{value}', '999'), '23514'); -- inconsistent projection
    changed := jsonb_set(meteo, '{unit}', '"m/s"');
    changed := jsonb_set(changed, '{document,unit}', '"m/s"');
    PERFORM pg_temp.expect_rejection(changed, '23514'); -- promoted meteo unit
    PERFORM pg_temp.expect_rejection(jsonb_set(air, '{document,sensor_id}', '"invented"'), '23514');

    SELECT * INTO STRICT result FROM sprint1.air_statistics(
        air->>'channel_id', air->>'source_version', '2025-01-01Z', '2025-02-01Z');
    IF result.n <> 1 OR result.minimum <> (air->>'value')::float8
       OR result.maximum <> result.minimum OR result.average <> result.minimum THEN
        RAISE EXCEPTION 'Unexpected air statistics';
    END IF;
    SELECT count(*) INTO n FROM sprint1.air_statistics(
        air->>'channel_id', air->>'source_version', '2024-12-31Z', '2025-01-01Z');
    IF n <> 0 THEN RAISE EXCEPTION 'End date must be exclusive'; END IF;
    SELECT count(*) INTO n FROM sprint1.air_statistics(
        meteo->>'channel_id', meteo->>'source_version', '2025-01-01Z', '2025-02-01Z');
    IF n <> 0 THEN RAISE EXCEPTION 'Meteo must not enter air statistics'; END IF;
    SELECT sum(reading_count) INTO n FROM sprint1.quality_summary;
    IF n <> 3 THEN RAISE EXCEPTION 'Quality counts changed'; END IF;
    SELECT count(*) INTO n FROM sprint1.readings;
    IF n <> 3 THEN RAISE EXCEPTION 'Rejected records must leave no rows'; END IF;
END;
$tests$;
SELECT 'POSTGRES_INTEGRATION_PASS' AS result, version();
EXPLAIN (FORMAT JSON) SELECT * FROM sprint1.readings
WHERE source_id = 'MAD-AIR' AND timestamp_status = 'documented_local'
AND observed_at >= '2025-01-01Z' AND observed_at < '2025-02-01Z';
