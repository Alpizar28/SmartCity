# SmartCity

Proyecto de CE3101 Bases de Datos (TEC): aire y tráfico de Madrid en PostgreSQL y MongoDB. `final/` añade HDFS, Spark y un panel.

## Carpetas

- `final/`: Sprint 2. Se opera con `python -m final.manage` (`up`, `status`, `stop`, `upload`, `batch`, `spark`). Dependencias en `final/requirements.txt`. Panel: `streamlit run final/dashboard.py` desde la raíz.
- `sprint1/postgres/`: esquema (`schema_v2_3nf.sql`) y consultas (`queries_v2_3nf.sql`).
- `sprint1/basico/`: `preparar_v2.py` (enero 2025) y scripts de MongoDB (`cargar_mongodb_v2.js`, `consultas_mongodb_v2.js`, `crud_mongodb.js`).
- `compose.yaml`: PostgreSQL y MongoDB locales del Sprint 1. Copiar `.env.example` a `.env` y ejecutar `docker compose up -d`.

Los datos grandes no van en git (`data/`, `raw/`, `private_results/`).

## Ejecutar Sprint 2 desde cero

Ejecutá desde la raíz, con Docker Compose y un entorno Python activo. Usá una carga
nueva: los comandos no sobrescriben generaciones ni informes existentes.

```bash
python -m pip install -r final/requirements.txt
ZIP=data/releases/SmartCity_DATASET_COMPLETO_PRIVADO.zip
V2=research/datasets/private_results/expanded-v2-2025-01
unzip -n "$ZIP" "$V2/*"
mkdir -p data/reportes-local

python -m final.manage up
python -m final.manage status
python -m final.prepare --archive "$ZIP" --v2 "$V2" --output data/final
python -m final.manage upload --report data/reportes-local/upload.json
python -m final.manage batch --report data/reportes-local/batch.json
python -m final.manage batch-activity --report data/reportes-local/batch-activity.json
python -m final.manage spark --report data/reportes-local/spark.json
python -m final.postgres
python -m final.mongo init --report data/reportes-local/mongo-init.json
python -m final.postgres_normalized
python -m final.mongo load --report data/reportes-local/mongo.json
python -m final.mongo load-incidents --report data/reportes-local/incidents.json
python -m final.mongo_queries
python -m final.verify --report data/reportes-local/verify.json
streamlit run final/dashboard.py
```
