# SmartCity

Proyecto de CE3101 Bases de Datos (TEC): aire y tráfico de Madrid en PostgreSQL y MongoDB. `final/` añade HDFS, Spark y un panel.

## Carpetas

- `final/`: Sprint 2. Se opera con `python -m final.manage` (`up`, `status`, `stop`, `upload`, `batch`, `spark`). Dependencias en `final/requirements.txt`. Panel: `streamlit run final/dashboard.py` desde la raíz.
- `sprint1/postgres/`: esquema (`schema_v2_3nf.sql`) y consultas (`queries_v2_3nf.sql`).
- `sprint1/basico/`: `preparar_v2.py` (enero 2025) y scripts de MongoDB (`cargar_mongodb_v2.js`, `consultas_mongodb_v2.js`, `crud_mongodb.js`).
- `compose.yaml`: PostgreSQL y MongoDB locales del Sprint 1. Copiar `.env.example` a `.env` y ejecutar `docker compose up -d`.

Los datos grandes no van en git (`data/`, `raw/`, `private_results/`).
