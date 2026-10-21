-- REVIEW ONLY. Not an init script or migration. No data or remote connections.
-- Apply only in an explicitly authorized disposable PostgreSQL 16 database.
BEGIN;
CREATE SCHEMA sprint1;

CREATE TABLE sprint1.sources (
    source_id text PRIMARY KEY CHECK (source_id IN ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC')),
    name text NOT NULL,
    publisher text NOT NULL
);
CREATE TABLE sprint1.source_versions (
    source_version text PRIMARY KEY CHECK (source_version ~ '^[0-9a-f]{64}$'),
    source_id text NOT NULL REFERENCES sprint1.sources,
    original_path text NOT NULL,
    acquired_at timestamptz,
    UNIQUE (source_version, source_id)
);
CREATE TABLE sprint1.stations (
    station_id text PRIMARY KEY CHECK (station_id ~ '^station:[0-9a-f]{64}$'),
    source_id text NOT NULL REFERENCES sprint1.sources,
    source_key text NOT NULL,
    name text,
    inventory_present boolean,
    UNIQUE (source_id, source_key),
    UNIQUE (station_id, source_id)
);
CREATE TABLE sprint1.channels (
    channel_id text PRIMARY KEY CHECK (channel_id ~ '^channel:[0-9a-f]{64}$'),
    station_id text NOT NULL,
    source_id text NOT NULL,
    measurement_type text NOT NULL,
    source_key jsonb NOT NULL CHECK (jsonb_typeof(source_key) = 'array'),
    catalog_basis text NOT NULL CHECK (catalog_basis = 'observations'),
    FOREIGN KEY (station_id, source_id) REFERENCES sprint1.stations (station_id, source_id),
    UNIQUE (channel_id, source_id)
);
-- Internal GENERATED ID is a staging locator, never measurement_id.
-- Optional/unresolved geography and metadata stay in the validated document.
CREATE TABLE sprint1.readings (
    storage_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id text NOT NULL,
    source_version text NOT NULL,
    channel_id text NOT NULL,
    source_key jsonb NOT NULL CHECK (jsonb_typeof(source_key) = 'array'),
    original_time timestamp NOT NULL,
    original_timezone text NOT NULL CHECK (original_timezone = 'Europe/Madrid'),
    timestamp_role text NOT NULL,
    timestamp_status text NOT NULL,
    observed_at timestamptz,
    value double precision NOT NULL CHECK (value > '-Infinity'::float8 AND value < 'Infinity'::float8),
    unit text,
    unit_status text NOT NULL,
    quality_flag text NOT NULL,
    payload_hash text NOT NULL CHECK (payload_hash ~ '^payload:[0-9a-f]{64}$'),
    raw_reference jsonb NOT NULL,
    schema_version text NOT NULL CHECK (schema_version = 'madrid-draft-v1-frozen'),
    document jsonb NOT NULL CHECK (jsonb_typeof(document) = 'object'),
    CHECK (document @> jsonb_build_object(
        'source_id', source_id, 'source_version', source_version,
        'channel_id', channel_id, 'source_key', source_key,
        'original_timezone', original_timezone, 'timestamp_role', timestamp_role,
        'timestamp_status', timestamp_status, 'value', value, 'unit_status', unit_status,
        'quality_flag', quality_flag, 'payload_hash', payload_hash,
        'raw_reference', raw_reference, 'schema_version', schema_version)),
    CHECK (document->>'unit' IS NOT DISTINCT FROM unit),
    CHECK (document ? 'original_time' AND
           (document->>'original_time')::timestamp IS NOT DISTINCT FROM original_time),
    CHECK ((document->'observed_at'->>'$date')::timestamptz IS NOT DISTINCT FROM observed_at),
    CHECK (NOT (document ?| ARRAY['_id', 'measurement_id']) AND
           document->>'sensor_id' IS NULL AND document->>'organization_id' IS NULL AND
           document->>'user_id' IS NULL AND document->>'installation_date' IS NULL AND
           document->>'administrative_status' IS NULL),
    FOREIGN KEY (source_version, source_id) REFERENCES sprint1.source_versions (source_version, source_id),
    FOREIGN KEY (channel_id, source_id) REFERENCES sprint1.channels (channel_id, source_id),
    UNIQUE (source_version, channel_id, source_key),
    CHECK (original_time >= timestamp '2025-01-01' AND original_time <= timestamp '2025-02-01'),
    CHECK (jsonb_typeof(raw_reference) = 'object' AND raw_reference ? 'sha256'
           AND raw_reference->>'sha256' = source_version),
    CHECK (CASE source_id
        WHEN 'MAD-AIR' THEN timestamp_role = 'hour_end' AND timestamp_status = 'documented_local'
             AND unit IS NOT NULL AND unit_status = 'verified_dictionary'
        WHEN 'MAD-METEO' THEN timestamp_role = 'hour_end'
             AND timestamp_status = 'assumed_same_H_format_pending_dictionary'
             AND unit IS NULL AND unit_status = 'pending_dictionary'
        WHEN 'MAD-TRAFFIC' THEN timestamp_role = 'publisher_label'
             AND timestamp_status = 'assumed_local_label_pending_provider_confirmation'
             AND unit IS NOT NULL AND unit = 'veh/h' AND unit_status = 'documented_phase1_dictionary'
        ELSE false END)
);
CREATE INDEX readings_channel_quality ON sprint1.readings (channel_id, quality_flag);
CREATE INDEX readings_source_version ON sprint1.readings (source_id, source_version);
CREATE INDEX readings_air_time ON sprint1.readings (observed_at)
    WHERE source_id = 'MAD-AIR' AND timestamp_status = 'documented_local';
CREATE INDEX channels_station ON sprint1.channels (station_id, source_id);
-- Application must compare payload_hash before insert. Never use ON CONFLICT
-- DO UPDATE for readings. Contradictions go to quarantine for manual review.
CREATE TABLE sprint1.quarantine (
    storage_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reason text NOT NULL,
    document jsonb NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now()
);
COMMIT;
