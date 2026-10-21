"""Carga sencilla de MongoDB. Sin --guardar solo se revisan los archivos."""
import argparse
from datetime import datetime, timezone
import os

from sprint1.basico.archivos import documento_mongo, leer_entrada


def guardar_lectura(lecturas, cuarentena, documento, error_duplicado):
    try:
        # Una copia evita que el driver agregue _id al documento del llamador.
        lecturas.insert_one(documento.copy())
        return 'accepted'
    except error_duplicado:
        anterior = lecturas.find_one({'staging_key': documento['staging_key']})
        if anterior is None:
            raise  # El duplicado era por otra clave; no asumir que todo salió bien.
        if anterior['payload_hash'] == documento['payload_hash']:
            return 'duplicate'
        cuarentena.insert_one({
            'reason': 'conflicting_payload_same_original_key',
            'existing_id': anterior['_id'],
            'incoming': documento,
            'recorded_at': datetime.now(timezone.utc),
        })
        return 'quarantined'


def comprobar_coleccion(coleccion):
    opciones = coleccion.options()
    if opciones.get('validationAction', 'error') != 'error':
        raise ValueError('La colección debe rechazar documentos inválidos.')
    if opciones.get('validationLevel', 'strict') != 'strict' or not opciones.get('validator'):
        raise ValueError('Primero instala el validador estricto revisado.')
    indice_correcto = False
    for indice in coleccion.list_indexes():
        if dict(indice['key']) == {'staging_key': 1} and indice.get('unique') is True:
            if not indice.get('sparse') and not indice.get('partialFilterExpression'):
                indice_correcto = True
    if not indice_correcto:
        raise ValueError('Falta el índice único completo sobre staging_key.')


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('lecturas', help='Archivo JSON con las lecturas nuevas.')
    argumentos.add_argument('catalogos', help='Catálogos JSON revisados por separado.')
    argumentos.add_argument('--guardar', action='store_true', help='Guardar en la base LOCAL preparada.')
    argumentos.add_argument('--puerto', type=int, default=27017)
    opciones = argumentos.parse_args()
    lecturas, _ = leer_entrada(opciones.lecturas, opciones.catalogos)
    print('Lecturas revisadas:', len(lecturas))
    if not opciones.guardar:
        print('Solo revisión. No se abrió una conexión ni se guardaron datos.')
        return
    if not 1 <= opciones.puerto <= 65535:
        raise ValueError('Puerto inválido.')

    from pymongo import MongoClient
    from pymongo.errors import DuplicateKeyError

    usuario = os.environ.get('SMARTCITY_MONGO_USER')
    clave = os.environ.get('SMARTCITY_MONGO_PASSWORD')
    if not usuario or not clave:
        raise ValueError('Define SMARTCITY_MONGO_USER y SMARTCITY_MONGO_PASSWORD en tu entorno local.')
    resultados = {'accepted': 0, 'duplicate': 0, 'quarantined': 0}
    with MongoClient(host='127.0.0.1', port=opciones.puerto, username=usuario,
                     password=clave, authSource='admin', directConnection=True,
                     retryWrites=False, serverSelectionTimeoutMS=5000,
                     connectTimeoutMS=5000, socketTimeoutMS=10000) as cliente:
        base = cliente['smartcity_sprint1_local']
        comprobar_coleccion(base.readings)
        for lectura in lecturas:
            documento = documento_mongo(lectura)
            estado = guardar_lectura(base.readings, base.quarantine, documento, DuplicateKeyError)
            resultados[estado] += 1
    print('Resultados confirmados:', resultados)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Carga detenida. Tipo de error:', type(error).__name__)
        print('MongoDB puede haber guardado parte del archivo. El replay detecta duplicados.')
        raise SystemExit(1)
