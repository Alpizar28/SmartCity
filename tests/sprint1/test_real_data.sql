-- Ejecutar después de cargar expanded-2025 en una base temporal.
-- Estas consultas no agregan ni modifican mediciones.
\set ON_ERROR_STOP on

DO $pruebas$
DECLARE
    pruebas_aprobadas integer := 0;
    cantidad_encontrada bigint;
    lecturas_en_vista bigint;
    estacion_elegida text;
BEGIN
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.observations;
    IF cantidad_encontrada <> 1076813 THEN
        RAISE EXCEPTION 'No se cargaron 1.076.813 observaciones';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.observations
    WHERE source_id <> 'MAD-AIR'
       OR data_origin <> 'observed'
       OR schema_version <> 'madrid-draft-v1'
       OR catalog_version <> 'madrid-draft-v1';
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Fuente, origen o contrato incorrectos';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM (
        SELECT measurement_id
        FROM smartcity.observations
        GROUP BY measurement_id
        HAVING COUNT(*) > 1
    ) AS identificadores_repetidos;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Hay measurement_id repetidos';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM (
        SELECT channel_id, observed_at, timestamp_role
        FROM smartcity.observations
        GROUP BY channel_id, observed_at, timestamp_role
        HAVING COUNT(*) > 1
    ) AS lecturas_repetidas;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Hay claves naturales repetidas';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.observations
    LEFT JOIN smartcity.channels
        ON smartcity.channels.channel_id = smartcity.observations.channel_id
       AND smartcity.channels.source_id = smartcity.observations.source_id
    LEFT JOIN smartcity.stations
        ON smartcity.stations.station_id = smartcity.channels.station_id
       AND smartcity.stations.source_id = smartcity.observations.source_id
    LEFT JOIN smartcity.measurement_types
        ON smartcity.measurement_types.measurement_type = smartcity.channels.measurement_type
       AND smartcity.measurement_types.source_id = smartcity.observations.source_id
    LEFT JOIN smartcity.source_versions
        ON smartcity.source_versions.source_version = smartcity.observations.source_version
       AND smartcity.source_versions.source_id = smartcity.observations.source_id
    WHERE smartcity.channels.channel_id IS NULL
       OR smartcity.stations.station_id IS NULL
       OR smartcity.measurement_types.measurement_type IS NULL
       OR smartcity.source_versions.source_version IS NULL;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'La relación fuente, estación, canal o versión falla';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.observations
    WHERE source_version <> '9122af41d3e73e71f5a0e0a22b99a0cefbd4c7f8abe9e2fae344207482398471'
       OR raw_reference->>'sha256' <> source_version
       OR raw_reference->>'path' <> 'raw/MAD-AIR-file.attempt1.bin'
       OR (raw_reference->>'row')::integer < 2
       OR raw_reference->>'column' NOT BETWEEN 'H01' AND 'H24';
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'La referencia al CSV original no coincide';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.observations
    WHERE payload_hash !~ '^payload:[0-9a-f]{64}$'
       OR transformation_method <> 'madrid-normalize'
       OR transformation_version <> 'madrid-normalize-v2'
       OR provenance IS NULL;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Hash o transformación incorrectos';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.observations
    WHERE observed_at <> original_time AT TIME ZONE 'Europe/Madrid'
       OR timestamp_status <> 'documented_local'
       OR original_timezone <> 'Europe/Madrid';
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Reloj original o UTC incorrecto';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.sensors;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Se añadieron sensores físicos al lote real';
    END IF;
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.organizations;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Se añadieron organismos al lote real';
    END IF;
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.users;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Se añadieron usuarios al lote real';
    END IF;
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity_demo.entities;
    IF cantidad_encontrada <> 0 THEN
        RAISE EXCEPTION 'Se añadió el demo sintético a esta carga';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT SUM(readings) INTO lecturas_en_vista
    FROM smartcity.channel_activity;
    IF lecturas_en_vista <> 1076813 THEN
        RAISE EXCEPTION 'La vista no suma todas las lecturas';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT station_id INTO estacion_elegida
    FROM smartcity.stations
    ORDER BY station_id
    LIMIT 1;
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM smartcity.channels
    WHERE station_id = estacion_elegida;
    IF smartcity.channels_at_station(estacion_elegida) <> cantidad_encontrada THEN
        RAISE EXCEPTION 'La función no cuenta los canales de la estación';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    IF pruebas_aprobadas <> 11 THEN
        RAISE EXCEPTION 'Se esperaban 11 verificaciones reales';
    END IF;
    RAISE NOTICE 'RESULTADO: % verificaciones con datos reales aprobadas', pruebas_aprobadas;
END
$pruebas$;
