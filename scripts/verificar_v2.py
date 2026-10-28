#!/usr/bin/env python3
"""Comprueba dos informes de la MISMA generación, sin cargar bases ni inventar PASS."""
import argparse
import json
from pathlib import Path
import sys

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO))
from sprint1.basico.preparar_v2 import DATOS, verificar_paquete
from phase5_contract import digest


def verificar(carpeta):
    preparacion = verificar_paquete(carpeta)
    informes = []
    for ruta in sorted((DATOS / 'results' / preparacion['generation']).glob('execution-*.json')):
        informe = json.loads(ruta.read_text())
        if informe.get('status') == 'PASS' and informe.get('generation') == preparacion['generation']:
            informes.append((ruta, informe))
    motores = {}
    for motor in ('postgresql', 'mongodb'):
        candidatos = [(ruta, informe) for ruta, informe in informes if motor in informe]
        if not candidatos:
            raise ValueError('No hay ejecución PASS para ' + motor)
        ruta, informe = max(candidatos, key=lambda par: par[1]['finished_at'])
        datos = informe[motor]
        if (datos.get('count') != preparacion['accepted'] or not datos.get('replay_verified')
            or not datos.get('container_removed') or not datos.get('anonymous_volumes_removed')
            or informe.get('shared_server_modified') is not False):
            raise ValueError('Faltan volumen, replay o limpieza: ' + motor)
        for nombre, sha in informe['source_hashes'].items():
            # El informe enumera ambos motores. Un cambio de JS no invalida SQL ya ejecutado,
            # ni un cambio del DDL SQL altera una ejecución exclusivamente MongoDB.
            if motor == 'postgresql' and nombre.endswith('.js'):
                continue
            if motor == 'mongodb' and nombre.endswith('.sql'):
                continue
            if digest(PROYECTO / nombre) != sha:
                raise ValueError('Código cambiado desde la ejecución: ' + nombre + ' (' + motor + ')')
        if set(datos['results']) != {('PG' if motor == 'postgresql' else 'MG') + f'{i:02d}' for i in range(1, 11)}:
            raise ValueError('Faltan resultados de consultas: ' + motor)
        motores[motor] = {'report': str(ruta.relative_to(PROYECTO)), 'report_sha256': digest(ruta),
            'count': datos['count'], 'ids_payload_sha256': datos['ids_payload_sha256']}
    if motores['postgresql']['ids_payload_sha256'] != motores['mongodb']['ids_payload_sha256']:
        raise ValueError('Los motores no contienen las mismas identidades y payloads')
    return {'verified': True, 'generation': preparacion['generation'], 'engines': motores,
        'accepted': preparacion['accepted'], 'sources': list(preparacion['by_source']),
        'two_sources': len(preparacion['by_source']) >= 2,
        'events': preparacion['expected_events'], 'alerts': preparacion['expected_alerts_with_zone'],
        'incidents': preparacion['incidents'], 'incident_year': preparacion['incident_year'],
        'limits': ['No physical sensor-channel relationship is invented.',
            'Events/alerts use an academic demo rule and local replay, not official warnings.',
            'District inventory has no verified historical validity.',
            'No shared server modified; academic acceptance remains separate.']}


if __name__ == '__main__':
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--generacion', default='expanded-v2-2025-01')
    opciones = argumentos.parse_args()
    if not opciones.generacion.startswith('expanded-v2-') or Path(opciones.generacion).name != opciones.generacion:
        raise ValueError('Generación inválida')
    print(json.dumps(verificar(DATOS / 'private_results' / opciones.generacion), ensure_ascii=False, indent=2))
