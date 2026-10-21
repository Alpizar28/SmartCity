-- Consultas sencillas: ejecutar en una base LOCAL con el esquema sprint1.
-- Los registros son canales y estaciones, NO sensores físicos acreditados.

-- 1. Ver algunas lecturas y elegir los campos que interesan.
SELECT channel_id, original_time, value, unit, quality_flag
FROM sprint1.readings
ORDER BY original_time, storage_id
LIMIT 20;

-- 2. Filtrar por fuente y calidad.
SELECT channel_id, value, unit
FROM sprint1.readings
WHERE source_id = 'MAD-AIR' AND quality_flag = 'V'
ORDER BY value DESC
LIMIT 20;

-- 3. Ver las fuentes diferentes que ya tienen datos.
SELECT DISTINCT source_id
FROM sprint1.readings
ORDER BY source_id;

-- 4. Contar canales por tipo de medición. Alternativa PARCIAL a PG01.
SELECT source_id, measurement_type, COUNT(*) AS cantidad_canales
FROM sprint1.channels
GROUP BY source_id, measurement_type
ORDER BY source_id, measurement_type;

-- 5. Unir canales con estaciones. Alternativa PARCIAL a PG02.
SELECT s.station_id, s.name, c.channel_id, c.measurement_type
FROM sprint1.stations s
INNER JOIN sprint1.channels c ON c.station_id = s.station_id
ORDER BY s.station_id, c.channel_id
LIMIT 20;

-- 6. Estaciones con más canales, sin función de ventana. PARCIAL a PG05.
SELECT s.station_id, s.name, COUNT(c.channel_id) AS cantidad_canales
FROM sprint1.stations s
LEFT JOIN sprint1.channels c ON c.station_id = s.station_id
GROUP BY s.station_id, s.name
HAVING COUNT(c.channel_id) > 0
ORDER BY cantidad_canales DESC, s.station_id
LIMIT 20;

-- 7. Canales sin lecturas EN ESTA BASE. No prueba inactividad física. PG07 parcial.
SELECT c.channel_id
FROM sprint1.channels c
LEFT JOIN sprint1.readings r ON r.channel_id = c.channel_id
WHERE r.storage_id IS NULL
ORDER BY c.channel_id
LIMIT 20;

-- 8. MIN, MAX, AVG de aire válido: separar canal, snapshot y unidad.
-- No incluir meteo, cuyas unidades siguen pendientes.
SELECT channel_id, source_version, unit, COUNT(*) AS cantidad,
       MIN(value) AS minimo, MAX(value) AS maximo, AVG(value) AS promedio
FROM sprint1.readings
WHERE source_id = 'MAD-AIR'
  AND quality_flag = 'V'
  AND unit_status = 'verified_dictionary'
  AND timestamp_status = 'documented_local'
  AND observed_at >= TIMESTAMPTZ '2025-01-01 00:00:00+00'
  AND observed_at < TIMESTAMPTZ '2025-02-01 00:00:00+00'
GROUP BY channel_id, source_version, unit
ORDER BY channel_id, source_version;

-- 9. Consultar la vista que ya se creó, sin definir otra función compleja.
SELECT * FROM sprint1.quality_summary
ORDER BY source_id, channel_id, quality_flag
LIMIT 20;

-- 10. Sumar conteos de la vista. No sumar concentraciones o intensidades físicas.
SELECT source_id, source_version, SUM(reading_count) AS total_lecturas
FROM sprint1.quality_summary
GROUP BY source_id, source_version
ORDER BY source_id, source_version;

-- PG03, PG04, PG06 y PG08 NO se resuelven con estas consultas.
-- PG10 sigue en la función ya probada sprint1.air_statistics.
