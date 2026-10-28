-- Modelo v2 normalizado. Se aplica exclusivamente en una base local NUEVA.
-- El DTO madrid-draft-v2 se reconstruye mediante observation_contract.
BEGIN;
CREATE SCHEMA smartcity;
SET LOCAL search_path=smartcity,pg_temp;

CREATE TABLE sources (
 source_id text PRIMARY KEY CHECK(source_id IN ('MAD-AIR','MAD-METEO','MAD-TRAFFIC')),
 name text NOT NULL, publisher text NOT NULL
);
-- Política invariable de esta versión contractual: se calcula, no se almacena
-- repetida por medición. Meteorología continúa fuera del conjunto aceptado.
CREATE VIEW accepted_source_policy AS SELECT source_id,
 CASE source_id WHEN 'MAD-AIR' THEN 'V' WHEN 'MAD-TRAFFIC' THEN 'N' END AS accepted_quality,
 CASE source_id WHEN 'MAD-AIR' THEN 'documented_local' WHEN 'MAD-TRAFFIC' THEN 'publisher_confirmed_local' END AS accepted_timestamp_status,
 CASE source_id WHEN 'MAD-AIR' THEN 'hour_end' WHEN 'MAD-TRAFFIC' THEN 'publisher_label' END AS accepted_timestamp_role,
 CASE WHEN source_id='MAD-TRAFFIC' THEN 15 END AS accepted_interval_minutes
 FROM sources;
CREATE TABLE source_versions (
 source_version text PRIMARY KEY CHECK(source_version ~ '^[0-9a-f]{64}$'),
 source_id text NOT NULL REFERENCES sources, original_path text NOT NULL,
 acquired_at timestamptz
);
-- Un distrito es una zona administrativa. Una zona local puede pertenecer a él.
CREATE TABLE zones (
 zone_id text PRIMARY KEY, name text NOT NULL,
 level text NOT NULL CHECK(level IN ('city','district','local')),
 parent_zone_id text REFERENCES zones,
 CHECK(parent_zone_id IS NULL OR level='local'),
 CHECK(parent_zone_id IS NULL OR parent_zone_id<>zone_id)
);
CREATE TABLE locations (
 location_id text PRIMARY KEY, zone_id text REFERENCES zones, name text,
 latitude double precision CHECK(latitude BETWEEN -90 AND 90),
 longitude double precision CHECK(longitude BETWEEN -180 AND 180),
 coordinate_crs text NOT NULL, historical_location_verified boolean NOT NULL DEFAULT false,
 inventory_version text REFERENCES source_versions,
 CHECK((latitude IS NULL)=(longitude IS NULL))
);
CREATE TABLE stations (
 station_id text PRIMARY KEY, source_id text NOT NULL REFERENCES sources,
 source_key text NOT NULL, name text, location_id text REFERENCES locations,
 inventory_present boolean NOT NULL, UNIQUE(source_id,source_key)
);
CREATE TABLE sensor_categories (category_id text PRIMARY KEY, name text NOT NULL);
-- Las magnitudes medidas ya no pertenecen a categorías de dispositivos.
CREATE TABLE measurement_types (
 measurement_type text PRIMARY KEY, source_id text NOT NULL REFERENCES sources,
 code text NOT NULL, unit text, candidate_unit text, unit_status text NOT NULL,
 CHECK((unit IS NULL)=(unit_status='pending_dictionary')), UNIQUE(source_id,code)
);
CREATE TABLE organizations (
 organization_id text PRIMARY KEY, name text NOT NULL, responsible_person_or_role text,
 evidence_reference text, data_origin text NOT NULL CHECK(data_origin IN ('observed','synthetic')),
 provenance jsonb NOT NULL
);
CREATE TABLE users (
 user_id text PRIMARY KEY, name text NOT NULL, email text NOT NULL UNIQUE,
 consent_reference text NOT NULL, demo_only boolean NOT NULL DEFAULT false,
 data_origin text NOT NULL CHECK(data_origin IN ('observed','synthetic'))
);
CREATE TABLE sensor_types (
 sensor_type text PRIMARY KEY, name text NOT NULL,
 category_id text NOT NULL REFERENCES sensor_categories,
 data_origin text NOT NULL CHECK(data_origin IN ('observed','synthetic')),
 evidence_reference text NOT NULL
);
CREATE TABLE sensors (
 sensor_id text PRIMARY KEY, name text NOT NULL,
 sensor_type text REFERENCES sensor_types, station_id text NOT NULL REFERENCES stations,
 installation_date date, administrative_status text CHECK(administrative_status IN ('active','inactive')),
 status_effective_at timestamptz, organization_id text REFERENCES organizations,
 identity_evidence_reference text NOT NULL,
 data_origin text NOT NULL CHECK(data_origin IN ('observed','synthetic')), provenance jsonb NOT NULL
);
CREATE TABLE channels (
 channel_id text PRIMARY KEY, station_id text NOT NULL REFERENCES stations,
 source_key jsonb NOT NULL, measurement_type text NOT NULL REFERENCES measurement_types,
 catalog_basis text NOT NULL CHECK(catalog_basis IN ('observations','independent_inventory')),
 UNIQUE(station_id,source_key)
);
-- No repetir station_id aquí: sensor_id -> station_id se conserva en sensors.
CREATE TABLE channel_sensors (
 channel_id text PRIMARY KEY REFERENCES channels, sensor_id text NOT NULL REFERENCES sensors
);
CREATE TABLE observations (
 measurement_id text PRIMARY KEY, channel_id text NOT NULL REFERENCES channels,
 observed_at timestamptz NOT NULL,
 value double precision NOT NULL CHECK(value>'-Infinity'::float8 AND value<'Infinity'::float8),
 source_version text NOT NULL REFERENCES source_versions,
 payload_hash text NOT NULL CHECK(payload_hash ~ '^payload:[0-9a-f]{64}$'),
 transformation_method text NOT NULL CHECK(length(transformation_method)>0),
 transformation_version text NOT NULL CHECK(length(transformation_version)>0),
 raw_locator jsonb NOT NULL CHECK(jsonb_typeof(raw_locator)='object' AND NOT raw_locator ? 'sha256'),
 source_key jsonb NOT NULL, provenance jsonb NOT NULL,
 element_type text CHECK(element_type IN ('URB','M30')),
 measurements jsonb, integration_sample_count integer, zone_scope text NOT NULL
 CHECK(zone_scope IN ('unknown','current_inventory_not_historically_verified')),
 UNIQUE(channel_id,observed_at)
);

