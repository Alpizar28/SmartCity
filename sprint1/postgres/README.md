# PostgreSQL — ruta canónica del Sprint 1

## Cierre para revisión del equipo

- [Auditoría formal 3FN de las doce tablas](normalizacion_3fn.md): excepciones
  reales en `channels` y `observations`; no se modificó el DDL común.
- [PG07: prueba exacta y límite de evidencia física](pg07_limite_evidencia.md).
- [Matriz PG01–PG10, muestras y trazabilidad SQL](evidencia_final_postgresql.md).
- [Reproducción y prerrequisitos reales](reproduccion_cierre.md).
- [Tres reportes acotados verificables](evidencias/README.md).

V2 prioritaria: `contract_v2.sql` se aplica únicamente después del DDL común
en una base local nueva. No sumar sus lecturas de enero a la carga anual v1.
El encabezado v1 del SQL canónico conserva su identidad histórica; los diez
SELECT también se ejecutaron con el contrato v2 sin cambiar sus bytes.

## Qué archivo usar

- **DDL común:** `research/datasets/scripts/phase5_postgresql.sql`, esquema `smartcity`.
- **Diez consultas de entrega:** `sprint1/postgres/queries.sql`, PG01–PG10.
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
por ese reproductor; no se ha reejecutado para este arreglo. El informe
`performance_real_2025.md` conserva mediciones históricas, no resultados nuevos.
Las pruebas pequeñas no acreditan volumen, 3FN final ni mejora de un índice.
