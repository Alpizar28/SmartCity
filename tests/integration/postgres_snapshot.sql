-- Logical snapshot excludes physical OIDs, statistics and database name.
-- It includes every persistent application table plus sequence positions,
-- indexes, view/function definitions and constraints, with deterministic order.
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
