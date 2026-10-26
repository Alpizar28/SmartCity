"""Read-only compatibility for saved Phase 5 evidence, NOT the current exporter."""
from datetime import datetime
from phase5_contract import (ROOT, canonical, digest, hourly_endpoint, local_to_utc,
                             numeric, stable_id)

OUT = ROOT / 'results/phase5'
PRIVATE = ROOT / 'private_results/phase5'
VERSION = 'madrid-draft-v1'


def base_document(source, source_version, station_code, channel_key, local, role):
    station = stable_id('station', source, str(station_code))
    channel = stable_id('channel', source, channel_key)
    utc = local_to_utc(local).isoformat().replace('+00:00', 'Z')
    ident = stable_id('measurement', channel, utc, role)
    return {'_id': ident, 'measurement_id': ident, 'sensor_id': None,
            'station_id': station, 'channel_id': channel, 'zone_id': None,
            'observed_at': {'$date': utc}, 'original_time': local.isoformat(),
            'original_timezone': 'Europe/Madrid', 'timestamp_role': role,
            'source_id': source, 'source_version': source_version,
            'schema_version': VERSION, 'catalog_version': VERSION,
            'data_origin': 'observed', 'transformation_method': 'phase5-normalize-v1'}


def validate_document(doc, catalogs=None):
    for key in ('measurement_id', 'station_id', 'channel_id', 'source_id', 'source_version',
                'measurement_type', 'original_time', 'original_timezone', 'data_origin'):
        if not isinstance(doc.get(key), str) or not doc[key]:
            raise ValueError('missing_' + key)
    if doc['_id'] != doc['measurement_id'] or doc['data_origin'] not in ('observed', 'derived', 'synthetic'):
        raise ValueError('identity_or_origin')
    if doc['sensor_id'] is not None:
        raise ValueError('Physical identity not supported by historical exporter')
    if numeric(doc['value']) is None:
        raise ValueError('nonfinite_value')
    utc = local_to_utc(datetime.fromisoformat(doc['original_time'])).isoformat().replace('+00:00', 'Z')
    if doc['observed_at'] != {'$date': utc}:
        raise ValueError('utc_roundtrip')
    if doc['source_version'] != doc['raw_reference']['sha256']:
        raise ValueError('provenance_hash')
    if catalogs:
        channel = catalogs['channels'].get(doc['channel_id'])
        if not channel or channel['station_id'] != doc['station_id']:
            raise ValueError('catalog_channel_or_station')
        if channel['source_id'] != doc['source_id'] or channel['category_id'] != doc['measurement_type']:
            raise ValueError('catalog_source_or_variable')
        if doc['station_id'] not in catalogs['stations']:
            raise ValueError('catalog_station')
        if doc['zone_id'] is not None and doc['zone_id'] not in catalogs['zones']:
            raise ValueError('catalog_zone')
        if catalogs['stations'][doc['station_id']]['zone_id'] != doc['zone_id']:
            raise ValueError('catalog_station_zone')
    return True
