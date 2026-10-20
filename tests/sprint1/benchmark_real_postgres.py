"""Mide consultas de lectura sobre el PostgreSQL local ya cargado."""

import json
from pathlib import Path
import re
from statistics import median


def read_air_summary(path):
    lines = Path(path).read_text().splitlines()
    reading = False
    statement = []
    for line in lines:
        if line.startswith("-- Aire con unidad acreditada"):
            reading = True
            continue
        if reading and not line.lstrip().startswith("--"):
            statement.append(line)
            if line.rstrip().endswith(";"):
                return "\n".join(statement).strip().removesuffix(";")
    raise ValueError("No se encontró el resumen de aire")


def is_read_only(statement):
    return re.match(r"^(SELECT|WITH)\b", statement.lstrip(), re.IGNORECASE) is not None


def explain(sql, statement, analyze):
    if not is_read_only(statement):
        raise ValueError("EXPLAIN ANALYZE solo se permite sobre SELECT o WITH")
    options = "ANALYZE, BUFFERS, FORMAT JSON" if analyze else "FORMAT JSON"
    output = sql(
        "BEGIN; SET TRANSACTION READ ONLY; "
        f"EXPLAIN ({options}) {statement}; ROLLBACK;"
    )
    return json.loads(output)[0]


def plan_nodes(plan):
    nodes = [plan]
    for child in plan.get("Plans", []):
        nodes.extend(plan_nodes(child))
    return nodes


def index_catalog(sql):
    query = """
    SELECT COALESCE(json_agg(index_details), '[]'::json)
    FROM (
        SELECT
            table_info.relname AS table_name,
            index_info.relname AS index_name,
            access_method.amname AS index_method,
            index_properties.indisunique AS is_unique,
            COALESCE(index_constraint.contype::text, '') AS constraint_type,
            pg_get_indexdef(index_properties.indexrelid) AS definition,
            pg_relation_size(index_properties.indexrelid) AS size_bytes,
            COALESCE(index_usage.idx_scan, 0) AS scans
        FROM pg_catalog.pg_index AS index_properties
        INNER JOIN pg_catalog.pg_class AS index_info
            ON index_info.oid = index_properties.indexrelid
        INNER JOIN pg_catalog.pg_class AS table_info
            ON table_info.oid = index_properties.indrelid
        INNER JOIN pg_catalog.pg_namespace AS table_namespace
            ON table_namespace.oid = table_info.relnamespace
        INNER JOIN pg_catalog.pg_am AS access_method
            ON access_method.oid = index_info.relam
        LEFT JOIN pg_catalog.pg_constraint AS index_constraint
            ON index_constraint.conindid = index_properties.indexrelid
           AND index_constraint.contype IN ('p', 'u')
        LEFT JOIN pg_catalog.pg_stat_user_indexes AS index_usage
            ON index_usage.indexrelid = index_properties.indexrelid
        WHERE table_namespace.nspname = 'smartcity'
        ORDER BY table_info.relname, index_info.relname
    ) AS index_details;
    """
    return json.loads(sql(query))


def query_plans(sql, queries):
    plans = {}
    for number in range(1, 9):
        name = f"PG{number:02d}"
        plan = explain(sql, queries[name], analyze=False)["Plan"]
        nodes = plan_nodes(plan)
        plans[name] = {
            "representative": False,
            "reason": "La tabla de sensores físicos está vacía",
            "plan_nodes": [node["Node Type"] for node in nodes],
            "planned_indexes": sorted({node["Index Name"] for node in nodes
                                       if "Index Name" in node}),
        }
    return plans


def representative_queries(queries, first_channel, queries_path):
    if not re.fullmatch(r"channel:[0-9a-f]{64}", first_channel):
        raise ValueError("El ID del canal de referencia no es válido")
    first_day = "2025-06-01 00:00:00+00"
    next_day = "2025-06-02 00:00:00+00"
    week_start = "2025-01-01 00:00:00+00"
    week_end = "2025-01-08 00:00:00+00"
    return {
        "PG09": queries["PG09"],
        "PG10": queries["PG10"],
        "channel_filter": (
            "SELECT measurement_id, observed_at, value "
            "FROM smartcity.observations "
            f"WHERE channel_id = '{first_channel}' "
            "ORDER BY observed_at DESC LIMIT 20"
        ),
        "time_filter": (
            "SELECT COUNT(*) FROM smartcity.observations "
            f"WHERE observed_at >= TIMESTAMPTZ '{first_day}' "
            f"AND observed_at < TIMESTAMPTZ '{next_day}'"
        ),
        "channel_time_filter": (
            "SELECT COUNT(*) FROM smartcity.observations "
            f"WHERE channel_id = '{first_channel}' "
            f"AND observed_at >= TIMESTAMPTZ '{week_start}' "
            f"AND observed_at < TIMESTAMPTZ '{week_end}'"
        ),
        "group_by_channel": (
            "SELECT channel_id, COUNT(*) AS reading_count "
            "FROM smartcity.observations GROUP BY channel_id "
            "ORDER BY reading_count DESC LIMIT 10"
        ),
        "air_quality": read_air_summary(queries_path),
    }


def measure(sql, name, statement):
    try:
        warmup = explain(sql, statement, analyze=True)
        # Las consultas costosas se repiten menos, sin inventar un promedio.
        repetitions = 3 if warmup["Execution Time"] < 8000 else 1
        if warmup["Execution Time"] > 15000:
            repetitions = 0
        measured = [explain(sql, statement, analyze=True) for _ in range(repetitions)]
    except Exception as error:
        print("Falló la medición de", name, ":", error)
        try:
            print("Plan sin ejecutar:", explain(sql, statement, analyze=False)["Plan"])
        except Exception as plan_error:
            print("No se pudo inspeccionar el plan:", plan_error)
        raise
    selected = measured[-1] if measured else warmup
    nodes = plan_nodes(selected["Plan"])
    execution_times = [run["Execution Time"] for run in measured]
    return {
        "warmup_ms": warmup["Execution Time"],
        "execution_ms": execution_times,
        "planning_ms": [run["Planning Time"] for run in measured],
        "median_ms": median(execution_times) if execution_times else None,
        "minimum_ms": min(execution_times) if execution_times else None,
        "maximum_ms": max(execution_times) if execution_times else None,
        "warmup_only": not bool(execution_times),
        "root_node": selected["Plan"]["Node Type"],
        "estimated_rows": selected["Plan"].get("Plan Rows"),
        "actual_rows": selected["Plan"].get("Actual Rows"),
        "shared_hit_blocks": selected["Plan"].get("Shared Hit Blocks", 0),
        "shared_read_blocks": selected["Plan"].get("Shared Read Blocks", 0),
        "nodes": [node["Node Type"] for node in nodes],
        "indexes": sorted({node["Index Name"] for node in nodes
                           if "Index Name" in node}),
        "sequential_scans": sorted({node.get("Relation Name", "") for node in nodes
                                    if node["Node Type"] == "Seq Scan"}),
    }


def run_benchmarks(sql, queries, first_channel, queries_path):
    results = {"indexes_before": index_catalog(sql),
               "nonrepresentative": query_plans(sql, queries),
               "measured": {}}
    for name, statement in representative_queries(queries, first_channel, queries_path).items():
        results["measured"][name] = measure(sql, name, statement)
    results["indexes_after"] = index_catalog(sql)
    return results
