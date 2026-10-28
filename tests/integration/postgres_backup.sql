-- psql -v snapshot=true: estado lógico; snapshot=false: verificar restauración.
-- El ejecutor selecciona la base: la verificación nunca se aplica al origen.
\if :snapshot
-- Sin OID, estadísticas ni nombre de base; orden estable para comparar.
SELECT jsonb_build_object(
    'sources', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY source_id), '[]') FROM sprint1.sources t),
    'versions', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY source_version), '[]') FROM sprint1.source_versions t),
    'stations', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY station_id), '[]') FROM sprint1.stations t),
    'channels', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY channel_id), '[]') FROM sprint1.channels t),
    'readings', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY storage_id), '[]') FROM sprint1.readings t),
    'quarantine', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY storage_id), '[]') FROM sprint1.quarantine t),
    'reading_sequence', (SELECT jsonb_build_object('last_value', last_value, 'is_called', is_called)
        FROM sprint1.readings_storage_id_seq),
    'quarantine_sequence', (SELECT jsonb_build_object('last_value', last_value, 'is_called', is_called)
        FROM sprint1.quarantine_storage_id_seq),
    'indexes', (SELECT jsonb_agg(indexdef ORDER BY indexname) FROM pg_indexes WHERE schemaname = 'sprint1'),
    'views', (SELECT jsonb_agg(definition ORDER BY viewname) FROM pg_views WHERE schemaname = 'sprint1'),
    'functions', (SELECT jsonb_agg(pg_get_functiondef(p.oid) ORDER BY p.proname)
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'sprint1'),
    'constraints', (SELECT jsonb_agg(jsonb_build_object('table', c.relname, 'name', k.conname,
        'definition', pg_get_constraintdef(k.oid)) ORDER BY c.relname, k.conname)
        FROM pg_constraint k JOIN pg_class c ON c.oid = k.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'sprint1')
);
\else
DO $verify$
DECLARE row_record record; original bigint; result record;
BEGIN
    IF current_database() <> 'sprint1_restore' THEN
        RAISE EXCEPTION 'Restore checks require the disposable restore target';
    END IF;
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
\endif
