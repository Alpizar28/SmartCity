"""Lectura de archivos y conversiones sencillas, sin conexiones a bases de datos."""
import json
from datetime import datetime
from pathlib import Path

from sprint1.core.contract import staging_key
from sprint1.core.validation import validate_document


def leer_json(ruta):
    # El límite evita cargar accidentalmente un archivo enorme en memoria.
    with Path(ruta).open('rb') as archivo:
        contenido = archivo.read(5 * 1024 * 1024 + 1)
    if len(contenido) > 5 * 1024 * 1024:
        raise ValueError('Cada archivo debe pesar como máximo 5 MiB.')
    return json.loads(contenido.decode('utf-8'))


def leer_entrada(ruta_lecturas, ruta_catalogos):
    lecturas = leer_json(ruta_lecturas)
    catalogos = leer_json(ruta_catalogos)

    if not isinstance(lecturas, list) or not 1 <= len(lecturas) <= 5000:
        raise ValueError('Se necesita una lista de 1 a 5000 lecturas.')
    if not isinstance(catalogos, dict):
        raise ValueError('Los catálogos deben ser un objeto JSON.')
    for nombre in ['sources', 'versions', 'stations', 'channels', 'zones']:
        if not isinstance(catalogos.get(nombre), dict):
            raise ValueError('Falta el catálogo: ' + nombre)

    # Se valida TODO antes de abrir una conexión o escribir una lectura.
    for numero, lectura in enumerate(lecturas, start=1):
        try:
            validate_document(lectura, catalogos)
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            raise ValueError('Lectura inválida en la posición ' + str(numero)) from error
    return lecturas, catalogos


def documento_mongo(lectura):
    # La copia permite trabajar sin modificar el archivo original.
    documento = lectura.copy()
    documento.pop('storage_id', None)
    documento['staging_key'] = staging_key(lectura)
    fecha = lectura.get('observed_at')
    if fecha is not None:
        documento['observed_at'] = datetime.fromisoformat(fecha['$date'].replace('Z', '+00:00'))
    return documento


def registro_postgres(lectura):
    # La función SQL recibe JSON: las fechas siguen como cadenas ISO.
    campos = ['source_id', 'source_version', 'channel_id', 'source_key',
              'original_time', 'original_timezone', 'timestamp_role',
              'timestamp_status', 'value', 'unit', 'unit_status', 'quality_flag',
              'payload_hash', 'raw_reference', 'schema_version']
    registro = {}
    for campo in campos:
        registro[campo] = lectura.get(campo)
    fecha = lectura.get('observed_at')
    registro['observed_at'] = None
    if fecha is not None:
        registro['observed_at'] = fecha['$date']
    registro['document'] = lectura
    return registro
