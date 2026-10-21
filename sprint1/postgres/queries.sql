-- Review only. No execution is implied. All names are logical channels/sites.
-- PG01 partial: channels by source and measurement type, not physical sensors.
SELECT source_id, measurement_type, count(*) AS channel_count
FROM sprint1.channels GROUP BY source_id, measurement_type
ORDER BY source_id, measurement_type;

-- PG02 partial: channels per published site, no geographic/historical claim.
SELECT s.station_id, s.name, c.channel_id, c.measurement_type
FROM sprint1.stations AS s INNER JOIN sprint1.channels AS c USING (station_id, source_id)
ORDER BY s.station_id, c.channel_id;

-- PG05 partial: rank sites by logical channels, not number of devices.
WITH counts AS (
    SELECT station_id, count(*) AS channel_count
    FROM sprint1.channels GROUP BY station_id HAVING count(*) > 0
)
SELECT station_id, channel_count, dense_rank() OVER (ORDER BY channel_count DESC) AS rank
FROM counts ORDER BY rank, station_id;

-- PG07 partial: catalog channels without readings IN THIS snapshot/staging only.
SELECT c.channel_id FROM sprint1.channels AS c
WHERE NOT EXISTS (SELECT 1 FROM sprint1.readings AS r WHERE r.channel_id = c.channel_id)
ORDER BY c.channel_id;

-- PG09 scoped view. Counts, not averages across incompatible units/clocks.
CREATE VIEW sprint1.quality_summary AS
SELECT source_id, source_version, channel_id, quality_flag, count(*) AS reading_count
FROM sprint1.readings GROUP BY source_id, source_version, channel_id, quality_flag;
SELECT * FROM sprint1.quality_summary ORDER BY source_id, channel_id, quality_flag;

-- PG10 parameterized function; temporal analytics exclusively documented air.
-- p_version prevents silent mixing of alternative snapshots of the same period.
CREATE FUNCTION sprint1.air_statistics(p_channel text, p_version text,
                                      p_start timestamptz, p_end timestamptz)
RETURNS TABLE(unit text, n bigint, minimum double precision,
              maximum double precision, average double precision)
LANGUAGE sql STABLE SET search_path = pg_catalog
AS $$
    SELECT r.unit, count(*), min(r.value), max(r.value), avg(r.value)
    FROM sprint1.readings AS r
    WHERE r.source_id = 'MAD-AIR' AND r.timestamp_status = 'documented_local'
      AND r.unit_status = 'verified_dictionary' AND r.quality_flag = 'V'
      AND r.channel_id = p_channel AND r.source_version = p_version
      AND r.observed_at >= p_start AND r.observed_at < p_end
    GROUP BY r.unit
$$;

-- Traceability, source cardinality and quality counts (not physical totals).
SELECT DISTINCT source_id, source_version FROM sprint1.readings ORDER BY source_id;
SELECT source_id, quality_flag, count(*), sum(count(*)) OVER (PARTITION BY source_id)
FROM sprint1.readings GROUP BY source_id, quality_flag;

-- PG03/04/06 blocked; PG08 geography unresolved. No substitute results emitted.
