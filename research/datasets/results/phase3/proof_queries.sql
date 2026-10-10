
CREATE SCHEMA proof;
SET search_path=proof;
CREATE TABLE categories(category_id text PRIMARY KEY, variable text NOT NULL, unit text NOT NULL);
CREATE TABLE locations(location_id text PRIMARY KEY, zone text, lat double precision, lon double precision,
 name text, district text, site_opened timestamp,
 CHECK(lat IS NULL OR lat BETWEEN -90 AND 90),CHECK(lon IS NULL OR lon BETWEEN -180 AND 180));
CREATE TABLE organizations(organization_id text PRIMARY KEY,name text NOT NULL,responsible text);
CREATE TABLE users(user_id text PRIMARY KEY,name text, email text UNIQUE);
CREATE TABLE channels(channel_id text PRIMARY KEY,entity text NOT NULL,
 category_id text NOT NULL REFERENCES categories,location_id text NOT NULL REFERENCES locations,
 source text NOT NULL,name text,installation_date date,administrative_status text,
 organization_id text REFERENCES organizations,entity_kind text NOT NULL);
CREATE TABLE readings(measurement_id text PRIMARY KEY,channel_id text NOT NULL REFERENCES channels,
 observed_at timestamp NOT NULL,value double precision,quality text NOT NULL,clock text NOT NULL,
 UNIQUE(channel_id,observed_at));
CREATE INDEX channel_location ON channels(location_id);
CREATE INDEX channel_category ON channels(category_id);
CREATE INDEX reading_channel_time ON readings(channel_id,observed_at);
CREATE VIEW sensor_scope AS SELECT * FROM channels
 WHERE entity_kind NOT IN ('campaign_segment_direction','anonymous_household_channel');
CREATE VIEW channel_by_type AS SELECT category_id,count(*) AS n FROM sensor_scope GROUP BY category_id;
CREATE FUNCTION channels_at_location(target text) RETURNS bigint LANGUAGE SQL STABLE
 AS $$ SELECT count(*) FROM proof.sensor_scope WHERE location_id=target $$;

-- PG01
SELECT coalesce(json_object_agg(category_id,n),'{}') FROM (SELECT category_id,count(*) n FROM sensor_scope GROUP BY category_id) x;
-- PG02
SELECT coalesce(json_object_agg(location_id,n),'{}') FROM (SELECT l.location_id,count(c.channel_id) n FROM locations l JOIN sensor_scope c USING(location_id) GROUP BY l.location_id) x;
-- PG03
SELECT json_build_object('unknown_status',count(*) FILTER(WHERE administrative_status IS NULL),'known_status',count(administrative_status)) FROM sensor_scope;
-- PG04
SELECT json_build_object('known_owner',count(organization_id),'unknown_owner',count(*) FILTER(WHERE organization_id IS NULL)) FROM sensor_scope LEFT JOIN organizations USING(organization_id);
-- PG05
SELECT coalesce(json_object_agg(location_id,n),'{}') FROM (SELECT location_id,count(*) n FROM sensor_scope GROUP BY location_id HAVING count(*)>0 ORDER BY n DESC,location_id) x;
-- PG06
SELECT json_build_object('known_installation_date',count(installation_date)) FROM sensor_scope;
-- PG07
SELECT json_build_object('without_activity_in_loaded_window',count(*),'independent_inventory_test_pending',true) FROM sensor_scope c WHERE NOT EXISTS(SELECT 1 FROM readings r WHERE r.channel_id=c.channel_id);
-- PG08
WITH counts AS (SELECT l.zone,count(*) n FROM sensor_scope c JOIN locations l USING(location_id) WHERE l.zone IS NOT NULL GROUP BY l.zone), ranked AS(SELECT zone,n,dense_rank() OVER(ORDER BY n DESC) AS rank FROM counts) SELECT json_build_object('counts',coalesce(json_object_agg(zone,n),'{}'),'ranks',coalesce(json_object_agg(zone,rank),'{}')) FROM ranked;
-- PG09
SELECT coalesce(json_object_agg(category_id,n),'{}') FROM channel_by_type;
-- PG10
SELECT coalesce(json_object_agg(location_id,channels_at_location(location_id)),'{}') FROM locations WHERE location_id IN(SELECT location_id FROM sensor_scope);
-- readings
SELECT to_json(count(*)) FROM readings;
-- sum_values
SELECT to_json(sum(value)) FROM readings;
-- min_value
SELECT to_json(min(value)) FROM readings;
-- max_value
SELECT to_json(max(value)) FROM readings;