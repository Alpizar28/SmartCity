"""Madrid draft-v1: shared identities and fail-closed local-time conversion."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
import re
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified-v1'
PRIVATE = ROOT / 'private_results/unified-v1'
VERSION = 'madrid-draft-v1'
IMPLEMENTATION = 'unified-v1'
TRANSFORMATION_VERSION = 'madrid-normalize-v2'
SOURCES = ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC')
ACCEPTED_TIME = {'documented_local', 'publisher_confirmed_local'}
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


def base_document(source, source_version, station_code, channel_key, local, role,
                  timestamp_status='documented_local'):
    if source not in SOURCES:
        raise ValueError('unknown_source')
    station = stable_id('station', source, str(station_code))
    channel = stable_id('channel', source, station, channel_key)
    utc, time_error = None, None
    try:
        converted = local_to_utc(local).isoformat().replace('+00:00', 'Z')
        if timestamp_status in ACCEPTED_TIME:
            utc = converted
        else:
            time_error = 'unconfirmed_temporal_semantics'
    except ValueError as exc:
        time_error = str(exc)
    ident = stable_id('measurement', channel, utc, role) if utc else None
    return {'_id': ident, 'measurement_id': ident, 'sensor_id': None,
            'station_id': station, 'channel_id': channel, 'zone_id': None,
            'observed_at': {'$date': utc} if utc else None, 'original_time': local.isoformat(),
            'original_timezone': 'Europe/Madrid', 'timestamp_role': role,
            'timestamp_status': timestamp_status, 'time_error': time_error,
            'source_id': source, 'source_version': source_version,
            'schema_version': VERSION, 'catalog_version': VERSION,
            'data_origin': 'observed', 'transformation_method': 'madrid-normalize',
            'transformation_version': TRANSFORMATION_VERSION}


def payload_hash(doc):
    """Exclude physical row locator, hash itself and nonsemantic diagnostics."""
    return stable_id('payload', {k:v for k,v in doc.items()
                                if k not in ('raw_reference', 'payload_hash', 'time_error')})


def validate_bundle():
    """Only completed, hash-verified generations may be consumed by local loaders."""
    report = json.loads((OUT/'preparation.json').read_text())
    if report.get('implementation') != IMPLEMENTATION:
        raise ValueError('implementation_generation')
    if report['configuration']['contract_sha256'] != digest(__file__):
        raise ValueError('contract_changed_since_preparation')
    if report['configuration']['script_sha256'] != digest(ROOT/'scripts/phase5_prepare.py'):
        raise ValueError('exporter_changed_since_preparation')
    for filename, expected in report['private_output_hashes'].items():
        if digest(PRIVATE/filename) != expected:
            raise ValueError('changed_output_' + filename)
    return report


def validate_document(doc, catalogs=None):
    required = {'_id','measurement_id','station_id','channel_id','source_id','source_version',
                'measurement_type','original_time','original_timezone','data_origin','sensor_id',
                'zone_id','value','unit','observed_at','raw_reference','schema_version','catalog_version',
                'payload_hash','transformation_method','transformation_version','timestamp_role',
                'timestamp_status','quality_flag','unit_status'}
    if not isinstance(doc, dict) or required - doc.keys():
        raise ValueError('missing_required_fields')
    reference = doc['raw_reference']
    if (not isinstance(reference, dict) or not isinstance(reference.get('path'), str)
            or not reference['path'] or not isinstance(reference.get('row'), int)
            or reference['row'] < 2 or not isinstance(reference.get('column'), str)):
        raise ValueError('raw_reference_locator')
    if doc['original_timezone'] != 'Europe/Madrid':
        raise ValueError('original_timezone')
    if doc.get('source_id') not in SOURCES or doc.get('schema_version') != VERSION or doc.get('catalog_version') != VERSION:
        raise ValueError('source_or_contract_version')
    if doc.get('timestamp_status') not in ACCEPTED_TIME or doc.get('time_error'):
        raise ValueError('unaccepted_time')
    for key in ('transformation_method', 'transformation_version', 'timestamp_role', 'quality_flag', 'unit_status'):
        if not isinstance(doc.get(key), str) or not doc[key]:
            raise ValueError('missing_' + key)
    if doc['timestamp_role'] not in ('hour_end', 'publisher_label'):
        raise ValueError('timestamp_role')
    if not re.fullmatch('[0-9a-f]{64}', doc.get('source_version', '')):
        raise ValueError('source_version_hash')
    if doc.get('payload_hash') != payload_hash(doc):
        raise ValueError('payload_hash')
    for k in ('measurement_id', 'station_id', 'channel_id', 'source_id', 'source_version',
              'measurement_type', 'original_time', 'original_timezone', 'data_origin'):
        if not isinstance(doc.get(k), str) or not doc[k]:
            raise ValueError('missing_' + k)
    if doc['_id'] != doc['measurement_id'] or doc['data_origin'] != 'observed':
        raise ValueError('identity_or_origin')
    if doc['sensor_id'] is not None:
        raise ValueError('Physical identity not supported by this draft exporter')
    if isinstance(doc['value'], bool) or not isinstance(doc['value'], (int, float)) or numeric(doc['value']) is None:
        raise ValueError('nonfinite_value')
    utc = local_to_utc(datetime.fromisoformat(doc['original_time'])).isoformat().replace('+00:00', 'Z')
    if doc['observed_at'] != {'$date': utc}:
        raise ValueError('utc_roundtrip')
    if doc['source_version'] != doc['raw_reference']['sha256']:
        raise ValueError('provenance_hash')
    if doc['measurement_id'] != stable_id('measurement', doc['channel_id'], utc, doc['timestamp_role']):
        raise ValueError('measurement_identity')
    if (doc.get('unit') is None) != (doc['unit_status'] == 'pending_dictionary'):
        raise ValueError('unit_status')
    if catalogs:
        channel = catalogs['channels'].get(doc['channel_id'])
        if not channel or channel['station_id'] != doc['station_id']:
            raise ValueError('catalog_channel_or_station')
        if channel['source_id']!=doc['source_id'] or channel['measurement_type']!=doc['measurement_type']:
            raise ValueError('catalog_source_or_variable')
        if doc['station_id'] not in catalogs['stations']:
            raise ValueError('catalog_station')
        station = catalogs['stations'][doc['station_id']]
        if station['source_id'] != doc['source_id']:
            raise ValueError('catalog_station_source')
        if doc['station_id'] != stable_id('station', doc['source_id'], station['source_key']):
            raise ValueError('station_identity')
        if doc['channel_id'] != stable_id('channel', doc['source_id'], doc['station_id'], channel['source_key']):
            raise ValueError('channel_identity')
        typ = catalogs['measurement_types'].get(doc['measurement_type'])
        if (not typ or typ['source_id'] != doc['source_id'] or typ['unit'] != doc.get('unit')
                or typ['unit_status'] != doc['unit_status']):
            raise ValueError('catalog_type_or_unit')
        if catalogs['source_versions'].get(doc['source_version'], {}).get('source_id') != doc['source_id']:
            raise ValueError('catalog_source_version')
        if doc['zone_id'] is not None and doc['zone_id'] not in catalogs['zones']:
            raise ValueError('catalog_zone')
        if catalogs['stations'][doc['station_id']]['zone_id']!=doc['zone_id']:
            raise ValueError('catalog_station_zone')
    return True
