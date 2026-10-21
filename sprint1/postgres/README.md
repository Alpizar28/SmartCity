# PostgreSQL: propuesta local revisable

`schema_proposal.sql`, `queries.sql` y `staging.sql` **no son migraciones definitivas**.
Sí se ejecutaron en PostgreSQL 16.6 desechable con tres ejemplos publicados,
mediante `scripts/test_sprint1_engines.py`. No están conectados a Compose ni a
`postgres/init/`; no hay despliegue compartido ni carga masiva.

## Alcance de consultas

| Consulta | Implementación propuesta | Límite |
|---|---|---|
| PG01/02/05/07 | Consultas por canal/sitio | Parciales; no sensores físicos ni inventario independiente |
| PG03/04/06 | Ninguna | Estado, organismos e instalación no acreditados |
| PG08 | Ninguna | Geografía/vigencia abiertas |
| PG09 | `quality_summary` | Vista comprobada con tres lecturas locales |
| PG10 | `air_statistics` | Canal+snapshot, aire válido, intervalo UTC semiabierto |

Fuentes, versiones, estaciones y canales se separan para evitar duplicar sus
atributos en cada lectura. Las FK compuestas impiden mezclar redes/snapshots.
El documento JSONB conserva procedencia, payload y campos abiertos; no sustituye
los catálogos. No se declara una demostración académica completa de 3FN,
particionamiento, vistas materializadas ni rendimiento.

## Frontera de validación

Antes de cualquier futura escritura debe ejecutarse `validate_document` con
catálogos explícitos. Las columnas SQL son una proyección del documento validado:
`ReadingDTO.postgres_record()` genera una proyección consistente, pero todavía
`stage_reading(record jsonb)` ofrece la escritura/reconciliación del lado SQL.
Existe un CLI básico en `basico/cargar_postgres.py`, sin importación masiva;
su conexión mediante psycopg todavía no se probó de extremo a extremo. Los checks SQL son
defensa adicional, no un reemplazo del
validador. El DTO convierte Extended JSON a `datetime` UTC; la futura capa debe
envolver los objetos JSONB con el tipo del driver y enlazar todos los parámetros.
El ID autogenerado solo localiza staging. La unicidad usa snapshot/canal/clave
original, nunca UTC hipotético, valor o fila. Una colisión contradictoria debe
cuarentenarse; queda prohibido sobrescribirla con un upsert.

Los índices cubren FK/filtros y el tiempo de aire exclusivamente. Su efectividad
requiere futuros `EXPLAIN (ANALYZE, BUFFERS)` con datos reales autorizados.
`air_statistics` recibe parámetros; no construir SQL concatenando entradas.

`stage_reading` usa unicidad snapshot/canal/clave original y `ON CONFLICT DO
NOTHING`, nunca `DO UPDATE`. Repite como `duplicate` o guarda el documento en
cuarentena sin modificar la lectura aceptada. Las lecturas deben ser append-only.
Usar transacciones READ COMMITTED; a mayor aislamiento, reintentar errores de
serialización en la futura capa cliente. Se comprobó una carrera de ocho
conexiones y dos payloads para una clave, no estrés sostenido. También se verificó
respaldo/restauración de datos, esquema y secuencias; véase [respaldos](../RESPALDOS.md).
`inventory_present` permite NULL porque los ejemplos públicos no acreditan
presencia en un inventario independiente; desconocido no equivale a falso.
