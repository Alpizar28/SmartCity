-- PRELIMINARY ONLY. Run on disposable local DB; never apply to shared server without review.
BEGIN;
CREATE SCHEMA smartcity;
SET LOCAL search_path=smartcity,pg_temp;
CREATE TABLE sources(source_id text PRIMARY KEY CHECK(source_id IN ('MAD-AIR','MAD-METEO','MAD-TRAFFIC')), name text NOT NULL, publisher text NOT NULL);
CREATE TABLE source_versions(source_version text PRIMARY KEY CHECK(source_version ~ '^[0-9a-f]{64}$'),
 source_id text NOT NULL REFERENCES sources, original_path text NOT NULL, acquired_at timestamptz,
 UNIQUE(source_version,source_id));
CREATE TABLE zones(zone_id text PRIMARY KEY, name text NOT NULL, level text NOT NULL CHECK(level IN ('district','city')));
CREATE TABLE locations(location_id text PRIMARY KEY, zone_id text REFERENCES zones, name text,
 latitude double precision CHECK(latitude BETWEEN -90 AND 90),
 longitude double precision CHECK(longitude BETWEEN -180 AND 180),
 coordinate_crs text NOT NULL, historical_location_verified boolean NOT NULL DEFAULT false,
 inventory_version text REFERENCES source_versions,
 CHECK((latitude IS NULL)=(longitude IS NULL)));
CREATE TABLE stations(station_id text PRIMARY KEY, source_id text NOT NULL REFERENCES sources,
 source_key text NOT NULL, name text, location_id text REFERENCES locations,
 inventory_present boolean NOT NULL, UNIQUE(source_id,source_key), UNIQUE(station_id,source_id));
CREATE TABLE sensor_categories(category_id text PRIMARY KEY, name text NOT NULL);
CREATE TABLE measurement_types(measurement_type text PRIMARY KEY, source_id text NOT NULL REFERENCES sources,
 code text NOT NULL, category_id text NOT NULL REFERENCES sensor_categories,
 unit text, candidate_unit text, unit_status text NOT NULL,
 CHECK((unit IS NULL)=(unit_status='pending_dictionary')),
 UNIQUE(source_id,code), UNIQUE(measurement_type,source_id));
CREATE TABLE organizations(organization_id text PRIMARY KEY, name text NOT NULL,
 responsible_person_or_role text, evidence_reference text,
 data_origin text NOT NULL CHECK(data_origin IN ('observed','synthetic')), provenance jsonb NOT NULL);
CREATE TABLE users(user_id text PRIMARY KEY, name text NOT NULL, email text NOT NULL UNIQUE,
 consent_reference text NOT NULL, demo_only boolean NOT NULL DEFAULT false,
 data_origin text NOT NULL CHECK(data_origin IN ('observed','synthetic')));
-- Physical sensors intentionally EMPTY until inventory proves actual devices.
CREATE TABLE sensors(sensor_id text PRIMARY KEY, name text NOT NULL,
 category_id text NOT NULL REFERENCES sensor_categories, station_id text NOT NULL REFERENCES stations,
 installation_date date, administrative_status text CHECK(administrative_status IN ('active','inactive')),
 status_effective_at timestamptz, organization_id text REFERENCES organizations,
  identity_evidence_reference text NOT NULL,
  data_origin text NOT NULL DEFAULT 'observed' CHECK(data_origin IN ('observed','synthetic')),
  provenance jsonb NOT NULL, UNIQUE(sensor_id,station_id));
CREATE TABLE channels(channel_id text PRIMARY KEY, station_id text NOT NULL REFERENCES stations,
 source_id text NOT NULL REFERENCES sources,
 sensor_id text REFERENCES sensors, source_key jsonb NOT NULL,
 measurement_type text NOT NULL REFERENCES measurement_types,
 catalog_basis text NOT NULL CHECK(catalog_basis IN ('observations','independent_inventory')),
 UNIQUE(station_id,source_key), UNIQUE(channel_id,source_id),
 FOREIGN KEY(station_id,source_id) REFERENCES stations(station_id,source_id),
 FOREIGN KEY(measurement_type,source_id) REFERENCES measurement_types(measurement_type,source_id),
 FOREIGN KEY(sensor_id,station_id) REFERENCES sensors(sensor_id,station_id));
