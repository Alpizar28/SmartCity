# Sprint 1 — PostgreSQL y MongoDB

## Alcance

Primer avance del 28/10/2026: modelos, datos, índices, **10 consultas SQL y
10 MongoDB**, CRUD Mongo, vistas/funciones SQL, resultados y documentación.
El plan del equipo incluye dos fuentes y mínimos de 100.000 registros PostgreSQL
y 500.000 documentos MongoDB. Spark, Hadoop e interfaz quedan para noviembre.

La ruta siguiente prueba las diez consultas SQL con fixtures controladas y añade
una demostración complementaria SQL/Mongo de tres ejemplos. No sustituye todos
los requisitos. El [estado](docs/equipo/ESTADO_SPRINT1.md) y la
[matriz de consultas](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md) indican lo pendiente.

## Una entrada de ejecución

Desde la raíz, con Python 3.10+ y Node.js 18+:

```bash
bash scripts/validate_sprint1.sh
```

Para probar ambos motores se necesita Docker local y las imágenes
`postgres:16.6-alpine` y `mongo:7.0.16` ya descargadas:

```bash
bash scripts/validate_sprint1.sh --engines
```

El comando ejecuta, en orden: pruebas offline, diez consultas SQL canónicas
(`scripts/test_sprint1_sql.py`) e integración complementaria SQL/Mongo
(`scripts/test_sprint1_engines.py`). Deben aparecer `Sprint 1 canonical SQL: PASS`
y `Sprint 1 disposable engines: PASS`.

Solo crea y elimina contenedores propios, sin puertos ni bases persistentes.
Los informes nuevos quedan en `/tmp/opencode/smartcity-s1-sql-*.json` y
`/tmp/opencode/smartcity-s1-integration-*.json`; incluyen resultados, hashes y limpieza.

**Verificado el 27/10/2026:** 38 pruebas Python, 8 Node, las diez consultas SQL
con resultados esperados e integración SQL/Mongo PASS.
Se comprobaron consultas, índices, replay, cuarentena, CRUD, respaldo/restauración
y concurrencia PostgreSQL acotada. No prueba los clientes Python con autenticación real.

## Archivos para explicar en clase

- PostgreSQL canónico: DDL `research/datasets/scripts/phase5_postgresql.sql`
  y consultas `sprint1/postgres/queries.sql`, ambos para el esquema `smartcity`.
- SQL de práctica: `schema_proposal.sql`, `staging_queries.sql` y `staging.sql`
  dentro de `sprint1/postgres/`; solo para el esquema `sprint1`.
- MongoDB: `sprint1/mongodb/validator.js`, `indexes.js`, `queries.js` y `staging.js`.
- Ejemplos comentados y CRUD: [sprint1/basico](sprint1/basico/README.md).

PG07 evalúa enero de 2025 en Madrid y excluye sensores sin vínculo a un canal:
una relación desconocida no significa falta de actividad. La prueba incluye un
sensor con lectura en el inicio incluido y otro solo en el final excluido.
Su PASS con fixtures no acredita inventario físico ni cierra el bloqueo de datos anuales.

Para ejecutar el archivo completo manualmente en una base **local ya preparada**:

```bash
PGOPTIONS='-c default_transaction_read_only=on' \
psql -X --set=ON_ERROR_STOP=1 --single-transaction \
  --host=127.0.0.1 --port=5433 --username=smartcity \
  --dbname=smartcity --file=sprint1/postgres/queries.sql
```

El comando impone una transacción de solo lectura. El usuario, puerto y nombre de base deben corresponder
a tu configuración local; no pasar contraseñas en el comando. El DDL no se instala
automáticamente y no debe aplicarse a una base poblada.

Detalles de pruebas y respaldos: [integración](sprint1/INTEGRACION.md) y
[restauración](sprint1/RESPALDOS.md).

## Validación documental

Para la suite pública del repositorio, crear el entorno **en la raíz**:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r research/datasets/scripts/requirements.lock
./scripts/validate_repo.sh
```

La instalación requiere acceso al repositorio de paquetes. Esta suite no reproduce
las cargas anuales ni recupera snapshots privados. Para usar otro intérprete,
definir `PYTHON=/ruta/al/python` al ejecutar el validador.

## Evidencia anual, separada de la demostración

El [cierre anual](docs/equipo/CIERRE_VALIDACION_SPRINT1.md) registra 1.076.813
lecturas reales de aire por motor en contenedores locales desechables.
Su contrato es [madrid-draft-v1](docs/equipo/CONTRATO_UNIFICADO.md).
No acredita una segunda fuente aceptada, 20 consultas completas ni carga compartida.