CREATE FUNCTION check_zone_parent() RETURNS trigger LANGUAGE plpgsql
 SET search_path=smartcity,pg_temp AS $$
BEGIN
 IF NEW.parent_zone_id IS NOT NULL THEN
  PERFORM 1 FROM zones WHERE zone_id=NEW.parent_zone_id AND level='district' FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'a local zone must reference a district'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER zone_parent BEFORE INSERT OR UPDATE ON zones
 FOR EACH ROW EXECUTE FUNCTION check_zone_parent();

-- La identidad y las políticas de un catálogo publicado son inmutables.
-- Incluye cambios de padres: una FK simple no comprueba igualdad entre fuentes.
CREATE FUNCTION immutable_catalog_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW IS DISTINCT FROM OLD THEN RAISE EXCEPTION 'published catalog identity is immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER source_identity BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION immutable_catalog_identity();
CREATE TRIGGER version_identity BEFORE UPDATE OF source_version,source_id ON source_versions FOR EACH ROW EXECUTE FUNCTION immutable_catalog_identity();
CREATE TRIGGER station_identity BEFORE UPDATE OF station_id,source_id ON stations FOR EACH ROW EXECUTE FUNCTION immutable_catalog_identity();
CREATE TRIGGER type_identity BEFORE UPDATE OF measurement_type,source_id ON measurement_types FOR EACH ROW EXECUTE FUNCTION immutable_catalog_identity();
CREATE TRIGGER sensor_identity BEFORE UPDATE OF sensor_id,station_id ON sensors FOR EACH ROW EXECUTE FUNCTION immutable_catalog_identity();
CREATE TRIGGER zone_identity BEFORE UPDATE OF zone_id,level,parent_zone_id ON zones FOR EACH ROW EXECUTE FUNCTION immutable_catalog_identity();

CREATE FUNCTION check_channel() RETURNS trigger LANGUAGE plpgsql
 SET search_path=smartcity,pg_temp AS $$
DECLARE station_source text; type_source text;
BEGIN
 SELECT source_id INTO STRICT station_source FROM stations WHERE station_id=NEW.station_id FOR SHARE;
 SELECT source_id INTO STRICT type_source FROM measurement_types WHERE measurement_type=NEW.measurement_type FOR SHARE;
 IF station_source<>type_source THEN RAISE EXCEPTION 'channel source mismatch'; END IF;
 IF TG_OP='UPDATE' AND NEW IS DISTINCT FROM OLD THEN
  RAISE EXCEPTION 'published channel is immutable';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER channel_integrity BEFORE INSERT OR UPDATE ON channels FOR EACH ROW EXECUTE FUNCTION check_channel();
CREATE FUNCTION check_channel_sensor() RETURNS trigger LANGUAGE plpgsql
 SET search_path=smartcity,pg_temp AS $$
DECLARE channel_station text; sensor_station text;
BEGIN
 SELECT station_id INTO STRICT channel_station FROM channels WHERE channel_id=NEW.channel_id FOR SHARE;
 SELECT station_id INTO STRICT sensor_station FROM sensors WHERE sensor_id=NEW.sensor_id FOR SHARE;
 IF channel_station<>sensor_station THEN RAISE EXCEPTION 'sensor station mismatch'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER channel_sensor_integrity BEFORE INSERT OR UPDATE ON channel_sensors
 FOR EACH ROW EXECUTE FUNCTION check_channel_sensor();