CREATE TABLE observations(measurement_id text PRIMARY KEY, channel_id text NOT NULL REFERENCES channels,
 source_id text NOT NULL REFERENCES sources,
 observed_at timestamptz NOT NULL, original_time timestamp NOT NULL,
 original_timezone text NOT NULL CHECK(original_timezone='Europe/Madrid'),
 timestamp_role text NOT NULL CHECK(timestamp_role IN ('hour_end','publisher_label')),
 timestamp_status text NOT NULL CHECK(timestamp_status IN ('documented_local','publisher_confirmed_local')), value double precision NOT NULL
 CHECK(value>'-Infinity'::double precision AND value<'Infinity'::double precision),
 quality_flag text NOT NULL, source_version text NOT NULL REFERENCES source_versions,
 data_origin text NOT NULL CHECK(data_origin='observed'),
 payload_hash text NOT NULL CHECK(payload_hash ~ '^payload:[0-9a-f]{64}$'),
 transformation_method text NOT NULL CHECK(length(transformation_method)>0),
 transformation_version text NOT NULL CHECK(length(transformation_version)>0),
 catalog_version text NOT NULL CHECK(catalog_version='madrid-draft-v1'),
 raw_reference jsonb NOT NULL, interval_minutes integer CHECK(interval_minutes BETWEEN 1 AND 30),
 source_key jsonb NOT NULL, provenance jsonb NOT NULL,
 element_type text CHECK(element_type IN ('URB','M30','C30')),
 -- One traffic interval remains ONE row. Optional fields are a dynamic payload, not extra observations.
 measurements jsonb,
 schema_version text NOT NULL CHECK(schema_version='madrid-draft-v1'),
 CHECK(raw_reference ? 'sha256' AND jsonb_typeof(raw_reference->'sha256')='string'
       AND raw_reference->>'sha256'=source_version),
 FOREIGN KEY(channel_id,source_id) REFERENCES channels(channel_id,source_id),
 FOREIGN KEY(source_version,source_id) REFERENCES source_versions(source_version,source_id),
 UNIQUE(channel_id,observed_at,timestamp_role));
CREATE FUNCTION consistent_observation_source() RETURNS trigger LANGUAGE plpgsql SET search_path=smartcity,pg_temp AS $$
BEGIN
 IF TG_OP='UPDATE' AND NEW IS DISTINCT FROM OLD THEN
  RAISE EXCEPTION 'immutable observation / payload conflict: %', OLD.measurement_id;
 END IF;
 IF NEW.observed_at AT TIME ZONE 'Europe/Madrid' <> NEW.original_time
 OR (NEW.observed_at + interval '1 hour') AT TIME ZONE 'Europe/Madrid' = NEW.original_time
 OR (NEW.observed_at - interval '1 hour') AT TIME ZONE 'Europe/Madrid' = NEW.original_time THEN
  RAISE EXCEPTION 'invalid or ambiguous Madrid wall clock';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM channels c JOIN stations s USING(station_id)
 JOIN measurement_types t ON t.measurement_type=c.measurement_type
 JOIN source_versions v ON v.source_version=NEW.source_version
  WHERE c.channel_id=NEW.channel_id AND s.source_id=v.source_id AND t.source_id=v.source_id
  AND c.source_id=NEW.source_id) THEN
  RAISE EXCEPTION 'channel/station/type/source version mismatch';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER observation_source BEFORE INSERT OR UPDATE ON observations
 FOR EACH ROW EXECUTE FUNCTION consistent_observation_source();
CREATE INDEX sensor_station ON sensors(station_id);
CREATE INDEX sensor_category ON sensors(category_id);
CREATE INDEX sensor_org ON sensors(organization_id);
CREATE INDEX channel_station ON channels(station_id);
CREATE INDEX observations_time ON observations(observed_at);
-- UNIQUE(channel_id,observed_at,timestamp_role) already provides leading channel/time B-tree.
CREATE VIEW channel_activity AS SELECT channel_id,min(observed_at) AS first_observed_at,
 max(observed_at) AS last_observed_at,count(*) AS readings FROM observations GROUP BY channel_id;
CREATE VIEW observation_contract AS
  SELECT o.*,o.measurement_id AS _id,c.sensor_id,c.station_id,c.measurement_type,
   t.unit,t.unit_status,t.candidate_unit,l.zone_id,NULL::text AS time_error
 FROM observations o JOIN channels c USING(channel_id) JOIN stations s USING(station_id)
 JOIN measurement_types t USING(measurement_type) LEFT JOIN locations l USING(location_id);
CREATE FUNCTION channels_at_station(target text) RETURNS bigint LANGUAGE SQL STABLE AS
  $$SELECT count(*) FROM smartcity.channels WHERE station_id=target$$;
-- Only the separate demo dataset may contain fictitious physical identities.
CREATE SCHEMA smartcity_demo;
CREATE TABLE smartcity_demo.entities (
 entity_id text PRIMARY KEY, entity_type text NOT NULL CHECK(entity_type IN ('sensor','organization','user')),
 data_origin text NOT NULL CHECK(data_origin='synthetic'), seed bigint NOT NULL,
 generator_version text NOT NULL, payload jsonb NOT NULL, provenance jsonb NOT NULL);
COMMIT;
-- Materialized view and temporal partition migration remain proposals, not silently introduced.
