-- Pruebas controladas en transacción; ningún dato ficticio queda en la base.
-- Estas pruebas no acreditan inventario de sensores físicos reales.
\set ON_ERROR_STOP on
BEGIN;

INSERT INTO smartcity.sources (source_id, name, publisher)
VALUES ('MAD-AIR', 'Fuente de prueba', 'Publicador de prueba');

INSERT INTO smartcity.source_versions (source_version, source_id, original_path)
VALUES (repeat('a', 64), 'MAD-AIR', 'controlled-test');

INSERT INTO smartcity.zones (zone_id, name, level)
VALUES ('zona-de-prueba', 'Zona ficticia', 'district');

INSERT INTO smartcity.locations
    (location_id, zone_id, name, coordinate_crs) VALUES
    ('location:350fe7cfb013ce1fb196ed9b57904fb7b93ac9f5b828ee56e4d2f9930173a581',
     'zona-de-prueba', 'Lugar ficticio 1', 'unverified_decimal_geographic'),
    ('location:a5f5add2c3b845dc8c163aab954a520d16297b1c44ba608b80a31feff1831983',
     'zona-de-prueba', 'Lugar ficticio 2', 'unverified_decimal_geographic');

INSERT INTO smartcity.stations
    (station_id, source_id, source_key, name, location_id, inventory_present) VALUES
    ('station:1e17fd190ceb28eec96308a3dd625d7fd2ff8f96e7a1ff9723a54e01be26907f',
     'MAD-AIR', 'test-site', 'Sitio ficticio 1',
     'location:350fe7cfb013ce1fb196ed9b57904fb7b93ac9f5b828ee56e4d2f9930173a581', false),
    ('station:b79de4ca9ea89c887c89a469367a6e29752b5ec0efc54c4d7af5afb797da80ab',
     'MAD-AIR', 'test-site-2', 'Sitio ficticio 2',
     'location:a5f5add2c3b845dc8c163aab954a520d16297b1c44ba608b80a31feff1831983', false);

INSERT INTO smartcity.sensor_categories (category_id, name)
VALUES ('categoria-de-prueba', 'Categoría ficticia');

INSERT INTO smartcity.measurement_types
    (measurement_type, source_id, code, category_id, unit, unit_status)
VALUES ('MAD-AIR:8', 'MAD-AIR', '8', 'categoria-de-prueba', 'ug/m3',
        'verified_dictionary');

INSERT INTO smartcity.organizations
    (organization_id, name, data_origin, provenance)
VALUES ('organismo-de-prueba', 'Organismo ficticio', 'synthetic',
        '{"purpose":"test_rollback"}'::jsonb);

INSERT INTO smartcity.sensors
    (sensor_id, name, category_id, station_id, installation_date,
     administrative_status, organization_id, identity_evidence_reference,
     data_origin, provenance) VALUES
    ('sensor-de-prueba-1', 'Dispositivo ficticio 1', 'categoria-de-prueba',
     'station:1e17fd190ceb28eec96308a3dd625d7fd2ff8f96e7a1ff9723a54e01be26907f',
     DATE '2024-02-03', 'active', 'organismo-de-prueba', 'test-only', 'synthetic',
     '{"purpose":"test_rollback","physical_inventory_evidence":false}'::jsonb),
    ('sensor-de-prueba-2', 'Dispositivo ficticio 2', 'categoria-de-prueba',
     'station:b79de4ca9ea89c887c89a469367a6e29752b5ec0efc54c4d7af5afb797da80ab',
     NULL, NULL, NULL, 'test-only', 'synthetic',
     '{"purpose":"test_rollback","physical_inventory_evidence":false}'::jsonb);

INSERT INTO smartcity.channels
    (channel_id, station_id, source_id, sensor_id,
     source_key, measurement_type, catalog_basis) VALUES
    ('channel:0d7ff3f724b8094157b698d35590b1114e3d8fd36d4c7ef14f4a46c31a0eaf1f',
     'station:1e17fd190ceb28eec96308a3dd625d7fd2ff8f96e7a1ff9723a54e01be26907f',
     'MAD-AIR', 'sensor-de-prueba-1', '["test-site","8",null]'::jsonb,
     'MAD-AIR:8', 'observations'),
    ('channel:59b0181bfe93fd9cc9cf71d63c2dc72400d9a0d55c7e9765f1aef1318bfc1335',
     'station:b79de4ca9ea89c887c89a469367a6e29752b5ec0efc54c4d7af5afb797da80ab',
     'MAD-AIR', 'sensor-de-prueba-2', '["test-site-2","8",null]'::jsonb,
     'MAD-AIR:8', 'observations');

