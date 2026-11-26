-- Ruta canónica del Sprint 1: esquema smartcity, contrato madrid-draft-v1.
-- Ejecutar después de research/datasets/scripts/phase5_postgresql.sql.
-- Solo lectura. Los resultados administrativos pueden ser sintéticos:
-- no acreditan dispositivos físicos ni productores de las lecturas públicas.

-- PG01: cantidad de sensores por categoría, incluyendo categoría desconocida.
SELECT
    smartcity.sensors.category_id,
    smartcity.sensor_categories.name AS category_name,
    COUNT(smartcity.sensors.sensor_id) AS sensor_count
FROM smartcity.sensors
LEFT JOIN smartcity.sensor_categories
    ON smartcity.sensor_categories.category_id = smartcity.sensors.category_id
GROUP BY smartcity.sensors.category_id, smartcity.sensor_categories.name
ORDER BY smartcity.sensors.category_id NULLS LAST;

-- PG02: sensores por ubicación del inventario; vigencia histórica pendiente.
SELECT
    smartcity.stations.station_id,
    smartcity.locations.location_id,
    smartcity.locations.name AS location_name,
    COUNT(DISTINCT smartcity.sensors.sensor_id) AS sensor_count
FROM smartcity.stations
INNER JOIN smartcity.sensors
    ON smartcity.sensors.station_id = smartcity.stations.station_id
LEFT JOIN smartcity.locations
    ON smartcity.locations.location_id = smartcity.stations.location_id
GROUP BY smartcity.stations.station_id, smartcity.locations.location_id,
         smartcity.locations.name
ORDER BY smartcity.stations.station_id;

-- PG03: estados administrativos activos, inactivos y NULL por separado.
SELECT
    smartcity.sensors.administrative_status,
    COUNT(*) AS sensor_count
FROM smartcity.sensors
GROUP BY smartcity.sensors.administrative_status
ORDER BY smartcity.sensors.administrative_status NULLS LAST;

-- PG04: sensores por organismo; incluir organismos sin sensores.
SELECT
    smartcity.organizations.organization_id,
    smartcity.organizations.name,
    COUNT(smartcity.sensors.sensor_id) AS sensor_count
FROM smartcity.organizations
LEFT JOIN smartcity.sensors
    ON smartcity.sensors.organization_id = smartcity.organizations.organization_id
GROUP BY smartcity.organizations.organization_id, smartcity.organizations.name
ORDER BY smartcity.organizations.organization_id;

-- PG05: ubicaciones con mayor número de sensores del inventario.
SELECT
    smartcity.locations.location_id,
    smartcity.locations.name,
    COUNT(DISTINCT smartcity.sensors.sensor_id) AS sensor_count
FROM smartcity.locations
INNER JOIN smartcity.stations
    ON smartcity.stations.location_id = smartcity.locations.location_id
INNER JOIN smartcity.sensors
    ON smartcity.sensors.station_id = smartcity.stations.station_id
GROUP BY smartcity.locations.location_id, smartcity.locations.name
HAVING COUNT(DISTINCT smartcity.sensors.sensor_id) > 0
ORDER BY sensor_count DESC, smartcity.locations.location_id;

-- PG06: sensores instalados por año; no convertir fechas desconocidas en cero.
SELECT
    EXTRACT(YEAR FROM smartcity.sensors.installation_date) AS installation_year,
    COUNT(*) AS sensor_count
FROM smartcity.sensors
WHERE smartcity.sensors.installation_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM smartcity.sensors.installation_date)
ORDER BY installation_year;

-- PG07: sensores con canal asociado pero sin lecturas en enero de 2025 (Madrid).
-- Sin relación sensor-canal no hay evidencia para evaluar actividad: excluirlos.
-- La ventana es [2025-01-01, 2025-02-01), no una afirmación de avería o estado.
SELECT
    smartcity.sensors.sensor_id
