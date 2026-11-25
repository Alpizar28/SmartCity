"""Consultas MongoDB del panel y carga de las demostraciones separadas."""
import argparse
from pathlib import Path

from bson.json_util import loads
from pymongo import UpdateOne
from pymongo.write_concern import WriteConcern

from final.mongo import primary

FIXTURES = Path(__file__).resolve().parents[1] / 'sprint1/mongodb/academico/fixtures.json'
LIMIT = 100
ACADEMIC_COLLECTIONS = ('sensor_types', 'sensors', 'readings', 'dynamic_information')
TITLES = {
    'MG01': 'Lecturas por sensor (demo)',
    'MG02': 'Lecturas por fecha',
    'MG04': 'Eventos críticos (demo)',
    'MG05': 'Alertas por distrito (demo)',
    'MG06': 'Promedio por distrito',
    'MG07': 'Promedio por tipo de sensor (demo)',
    'MG09': 'Lecturas por fuente y medición',
    'MG10': 'Lecturas con filtros combinados',
}
NOTES = {
    'MG01': 'Lecturas sintéticas del laboratorio académico, separadas de las lecturas municipales.',
    'MG02': 'Se muestran hasta 100 lecturas del periodo seleccionado, en orden de fecha.',
    'MG04': 'Hasta 100 eventos derivados de lecturas superiores a 2.000 veh/h. No son avisos oficiales ni accidentes.',
    'MG05': 'Alertas de una reproducción local de la regla demo. Solo se emiten para eventos con distrito registrado.',
    'MG06': 'Promedios por distrito para una sola medición y unidad. Excluye lecturas sin distrito.',
    'MG07': 'Dispositivos y lecturas sintéticos del laboratorio académico. No representan sensores físicos de Madrid.',
    'MG09': 'La agregación cuenta observaciones de la carga completa por fuente, tipo de medición y unidad.',
    'MG10': 'Se muestran hasta 100 lecturas, ordenadas por valor, que cumplen todos los filtros.',
}


def load_demos():
    fixtures = loads(FIXTURES.read_text(encoding='utf-8'))
    with primary() as connection:
        db = connection.get_database('smartcity_final', write_concern=WriteConcern('majority', wtimeout=60000))
        if not db.runs.find_one():
            raise ValueError('Carga primero las observaciones del laboratorio final')
        academic = connection.get_database('smartcity_final_academic', write_concern=db.write_concern)
        for name in ACADEMIC_COLLECTIONS:
            documents = fixtures[name]
            academic[name].bulk_write([UpdateOne(doc, {'$setOnInsert': doc}, upsert=True)
                                       for doc in documents])
        list(db.observations.aggregate([
            {'$match': {'measurement_type': 'MAD-TRAFFIC:intensidad', 'demo_event': True,
                        'zone_id': {'$type': 'string'}}},
            {'$project': {'zone_id': 1, 'source_day': 1, 'data_origin': {'$literal': 'derived'},
                          'official_alert': {'$literal': False}, 'emitted_at': '$$NOW'}},
            {'$merge': {'into': 'demo_alerts', 'on': '_id',
                        'whenMatched': 'keepExisting', 'whenNotMatched': 'insert'}},
        ], maxTimeMS=60000))
        counts = {name: academic[name].count_documents({}) for name in ACADEMIC_COLLECTIONS}
        counts['demo_alerts'] = db.demo_alerts.count_documents({})
        return counts


class DemoNotLoaded(RuntimeError):
    pass


def sensors():
    with primary() as connection:
        rows = list(connection.smartcity_final_academic.sensors.find(
            {'data_origin': 'synthetic'}, {'name': 1}).sort('name', 1))
        if not rows:
            raise DemoNotLoaded('No academic sensors')
        return rows


def query(code, *, sensor=None, measurement=None, unit=None, start=None, end=None,
          zone=None, minimum=None):
    with primary() as connection:
        db = connection.smartcity_final
        academic = connection.smartcity_final_academic
        if code == 'MG01':
            return list(academic.readings.find(
                {'sensor_id': sensor, 'data_origin': 'synthetic'},
                {'_id': 0, 'observed_at': 1, 'value': 1, 'unit': 1}
            ).sort([('observed_at', 1), ('_id', 1)]).limit(LIMIT).max_time_ms(8000))
        if code == 'MG07':
            if not academic.readings.find_one({'data_origin': 'synthetic'}):
                raise DemoNotLoaded('No academic readings')
            return list(academic.readings.aggregate([
                {'$match': {'data_origin': 'synthetic'}},
                {'$lookup': {'from': 'sensors', 'localField': 'sensor_id',
                             'foreignField': '_id', 'as': 'sensor'}},
                {'$unwind': '$sensor'},
                {'$lookup': {'from': 'sensor_types', 'localField': 'sensor.sensor_type',
                             'foreignField': '_id', 'as': 'kind'}},
                {'$unwind': '$kind'},
                {'$group': {'_id': {'device_type': '$kind.name', 'measurement_type': '$measurement_type',
                                    'unit': '$unit'}, 'count': {'$sum': 1}, 'mean': {'$avg': '$value'}}},
                {'$sort': {'_id.device_type': 1, '_id.measurement_type': 1, '_id.unit': 1}},
            ], maxTimeMS=8000))
        if code == 'MG05':
            if 'demo_alerts' not in db.list_collection_names():
                raise DemoNotLoaded('No demo alerts')
            return list(db.demo_alerts.aggregate([
                {'$match': {'official_alert': False}},
                {'$group': {'_id': {'zone_id': '$zone_id'}, 'count': {'$sum': 1}}},
                {'$sort': {'count': -1, '_id.zone_id': 1}},
            ], maxTimeMS=8000))
        if code == 'MG09':
            return list(db.observations.aggregate([
                {'$group': {'_id': {'source_id': '$source_id', 'measurement_type': '$measurement_type',
                                    'unit': '$unit'}, 'count': {'$sum': 1}}},
                {'$sort': {'count': -1, '_id.measurement_type': 1}},
            ], maxTimeMS=15000))
        match = {}
        if start is not None and end is not None:
            match['source_day'] = {'$gte': start.isoformat(), '$lte': end.isoformat()}
        if measurement is not None:
            match.update(measurement_type=measurement, unit=unit)
        if zone is not None:
            match['zone_id'] = zone
        if code == 'MG06':
            match.setdefault('zone_id', {'$type': 'string'})
            return list(db.observations.aggregate([
                {'$match': match},
                {'$group': {'_id': {'zone_id': '$zone_id'}, 'count': {'$sum': 1}, 'mean': {'$avg': '$value'}}},
                {'$sort': {'mean': -1, '_id.zone_id': 1}},
            ], maxTimeMS=10000))
        if code == 'MG04':
            match.update(measurement_type='MAD-TRAFFIC:intensidad', demo_event=True)
        if code == 'MG10':
            match['value'] = {'$gte': minimum}
        if code not in ('MG02', 'MG04', 'MG10'):
            raise ValueError('Unknown MongoDB query')
        order = [('value', -1), ('observed_at', 1)] if code == 'MG10' else [('source_day', 1), ('observed_at', 1)]
        return list(db.observations.find(match, {
            '_id': 0, 'source_day': 1, 'observed_at': 1, 'station_name': 1,
            'zone_id': 1, 'value': 1, 'unit': 1,
        }).sort(order).limit(LIMIT).max_time_ms(15000))


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(load_demos())
