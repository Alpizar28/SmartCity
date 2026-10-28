"""Semantic regressions for normalized v2; no database or private inputs."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('normalized_v2', ROOT / 'scripts/validar_postgresql_3nf.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class NormalizedModelTests(unittest.TestCase):
    def test_declared_dependencies_and_candidate_keys(self):
        result = model.check_dependencies()
        self.assertEqual(len(result['relations']), 14)
        self.assertTrue(all(r['third_normal_form'] for r in result['relations'].values()))

    def test_detects_partial_dependency_instead_of_assuming_keys_prove_3nf(self):
        # Add a genuine non-key determinant: station -> source in channels.
        content = json.loads((ROOT / 'sprint1/postgres/dependencias_3nf.json').read_text())
        content = copy.deepcopy(content)
        c = content['relations']['channels']
        c['attributes'].append('source_id')
        for key, dependent in c['dependencies']:
            dependent.append('source_id')
        c['dependencies'].append([['station_id'], ['source_id']])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'sprint1/postgres'
            target.mkdir(parents=True)
            (target / 'dependencias_3nf.json').write_text(json.dumps(content))
            previous = model.ROOT
            try:
                model.ROOT = Path(directory)
                with self.assertRaisesRegex(ValueError, '3NF violation: channels'):
                    model.check_dependencies()
            finally:
                model.ROOT = previous

    def test_detects_constant_attribute_dependency(self):
        content = json.loads((ROOT / 'sprint1/postgres/dependencias_3nf.json').read_text())
        c = content['relations']['observations']
        c['attributes'].append('schema_version')
        for key, dependent in c['dependencies']:
            dependent.append('schema_version')
        c['dependencies'].append([[], ['schema_version']])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'sprint1/postgres'
            target.mkdir(parents=True)
            (target / 'dependencias_3nf.json').write_text(json.dumps(content))
            previous = model.ROOT
            try:
                model.ROOT = Path(directory)
                with self.assertRaisesRegex(ValueError, '3NF violation: observations'):
                    model.check_dependencies()
            finally:
                model.ROOT = previous

    def test_district_dictionary_has_public_names_and_snapshot_scope(self):
        names = json.loads(model.DISTRICTS.read_text())
        self.assertEqual(set(names['names']), {f'madrid:district:{n}' for n in range(1, 22)})
        self.assertEqual(names['source_sha256'], '25a84e6af0b213d6194df7c378490ef9c68e0156c165e0761a0a6c7b7ae4e321')
        self.assertEqual(names['snapshot_year'], 2026)

    def test_type_query_is_independent_of_measured_variable(self):
        queries = model.read_queries(model.QUERIES)
        self.assertIn('smartcity.sensor_types', queries['PG01'])
        self.assertNotIn('measurement_types', queries['PG01'])
        self.assertIn('smartcity.channel_contract', queries['PG07'])
        self.assertIn('observed_at < TIMESTAMPTZ', queries['PG07'])

    def test_native_runner_has_no_tcp_or_shared_host_option(self):
        source = Path(model.__file__).read_text()
        self.assertIn("listen_addresses=''", source)
        self.assertIn("--auth-host=reject", source)
        # Only sampling is configurable; no host, port or DSN CLI is exposed.
        options = {
            arg.value
            for call in ast.walk(ast.parse(source))
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == 'add_argument'
            for arg in call.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        }
        self.assertEqual(options, {'--sample'})


class DiagramaNormalizadoTests(unittest.TestCase):
    """El lector está acotado al DDL actual, no es un parser SQL general."""

    def test_tablas_columnas_y_cardinalidades_coinciden_con_ddl(self):
        ddl = (ROOT / 'sprint1/postgres/schema_v2_3nf.sql').read_text()
        documento = (ROOT / 'docs/arquitectura/diagrama_3nf.md').read_text()
        mermaid = documento.split('```mermaid', 1)[1].split('```', 1)[0]
        tablas = dict(re.findall(r'CREATE TABLE (\w+)\s*\((.*?)\n?\);', ddl, re.S))
        entidades = dict(re.findall(r'^  (\w+) \{\n(.*?)^  \}', mermaid, re.M | re.S))
        self.assertEqual(set(tablas), set(entidades))
        self.assertEqual(len(tablas), 14)

        relaciones = set()
        for tabla, cuerpo in tablas.items():
            columnas = {}
            # Las comas dentro de CHECK/UNIQUE no separan columnas.
            nivel = 0
            inicio = 0
            partes = []
            for indice, caracter in enumerate(cuerpo):
                if caracter == '(':
                    nivel += 1
                elif caracter == ')':
                    nivel -= 1
                elif caracter == ',' and nivel == 0:
                    partes.append(cuerpo[inicio:indice].strip())
                    inicio = indice + 1
            partes.append(cuerpo[inicio:].strip())

            for parte in partes:
                if parte.startswith(('CHECK', 'UNIQUE')):
                    continue
                nombre = parte.split()[0]
                columnas[nombre] = parte
                referencia = re.search(r'REFERENCES (\w+)', parte)
                if referencia:
                    padre = referencia.group(1)
                    obligatorio = 'NOT NULL' in parte or 'PRIMARY KEY' in parte
                    extremo_padre = '||' if obligatorio else 'o|'
                    extremo_hijo = 'o|' if 'PRIMARY KEY' in parte else 'o{'
                    relaciones.add((padre, extremo_padre, extremo_hijo, tabla, nombre))

            atributos = set(re.findall(r'^    \w+ (\w+)', entidades[tabla], re.M))
            self.assertEqual(set(columnas), atributos, tabla)

        dibujadas = set(re.findall(
            r'^  (\w+) (\|\||o\|)\.\.(o\{|o\|) (\w+) : (\w+)$', mermaid, re.M
        ))
        self.assertEqual(len(relaciones), 17)
        self.assertEqual(relaciones, dibujadas)


class PostgresProposalTests(unittest.TestCase):
    """El esquema de práctica se comprueba aparte del modelo de entrega."""

    def test_proposal_has_composite_references_and_original_key_uniqueness(self):
        sql = (ROOT / 'sprint1/postgres/schema_proposal.sql').read_text()
        self.assertIn('FOREIGN KEY (source_version, source_id)', sql)
        self.assertIn('FOREIGN KEY (channel_id, source_id)', sql)
        self.assertIn('UNIQUE (source_version, channel_id, source_key)', sql)
        self.assertIn('GENERATED ALWAYS AS IDENTITY', sql)
        self.assertNotIn('UNIQUE (channel_id, observed_at)', sql)

    def test_function_is_snapshot_and_evidence_scoped(self):
        sql = (ROOT / 'sprint1/postgres/staging_queries.sql').read_text()
        self.assertIn('CREATE VIEW sprint1.quality_summary', sql)
        self.assertIn('CREATE FUNCTION sprint1.air_statistics', sql)
        self.assertIn('r.source_version = p_version', sql)
        self.assertIn("r.source_id = 'MAD-AIR'", sql)
        self.assertIn('r.observed_at < p_end', sql)
        self.assertIn('SET search_path = pg_catalog', sql)

    def test_init_directories_remain_empty(self):
        for engine in ('postgres', 'mongodb'):
            directory = ROOT / engine / 'init'
            if directory.exists():
                self.assertEqual(list(directory.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