CREATE FUNCTION check_observation() RETURNS trigger LANGUAGE plpgsql
 SET search_path=smartcity,pg_temp AS $$
DECLARE channel_source text; version_source text; local_time timestamp;
BEGIN
 IF TG_OP='UPDATE' AND NEW IS DISTINCT FROM OLD THEN
  RAISE EXCEPTION 'immutable observation / payload conflict';
 END IF;
 SELECT s.source_id INTO STRICT channel_source FROM channels c
 JOIN stations s USING(station_id) WHERE c.channel_id=NEW.channel_id FOR SHARE OF c,s;
 SELECT source_id INTO STRICT version_source FROM source_versions
 WHERE source_version=NEW.source_version FOR SHARE;
 IF channel_source<>version_source OR channel_source NOT IN ('MAD-AIR','MAD-TRAFFIC') THEN
  RAISE EXCEPTION 'observation source mismatch or unsupported source';
 END IF;
 local_time := NEW.observed_at AT TIME ZONE 'Europe/Madrid';
 IF (NEW.observed_at + interval '1 hour') AT TIME ZONE 'Europe/Madrid'=local_time
 OR (NEW.observed_at - interval '1 hour') AT TIME ZONE 'Europe/Madrid'=local_time THEN
  RAISE EXCEPTION 'ambiguous Madrid wall clock';
 END IF;
 IF channel_source='MAD-TRAFFIC' THEN
  IF (NEW.element_type IN ('URB','M30') AND NEW.integration_sample_count>0
       AND NEW.value>=0) IS NOT TRUE THEN RAISE EXCEPTION 'invalid traffic v2'; END IF;
 ELSIF NEW.integration_sample_count IS NOT NULL THEN
  RAISE EXCEPTION 'air cannot contain integration sample count';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER observation_integrity BEFORE INSERT OR UPDATE ON observations
 FOR EACH ROW EXECUTE FUNCTION check_observation();
CREATE INDEX sensor_station ON sensors(station_id);
CREATE INDEX sensor_type ON sensors(sensor_type);
CREATE INDEX sensor_org ON sensors(organization_id);
CREATE INDEX channel_station ON channels(station_id);
CREATE INDEX channel_sensor ON channel_sensors(sensor_id);
CREATE INDEX observations_time ON observations(observed_at);

CREATE VIEW channel_contract AS SELECT c.*,s.source_id,cs.sensor_id
 FROM channels c JOIN stations s USING(station_id) LEFT JOIN channel_sensors cs USING(channel_id);
CREATE VIEW location_geography AS
 SELECT l.*,z.name AS zone_name,z.level AS zone_level,
 CASE WHEN z.level='district' THEN z.zone_id ELSE d.zone_id END AS district_id,
 CASE WHEN z.level='district' THEN z.name ELSE d.name END AS district_name
 FROM locations l LEFT JOIN zones z USING(zone_id)
 LEFT JOIN zones d ON z.parent_zone_id=d.zone_id;
CREATE VIEW observation_contract AS
 SELECT o.measurement_id,o.channel_id,s.source_id,o.observed_at,
 o.observed_at AT TIME ZONE 'Europe/Madrid' AS original_time,
 'Europe/Madrid'::text AS original_timezone,
 src.accepted_timestamp_role AS timestamp_role,src.accepted_timestamp_status AS timestamp_status,
 o.value,src.accepted_quality AS quality_flag,o.source_version,'observed'::text AS data_origin,
 o.payload_hash,o.transformation_method,o.transformation_version,
 'madrid-draft-v2'::text AS catalog_version,
 o.raw_locator || jsonb_build_object('sha256',o.source_version) AS raw_reference,
 src.accepted_interval_minutes AS interval_minutes,o.source_key,o.provenance,o.element_type,
 o.measurements,'madrid-draft-v2'::text AS schema_version,
 o.integration_sample_count,o.zone_scope,o.measurement_id AS _id,cs.sensor_id,c.station_id,
 c.measurement_type,t.unit,t.unit_status,t.candidate_unit,l.zone_id,NULL::text AS time_error
 FROM observations o JOIN channels c USING(channel_id) JOIN stations s USING(station_id)
 JOIN accepted_source_policy src ON src.source_id=s.source_id JOIN measurement_types t USING(measurement_type)
 LEFT JOIN channel_sensors cs USING(channel_id) LEFT JOIN locations l USING(location_id);
CREATE VIEW channel_activity AS SELECT channel_id,min(observed_at) AS first_observed_at,
 max(observed_at) AS last_observed_at,count(*) AS readings FROM observations GROUP BY channel_id;
CREATE FUNCTION channels_at_station(target text) RETURNS bigint LANGUAGE SQL STABLE AS
 $$SELECT count(*) FROM smartcity.channels WHERE station_id=target$$;
COMMIT;
