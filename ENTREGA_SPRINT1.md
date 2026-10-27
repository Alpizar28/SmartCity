# Sprint 1 — PostgreSQL y MongoDB

## Alcance

Primer avance del 28/10/2026: modelos, datos, índices, **10 consultas SQL y
10 MongoDB**, CRUD Mongo, vistas/funciones SQL, resultados y documentación.
El plan del equipo incluye dos fuentes y mínimos de 100.000 registros PostgreSQL
y 500.000 documentos MongoDB. Spark, Hadoop e interfaz quedan para noviembre.

La demostración que sigue es **parcial**: funciona con tres ejemplos, pero no
sustituye esos requisitos. El [estado](docs/equipo/ESTADO_SPRINT1.md) y la
[matriz de consultas](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md) indican lo pendiente.

## Ejecutar la demostración local

Desde la raíz, con Python 3.10+ y Node.js 18+:

```bash
bash scripts/validate_sprint1.sh
```

Para probar ambos motores se necesita Docker local y las imágenes
`postgres:16.6-alpine` y `mongo:7.0.16` ya descargadas:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_engines.py
```

Resultado esperado: `Sprint 1 disposable engines: PASS`. Crea y elimina solo
contenedores de prueba propios, sin puertos publicados ni bases persistentes.
El informe queda en `/tmp/opencode/smartcity-s1-integration-*.json`.

**Verificado el 27/10/2026:** 32 pruebas Python, 8 Node e integración PASS.
Se comprobaron consultas, índices, replay, cuarentena, CRUD, respaldo/restauración
y concurrencia PostgreSQL acotada. No prueba los clientes Python con autenticación real.

## Archivos para explicar en clase

- PostgreSQL: `sprint1/postgres/schema_proposal.sql`, `queries.sql` y `staging.sql`.
- MongoDB: `sprint1/mongodb/validator.js`, `indexes.js`, `queries.js` y `staging.js`.
- Ejemplos comentados y CRUD: [sprint1/basico](sprint1/basico/README.md).

Estos archivos usan el núcleo `sprint1`, no el esquema anual `smartcity`.
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
