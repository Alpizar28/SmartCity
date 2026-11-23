"""Colección analítica en el replica set local. No es sharding."""
import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import time

from pymongo import MongoClient, InsertOne
from pymongo.write_concern import WriteConcern

ROOT = Path(__file__).resolve().parents[1]


# Qué hace: lee la clave local del laboratorio. No la imprime.
def password():
    db_credential = os.environ.get('SMARTCITY_FINAL_PASSWORD')
    if db_credential:
        return db_credential.strip()
    return (ROOT / '.cache/final-password').read_text().strip()


# Qué hace: abre un nodo de Mongo en el puerto local, con el usuario admin.
def client(port=57027):
    return MongoClient('127.0.0.1', port, username='admin', authSource='admin',
                       directConnection=True, serverSelectionTimeoutMS=5000,
                       connectTimeoutMS=5000, **{'password': password()})


# Qué hace: busca cuál de los dos nodos de datos está aceptando escrituras.
def primary():
    for port in (57027, 57028):
        connection = client(port)
        try:
            if connection.admin.command('hello')['isWritablePrimary']:
                return connection
        except Exception:
            connection.close()
            continue
        connection.close()
    raise RuntimeError('No primary available in the two owned local ports')


# Qué hace: arma el replica set (dos nodos y un árbitro) si todavía no existe.
def initialize():
    with client() as connection:
        try:
            connection.admin.command('replSetGetStatus')
            return {'already_initialized': True}
        except Exception as exc:
            if getattr(exc, 'code', None) != 94:
                raise
        return connection.admin.command('replSetInitiate', {'_id': 'scfinal', 'members': [
            {'_id': 0, 'host': 'mongo1:27017', 'priority': 2},
            {'_id': 1, 'host': 'mongo2:27017'},
            {'_id': 2, 'host': 'mongo-arbiter:27017', 'arbiterOnly': True}]})


# Qué hace: mete el JSONL en la colección, espera mayoría y lo compara con el manifiesto.
def load(generation):
    manifest = json.loads((generation / 'manifest.json').read_text())
    source = generation / 'observations.jsonl'
    digest = hashlib.sha256()
    with source.open('rb') as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    file_hash = digest.hexdigest()
    if file_hash != manifest['output_hashes']['observations.jsonl']:
        raise ValueError('Changed analytical generation')
    started = time.perf_counter()
    with primary() as connection:
        db = connection.get_database('smartcity_final', write_concern=WriteConcern('majority', wtimeout=60000))
        previous = db.runs.find_one({'_id': file_hash})
        if previous:
            if db.observations.count_documents({}) != manifest['count']:
                raise ValueError('Published collection count changed')
            return {'status': 'PASS', 'idempotent_reuse': True, 'count': manifest['count']}
        if db.observations.estimated_document_count() or db.runs.count_documents({}):
            raise ValueError('Existing incomplete/different data: use a new isolated environment, no overwrite')
        if 'observations' not in db.list_collection_names():
            db.create_collection('observations', validator={'$jsonSchema': {
                'bsonType': 'object', 'required': ['_id', 'channel_id', 'observed_at', 'value', 'record_hash', 'schema_version'],
                'properties': {'_id': {'bsonType': 'string'}, 'value': {'bsonType': ['double', 'int', 'long']},
                    'schema_version': {'enum': ['smartcity-analytics-v1']}, 'record_hash': {'bsonType': 'string'}}}})
        batch = []
        count = 0
        with source.open() as stream:
            for line in stream:
                row = json.loads(line)
                row['local_hour'] = datetime.fromisoformat(row['original_time']).hour
                batch.append(InsertOne(row))
                if len(batch) == 2000:
                    db.observations.bulk_write(batch, ordered=True)
                    count += len(batch)
                    batch = []
                    if count % 100000 == 0:
                        print('Mongo replicated records:', count, flush=True)
        if batch:
            db.observations.bulk_write(batch, ordered=True)
            count += len(batch)
        db.observations.create_index([('channel_id', 1), ('observed_at', 1)], unique=True)
        db.observations.create_index([('measurement_type', 1), ('source_day', 1), ('local_hour', 1)])
        db.observations.create_index([('zone_id', 1), ('measurement_type', 1)])
        if count != manifest['count'] or db.observations.count_documents({}) != count:
            raise ValueError('Mongo count mismatch')
        groups = list(db.observations.aggregate([{'$group': {'_id': '$measurement_type',
            'count': {'$sum': 1}, 'sum': {'$sum': '$value'}, 'min': {'$min': '$value'}, 'max': {'$max': '$value'}}}],
            allowDiskUse=True))
        for group in groups:
            ref = manifest['reference_by_measurement'][group['_id']]
            if group['count'] != ref['count'] or group['min'] != ref['min'] or group['max'] != ref['max']:
                raise ValueError('Mongo independent extrema/count mismatch')
            if not math.isclose(group['sum'], ref['sum'], rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError('Mongo independent sum mismatch')
        db.runs.insert_one({'_id': file_hash, 'count': count})
        status = connection.admin.command('replSetGetStatus')
        members = [{key: item.get(key) for key in ('name', 'health', 'stateStr', 'optimeDate')}
                   for item in status['members']]
        return {'status': 'PASS', 'count': count, 'independent_reference_verified': True,
                'elapsed_seconds': time.perf_counter() - started, 'members': members,
                'limits': 'Replica set: two data-bearing nodes + arbiter on one host; not sharding'}


# Qué hace: agrupa las observaciones igual que la consulta de PostgreSQL.
def query(measurement, start, end, zone, hour_start=0, hour_end=23):
    match = {'measurement_type': measurement, 'source_day': {'$gte': str(start), '$lte': str(end)},
             'local_hour': {'$gte': hour_start, '$lte': hour_end}}
    if zone is not None:
        match['zone_id'] = zone
    with primary() as connection:
        rows = list(connection.smartcity_final.observations.aggregate([
            {'$match': match}, {'$group': {'_id': {'source_day': '$source_day', 'zone_id': '$zone_id', 'unit': '$unit'},
                'count': {'$sum': 1}, 'total_value': {'$sum': '$value'}, 'min': {'$min': '$value'},
                'max': {'$max': '$value'}, 'demo_events': {'$sum': {'$toInt': '$demo_event'}}}},
            {'$sort': {'_id.source_day': 1}}], maxTimeMS=10000, allowDiskUse=True))
        return [{**row['_id'], **{key: value for key, value in row.items() if key != '_id'}} for row in rows]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'load'])
    parser.add_argument('--generation', type=Path, default=ROOT / 'data/final-20261111')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Use a new evidence path')
    if args.action == 'init':
        result = initialize()
    else:
        result = load(args.generation)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, default=str)
    print('Evidence:', args.report)
