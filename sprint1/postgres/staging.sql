-- Local proposal, executed only by the disposable integration harness so far.
-- Call with the parameter-bound output of ReadingDTO.postgres_record().
-- Application validation against independently reviewed catalogs is mandatory.
CREATE FUNCTION sprint1.stage_reading(record jsonb) RETURNS text
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE inserted_id bigint; previous_hash text;
BEGIN
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
    ) ON CONFLICT (source_version, channel_id, source_key) DO NOTHING
    RETURNING storage_id INTO inserted_id;
    IF inserted_id IS NOT NULL THEN RETURN 'accepted'; END IF;
    -- Separate statement: under READ COMMITTED, see the winning committed insert.
    SELECT payload_hash INTO STRICT previous_hash FROM sprint1.readings
    WHERE source_version = record->>'source_version'
      AND channel_id = record->>'channel_id' AND source_key = record->'source_key';
    IF previous_hash = record->>'payload_hash' THEN RETURN 'duplicate'; END IF;
    INSERT INTO sprint1.quarantine (reason, document)
    VALUES ('conflicting_payload_same_original_key', record->'document');
    RETURN 'quarantined';
END;
$$;
