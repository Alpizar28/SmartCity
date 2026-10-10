"""Madrid draft-v1: shared identities and fail-closed local-time conversion."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/phase5'
PRIVATE = ROOT / 'private_results/phase5'
VERSION = 'madrid-draft-v1'
ZONE = ZoneInfo('Europe/Madrid')


def digest(path):
    h = sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def stable_id(kind, *parts):
    # Length-safe JSON tuple, never concatenation with ambiguous separators or values in keys.
    return kind + ':' + sha256(canonical(['sca-id-v1', *parts]).encode()).hexdigest()


def numeric(value):
    try:
        n = float(str(value).strip().replace(',', '.'))
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def local_to_utc(local, fold=None):
    """Reject nonexistent/ambiguous wall clock. Explicit fold only with source evidence."""
    if local.tzinfo is not None:
        raise ValueError('Expected original naive local wall clock')
    candidates = {}
    for f in (0, 1):
        aware = local.replace(tzinfo=ZONE, fold=f)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(ZONE).replace(tzinfo=None) == local:
            candidates[f] = utc
    if not candidates:
        raise ValueError('nonexistent_local_time')
    if len(set(candidates.values())) > 1 and fold is None:
        raise ValueError('ambiguous_local_time_requires_publisher_fold')
    if fold is not None and fold not in candidates:
        raise ValueError('invalid_fold')
    return candidates[fold if fold is not None else min(candidates)]


def hourly_endpoint(day, hour):
    if not 1 <= hour <= 24:
        raise ValueError('H01..H24 required')
    return datetime.fromisoformat(day) + timedelta(hours=hour)


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
    for k in ('measurement_id', 'station_id', 'channel_id', 'source_id', 'source_version',
              'measurement_type', 'original_time', 'original_timezone', 'data_origin'):
        if not isinstance(doc.get(k), str) or not doc[k]:
            raise ValueError('missing_' + k)
    if doc['_id'] != doc['measurement_id'] or doc['data_origin'] not in ('observed', 'derived', 'synthetic'):
        raise ValueError('identity_or_origin')
    if doc['sensor_id'] is not None:
        raise ValueError('Physical identity not supported by this draft exporter')
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
        if channel['source_id']!=doc['source_id'] or channel['category_id']!=doc['measurement_type']:
            raise ValueError('catalog_source_or_variable')
        if doc['station_id'] not in catalogs['stations']:
            raise ValueError('catalog_station')
        if doc['zone_id'] is not None and doc['zone_id'] not in catalogs['zones']:
            raise ValueError('catalog_zone')
        if catalogs['stations'][doc['station_id']]['zone_id']!=doc['zone_id']:
            raise ValueError('catalog_station_zone')
    return True
