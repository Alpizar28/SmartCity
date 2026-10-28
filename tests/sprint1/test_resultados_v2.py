"""Una bandera PASS no sustituye resultados: comprobar filas y valores."""
from copy import deepcopy
import unittest

from scripts.validar_v2 import comprobar_consultas


class ResultadosV2Tests(unittest.TestCase):
    def datos(self):
        aire = ('MAD-AIR', 'MAD-AIR:8', 'ug/m3')
        trafico = ('MAD-TRAFFIC', 'MAD-TRAFFIC:intensidad', 'veh/h')
        grupo_aire = {'fuente': aire[0], 'tipo': aire[1], 'unidad': aire[2]}
        grupo_trafico = {'fuente': trafico[0], 'tipo': trafico[1], 'unidad': trafico[2]}
        esperados = {'tipos': {
            aire: {'cantidad': 2, 'suma': 30, 'minimo': 10, 'maximo': 20},
            trafico: {'cantidad': 1, 'suma': 2500, 'minimo': 2500, 'maximo': 2500}},
            'zonas': {('district-1', *trafico): {'cantidad': 1, 'suma': 2500}},
            'canales': {'test-channel': 1}, 'fechas': 3, 'eventos': 1, 'alertas': 1}
        resultados = {
            'MG01': {'parametros': {'channel_id': 'test-channel'}, 'total': 1},
            'MG02': {'total': 3},
            'MG03': [{'_id': grupo_aire, 'cantidad': 2, 'promedio': 15, 'minimo': 10, 'maximo': 20}],
            'MG04': {'total': 1},
            'MG05': [{'_id': 'district-1', 'cantidad': 1}],
            'MG06': [{'_id': {'zona': 'district-1', **grupo_trafico}, 'cantidad': 1, 'promedio': 2500}],
            'MG07': [{'_id': grupo_aire, 'cantidad': 2, 'promedio': 15},
                     {'_id': grupo_trafico, 'cantidad': 1, 'promedio': 2500}],
            'MG08': [{'_id': 'test-category', 'cantidad': 1}],
            'MG09': [{'_id': {'fuente': 'MAD-AIR', 'calidad': 'V'}, 'cantidad': 2},
                     {'_id': {'fuente': 'MAD-TRAFFIC', 'calidad': 'N'}, 'cantidad': 1}],
            'MG10': {'total': 1},
        }
        preparacion = {'incident_categories': {'test-category': 1},
            'by_source': {'MAD-AIR': {'accepted': 2}, 'MAD-TRAFFIC': {'accepted': 1}}}
        return {'results': resultados}, esperados, preparacion

    def test_resultados_coherentes_pasan(self):
        mongo, esperados, preparacion = self.datos()
        comprobar_consultas(mongo, esperados, preparacion)

    def test_resultados_incorrectos_no_se_aceptan_por_tener_pass(self):
        original, esperados, preparacion = self.datos()
        cambios = [
            ('MG02', {'total': 1}),
            ('MG03', [{'_id': {'fuente': 'MAD-AIR', 'tipo': 'MAD-AIR:8', 'unidad': 'ug/m3'},
                       'cantidad': 2, 'promedio': 15, 'minimo': -999, 'maximo': 20}]),
            ('MG04', {'total': 999, 'status': 'PASS'}),
            ('MG05', []), ('MG06', []),
            ('MG08', [{'_id': 'invented-category', 'cantidad': 1}]),
            ('MG10', {'total': 999}),
        ]
        for clave, valor in cambios:
            with self.subTest(consulta=clave):
                mongo = deepcopy(original)
                mongo['results'][clave] = valor
                with self.assertRaises(ValueError):
                    comprobar_consultas(mongo, esperados, preparacion)
