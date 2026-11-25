"""Carga y consultas PG01–PG10 en una base separada del laboratorio local."""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import sys

from psycopg.errors import DuplicateDatabase
from psycopg.rows import dict_row

from final.postgres import connection

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / 'research/datasets/private_results/expanded-v2-2025-01'
TITLES = {
    'PG01': 'Sensores por tipo',
    'PG02': 'Sensores por ubicación',
    'PG03': 'Sensores activos e inactivos',
    'PG04': 'Sensores por organismo',
    'PG05': 'Ubicaciones con más sensores',
    'PG06': 'Sensores instalados por año',
    'PG07': 'Sensores sin actividad registrada',
    'PG08': 'Ranking de zonas monitoreadas',
    'PG09': 'Actividad por canal (vista SQL)',
    'PG10': 'Canales por estación (función SQL)',
}


@lru_cache(maxsize=1)
def normalized_tools():
    # El validador de Sprint 1 también se ejecuta como script independiente.
    scripts = str(ROOT / 'scripts')
    if scripts not in sys.path:
        sys.path.append(scripts)
    from scripts import validar_postgresql_3nf

    return validar_postgresql_3nf


@lru_cache(maxsize=1)
def statements():
    tools = normalized_tools()
    return tools.read_queries(tools.QUERIES)


def load(v2):
    tools = normalized_tools()
    manifest = tools.verificar_paquete(v2)
    catalogs = json.loads((v2 / 'catalogs.json').read_text())
    admin = json.loads((v2 / 'administrative_seed.json').read_text())
    with connection(autocommit=True) as conn:
        try:
            conn.execute('CREATE DATABASE smartcity_normalized')
        except DuplicateDatabase:
            pass
    with connection(normalized=True) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('smartcity-normalized-v2'))")
        if conn.execute("SELECT to_regnamespace('smartcity')").fetchone()[0] is not None:
            raise ValueError('The normalized schema already exists; this loader does not overwrite it')
        _, begin, ddl = tools.DDL.read_text().partition('\nBEGIN;\n')
        ddl, commit, remainder = ddl.rpartition('\nCOMMIT;')
        if not begin or not commit or remainder.strip():
            raise ValueError('Unexpected normalized DDL transaction')
        conn.execute(ddl)
        conn.execute(tools.catalogs_sql(catalogs, admin))
        conn.execute('CREATE TEMP TABLE normalized_input(doc jsonb) ON COMMIT DROP')
        with (v2 / 'accepted.extjsonl').open('rb') as rows, conn.cursor() as cursor:
            with cursor.copy(r"COPY normalized_input FROM STDIN (FORMAT csv, DELIMITER E'\x02', QUOTE E'\x01')") as stream:
                for block in iter(lambda: rows.read(1024 * 1024), b''):
                    stream.write(block)
        inserted = conn.execute("""
            INSERT INTO smartcity.observations
            SELECT (jsonb_populate_record(NULL::smartcity.observations, doc ||
                jsonb_build_object('observed_at', doc->'observed_at'->>'$date',
                                   'raw_locator', (doc->'raw_reference')-'sha256'))).*
            FROM normalized_input
        """).rowcount
        if inserted != manifest['accepted']:
            raise ValueError('Normalized load count differs from the manifest')
        conn.execute('ANALYZE smartcity.observations')
    return inserted


def query(code):
    statement = statements()[code]
    with connection(readonly=True, normalized=True) as conn:
        conn.execute("SET LOCAL statement_timeout = '8s'")
        with conn.cursor(row_factory=dict_row) as cursor:
            return cursor.execute(statement).fetchall()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v2', type=Path, default=V2)
    args = parser.parse_args()
    print(f'Lecturas cargadas en smartcity_normalized: {load(args.v2):,}')
