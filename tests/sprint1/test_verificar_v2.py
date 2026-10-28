"""El verificador no debe dar PASS a una carga incompleta o divergente."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import verificar_v2 as verificador


class VerificacionV2Tests(unittest.TestCase):
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
