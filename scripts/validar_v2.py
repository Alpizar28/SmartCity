#!/usr/bin/env python3
"""Carga y compara ambas fuentes en bases LOCALES desechables, sin tocar v1.

Usar research/datasets/.venv/bin/python scripts/validar_v2.py.
No acepta host, DSN ni credenciales de servidores compartidos.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO))
from sprint1.basico.preparar_v2 import DATOS, VERSION, verificar_paquete
sys.path.insert(0, str(DATOS / 'scripts'))
from phase5_contract import canonical, digest, local_to_utc, payload_hash, stable_id


def agregar(grupos, clave, valor):
    grupo = grupos.setdefault(clave, {'cantidad': 0, 'suma': 0, 'minimo': valor, 'maximo': valor})
    grupo['cantidad'] += 1
    grupo['suma'] += valor
    grupo['minimo'] = min(grupo['minimo'], valor)
    grupo['maximo'] = max(grupo['maximo'], valor)


def revisar_entrada(carpeta, preparacion):
    """Cálculos Python independientes para contrastar resultados de MongoDB."""
    catalogos = json.loads((carpeta / 'catalogs.json').read_text())
    tipos, zonas, canales = {}, {}, Counter()
    fechas = eventos = alertas = 0
    with (carpeta / 'accepted.extjsonl').open() as archivo:
        for linea in archivo:
            d = json.loads(linea)
            if d['schema_version'] != VERSION or d['catalog_version'] != VERSION:
                raise ValueError('Contrato incorrecto')
            if d['payload_hash'] != payload_hash(d) or d['source_version'] != d['raw_reference']['sha256']:
                raise ValueError('Hash de contenido o procedencia incorrecto')
            canal = catalogos['channels'][d['channel_id']]
            estacion = catalogos['stations'][d['station_id']]
            tipo = catalogos['measurement_types'][d['measurement_type']]
            if (d['sensor_id'] is not None or canal['sensor_id'] is not None
                or canal['station_id'] != d['station_id'] or canal['source_id'] != d['source_id']
                or tipo['source_id'] != d['source_id'] or tipo['unit'] != d['unit']
                or estacion['zone_id'] != d['zone_id']):
                raise ValueError('Referencia de catálogo contradictoria o sensor inventado')
            utc = local_to_utc(datetime.fromisoformat(d['original_time'])).isoformat().replace('+00:00', 'Z')
            if d['observed_at'] != {'$date': utc} or d['_id'] != stable_id('measurement', d['channel_id'], utc, d['timestamp_role']):
                raise ValueError('Identidad o reloj contradictorios')
            if not isinstance(d['value'], (int, float)) or isinstance(d['value'], bool) or not math.isfinite(d['value']):
                raise ValueError('Valor no finito')
            if d['source_id'] == 'MAD-TRAFFIC':
                if (d['interval_minutes'] != 15 or not isinstance(d['integration_sample_count'], int)
                    or d['integration_sample_count'] <= 0 or d['element_type'] not in ('URB', 'M30')
                    or d['quality_flag'] != 'N' or d['timestamp_status'] != 'publisher_confirmed_local'):
                    raise ValueError('Semántica de tráfico v2 incorrecta')
            elif d['source_id'] != 'MAD-AIR' or d['quality_flag'] != 'V':
                raise ValueError('Fuente o calidad no aceptada')
            agregar(tipos, (d['source_id'], d['measurement_type'], d['unit']), d['value'])
            if d['zone_id'] is not None:
                agregar(zonas, (d['zone_id'], d['source_id'], d['measurement_type'], d['unit']), d['value'])
            canales[d['channel_id']] += 1
            if '2024-12-31T23:00:00Z' <= utc < '2025-01-31T23:00:00Z':
                fechas += 1
            if d['source_id'] == 'MAD-TRAFFIC' and d['value'] > preparacion['demo_rule']['threshold']:
                eventos += 1
                alertas += d['zone_id'] is not None
    huella = sha256()
    with sqlite3.connect(f'file:{carpeta / "identities.sqlite"}?mode=ro', uri=True) as ledger:
        for ident, firma in ledger.execute('SELECT id,signature FROM identities ORDER BY id'):
            huella.update((canonical([ident, firma]) + '\n').encode())
    return {'tipos': tipos, 'zonas': zonas, 'canales': canales, 'fechas': fechas,
            'eventos': eventos, 'alertas': alertas, 'huella': huella.hexdigest()}


def comprobar_consultas(mongo, esperados, preparacion):
    r = mongo['results']
    if set(r) != {f'MG{i:02d}' for i in range(1, 11)}:
        raise ValueError('Faltan consultas Mongo')
    if r['MG01']['total'] != esperados['canales'][r['MG01']['parametros']['channel_id']]:
        raise ValueError('MG01 no coincide con el archivo')
    if r['MG02']['total'] != esperados['fechas']:
        raise ValueError('MG02 no coincide con las fechas del archivo')
    for nombre, campos, grupos in [('MG03', ('fuente', 'tipo', 'unidad'), esperados['tipos']),
                                   ('MG06', ('zona', 'fuente', 'tipo', 'unidad'), esperados['zonas']),
                                   ('MG07', ('fuente', 'tipo', 'unidad'), esperados['tipos'])]:
        claves = set()
        for fila in r[nombre]:
            clave = tuple(fila['_id'][campo] for campo in campos)
            grupo = grupos[clave]
            claves.add(clave)
            if fila['cantidad'] != grupo['cantidad'] or not math.isclose(fila['promedio'], grupo['suma'] / grupo['cantidad'], rel_tol=1e-10):
                raise ValueError(nombre + ': cantidad/promedio distintos de Python')
            if nombre == 'MG03' and (fila['minimo'] != grupo['minimo'] or fila['maximo'] != grupo['maximo']):
                raise ValueError('MG03: extremos distintos de Python')
        requerido = {k for k in grupos if nombre != 'MG03' or k[0] == 'MAD-AIR'}
        if claves != requerido:
            raise ValueError(nombre + ': faltan grupos')
    if r['MG04']['total'] != esperados['eventos'] or sum(f['cantidad'] for f in r['MG05']) != esperados['alertas']:
        raise ValueError('MG04/MG05 no coinciden con la regla calculada en Python')
    categorias = {f['_id']: f['cantidad'] for f in r['MG08']}
    if categorias != preparacion['incident_categories']:
        raise ValueError('MG08 no coincide con los accidentes deduplicados')
    cantidades = {f['_id']['fuente']: f['cantidad'] for f in r['MG09']}
    if cantidades != {s: c['accepted'] for s, c in preparacion['by_source'].items()}:
        raise ValueError('MG09 no coincide con las fuentes del archivo')
    if r['MG10']['total'] != esperados['alertas']:
        raise ValueError('MG10 no coincide con el filtro independiente')


def ejecutar(generacion, solo=None):
    # Reutilizar únicamente la creación/limpieza segura de contenedores y los catálogos.
    from unified_full_load import container, command, catalog_sql, administrative_sql, DOCKER
    from unified_expand import atomic_json
    sys.path.insert(0, str(PROYECTO / 'tests/sprint1'))
    from validate_real_postgres import read_queries

    if not generacion.startswith('expanded-v2-') or Path(generacion).name != generacion:
        raise ValueError('Generación v2 local inválida')
    carpeta = DATOS / 'private_results' / generacion
    preparacion = verificar_paquete(carpeta)
    print('Verificando documentos y resultados esperados en Python...', flush=True)
    esperados = revisar_entrada(carpeta, preparacion)
    informe = {'generation': generacion, 'contract': VERSION, 'status': 'FAIL',
        'shared_server_modified': False, 'started_at': datetime.now(timezone.utc).isoformat(),
        'accepted': preparacion['accepted'], 'by_source': preparacion['by_source'],
        'pg07_notice': 'No observed sensor-channel links: technically executed, physical activity not evaluable.',
        'derived_notice': 'Classroom traffic threshold, local alert replay now; no official historical warnings.',
        'incident_year': 2026, 'zone_scope': preparacion['zone_scope'],
        'source_hashes': {n: digest(PROYECTO / n) for n in [
            'scripts/validar_v2.py', 'sprint1/postgres/contract_v2.sql', 'sprint1/postgres/queries.sql',
            'sprint1/basico/consultas_mongodb_v2.js', 'sprint1/basico/cargar_mongodb_v2.js']}}
    salida = DATOS / 'results' / generacion
    salida.mkdir(parents=True, exist_ok=True)
    try:
        if solo in (None, 'postgresql'):
            print('Cargando ambas fuentes en PostgreSQL desechable...', flush=True)
            pg = informe['postgresql'] = {}
            with container('postgresql', 'postgres:16.6-alpine', carpeta, pg) as nombre:
                def sql(texto):
                    return command(['exec', '-i', nombre, 'psql', '-X', '-Atq', '-U', 'postgres',
                        '-v', 'ON_ERROR_STOP=1'], input="SET timezone='UTC'; SET statement_timeout='25min'; " + texto).stdout.strip()
                sql((DATOS / 'scripts/phase5_postgresql.sql').read_text())
                sql((PROYECTO / 'sprint1/postgres/contract_v2.sql').read_text())
                sql(catalog_sql(json.loads((carpeta / 'catalogs.json').read_text())))
                sql(administrative_sql(json.loads((carpeta / 'administrative_seed.json').read_text())))
                # Actualizar estadísticas de catálogos antes de validar cientos de miles de FK.
                sql('ANALYZE;')
                sql('CREATE UNLOGGED TABLE smartcity.import_stage(doc jsonb NOT NULL);')
                sql("\\copy smartcity.import_stage FROM '/inputs/accepted.extjsonl' WITH (FORMAT csv, DELIMITER E'\\x02', QUOTE E'\\x01');")
                # Materializar la conversión JSON una sola vez por fila, no por cada columna.
                # Los lotes acotan la transacción y permiten informar progreso real.
                sql('ALTER TABLE smartcity.import_stage ADD COLUMN row_id bigint GENERATED ALWAYS AS IDENTITY;')
                sql('CREATE UNIQUE INDEX import_stage_row ON smartcity.import_stage(row_id); ANALYZE smartcity.import_stage;')
                carga = """WITH converted AS MATERIALIZED (
                    SELECT jsonb_populate_record(NULL::smartcity.observations,
                     doc || jsonb_build_object('observed_at', doc->'observed_at'->>'$date')) AS record
                    FROM smartcity.import_stage WHERE row_id > {inicio} AND row_id <= {fin})
                    INSERT INTO smartcity.observations SELECT (record).* FROM converted"""
                for replay in (False, True):
                    comienzo = time.monotonic()
                    for inicio in range(0, preparacion['accepted'], 25000):
                        sentencia = carga.format(inicio=inicio, fin=inicio + 25000)
                        if replay:
                            sentencia += ' ON CONFLICT(measurement_id) DO UPDATE SET value=excluded.value,payload_hash=excluded.payload_hash'
                        sql(sentencia + ';')
                        if inicio % 100000 == 0:
                            print('PostgreSQL', 'replay' if replay else 'carga',
                                  min(inicio + 25000, preparacion['accepted']), '/', preparacion['accepted'], flush=True)
                    pg['replay_seconds' if replay else 'load_seconds'] = time.monotonic() - comienzo
                sql('ANALYZE smartcity.observations;')
                pg['count'] = int(sql('SELECT count(*) FROM smartcity.observations;'))
                errores = int(sql("""SELECT count(*) FROM smartcity.import_stage d
                    JOIN smartcity.observation_contract v ON v.measurement_id=d.doc->>'measurement_id'
                    WHERE NOT ((d.doc-'observed_at'-'time_error') <@ (to_jsonb(v)-'observed_at'-'time_error'))
                    OR v.observed_at<>(d.doc->'observed_at'->>'$date')::timestamptz;"""))
                if errores or pg['count'] != preparacion['accepted']:
                    raise ValueError('PostgreSQL no conserva todas las lecturas/metadatos')
                pg['metadata_verified'] = pg['count']
                pg['count_by_source'] = json.loads(sql("SELECT json_object_agg(source_id,n) FROM (SELECT source_id,count(*) n FROM smartcity.observations GROUP BY source_id) t;"))
                pg['sensor_links'] = int(sql('SELECT count(*) FROM smartcity.channels WHERE sensor_id IS NOT NULL;'))
                if pg['sensor_links'] != 0:
                    raise ValueError('No inventar enlaces a sensores')
                pg['results'] = {}
                for clave, consulta in read_queries().items():
                    pg['results'][clave] = {'total': int(sql('SELECT count(*) FROM (' + consulta + ') t;')),
                        'sample': json.loads(sql("SELECT COALESCE(json_agg(t),'[]') FROM (" + consulta + ' LIMIT 5) t;'))}
                if pg['results']['PG07']['total'] != 0:
                    raise ValueError('PG07 atribuyó actividad a sensores sin enlaces observados')
                huella = sha256()
                args = DOCKER + ['exec', nombre, 'psql', '-X', '-Atq', '-U', 'postgres', '-c',
                    'COPY (SELECT json_build_array(measurement_id,payload_hash) FROM smartcity.observations ORDER BY measurement_id) TO STDOUT;']
                with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proceso:
                    for linea in proceso.stdout:
                        huella.update((canonical(json.loads(linea)) + '\n').encode())
                    error = proceso.stderr.read()
                    if proceso.wait(timeout=1800):
                        raise RuntimeError(error)
                pg.update(ids_payload_sha256=huella.hexdigest(), replay_verified=True)
                if pg['ids_payload_sha256'] != esperados['huella']:
                    raise ValueError('PostgreSQL difiere del ledger')
            print('PostgreSQL: PASS, contenedor eliminado.', flush=True)
        if solo in (None, 'mongodb'):
            print('Cargando MongoDB y ejecutando MG01-MG10...', flush=True)
            mongo = informe['mongodb'] = {}
            with container('mongodb', 'mongo:7.0.16', carpeta, mongo) as nombre:
                for archivo in ['cargar_mongodb_v2.js', 'consultas_mongodb_v2.js']:
                    command(['cp', str(PROYECTO / 'sprint1/basico' / archivo), nombre + ':/tmp/' + archivo])
                base = 'smartcity_v2_' + uuid.uuid4().hex[:12]
                texto = command(['exec', nombre, 'mongosh', '--quiet',
                    'mongodb://127.0.0.1:27017/' + base, '/tmp/cargar_mongodb_v2.js']).stdout
                linea = next(l for l in texto.splitlines() if l.startswith('V2_MONGO_RESULT='))
                mongo.update(json.loads(linea.split('=', 1)[1]))
                comprobar_consultas(mongo, esperados, preparacion)
                if mongo['ids_payload_sha256'] != esperados['huella'] or mongo['count'] != preparacion['accepted']:
                    raise ValueError('MongoDB difiere del ledger')
            print('MongoDB: PASS, contenedor eliminado.', flush=True)
        for motor in ('postgresql', 'mongodb'):
            if motor in informe and not (informe[motor]['container_removed'] and informe[motor]['anonymous_volumes_removed']):
                raise ValueError('Falla al limpiar contenedor/volúmenes propios: ' + motor)
        informe['status'] = 'PASS'
    except Exception as error:
        informe['error'] = str(error)
        if isinstance(error, subprocess.CalledProcessError):
            informe['engine_error'] = (error.stderr or '')[-4000:]
        raise
    finally:
        informe['finished_at'] = datetime.now(timezone.utc).isoformat()
        # Nuevo informe de esta ejecución; nunca reemplazar evidencia v1 ni una ejecución anterior.
        nombre = 'execution-' + uuid.uuid4().hex[:12] + '.json'
        atomic_json(salida / nombre, informe)
        print('Informe:', salida / nombre, flush=True)
    return informe


if __name__ == '__main__':
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--generacion', default='expanded-v2-2025-01')
    argumentos.add_argument('--motor', choices=['postgresql', 'mongodb'])
    opciones = argumentos.parse_args()
    informe = ejecutar(opciones.generacion, opciones.motor)
    print('Validación local v2:', informe['status'])