FROM smartcity.sensors
WHERE EXISTS (
    SELECT 1
    FROM smartcity.channels
    WHERE smartcity.channels.sensor_id = smartcity.sensors.sensor_id
)
AND NOT EXISTS (
    SELECT 1
    FROM smartcity.channels
    INNER JOIN smartcity.observations
        ON smartcity.observations.channel_id = smartcity.channels.channel_id
    WHERE smartcity.channels.sensor_id = smartcity.sensors.sensor_id
      AND smartcity.observations.observed_at >= TIMESTAMPTZ '2025-01-01 00:00:00+01'
      AND smartcity.observations.observed_at < TIMESTAMPTZ '2025-02-01 00:00:00+01'
)
ORDER BY smartcity.sensors.sensor_id;

-- PG08: ranking de zonas con sensores asociados, sin inventar geografía.
WITH zone_counts AS (
    SELECT
        smartcity.zones.zone_id,
        smartcity.zones.name,
        COUNT(DISTINCT smartcity.sensors.sensor_id) AS sensor_count
    FROM smartcity.zones
    INNER JOIN smartcity.locations
        ON smartcity.locations.zone_id = smartcity.zones.zone_id
    INNER JOIN smartcity.stations
        ON smartcity.stations.location_id = smartcity.locations.location_id
    INNER JOIN smartcity.sensors
        ON smartcity.sensors.station_id = smartcity.stations.station_id
    GROUP BY smartcity.zones.zone_id, smartcity.zones.name
    HAVING COUNT(DISTINCT smartcity.sensors.sensor_id) > 0
)
SELECT
    zone_counts.zone_id,
    zone_counts.name,
    zone_counts.sensor_count,
    DENSE_RANK() OVER (ORDER BY zone_counts.sensor_count DESC) AS zone_rank
FROM zone_counts
ORDER BY zone_rank, zone_counts.zone_id;

-- PG09: consulta de la vista anual de actividad por canal.
SELECT
    smartcity.channel_activity.channel_id,
    smartcity.channel_activity.readings,
    smartcity.channel_activity.first_observed_at,
    smartcity.channel_activity.last_observed_at
FROM smartcity.channel_activity
ORDER BY smartcity.channel_activity.readings DESC,
         smartcity.channel_activity.channel_id;

-- PG10: función anual de conteo de canales por estación, no sensores físicos.
SELECT
    smartcity.stations.station_id,
    smartcity.channels_at_station(smartcity.stations.station_id) AS channel_count
FROM smartcity.stations
ORDER BY smartcity.stations.station_id;

-- Aire con unidad acreditada; no combinar unidades ni relojes provisionales.
SELECT
    smartcity.observation_contract.measurement_type,
    smartcity.observation_contract.unit,
    COUNT(*) AS reading_count,
    SUM(smartcity.observation_contract.value) AS total_value,
    AVG(smartcity.observation_contract.value) AS average_value,
    MIN(smartcity.observation_contract.value) AS minimum_value,
    MAX(smartcity.observation_contract.value) AS maximum_value
FROM smartcity.observation_contract
WHERE smartcity.observation_contract.source_id = 'MAD-AIR'
  AND smartcity.observation_contract.unit IS NOT NULL
  AND smartcity.observation_contract.unit_status = 'verified_dictionary'
  AND smartcity.observation_contract.timestamp_status = 'documented_local'
  AND smartcity.observation_contract.quality_flag = 'V'
  AND smartcity.observation_contract.original_time >= TIMESTAMP '2025-01-01 00:00:00'
  AND smartcity.observation_contract.original_time < TIMESTAMP '2025-01-02 00:00:00'
GROUP BY smartcity.observation_contract.measurement_type,
         smartcity.observation_contract.unit
ORDER BY smartcity.observation_contract.measurement_type;

-- EXPLAIN permite inspeccionar el plan; no acredita una mejora de rendimiento.
EXPLAIN
SELECT smartcity.observations.measurement_id
FROM smartcity.observations
WHERE smartcity.observations.channel_id = 'channel:22b22793147c07679ab9c6519ef25e4878314823835845b139091c1aa9033415'
ORDER BY smartcity.observations.observed_at;