INSERT INTO smartcity.observations
    (measurement_id, channel_id, source_id, observed_at, original_time,
     original_timezone, timestamp_role, timestamp_status, value, quality_flag,
     source_version, data_origin, payload_hash, transformation_method,
     transformation_version, catalog_version, raw_reference,
     source_key, provenance, schema_version)
VALUES
    ('measurement:600d9cdbc70069e6c8e47266b85c8578fdb425b716334d5f53983a580b21761d',
     'channel:0d7ff3f724b8094157b698d35590b1114e3d8fd36d4c7ef14f4a46c31a0eaf1f',
     'MAD-AIR', TIMESTAMPTZ '2025-01-01 00:00:00+00',
     TIMESTAMP '2025-01-01 01:00:00', 'Europe/Madrid', 'hour_end',
     'documented_local', 2, 'V', repeat('a', 64), 'observed',
     'payload:891c7b0ce91e23180e3efc0478b281aab1899f07eaa3717aeb4ef1072ad72cda',
     'madrid-normalize', 'madrid-normalize-v2', 'madrid-draft-v1',
     jsonb_build_object('path', 'controlled-test', 'sha256', repeat('a', 64),
                        'row', 2, 'column', 'H01'),
     '["test-site","8",null,"2025-01-01","H01"]'::jsonb,
     '{"value":"observed"}'::jsonb, 'madrid-draft-v1');

-- El mismo contenido se puede reimportar sin agregar otra lectura.
INSERT INTO smartcity.observations
SELECT *
FROM smartcity.observations
WHERE measurement_id = 'measurement:600d9cdbc70069e6c8e47266b85c8578fdb425b716334d5f53983a580b21761d'
ON CONFLICT (measurement_id) DO UPDATE
SET value = EXCLUDED.value,
    payload_hash = EXCLUDED.payload_hash;

DO $pruebas$
DECLARE
    pruebas_aprobadas integer := 0;
    cantidad_encontrada bigint;
    error_detectado text;
