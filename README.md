# SmartCity Analytics

Base reproducible infrastructure for the CE-3191 SmartCity Analytics project. This initial phase starts only PostgreSQL and MongoDB; it intentionally contains no data model, seed data, APIs, dashboards, Hadoop, Spark, or application services.

## Requirements

- Docker Desktop (Windows) or Docker Engine with Docker Compose v2 (Linux)
- A local `.env` file created from `.env.example`

The pinned official images are multi-architecture and work on both `amd64` and `arm64`:

- PostgreSQL: `postgres:16.6-alpine`
- MongoDB: `mongo:7.0.16`

## Start

```bash
cp .env.example .env
# Edit .env and replace all passwords before running the stack.
docker compose up -d
```

PowerShell:

```powershell
Copy-Item .env.example .env
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
