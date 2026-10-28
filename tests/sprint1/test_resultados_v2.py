"""Una bandera PASS no sustituye resultados: comprobar filas y valores."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.validar_v2 import comprobar_consultas
from scripts import verificar_v2 as verificador


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


class VerificacionV2Tests(unittest.TestCase):
    """Una carga incompleta o divergente nunca debe aprobarse."""

    def revisar(self, cambiar=None):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            carpeta = raiz / 'results/expanded-v2-test'
            carpeta.mkdir(parents=True)
            preparacion = {'generation': 'expanded-v2-test', 'accepted': 2,
                'by_source': {'MAD-AIR': {'accepted': 1}, 'MAD-TRAFFIC': {'accepted': 1}},
                'expected_events': 1, 'expected_alerts_with_zone': 1,
                'incidents': 1, 'incident_year': 2026}
            informes = {}
            for motor, prefijo in [('postgresql', 'PG'), ('mongodb', 'MG')]:
                informes[motor] = {'status': 'PASS', 'generation': 'expanded-v2-test',
                    'shared_server_modified': False, 'finished_at': '2026-10-27T00:00:00+00:00',
                    'source_hashes': {}, motor: {'count': 2, 'replay_verified': True,
                        'container_removed': True, 'anonymous_volumes_removed': True,
                        'results': {f'{prefijo}{i:02d}': {} for i in range(1, 11)},
                        'ids_payload_sha256': 'identical-test-hash'}}
            if cambiar:
                cambiar(informes)
            for motor, informe in informes.items():
                (carpeta / f'execution-{motor}.json').write_text(json.dumps(informe))
            with patch.object(verificador, 'DATOS', raiz), patch.object(verificador, 'PROYECTO', raiz), \
                 patch.object(verificador, 'verificar_paquete', return_value=preparacion):
                return verificador.verificar(raiz / 'private_results/expanded-v2-test')

    def test_exige_dos_motores_con_las_mismas_identidades(self):
        self.assertTrue(self.revisar()['verified'])
        with self.assertRaisesRegex(ValueError, 'identidades'):
            self.revisar(lambda d: d['mongodb']['mongodb'].update(ids_payload_sha256='different'))

    def test_rechaza_motor_fallido_consultas_faltantes_y_limpieza_fallida(self):
        def quitar_consulta(d):
            del d['mongodb']['mongodb']['results']['MG04']
        casos = [lambda d: d['postgresql'].update(status='FAIL'), quitar_consulta,
                 lambda d: d['mongodb']['mongodb'].update(container_removed=False),
                 lambda d: d['mongodb']['mongodb'].update(replay_verified=False),
                 lambda d: d['postgresql'].update(shared_server_modified=True)]
        for cambiar in casos:
            with self.subTest(caso=cambiar), self.assertRaises(ValueError):
                self.revisar(cambiar)
