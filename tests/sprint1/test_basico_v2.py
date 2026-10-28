"""Pruebas pequeñas de la nueva fuente y anonimización; sin bases ni descargas."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from sprint1.basico.preparar_v2 import (
    cambiar_version, documento_trafico, leer_incidentes, preparar, valor_opcional,
)


class BasicoV2Tests(unittest.TestCase):
    def fila(self, **cambios):
        fila = {'id': '20', 'fecha': '2025-01-01 00:15:00', 'tipo_elem': 'M30',
            'intensidad': '2500', 'ocupacion': '15', 'carga': '20', 'vmed': '80',
            'error': 'N', 'periodo_integracion': '30', 'raw_row': 2}
        fila.update(cambios)
        return fila

    def convertir(self, **cambios):
        return documento_trafico(self.fila(**cambios), {'sha256': 'a' * 64, 'path': 'test.zip'}, '01-2025.csv')

    def test_muestras_no_son_minutos_y_el_reloj_es_madrid(self):
        doc, motivo = self.convertir()
        self.assertEqual(motivo, 'accepted')
        self.assertEqual(doc['interval_minutes'], 15)
        self.assertEqual(doc['integration_sample_count'], 30)
        self.assertEqual(doc['observed_at'], {'$date': '2024-12-31T23:15:00Z'})
        self.assertIsNone(doc['sensor_id'])
        self.assertEqual(doc['measurements']['carga']['unit'], 'index')

    def test_urb_no_inventa_velocidad_y_sentinelas_son_faltantes(self):
        doc, _ = self.convertir(tipo_elem='URB', vmed='0', ocupacion='-1', carga='101')
        self.assertIsNone(doc['measurements']['vmed']['value'])
        self.assertEqual(doc['measurements']['vmed']['status'], 'not_applicable')
        self.assertIsNone(doc['measurements']['ocupacion']['value'])
        self.assertEqual(doc['measurements']['ocupacion']['raw_value'], '-1')
        self.assertEqual(doc['measurements']['carga']['status'], 'out_of_range')

    def test_clases_flags_y_campos_invalidos_se_rechazan(self):
        for cambios in [{'tipo_elem': 'C30'}, {'error': ''}, {'error': 'E'}, {'error': 'S'},
                        {'intensidad': '-1'}, {'intensidad': 'NaN'},
                        {'periodo_integracion': '0'}, {'periodo_integracion': '1.5'},
                        {'fecha': '01/01/2025'}, {'fecha': '2025-01-32 00:00:00'},
                        {'fecha': '2025-02-01 00:00:00'}]:
            with self.subTest(cambios=cambios):
                doc, motivo = self.convertir(**cambios)
                self.assertIsNone(doc)
                self.assertNotEqual(motivo, 'accepted')

    def test_dst_no_se_adivina(self):
        self.assertEqual(self.convertir(fecha='2025-03-30 02:30:00')[1], 'nonexistent_local_time')
        self.assertEqual(self.convertir(fecha='2025-10-26 02:30:00')[1],
                         'ambiguous_local_time_requires_publisher_fold')

    def test_migracion_conserva_id_y_valor_sin_mutar_v1(self):
        original, _ = self.convertir()
        nuevo = cambiar_version(original)
        self.assertEqual(original['schema_version'], 'madrid-draft-v1')
        self.assertEqual(nuevo['schema_version'], 'madrid-draft-v2')
        self.assertEqual(nuevo['_id'], original['_id'])
        self.assertEqual(nuevo['value'], original['value'])
        self.assertEqual(nuevo, cambiar_version(original))
        self.assertEqual(nuevo['zone_scope'], 'unknown')

    def test_opcional_cero_es_valido_y_negativo_no(self):
        self.assertEqual(valor_opcional('0', 'percent')['value'], 0)
        self.assertIsNone(valor_opcional('-1', 'percent')['value'])

    def incidentes(self, filas):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'crash.csv'
            campos = ['num_expediente', 'fecha', 'cod_distrito', 'tipo_accidente', 'sexo', 'rango_edad']
            with ruta.open('w', encoding='utf-8-sig', newline='') as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=campos, delimiter=';')
                escritor.writeheader()
                escritor.writerows(filas)
            return leer_incidentes(ruta, {'path': 'private/crash.csv', 'sha256': 'b' * 64})

    def test_accidentes_no_cuentan_personas_ni_exportan_campos_personales(self):
        fila = {'num_expediente': 'test-exp', 'fecha': '01/01/2026', 'cod_distrito': '03',
                'tipo_accidente': 'Colisión', 'sexo': 'NO_EXPORTAR', 'rango_edad': 'NO_EXPORTAR'}
        docs, cantidad = self.incidentes([fila, fila])
        self.assertEqual(cantidad, 2)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['zone_id'], 'madrid:district:3')
        self.assertTrue(docs[0]['person_fields_removed'])
        self.assertNotIn('NO_EXPORTAR', json.dumps(docs))
        self.assertNotIn('test-exp', json.dumps(docs))
        self.assertNotIn('observed_at', docs[0])  # No inventar reloj UTC para fecha sola.

    def test_incidente_con_categoria_contradictoria_no_se_inventa(self):
        fila = {'num_expediente': 'test-exp', 'fecha': '01/01/2026', 'cod_distrito': '1', 'tipo_accidente': 'A'}
        with self.assertRaisesRegex(ValueError, 'contradictoria'):
            self.incidentes([fila, {**fila, 'tipo_accidente': 'B'}])

    def test_generacion_no_puede_apuntar_fuera_del_paquete_v2(self):
        for nombre in ['expanded-2025', '../main', 'expanded-v2-../main']:
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                preparar(nombre)
