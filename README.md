# SmartCity Analytics

Proyecto académico SmartCity Analytics: investigación, preparación y análisis de datos urbanos para justificar el uso de PostgreSQL, MongoDB, Hadoop/HDFS y Apache Spark en CE-3191 Base de Datos. La identificación administrativa del curso debe confirmarse: el nombre del enunciado PDF dice CE3101.

**Estado real:** fases 0–5 de investigación y preparación documentadas; Fase 6 organiza la documentación. Madrid es una **recomendación condicionada**, pendiente de ratificación del equipo y decisiones docentes. Hay diseños preliminares y pruebas nativas locales desechables, no modelos definitivos ni cargas en las bases compartidas. Hadoop, Spark y Streamlit/dashboard **no están implementados**.

## Navegación

- [Documentación por temática](docs/README.md) y [texto listo para el informe](docs/academico/texto_para_informe.md).
- [Selección de Madrid](docs/datasets/seleccion_dataset.md), [fuentes y licencias](docs/datasets/fuentes_y_procedencia.md), [calidad y límites](docs/datasets/calidad_y_limitaciones.md).
- [Modelos preliminares](docs/arquitectura/modelos.md), [diagramas Mermaid](docs/arquitectura/diagramas.md) y [pipeline/reproducción](docs/arquitectura/pipeline.md).
- [Guía del equipo](docs/equipo/guia_integrantes.md), [preguntas al profesor](docs/equipo/preguntas_profesor.md) y [ADR condicionado](docs/decisiones/ADR-001-madrid.md).
- [Índice de evidencias de fases 0–5](docs/datasets/indice_evidencias.md). El [README de investigación](research/datasets/README.md) conserva su estado histórico de fases 0–1, no el estado actual.

## Arquitectura y organización

Originales inmutables → validación → normalización temporal → IDs deterministas → catálogos compartidos → PostgreSQL y MongoDB → exportaciones posteriores CSV/Parquet. El esquema relacional separa sitio, dispositivo físico, canal y observación; MongoDB mantiene un documento por intervalo multivariable de tráfico. No hay FK ni transacción automática entre motores.

El núcleo propuesto es enero de 2025: **832.668 observaciones estructuralmente elegibles**, no una carga definitiva. Véanse los [conteos y su evidencia](docs/datasets/calidad_y_limitaciones.md). Accidentes de 2026 y energía mensual permanecen separados.

| Ruta | Uso actual |
|---|---|
| `postgres/init/` | Reservada y sin scripts de inicialización; conservar estructura |
| `mongodb/init/` | Reservada y sin scripts de inicialización; conservar estructura |
| `data/` | Datos locales ignorados salvo marcador `.gitkeep` |
| `research/datasets/` | Investigación histórica, scripts, pruebas y evidencia técnica |
| `docs/` | Documentación académica, arquitectura, decisiones y handoff |

Los scripts preliminares están en [DDL PostgreSQL](research/datasets/scripts/phase5_postgresql.sql), [consultas SQL](research/datasets/scripts/phase5_postgresql_queries.sql) y [prueba MongoDB/CRUD/agregaciones](research/datasets/scripts/phase5_mongo_test.js). **No copiarlos a `init/` ni ejecutarlos sobre bases compartidas sin revisión y autorización.** No crear una carpeta duplicada `postgresql/`.

## Infraestructura local existente

Las instrucciones originales se conservan abajo. Ejecutarlas solo en un equipo de desarrollo autorizado, nunca en el servidor compartido desde esta fase. Compose inicia únicamente PostgreSQL y MongoDB; no aplica los diseños de investigación. `compose.yaml` no monta actualmente las carpetas `init/`.

## Requirements

- Docker Desktop (Windows) or Docker Engine with Docker Compose v2 (Linux)
- A local `.env` file created from `.env.example`

The pinned official images are multi-architecture and work on both `amd64` and `arm64`:

- PostgreSQL: `postgres:16.6-alpine`
- MongoDB: `mongo:7.0.16`

## Start

```bash
if [ ! -e .env ]; then cp .env.example .env; fi
# Edit .env and replace all passwords before running the stack.
docker compose up -d
```

PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env and replace all passwords before running the stack.
docker compose up -d
```

Validate the Compose configuration before starting it:

```bash
docker compose config
```

Check service health:

```bash
docker compose ps
docker compose logs postgres mongodb
```

Stop the local stack while preserving database data:

```bash
docker compose down
```

To remove persistent local development data deliberately:

**Destructivo: únicamente para datos locales propios y con autorización explícita. Nunca usar sobre volúmenes compartidos.**

```bash
docker compose down -v
```

## Configuration

All credentials and host ports come from `.env`, which is ignored by Git. `POSTGRES_PORT` defaults to `5433` to avoid a common local PostgreSQL collision; `MONGODB_PORT` defaults to `27017`.

Both databases use named Docker volumes (`postgres_data` and `mongodb_data`) and share the isolated `smartcity-network` bridge network. The `data/` directory is reserved for local datasets later in the project and is ignored except for its `.gitkeep` marker.

The services have a 512 MiB memory limit and a 0.25 CPU limit each, plus healthchecks. Initialization directories are intentionally empty in this phase:

- `postgres/init/`
- `mongodb/init/`

Do not add models, schemas, seed data, or initialization scripts until the data-design phase.

## Reproducción de la investigación y pruebas

Desde la raíz, con el entorno aislado existente y los snapshots locales autorizados:

```bash
cd research/datasets
.venv/bin/python scripts/phase5_prepare.py --dry-run
.venv/bin/python -m pytest tests -q --junitxml=results/phase6/tests.xml
.venv/bin/python scripts/phase6_validate_docs.py
```

Las 82 pruebas de fases 0–5 incluyen validación de datos locales y resultados nativos guardados; **no lanzan motores ni reemplazan una nueva corrida nativa**. Un clon no incluye `raw/`, `private_results/`, PDFs originales ni sus transcripciones completas: las pruebas de evidencia necesitan esos insumos. La [guía de reproducción](docs/arquitectura/pipeline.md) explica dependencias, temporales exclusivos, limitaciones del clon y comandos nativos opcionales; no descarga automáticamente datasets ni imágenes.

## Entorno compartido y colaboración segura

El servidor compartido de Coolify y el acceso privado por Tailscale están descritos por el usuario y el plan del equipo, **no verificados remotamente en estas fases**. Solicitar credenciales al administrador por un canal privado; no publicarlas en Git, capturas ni logs. No se conocen aquí reglas de redeploy, rama monitorizada ni configuración efectiva del panel. Un futuro push o merge debe coordinarse con José antes de publicarse.

Para colaborar: revisar la [guía de integrantes](docs/equipo/guia_integrantes.md), trabajar en ramas propias, conservar las fases históricas y enlazar cada afirmación a su evidencia. Revisar `git status`, el diff, [.gitignore](.gitignore) y los [controles de publicación](docs/equipo/revision_repositorio.md) antes de seleccionar archivos; no usar `git add .` sin auditoría.

Pendientes: aprobación conjunta/docente, unidades y relojes de meteorología/tráfico, CRS y geografía histórica, identidad física/instalación/estado/responsables, usuarios consentidos, MG04/MG05/MG08, mínimos cargados en el contrato aceptado, respaldo/restauración, ejecución distribuida y dashboard. La documentación de esta fase no autoriza despliegues, síntesis masiva ni implementación definitiva.