BEGIN
    SELECT COUNT(*) INTO cantidad_encontrada FROM smartcity.observations;
    IF cantidad_encontrada <> 1 THEN
        RAISE EXCEPTION 'La reimportación creó otra medición';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG01: ambos sensores son ficticios y tienen una categoría.
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.sensors
    WHERE category_id = 'categoria-de-prueba';
    IF cantidad_encontrada <> 2 THEN RAISE EXCEPTION 'PG01 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG02 y PG05: un sensor por cada ubicación de prueba.
    SELECT COUNT(DISTINCT smartcity.stations.location_id) INTO cantidad_encontrada
    FROM smartcity.sensors
    INNER JOIN smartcity.stations
        ON smartcity.stations.station_id = smartcity.sensors.station_id;
    IF cantidad_encontrada <> 2 THEN RAISE EXCEPTION 'PG02 o PG05 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG03: el segundo sensor no tiene estado administrativo.
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.sensors
    WHERE administrative_status IS NULL;
    IF cantidad_encontrada <> 1 THEN RAISE EXCEPTION 'PG03 convirtió NULL en estado'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG04: solo el primer sensor tiene organismo de prueba.
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.sensors
    WHERE organization_id = 'organismo-de-prueba';
    IF cantidad_encontrada <> 1 THEN RAISE EXCEPTION 'PG04 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG06: la única instalación anotada es de 2024.
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.sensors
    WHERE EXTRACT(YEAR FROM installation_date) = 2024;
    IF cantidad_encontrada <> 1 THEN RAISE EXCEPTION 'PG06 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG07: el segundo sensor no tiene lectura en la ventana indicada.
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.sensors
    WHERE sensor_id = 'sensor-de-prueba-2'
      AND NOT EXISTS (
          SELECT 1
          FROM smartcity.channels
          INNER JOIN smartcity.observations
              ON smartcity.observations.channel_id = smartcity.channels.channel_id
          WHERE smartcity.channels.sensor_id = smartcity.sensors.sensor_id
            AND smartcity.observations.observed_at >= TIMESTAMPTZ '2025-01-01 00:00:00+01'
            AND smartcity.observations.observed_at < TIMESTAMPTZ '2025-02-01 00:00:00+01'
      );
    IF cantidad_encontrada <> 1 THEN RAISE EXCEPTION 'PG07 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG08: los dos sitios de prueba apuntan a una misma zona ficticia.
    SELECT COUNT(DISTINCT smartcity.sensors.sensor_id) INTO cantidad_encontrada
    FROM smartcity.sensors
    INNER JOIN smartcity.stations
        ON smartcity.stations.station_id = smartcity.sensors.station_id
    INNER JOIN smartcity.locations
        ON smartcity.locations.location_id = smartcity.stations.location_id
    WHERE smartcity.locations.zone_id = 'zona-de-prueba';
    IF cantidad_encontrada <> 2 THEN RAISE EXCEPTION 'PG08 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG09: la vista de JP muestra solo canales con lecturas.
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.channel_activity
    WHERE channel_id = 'channel:0d7ff3f724b8094157b698d35590b1114e3d8fd36d4c7ef14f4a46c31a0eaf1f'
      AND readings = 1
      AND first_observed_at = TIMESTAMPTZ '2025-01-01 00:00:00+00';
    IF cantidad_encontrada <> 1 THEN RAISE EXCEPTION 'PG09 incorrecta'; END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- PG10: la función de JP cuenta canales, no sensores.
    IF smartcity.channels_at_station(
        'station:1e17fd190ceb28eec96308a3dd625d7fd2ff8f96e7a1ff9723a54e01be26907f'
    ) <> 1 THEN
        RAISE EXCEPTION 'PG10 incorrecta';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- No se permite cambiar una lectura aceptada.
    BEGIN
        UPDATE smartcity.observations
        SET value = 3
        WHERE measurement_id = 'measurement:600d9cdbc70069e6c8e47266b85c8578fdb425b716334d5f53983a580b21761d';
        RAISE EXCEPTION 'Se modificó una lectura aceptada';
    EXCEPTION WHEN raise_exception THEN
        GET STACKED DIAGNOSTICS error_detectado = MESSAGE_TEXT;
        IF error_detectado NOT LIKE 'immutable observation / payload conflict:%' THEN
            RAISE;
        END IF;
    END;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- La misma llave no puede crear una segunda observación.
    BEGIN
        INSERT INTO smartcity.observations
        SELECT *
        FROM smartcity.observations
        WHERE measurement_id = 'measurement:600d9cdbc70069e6c8e47266b85c8578fdb425b716334d5f53983a580b21761d';
        RAISE EXCEPTION 'Se duplicó una observación';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- El replay con un valor diferente debe bloquearse.
    BEGIN
        INSERT INTO smartcity.observations
            (measurement_id, channel_id, source_id, observed_at, original_time,
             original_timezone, timestamp_role, timestamp_status, value,
             quality_flag, source_version, data_origin, payload_hash,
             transformation_method, transformation_version, catalog_version,
             raw_reference, source_key, provenance, schema_version)
        SELECT
            measurement_id, channel_id, source_id, observed_at, original_time,
            original_timezone, timestamp_role, timestamp_status, value + 1,
            quality_flag, source_version, data_origin, payload_hash,
            transformation_method, transformation_version, catalog_version,
            raw_reference, source_key, provenance, schema_version
        FROM smartcity.observations
        WHERE measurement_id = 'measurement:600d9cdbc70069e6c8e47266b85c8578fdb425b716334d5f53983a580b21761d'
        ON CONFLICT (measurement_id) DO UPDATE
        SET value = EXCLUDED.value,
            payload_hash = EXCLUDED.payload_hash;
        RAISE EXCEPTION 'Se aceptó un replay con otro valor';
    EXCEPTION WHEN raise_exception THEN
        GET STACKED DIAGNOSTICS error_detectado = MESSAGE_TEXT;
        IF error_detectado NOT LIKE 'immutable observation / payload conflict:%' THEN
            RAISE;
        END IF;
    END;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    -- Un sensor de otra estación no puede atribuirse al canal.
    BEGIN
        UPDATE smartcity.channels
        SET sensor_id = 'sensor-de-prueba-2'
        WHERE channel_id = 'channel:0d7ff3f724b8094157b698d35590b1114e3d8fd36d4c7ef14f4a46c31a0eaf1f';
        RAISE EXCEPTION 'Se aceptó un sensor de otra estación';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    IF pruebas_aprobadas <> 14 THEN
        RAISE EXCEPTION 'Se esperaban 14 verificaciones locales: %', pruebas_aprobadas;
    END IF;
    RAISE NOTICE 'RESULTADO: % verificaciones locales con datos controlados', pruebas_aprobadas;
END
$pruebas$;

ROLLBACK;
