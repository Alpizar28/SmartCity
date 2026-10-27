"""Prueba el lote real de Madrid en PostgreSQL local y elimina su contenedor."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone


sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[2]
RESEARCH = PROJECT / "research/datasets"
PRIVATE = RESEARCH / "private_results/expanded-2025"
RESULTS = RESEARCH / "results/expanded-2025"
TABLES = (
    "sources", "source_versions", "zones", "locations", "stations",
    "sensor_categories", "measurement_types", "channels", "observations",
    "sensors", "organizations", "users",
)


def run_docker(arguments, input_text=None, timeout=3600):
    completed = subprocess.run(
        ["docker", *arguments], input=input_text, text=True,
        capture_output=True, timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError("Falló Docker/PostgreSQL: " + completed.stderr[-2500:])
    for line in completed.stderr.splitlines():
        if "RESULTADO:" in line:
            print(line)
    return completed.stdout.strip()


def check_input_files(preparation):
    if preparation["generation"] != "expanded-2025":
        raise ValueError("No corresponde a la generación expanded-2025")
    if preparation["configuration"]["contract"] != "madrid-draft-v1":
        raise ValueError("El contrato del lote es diferente")
    if preparation["accepted"] != 1076813:
        raise ValueError("El manifiesto declara otro total")
    for filename, expected in preparation["output_hashes"].items():
        path = PRIVATE / filename
        if not path.is_file() or path.stat().st_size != preparation["output_bytes"][filename]:
            raise ValueError("Falta un archivo o su tamaño cambió: " + filename)
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError("Hash distinto del manifiesto: " + filename)


def read_queries(path=None):
    """Read the ten canonical smartcity SELECTs, never the staging demo."""
    queries = {}
    number = None
    lines = []
    path = PROJECT / "sprint1/postgres/queries.sql" if path is None else Path(path)
    for line in path.read_text().splitlines():
        match = re.match(r"^-- (PG\d{2}):", line)
        if match:
            if number is not None:
                raise ValueError("Consulta sin punto y coma: " + number)
            number = match.group(1)
            if number in queries:
                raise ValueError("Consulta duplicada: " + number)
            lines = []
            continue
        if number is None or line.lstrip().startswith("--"):
            continue
        lines.append(line)
        if line.rstrip().endswith(";"):
            statement = "\n".join(lines).strip().removesuffix(";")
            if not re.match(r"^(SELECT|WITH)\b", statement, re.IGNORECASE):
                raise ValueError("Se esperaba una consulta SELECT/CTE: " + number)
            queries[number] = statement
            number = None
    if number is not None:
        raise ValueError("Consulta sin punto y coma: " + number)
    if sorted(queries) != [f"PG{index:02d}" for index in range(1, 11)]:
        raise ValueError("Falta alguna consulta PG01–PG10")
    return queries


def load_catalogs(sql, catalogs):
    # Se usan el mismo orden y columnas que el cargador de JP.
    def insert_rows(table, rows, types):
        columns = ",".join(item.split()[0] for item in types.split(","))
        literal = json.dumps(rows, ensure_ascii=False, allow_nan=False).replace("'", "''")
        sql(
            f"INSERT INTO smartcity.{table} ({columns}) "
            f"SELECT {columns} FROM json_to_recordset('{literal}') "
            f"AS records({types});"
        )

    insert_rows("sources", list(catalogs["sources"].values()),
                "source_id text,name text,publisher text")
    insert_rows("source_versions", list(catalogs["source_versions"].values()),
                "source_version text,source_id text,original_path text")
    insert_rows("zones", list(catalogs["zones"].values()),
                "zone_id text,name text,level text")

    sys.path.insert(0, str(RESEARCH / "scripts"))
    from phase5_contract import stable_id

    locations = []
    stations = []
    for station in catalogs["stations"].values():
        location_id = stable_id("location", station["station_id"], "current-inventory")
        locations.append({
            **station, "location_id": location_id,
            "inventory_version": station["inventory_reference"]["sha256"]
            if station.get("inventory_reference") else None,
        })
        stations.append({**station, "location_id": location_id})
    insert_rows("locations", locations,
                "location_id text,zone_id text,name text,latitude double precision,"
                "longitude double precision,coordinate_crs text,"
                "historical_location_verified boolean,inventory_version text")
    insert_rows("stations", stations,
                "station_id text,source_id text,source_key text,name text,"
                "location_id text,inventory_present boolean")

    measurement_types = list(catalogs["measurement_types"].values())
    insert_rows("sensor_categories", measurement_types, "category_id text,name text")
    insert_rows("measurement_types", measurement_types,
                "measurement_type text,source_id text,code text,category_id text,"
                "unit text,candidate_unit text,unit_status text")
    insert_rows("channels", list(catalogs["channels"].values()),
                "channel_id text,station_id text,source_id text,sensor_id text,"
                "source_key jsonb,measurement_type text,catalog_basis text")


def check_real_results(sql, preparation, catalogs):
    table_counts = {
        table: int(sql(f"SELECT COUNT(*) FROM smartcity.{table};")) for table in TABLES
    }
    for table in ("sources", "source_versions", "zones", "stations",
                  "measurement_types", "channels"):
        if table_counts[table] != len(catalogs[table]):
            raise ValueError("El catálogo no coincide: " + table)
    if table_counts["sensor_categories"] != len(catalogs["measurement_types"]):
        raise ValueError("Faltan categorías de los tipos de medición")
    if table_counts["locations"] != len(catalogs["stations"]):
        raise ValueError("Faltan ubicaciones del catálogo")
    if table_counts["observations"] != preparation["accepted"]:
        raise ValueError("No se cargó el lote completo")
    if any(table_counts[table] for table in ("sensors", "organizations", "users")):
        raise ValueError("Se poblaron tablas administrativas sin evidencia real")
    if int(sql("SELECT COUNT(*) FROM smartcity_demo.entities;")) != 0:
        raise ValueError("La demostración sintética entró en esta carga")

    source_counts = json.loads(sql(
        "SELECT json_object_agg(source_id, amount) FROM "
        "(SELECT source_id, COUNT(*) AS amount FROM smartcity.observations "
        "GROUP BY source_id) AS source_totals;"
    ))
    if source_counts != {"MAD-AIR": preparation["accepted"]}:
        raise ValueError("Fuente o cantidad incorrecta")
    monthly_counts = json.loads(sql(
        "SELECT json_object_agg(source_month, amount) FROM "
        "(SELECT LEFT(source_key->>3, 7) AS source_month, COUNT(*) AS amount "
        "FROM smartcity.observations GROUP BY LEFT(source_key->>3, 7)) AS month_totals;"
    ))
    if monthly_counts != {
        month: detail["accepted"] for month, detail in preparation["by_month"].items()
    }:
        raise ValueError("Conteos mensuales distintos del manifiesto")

    sql((PROJECT / "tests/sprint1/test_real_data.sql").read_text())
    queries = read_queries()
    rows = {}
    for number, statement in queries.items():
        rows[number] = int(sql(f"SELECT COUNT(*) FROM ({statement}) AS query_results;"))
    if any(rows[f"PG{number:02d}"] != 0 for number in range(1, 9)):
        raise ValueError("Hay resultados físicos sin sensores en el dataset")
    if rows["PG09"] < 1 or rows["PG10"] != table_counts["stations"]:
        raise ValueError("Resultado de vista o función inconsistente")

    first_channel = json.loads((RESEARCH / "results/unified-v1/sample_reference.json").read_text())["first_channel"]
    readings = int(sql(
        "SELECT readings FROM smartcity.channel_activity "
        f"WHERE channel_id = '{first_channel}';"
    ))
    direct_count = int(sql(
        "SELECT COUNT(*) FROM smartcity.observations "
        f"WHERE channel_id = '{first_channel}';"
    ))
    if readings < 1 or readings != direct_count:
        raise ValueError("La vista no coincide con el canal real")
    return table_counts, source_counts, monthly_counts, rows, first_channel, readings


def main():
    started_at = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true",
                        help="Mide consultas después de la validación real")
    options = parser.parse_args()
    preparation = json.loads((RESULTS / "preparation.json").read_text())
    check_input_files(preparation)
    read_queries()
    catalogs = json.loads((PRIVATE / "catalogs.json").read_text())
    run_docker(["image", "inspect", "postgres:16-alpine"])
    name = "smartcity-sprint1-real-" + uuid.uuid4().hex[:12]
    created = False
    owned_volumes = []
    try:
        run_docker([
            "run", "--detach", "--rm", "--pull=never", "--name", name,
            "--network", "none", "--memory=3g", "--cpus=2",
            "--mount", f"type=bind,src={PRIVATE.resolve()},dst=/inputs,readonly",
            "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "postgres:16-alpine",
        ])
        created = True
        mounts = json.loads(run_docker(["inspect", name, "--format", "{{json .Mounts}}"] ))
        owned_volumes = [mount["Name"] for mount in mounts if mount["Type"] == "volume"]
        for attempt in range(120):
            ready = subprocess.run(["docker", "exec", name, "pg_isready", "-U", "postgres"],
                                   capture_output=True, timeout=10)
            if ready.returncode == 0 and "init process complete" in run_docker(["logs", name]):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("PostgreSQL local no inició")

        def sql(statement):
            return run_docker(
                ["exec", "-i", name, "psql", "-X", "-Atq", "-U", "postgres",
                 "-v", "ON_ERROR_STOP=1"],
                input_text="SET statement_timeout='50min'; SET timezone='UTC'; " + statement,
            )

        version = sql("SELECT version();").splitlines()[-1]
        sql((RESEARCH / "scripts/phase5_postgresql.sql").read_text())
        sql((PROJECT / "tests/sprint1/test_schema.sql").read_text())
        sql((PROJECT / "tests/sprint1/test_queries.sql").read_text())
        load_catalogs(sql, catalogs)
        sql("CREATE UNLOGGED TABLE smartcity.import_stage (doc jsonb NOT NULL);")

        started = time.monotonic()
        run_docker(
            ["exec", "-i", name, "psql", "-X", "-Atq", "-U", "postgres",
             "-v", "ON_ERROR_STOP=1"],
            input_text="\\copy smartcity.import_stage FROM '/inputs/accepted.extjsonl' "
                       "WITH (FORMAT csv, DELIMITER E'\\x02', QUOTE E'\\x01');\n",
        )
        stage_seconds = round(time.monotonic() - started, 2)
        if int(sql("SELECT COUNT(*) FROM smartcity.import_stage;")) != preparation["accepted"]:
            raise ValueError("Staging no contiene el lote completo")

        started = time.monotonic()
        sql(
            "INSERT INTO smartcity.observations SELECT "
            "(jsonb_populate_record(NULL::smartcity.observations, "
            "doc || jsonb_build_object('observed_at', doc->'observed_at'->>'$date'))).* "
            "FROM smartcity.import_stage; ANALYZE smartcity.observations;"
        )
        import_seconds = round(time.monotonic() - started, 2)
        table_counts, source_counts, monthly_counts, rows, channel, readings = (
            check_real_results(sql, preparation, catalogs)
        )
        print("VALIDACION_REAL=" + json.dumps({
            "generation": "expanded-2025", "contract": "madrid-draft-v1",
            "tested_at_utc": datetime.now(timezone.utc).isoformat(),
            "postgresql_version": version, "real_observations": table_counts["observations"],
            "catalog_and_table_counts": table_counts, "sources": source_counts,
            "months": monthly_counts, "query_rows": rows,
            "pg09_checked_channel": channel, "pg09_channel_readings": readings,
            "stage_seconds": stage_seconds, "import_seconds": import_seconds,
            "verification_seconds": round(time.monotonic() - started_at, 2),
            "schema_checks": 9, "controlled_checks": 14, "real_data_checks": 11,
            "pg01_to_pg08": "empty: no accredited physical sensors",
            "pg09": "real channel readings", "pg10": "function counts channels, not sensors",
        }, ensure_ascii=False), flush=True)
        if options.benchmark:
            from benchmark_real_postgres import run_benchmarks

            benchmark = run_benchmarks(
                sql, read_queries(), channel, PROJECT / "sprint1/postgres/queries.sql"
            )
            print("BENCHMARK_REAL=" + json.dumps(benchmark, ensure_ascii=False), flush=True)
    finally:
        if created:
            subprocess.run(["docker", "stop", "--time", "60", name],
                           capture_output=True, text=True, timeout=120)
            subprocess.run(["docker", "rm", "--volumes", name],
                           capture_output=True, text=True, timeout=60)
            if subprocess.run(["docker", "inspect", name], capture_output=True).returncode == 0:
                raise RuntimeError("El contenedor temporal no se eliminó")
            for volume in owned_volumes:
                if subprocess.run(["docker", "volume", "inspect", volume],
                                  capture_output=True).returncode == 0:
                    run_docker(["volume", "rm", volume])


if __name__ == "__main__":
    main()
