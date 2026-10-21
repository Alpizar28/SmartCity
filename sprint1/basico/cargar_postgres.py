"""Carga pequeña y local. Por defecto solo revisa archivos, no guarda nada."""
import argparse
import json
import os

from sprint1.basico.archivos import leer_entrada, registro_postgres


def guardar_lecturas(cursor, lecturas):
    resultados = {'accepted': 0, 'duplicate': 0, 'quarantined': 0}
    for lectura in lecturas:
        # No creamos catálogos a partir de las lecturas: deben estar revisados
        # e instalados antes de cargar. Tampoco cambiamos los que ya existen.
        cursor.execute('''
            SELECT c.station_id, c.measurement_type, s.source_key, v.original_path
            FROM sprint1.channels c
            JOIN sprint1.stations s ON s.station_id = c.station_id AND s.source_id = c.source_id
            JOIN sprint1.source_versions v ON v.source_id = c.source_id
            WHERE c.channel_id = %s AND c.source_id = %s AND v.source_version = %s
        ''', (lectura['channel_id'], lectura['source_id'], lectura['source_version']))
        esperado = (lectura['station_id'], lectura['measurement_type'],
                    lectura['source_key'][0], lectura['raw_reference']['path'])
        if cursor.fetchone() != esperado:
            raise ValueError('El catálogo de PostgreSQL no coincide con la lectura.')

        registro = registro_postgres(lectura)
        # %s enlaza el valor como parámetro; no se concatena JSON dentro del SQL.
        cursor.execute('SELECT sprint1.stage_reading(%s::jsonb)', (json.dumps(registro, allow_nan=False),))
        estado = cursor.fetchone()[0]
        resultados[estado] += 1
    return resultados


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('lecturas', help='Archivo JSON con las lecturas nuevas.')
    argumentos.add_argument('catalogos', help='Catálogos JSON revisados por separado.')
    argumentos.add_argument('--guardar', action='store_true', help='Guardar en la base LOCAL preparada.')
    argumentos.add_argument('--puerto', type=int, default=5433)
    opciones = argumentos.parse_args()
    lecturas, _ = leer_entrada(opciones.lecturas, opciones.catalogos)
    print('Lecturas revisadas:', len(lecturas))
    if not opciones.guardar:
        print('Solo revisión. No se abrió una conexión ni se guardaron datos.')
        return
    if not 1 <= opciones.puerto <= 65535:
        raise ValueError('Puerto inválido.')

    # Estas dependencias solo se necesitan cuando se solicita guardar.
    import psycopg

    usuario = os.environ.get('SMARTCITY_PG_USER')
    clave = os.environ.get('SMARTCITY_PG_PASSWORD')
    if not usuario or not clave:
        raise ValueError('Define SMARTCITY_PG_USER y SMARTCITY_PG_PASSWORD en tu entorno local.')
    # Host y nombre fijos: no se acepta una URL de un servidor compartido.
    with psycopg.connect(host='127.0.0.1', port=opciones.puerto,
                          dbname='smartcity_sprint1_local', user=usuario,
                          password=clave, connect_timeout=5) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
            cursor.execute("SET LOCAL statement_timeout = '10s'")
            cursor.execute("SET LOCAL lock_timeout = '5s'")
            resultados = guardar_lecturas(cursor, lecturas)
        # El with confirma la transacción al salir; ante un error la revierte.
    print('Resultados confirmados:', resultados)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Los errores de conexión pueden incluir datos privados: no imprimirlos.
        print('Carga detenida. Tipo de error:', type(error).__name__)
        print('No se confirma una carga completa. Revisa archivos, dependencias y configuración local.')
        raise SystemExit(1)
