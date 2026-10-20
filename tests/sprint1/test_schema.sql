-- Comprobar el DDL común de JP en una base local vacía.
-- Esta prueba no agrega mediciones ni datos administrativos.
\set ON_ERROR_STOP on

DO $pruebas$
DECLARE
    pruebas_aprobadas integer := 0;
    cantidad_encontrada integer;
BEGIN
    SELECT COUNT(*) INTO cantidad_encontrada
    FROM pg_catalog.pg_tables
    WHERE schemaname = 'smartcity';
    IF cantidad_encontrada <> 12 THEN
        RAISE EXCEPTION 'Se esperaban 12 tablas del esquema común';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'smartcity'
      AND constraint_type = 'PRIMARY KEY';
    IF cantidad_encontrada <> 12 THEN
        RAISE EXCEPTION 'Faltan llaves primarias del esquema común';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'smartcity'
      AND constraint_type = 'FOREIGN KEY';
    IF cantidad_encontrada < 16 THEN
        RAISE EXCEPTION 'Faltan llaves foráneas del esquema común';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM information_schema.key_column_usage
    WHERE table_schema = 'smartcity'
      AND table_name = 'observations'
      AND constraint_name = 'observations_pkey'
      AND column_name = 'measurement_id';
    IF cantidad_encontrada <> 1 THEN
        RAISE EXCEPTION 'measurement_id no es la llave primaria';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM information_schema.key_column_usage
    WHERE table_schema = 'smartcity'
      AND table_name = 'stations'
      AND column_name = 'location_id';
    IF cantidad_encontrada <> 1 THEN
        RAISE EXCEPTION 'Falta la ubicación de stations';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM pg_catalog.pg_views
    WHERE schemaname = 'smartcity'
      AND viewname IN ('channel_activity', 'observation_contract');
    IF cantidad_encontrada <> 2 THEN
        RAISE EXCEPTION 'Faltan vistas del esquema común';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM pg_catalog.pg_trigger
    INNER JOIN pg_catalog.pg_class
        ON pg_catalog.pg_class.oid = pg_catalog.pg_trigger.tgrelid
    INNER JOIN pg_catalog.pg_namespace
        ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace
    WHERE pg_catalog.pg_namespace.nspname = 'smartcity'
      AND pg_catalog.pg_class.relname = 'observations'
      AND pg_catalog.pg_trigger.tgname = 'observation_source';
    IF cantidad_encontrada <> 1 THEN
        RAISE EXCEPTION 'Falta el trigger de observaciones';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM pg_catalog.pg_indexes
    WHERE schemaname = 'smartcity'
      AND indexname IN ('sensor_station', 'sensor_category', 'sensor_org',
                        'channel_station', 'observations_time');
    IF cantidad_encontrada <> 5 THEN
        RAISE EXCEPTION 'Faltan índices comunes de JP';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    SELECT COUNT(*) INTO cantidad_encontrada
    FROM pg_catalog.pg_tables
    WHERE schemaname = 'smartcity_demo'
      AND tablename = 'entities';
    IF cantidad_encontrada <> 1 THEN
        RAISE EXCEPTION 'Falta la tabla separada del demo sintético';
    END IF;
    pruebas_aprobadas := pruebas_aprobadas + 1;

    IF pruebas_aprobadas <> 9 THEN
        RAISE EXCEPTION 'Se esperaban 9 controles de esquema';
    END IF;
    RAISE NOTICE 'RESULTADO: % controles del esquema común aprobados', pruebas_aprobadas;
END
$pruebas$;
