#!/usr/bin/env python3
"""Crea un ZIP publicable de v2 y una muestra CSV para verla sin instalar bases.

No incluye originales de accidentes con datos personales, credenciales o .env.
El ZIP va a data/releases (ignorado por Git), no al historial del repositorio.
"""
import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import zipfile

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO))
from sprint1.basico.preparar_v2 import DATOS, verificar_paquete


def empaquetar(generacion):
    if not generacion.startswith('expanded-v2-') or Path(generacion).name != generacion:
        raise ValueError('Generación inválida')
    carpeta = DATOS / 'private_results' / generacion
    preparacion = verificar_paquete(carpeta)
    salida = PROYECTO / 'data/releases'
    salida.mkdir(parents=True, exist_ok=True)
    destino = salida / ('SmartCity_Dataset_' + generacion + '.zip')
    if destino.exists():
        raise ValueError('El ZIP ya existe; verificarlo antes de reemplazarlo.')
    # Lista explícita: nada de copiar todo raw/ o private_results/.
    nombres = [*preparacion['output_hashes'], 'preparation.json']
    archivos = [(carpeta / n, str((carpeta / n).relative_to(PROYECTO))) for n in nombres]
    for p in sorted((DATOS / 'results' / generacion).glob('execution-*.json')):
        archivos.append((p, str(p.relative_to(PROYECTO))))
    manifiesto = {'generation': generacion, 'created_at': datetime.now(timezone.utc).isoformat(),
        'license': 'Madrid observed data: CC BY 4.0; derived/synthetic fields explicitly labeled.',
        'publisher': 'Ayuntamiento de Madrid; not an official product or endorsement.',
        'accepted': preparacion['accepted'], 'by_source': preparacion['by_source'],
        'incident_year': 2026, 'incidents': preparacion['incidents'], 'files': []}
    muestra = io.StringIO()
    campos = ['source_id', 'channel_id', 'original_time', 'observed_at_utc',
              'measurement_type', 'value', 'unit', 'quality_flag', 'zone_id', 'zone_scope', 'data_origin']
    escritor = csv.DictWriter(muestra, fieldnames=campos, lineterminator='\n')
    escritor.writeheader()
    cantidad = {'MAD-AIR': 0, 'MAD-TRAFFIC': 0}
    with (carpeta / 'accepted.extjsonl').open() as entrada:
        for linea in entrada:
            d = json.loads(linea)
            if cantidad[d['source_id']] >= 100:
                continue
            fila = {campo: d.get(campo) for campo in campos}
            fila['observed_at_utc'] = d['observed_at']['$date']
            escritor.writerow(fila)
            cantidad[d['source_id']] += 1
            if all(n == 100 for n in cantidad.values()):
                break
    (salida / 'dataset_muestra.csv').write_text(muestra.getvalue(), encoding='utf-8-sig')
    resumen = {k: preparacion[k] for k in ['generation', 'contract', 'accepted', 'by_source',
        'rejection_reasons', 'incidents', 'incident_year', 'incident_categories', 'demo_rule',
        'expected_events', 'expected_alerts_with_zone', 'zone_scope']}
    (salida / 'dataset_resumen.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + '\n')
    instrucciones = '''# SmartCity — dataset v2 local

Fuente: Ayuntamiento de Madrid, CC BY 4.0. Conservar atribución y cambios.
Licencia: https://creativecommons.org/licenses/by/4.0/
Aire: https://datos.madrid.es/dataset/201200-0-calidad-aire-horario
Tráfico: https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico
Accidentes: https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle
No es un producto oficial ni está respaldado por el Ayuntamiento.

748.889 lecturas de enero de 2025: 91.959 aire + 656.930 tráfico (estrato id%20).
Los 14.388 accidentes son de 2026, separados y sin campos personales.
No incluye el original de accidentes, que contiene información de personas.
Organismos, usuarios y sensores administrativos son sintéticos y están etiquetados.
No hay vínculos inventados entre sensores demo y lecturas reales.
Las zonas son del inventario disponible; no hay vigencia histórica acreditada.
Los eventos/alertas usan una regla demo, no avisos oficiales ni límites legales.

## Ver sin instalar bases
Abrir dataset_muestra.csv en LibreOffice/Excel (200 filas, no el dataset completo).
Abrir dataset_resumen.json para ver cantidades y categorías.
accepted.extjsonl es el dataset completo, un documento Extended JSON por línea.

## Restaurar
Clonar main del repositorio https://github.com/Alpizar28/SmartCity y obtener el
commit/tag indicado en este Release. Verificar el SHA-256 antes de extraer.
Extraer desde la raíz del repo con: unzip -n /ruta/SmartCity_Dataset_expanded-v2-2025-01.zip
No sobrescribir paquetes existentes. Nunca extraer dentro de research/datasets.
Los archivos quedan ignorados por Git. No hay contraseñas ni configuración remota.

Para verificar cada archivo del ZIP, leer DATASET_manifest.json y comparar
SHA-256 y bytes después de extraer. Los hashes del paquete preparado también
están en research/datasets/private_results/expanded-v2-2025-01/preparation.json.

Con las dependencias de research/datasets/scripts/requirements.lock y Docker
local (imágenes postgres:16.6-alpine y mongo:7.0.16):
  research/datasets/.venv/bin/python scripts/validar_v2.py
  research/datasets/.venv/bin/python scripts/verificar_v2.py
Estas pruebas crean y eliminan bases locales propias. No cargan servidores compartidos.
Un informe FAIL no es una validación aprobada; revisar los execution-*.json.
'''
    temporal = destino.with_suffix('.zip.partial')
    try:
        with zipfile.ZipFile(temporal, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=5) as z:
            for origen, relativo in archivos:
                h = sha256()
                with origen.open('rb') as f:
                    for bloque in iter(lambda: f.read(1024 * 1024), b''):
                        h.update(bloque)
                manifiesto['files'].append({'path': relativo, 'bytes': origen.stat().st_size, 'sha256': h.hexdigest()})
                z.write(origen, relativo)
            z.writestr('dataset_muestra.csv', (salida / 'dataset_muestra.csv').read_bytes())
            z.writestr('dataset_resumen.json', (salida / 'dataset_resumen.json').read_bytes())
            z.writestr('DATASET_LEER_PRIMERO.md', instrucciones)
            z.writestr('DATASET_manifest.json', json.dumps(manifiesto, ensure_ascii=False, indent=2) + '\n')
        with zipfile.ZipFile(temporal) as z:
            fallo = z.testzip()
            if fallo:
                raise ValueError('CRC inválido: ' + fallo)
        temporal.replace(destino)
        h = sha256()
        with destino.open('rb') as f:
            for bloque in iter(lambda: f.read(1024 * 1024), b''):
                h.update(bloque)
        destino.with_suffix('.zip.sha256').write_text(h.hexdigest() + '  ' + destino.name + '\n')
        print(json.dumps({'zip': str(destino), 'bytes': destino.stat().st_size,
                          'sha256': h.hexdigest(), 'sample_rows': cantidad}, indent=2))
    except Exception:
        # Conservar .partial para inspección; no aparentar un ZIP terminado.
        raise
    return destino


def empaquetar_completo():
    """Copia privada de TODOS los datasets locales, no un asset público."""
    salida = PROYECTO / 'data/releases'
    salida.mkdir(parents=True, exist_ok=True)
    destino = salida / 'SmartCity_DATASET_COMPLETO_PRIVADO.zip'
    if destino.exists():
        raise ValueError('Ya existe el respaldo completo; no se reemplaza automáticamente.')
    excluidos = {'.venv', '__pycache__', '.pytest_cache', '.git', 'node_modules'}
    archivos = []
    omitidos = []
    for p in sorted(DATOS.rglob('*')):
        relativo = p.relative_to(PROYECTO)
        if any(parte in excluidos for parte in p.relative_to(DATOS).parts):
            continue
        if p.is_symlink():
            raise ValueError('Revisar enlace simbólico antes de empaquetar: ' + str(relativo))
        if not p.is_file():
            continue
        if p.name.startswith('.env') or p.suffix.lower() in {'.pem', '.key', '.p12'}:
            omitidos.append(str(relativo))
            continue
        if p.name.endswith(('.partial', '.lock', '.sqlite-wal', '.sqlite-shm')):
            omitidos.append(str(relativo))
            continue
        archivos.append(p)
    fecha = datetime.now(timezone.utc).isoformat()
    manifiesto = {'created_at': fecha, 'private_backup_not_public_release': True,
        'scope': 'All locally available research/datasets files, not just a sample or v2.',
        'warning': 'Contains original person-level incidents/311 data and academic originals; restricted sharing only.',
        'excluded_directories': sorted(excluidos), 'excluded_files': omitidos, 'files': []}
    instrucciones = '''# DATASET COMPLETO — COPIA PRIVADA

Contiene TODOS los archivos de datos disponibles localmente en research/datasets:
originales (raw), CSV/Parquet/SQLite procesados, paquetes de generaciones,
catálogos, cuarentena, manifiestos, investigación, scripts y evidencias.
Incluye Madrid y los datos de otras ciudades conservados durante la investigación.
NO es una muestra de 200 filas ni solo las 748.889 lecturas preparadas v2.

No inventa archivos históricos faltantes ni incluye una carga anual regenerada
que no exista localmente. El manifiesto enumera exactamente los archivos presentes.
Se excluyen entornos Python, cachés, secretos, locks y salidas parciales sin sellar.
No contiene bases remotas ni sus credenciales. Los scripts están incluidos para
referencia; el código completo del proyecto se obtiene de main en GitHub.

PRIVACIDAD: algunos originales de accidentes/311 conservan información de personas,
ubicaciones o detalles sensibles. Los PDFs académicos y fuentes de otras ciudades
tienen condiciones de redistribución diferentes. Este ZIP NO está anonimizado,
NO está cifrado y NO debe publicarse en GitHub Releases ni con enlace público.
Subir a Drive con acceso RESTRINGIDO e invitar únicamente al equipo autorizado.

Para restaurar: clonar https://github.com/Alpizar28/SmartCity, entrar a la raíz,
verificar el SHA-256 y extraer con unzip -n /ruta/SmartCity_DATASET_COMPLETO_PRIVADO.zip
No sobrescribir datos propios. Los datos privados deben seguir ignorados por Git.
DATASET_COMPLETO_manifest.json contiene ruta, bytes y SHA-256 de cada archivo.
El ZIP fue comprobado por CRC antes de sellar su checksum.
La integridad del ZIP no acredita que las cargas SQL/Mongo hayan terminado en PASS.
'''
    temporal = destino.with_suffix('.zip.partial')
    with zipfile.ZipFile(temporal, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=4) as z:
        for i, p in enumerate(archivos, 1):
            estado = p.stat()
            h = sha256()
            nombre = str(p.relative_to(PROYECTO))
            # Una sola lectura crea el archivo comprimido y calcula su hash.
            with p.open('rb') as entrada, z.open(nombre, 'w', force_zip64=True) as archivo_zip:
                for bloque in iter(lambda: entrada.read(1024 * 1024), b''):
                    h.update(bloque)
                    archivo_zip.write(bloque)
            actual = p.stat()
            if (actual.st_size, actual.st_mtime_ns) != (estado.st_size, estado.st_mtime_ns):
                raise ValueError('Archivo cambió durante la copia; no sellar ZIP: ' + nombre)
            manifiesto['files'].append({'path': nombre, 'bytes': estado.st_size, 'sha256': h.hexdigest()})
            if i % 50 == 0:
                print('Archivos completos empaquetados:', i, '/', len(archivos), flush=True)
        z.writestr('DATASET_COMPLETO_LEER_PRIMERO.md', instrucciones)
        z.writestr('DATASET_COMPLETO_manifest.json', json.dumps(manifiesto, ensure_ascii=False, indent=2) + '\n')
    with zipfile.ZipFile(temporal) as z:
        if z.testzip() is not None:
            raise ValueError('Falla CRC del respaldo completo')
    temporal.replace(destino)
    h = sha256()
    with destino.open('rb') as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloque)
    destino.with_suffix('.zip.sha256').write_text(h.hexdigest() + '  ' + destino.name + '\n')
    # Inventario junto al ZIP para ver su contenido sin extraer gigabytes.
    (salida / 'DATASET_COMPLETO_manifest.json').write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + '\n')
    (salida / 'DATASET_COMPLETO_LEER_PRIMERO.md').write_text(instrucciones)
    print(json.dumps({'zip': str(destino), 'files': len(archivos),
        'uncompressed_bytes': sum(f['bytes'] for f in manifiesto['files']),
        'zip_bytes': destino.stat().st_size, 'sha256': h.hexdigest(),
        'upload': 'Manual upload to restricted Google Drive; never public.'}, indent=2), flush=True)
    return destino


if __name__ == '__main__':
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--generacion', default='expanded-v2-2025-01')
    argumentos.add_argument('--completo', action='store_true', help='ZIP privado de todos los datos locales, no solo v2')
    opciones = argumentos.parse_args()
    if opciones.completo:
        empaquetar_completo()
    else:
        empaquetar(opciones.generacion)
