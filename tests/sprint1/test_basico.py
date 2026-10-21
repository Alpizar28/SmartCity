"""Pruebas sencillas, sin drivers ni bases, para los scripts de estudiante."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

from test_contract import examples
from sprint1.basico.archivos import documento_mongo, leer_entrada, leer_json, registro_postgres
from sprint1.basico.cargar_mongodb import comprobar_coleccion, guardar_lectura
from sprint1.basico.cargar_postgres import guardar_lecturas
from sprint1.core.adapters import ReadingDTO

ROOT = Path(__file__).resolve().parents[2]


class ErrorDuplicado(Exception):
    pass


class PruebasBasicas(unittest.TestCase):
    def setUp(self):
        self.lecturas, self.catalogos = examples()

    def test_conversion_mongo_coincide_con_adaptador_probado(self):
        for lectura in self.lecturas:
            copia = deepcopy(lectura)
            self.assertEqual(documento_mongo(lectura), ReadingDTO(lectura, self.catalogos).mongo_document())
            self.assertEqual(lectura, copia)

    def test_conversion_postgres_mantiene_documento_y_fechas(self):
        for lectura in self.lecturas:
            registro = registro_postgres(lectura)
            self.assertEqual(registro['document'], lectura)
            self.assertEqual(registro['original_time'], lectura['original_time'])
            self.assertEqual(registro['observed_at'], lectura['observed_at']['$date'])

    def test_json_y_catalogos_validos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            datos = Path(carpeta) / 'lecturas.json'
            catalogos = Path(carpeta) / 'catalogos.json'
            datos.write_text(json.dumps(self.lecturas))
            catalogos.write_text(json.dumps(self.catalogos))
            self.assertEqual(leer_entrada(datos, catalogos), (self.lecturas, self.catalogos))
            datos.write_text('[]')
            with self.assertRaises(ValueError):
                leer_entrada(datos, catalogos)
            datos.write_text(json.dumps(self.lecturas))
            catalogos.write_text('{}')
            with self.assertRaises(ValueError):
                leer_entrada(datos, catalogos)

    def test_limite_archivo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'grande.json'
            ruta.write_bytes(b' ' * (5 * 1024 * 1024 + 1))
            with self.assertRaises(ValueError):
                leer_json(ruta)

    def test_cli_por_defecto_no_necesita_drivers_ni_conecta(self):
        with tempfile.TemporaryDirectory() as carpeta:
            datos = Path(carpeta) / 'lecturas.json'
            catalogos = Path(carpeta) / 'catalogos.json'
            datos.write_text(json.dumps(self.lecturas))
            catalogos.write_text(json.dumps(self.catalogos))
            for modulo in ['cargar_postgres', 'cargar_mongodb']:
                proceso = subprocess.run([sys.executable, '-m', 'sprint1.basico.' + modulo,
                    str(datos), str(catalogos)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(proceso.returncode, 0, proceso.stdout + proceso.stderr)
                self.assertIn('No se abrió una conexión', proceso.stdout)

    def test_mongo_acepta_duplicado_y_conflicto(self):
        lecturas = Mock()
        cuarentena = Mock()
        documento = documento_mongo(self.lecturas[0])
        self.assertEqual(guardar_lectura(lecturas, cuarentena, documento, ErrorDuplicado), 'accepted')
        lecturas.insert_one.side_effect = ErrorDuplicado()
        lecturas.find_one.return_value = {'_id': 'local', 'payload_hash': documento['payload_hash']}
        self.assertEqual(guardar_lectura(lecturas, cuarentena, documento, ErrorDuplicado), 'duplicate')
        cuarentena.insert_one.assert_not_called()
        lecturas.find_one.return_value['payload_hash'] = 'otra_huella'
        self.assertEqual(guardar_lectura(lecturas, cuarentena, documento, ErrorDuplicado), 'quarantined')
        cuarentena.insert_one.assert_called_once()

    def test_mongo_no_oculta_fallos(self):
        lecturas = Mock()
        documento = documento_mongo(self.lecturas[0])
        lecturas.insert_one.side_effect = RuntimeError('fallo')
        with self.assertRaises(RuntimeError):
            guardar_lectura(lecturas, Mock(), documento, ErrorDuplicado)
        lecturas.insert_one.side_effect = ErrorDuplicado()
        lecturas.find_one.return_value = None
        with self.assertRaises(ErrorDuplicado):
            guardar_lectura(lecturas, Mock(), documento, ErrorDuplicado)

    def test_mongo_exige_indice_completo_y_validador(self):
        coleccion = Mock()
        coleccion.options.return_value = {'validator': {'$jsonSchema': {}}, 'validationLevel': 'strict'}
        coleccion.list_indexes.return_value = [{'key': {'staging_key': 1}, 'unique': True}]
        comprobar_coleccion(coleccion)
        coleccion.list_indexes.return_value[0]['sparse'] = True
        with self.assertRaises(ValueError):
            comprobar_coleccion(coleccion)
        coleccion.options.return_value['validationAction'] = 'warn'
        with self.assertRaises(ValueError):
            comprobar_coleccion(coleccion)

    def test_postgres_usa_parametros_y_catalogo_existente(self):
        lectura = self.lecturas[0]
        cursor = Mock()
        cursor.fetchone.side_effect = [
            (lectura['station_id'], lectura['measurement_type'], lectura['source_key'][0],
             lectura['raw_reference']['path']), ('accepted',)]
        resultado = guardar_lecturas(cursor, [lectura])
        self.assertEqual(resultado['accepted'], 1)
        consulta, parametros = cursor.execute.call_args.args
        self.assertEqual(consulta, 'SELECT sprint1.stage_reading(%s::jsonb)')
        self.assertEqual(json.loads(parametros[0])['document'], lectura)

    def test_postgres_rechaza_catalogo_distinto(self):
        cursor = Mock()
        cursor.fetchone.return_value = None
        with self.assertRaises(ValueError):
            guardar_lecturas(cursor, self.lecturas)
        self.assertEqual(cursor.execute.call_count, 1)
