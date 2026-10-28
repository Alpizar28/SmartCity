-- Solo para una base LOCAL NUEVA, después del DDL común y antes de cargar datos.
-- No migrar en sitio ni sobrescribir bases/generaciones v1.
BEGIN;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM smartcity.sources)
       OR EXISTS (SELECT 1 FROM smartcity.observations) THEN
        RAISE EXCEPTION 'v2 requiere una base nueva, sin catálogos ni lecturas';
    END IF;
END $$;
ALTER TABLE smartcity.observations DROP CONSTRAINT observations_schema_version_check;
ALTER TABLE smartcity.observations DROP CONSTRAINT observations_catalog_version_check;
ALTER TABLE smartcity.observations ADD CHECK (schema_version = 'madrid-draft-v2');
ALTER TABLE smartcity.observations ADD CHECK (catalog_version = 'madrid-draft-v2');
ALTER TABLE smartcity.observations ADD COLUMN integration_sample_count integer;
ALTER TABLE smartcity.observations ADD COLUMN zone_scope text NOT NULL;
ALTER TABLE smartcity.observations ADD CHECK (
    zone_scope IN ('unknown', 'current_inventory_not_historically_verified'));
ALTER TABLE smartcity.observations ADD CHECK (
    (source_id = 'MAD-AIR' AND quality_flag = 'V'
     AND timestamp_status = 'documented_local' AND integration_sample_count IS NULL)
    OR
    (source_id = 'MAD-TRAFFIC' AND quality_flag = 'N'
     AND element_type IN ('URB', 'M30') AND interval_minutes = 15
     AND integration_sample_count IS NOT NULL AND integration_sample_count > 0
     AND timestamp_role = 'publisher_label'
     AND timestamp_status = 'publisher_confirmed_local' AND value >= 0)
);
-- No hay dependencias ni datos: es el esquema recién creado del contenedor propio.
DROP VIEW smartcity.observation_contract;
CREATE VIEW smartcity.observation_contract AS
SELECT o.*, o.measurement_id AS _id, c.sensor_id, c.station_id, c.measurement_type,
       t.unit, t.unit_status, t.candidate_unit, l.zone_id, NULL::text AS time_error
FROM smartcity.observations o
JOIN smartcity.channels c USING (channel_id)
JOIN smartcity.stations s USING (station_id)
JOIN smartcity.measurement_types t USING (measurement_type)
LEFT JOIN smartcity.locations l USING (location_id);
COMMIT;
