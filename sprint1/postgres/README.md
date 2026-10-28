# PostgreSQL — modelo relacional del Sprint 1

## Modelo de entrega normalizado

Autoridad: [schema_v2_3nf.sql](schema_v2_3nf.sql),
[queries_v2_3nf.sql](queries_v2_3nf.sql), [cierre técnico vigente](cierre_3nf.md),
[prueba formal e impacto](impacto_3nf.md)
y [E-R completo](../../docs/arquitectura/diagrama_3nf.md).
El modelo tiene catorce tablas y conserva los 17 atributos exigidos. La vista
contractual reconstruye las mediciones v2 sin cambiar identidad ni payload.
Las [evidencias normalizadas](evidencias/3nf/) son nuevas y no sobrescriben las
anteriores. Reproducción local nativa:

```bash
python scripts/validar_postgresql_3nf.py --sample 1000
python scripts/validar_postgresql_3nf.py
```

Los apartados siguientes describen la ruta histórica de doce tablas y sus
excepciones, preservadas para reproducir los resultados anteriores.


## Antecedentes del modelo de doce tablas

- [Auditoría formal 3FN de las doce tablas](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/normalizacion_3fn.md): excepciones
  reales en `channels` y `observations`; no se modificó el DDL común.
- [PG07: prueba exacta y límite de evidencia física](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/pg07_limite_evidencia.md).
- [Matriz PG01–PG10, muestras y trazabilidad SQL](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/evidencia_final_postgresql.md).
- [Reproducción y prerrequisitos reales](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/reproduccion_cierre.md).
- [Tres reportes acotados verificables](evidencias/README.md).

En la reproducción histórica v2, `contract_v2.sql` se aplica después del DDL común
en una base local nueva. No sumar sus lecturas de enero a la carga anual v1.
El encabezado v1 del SQL canónico conserva su identidad histórica; los diez
SELECT también se ejecutaron con el contrato v2 sin cambiar sus bytes.

## Archivos de reproducción histórica

- **DDL común:** `research/datasets/scripts/phase5_postgresql.sql`, esquema `smartcity`.
- **Diez consultas históricas:** `sprint1/postgres/queries.sql`, PG01–PG10.
- **Reproductor anual:** `tests/sprint1/validate_real_postgres.py`; usa ese mismo archivo.
- **Práctica separada:** `schema_proposal.sql`, `staging_queries.sql` y `staging.sql`
  usan el esquema `sprint1`. No aplicarlos para preparar el esquema anual.

Los DDL no son inicializadores de Compose ni migraciones para bases pobladas.
No se aplican a un servidor compartido sin revisión y autorización.

## Un comando desde la raíz

```bash
bash scripts/validate_sprint1.sh --engines
```

Ejecuta pruebas offline, SQL canónico sobre PostgreSQL desechable y práctica
complementaria SQL/Mongo. Requiere Python 3.10+, Node.js 18+, Docker local e
imágenes ya descargadas `postgres:16.6-alpine` y `mongo:7.0.16`.
No descarga imágenes, publica puertos ni monta datos del host.

Para repetir **solo las diez consultas SQL**, sin Mongo ni insumos privados:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_sql.py
```

El informe `/tmp/opencode/smartcity-s1-sql-*.json` incluye las filas obtenidas
por cada consulta, hashes, rollback y limpieza del contenedor. Es una prueba
con fixtures fabricadas y explícitas, no una carga de mediciones reales.

Si ya existe otra imagen PostgreSQL 16 local, se puede seleccionar explícitamente
con `SMARTCITY_PG_IMAGE=postgres:16-alpine`; el informe registra imagen, ID y versión.
No descarga imágenes ni afirma haber usado el pin 16.6 si se seleccionó otra.

## Semántica de las consultas

PG01–PG06 y PG08 consultan sensores/organismos/ubicaciones del inventario, que
puede contener entidades administrativas sintéticas autorizadas. PG09 usa
`channel_activity`; PG10 invoca `channels_at_station()`, que cuenta canales.

PG07 busca sensores **con algún canal asociado** que no tienen lecturas en
`[2025-01-01 00:00+01, 2025-02-01 00:00+01)`. No equivale a estado inactivo,
avería o ausencia de información en todo el histórico. Un sensor sin relación
con canales se excluye porque no se puede evaluar su actividad.
La prueba cubre inicio incluido, fin excluido y relación desconocida.

Las diez consultas ejecutan con resultados comprobados en el caso controlado.
En el lote anual observado los sensores siguen sin enlace a las lecturas:
el bloqueo de datos de PG07 no se resuelve asignando dispositivos ficticios.
La matriz de entrega conserva ese límite.

## Evidencia anual y rendimiento

El parser y el resumen de aire del benchmark vuelven a leer el archivo canónico.
Repetir la carga anual necesita los snapshots privados y las imágenes indicadas
por ese reproductor. Los tiempos corresponden exclusivamente a la ejecución
histórica anual; ese benchmark no se repitió para el modelo normalizado. El informe
`performance_real_2025.md` conserva mediciones históricas, no resultados nuevos.
Las pruebas pequeñas no acreditan volumen, 3FN final ni mejora de un índice.
