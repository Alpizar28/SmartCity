-- Runs only against the new restore target, never the source database.
DO $verify$
DECLARE row_record record; original bigint; result record;
BEGIN
    IF (SELECT count(*) FROM sprint1.readings) <> 3 OR
       (SELECT count(*) FROM sprint1.quarantine) <> 1 THEN
        RAISE EXCEPTION 'Restore counts differ';
    END IF;
    IF (SELECT sum(reading_count) FROM sprint1.quality_summary) <> 3 THEN
        RAISE EXCEPTION 'Restored view failed';
    END IF;
    SELECT * INTO STRICT row_record FROM sprint1.readings WHERE source_id = 'MAD-AIR';
    SELECT * INTO STRICT result FROM sprint1.air_statistics(row_record.channel_id,
        row_record.source_version, '2025-01-01Z', '2025-02-01Z');
    IF result.n <> 1 OR result.average <> row_record.value THEN
        RAISE EXCEPTION 'Restored function failed';
    END IF;
    -- The returned record contains the exact staging projection, plus the local
    -- storage ID ignored by stage_reading. Replay must preserve the accepted row.
    IF sprint1.stage_reading(to_jsonb(row_record)) <> 'duplicate' THEN
        RAISE EXCEPTION 'Restored reconciliation failed';
    END IF;
    SELECT max(storage_id) INTO original FROM sprint1.quarantine;
    INSERT INTO sprint1.quarantine(reason, document) VALUES ('restore_sequence_probe', '{}')
    RETURNING storage_id INTO original;
    IF original <= 1 THEN RAISE EXCEPTION 'Identity sequence was not restored'; END IF;
END;
$verify$;
SELECT 'POSTGRES_RESTORE_PASS';
