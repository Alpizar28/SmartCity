"""Fail-closed staging validation. No I/O, automatic relabeling or data loading."""
from copy import deepcopy
from datetime import datetime
import math
import re

from .contract import METHOD, SOURCES, VERSION, hourly_endpoint, local_to_utc, payload_hash, stable_id, staging_key


def require(condition, code):
    if not condition:
        raise ValueError(code)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_document(doc, catalogs):
    """Validate a newly authored frozen-contract document against explicit catalogs.

    Catalogs are maps: sources[id], versions[sha], stations[id], channels[id].
    Version records contain source_id; channel records contain station_id,
    source_id, measurement_type, unit, unit_status. A snapshot belongs to exactly
    one source here. Catalogs must be independently reviewed, not inferred from
    each incoming reading by a future ingest service.
    """
    require(isinstance(doc, dict) and isinstance(catalogs, dict), 'expected_objects')
    for field in ('source_id', 'source_version', 'station_id', 'channel_id',
                  'measurement_type', 'original_time', 'original_timezone',
                  'timestamp_role', 'timestamp_status', 'quality_flag',
                  'catalog_version', 'transformation_method', 'unit_status'):
        require(text(doc.get(field)), 'missing_' + field)
    require(doc.get('schema_version') == VERSION, 'schema_version')
    require(doc['transformation_method'] == METHOD, 'transformation_method')
    require(not any(k in doc for k in ('_id', 'measurement_id', 'staging_key')), 'storage_or_final_identity_not_supported')
    require(doc['source_id'] in SOURCES, 'source_id')
    require(doc.get('data_origin') == 'observed', 'data_origin')
    for field in ('unit', 'candidate_unit', 'zone_id', 'element_type'):
        require(doc.get(field) is None or text(doc[field]), 'optional_text_' + field)
    for field in ('sensor_id', 'organization_id', 'user_id', 'installation_date', 'administrative_status'):
        require(doc.get(field) is None, 'unsupported_' + field)
    require(finite(doc.get('value')), 'finite_numeric_value_required')
    require(re.fullmatch(r'[0-9a-f]{64}', doc['source_version']) is not None, 'source_version_hash')
    ref = doc.get('raw_reference')
    require(isinstance(ref, dict), 'raw_reference')
    require(ref.get('sha256') == doc['source_version'], 'provenance_hash')
    require(text(ref.get('path')) and text(ref.get('column')), 'provenance_path_column')
    require(type(ref.get('row')) is int and ref['row'] >= 1, 'provenance_row')
    require(isinstance(doc.get('source_key'), list) and bool(doc['source_key']), 'source_key')
    require(doc['original_timezone'] == 'Europe/Madrid', 'original_timezone')
    try:
        local = datetime.fromisoformat(doc['original_time'])
        utc = local_to_utc(local)
    except (TypeError, ValueError) as exc:
        raise ValueError('original_time:' + str(exc)) from exc
    require(local.year == 2025 and (local.month == 1 or local == datetime(2025, 2, 1)), 'outside_January_scope')
    observed = doc.get('observed_at')
    if observed is not None:
        require(observed == {'$date': utc.isoformat().replace('+00:00', 'Z')}, 'utc_roundtrip')
    source = doc['source_id']
    expected_status = {'MAD-AIR': 'documented_local',
                       'MAD-METEO': 'assumed_same_H_format_pending_dictionary',
                       'MAD-TRAFFIC': 'assumed_local_label_pending_provider_confirmation'}
    require(doc['timestamp_status'] == expected_status[source], 'timestamp_evidence')
    require(doc['timestamp_role'] == ('publisher_label' if source == 'MAD-TRAFFIC' else 'hour_end'), 'timestamp_role')
    if source == 'MAD-METEO':
        require(doc.get('unit') is None and doc['unit_status'] == 'pending_dictionary', 'meteo_unit_unverified')
    else:
        require(text(doc.get('unit')), 'unit_required')
        require(doc['unit_status'] == ('verified_dictionary' if source == 'MAD-AIR' else 'documented_phase1_dictionary'), 'unit_evidence')
    if source != 'MAD-TRAFFIC':
        require(doc.get('zone_id') is None, 'zone_not_accredited')
        require(doc.get('measurements') is None, 'traffic_payload_only')
        require(len(doc['source_key']) == 5, 'hourly_source_key')
        code, variable, point, day, hour = doc['source_key']
        require(text(code) and text(variable) and text(day) and text(hour), 'hourly_source_key_types')
        require((point is None) if source == 'MAD-METEO' else text(point), 'channel_point')
        channel_key = [code, variable, point]
        require(doc['measurement_type'] == source + ':' + variable, 'measurement_type')
        require(re.fullmatch(r'H(0[1-9]|1[0-9]|2[0-4])', hour) is not None, 'hour_label')
        require(day.startswith('2025-01-') and hourly_endpoint(day, int(hour[1:])) == local, 'source_clock')
    else:
        require(len(doc['source_key']) == 3, 'traffic_source_key')
        code, clock, element = doc['source_key']
        require(all(text(v) for v in (code, clock, element)), 'traffic_source_key_types')
        require(datetime.fromisoformat(clock) == local and local.month == 1, 'source_clock')
        require(doc.get('element_type') == element, 'element_type')
        channel_key = [code, element]
        require(doc['measurement_type'] == 'MAD-TRAFFIC:intensidad' and doc['unit'] == 'veh/h', 'traffic_variable_unit')
        require(type(doc.get('interval_minutes')) is int and doc['interval_minutes'] > 0, 'interval_minutes')
        require(text(ref.get('member')), 'traffic_zip_member')
        measurements = doc.get('measurements')
        require(isinstance(measurements, dict) and set(measurements) == {'ocupacion', 'carga', 'vmed'}, 'traffic_measurements')
        for name, item in measurements.items():
            require(isinstance(item, dict), 'traffic_measurement_object')
            require(item.get('value') is None or finite(item['value']), 'traffic_finite_value')
            require(isinstance(item.get('raw_value'), str), 'traffic_raw_value')
            urb_speed = name == 'vmed' and element == 'URB'
            expected_qa = ('URB_zero_not_accepted_as_measured_speed' if urb_speed
                           else 'requires_type_specific_QA')
            require(item.get('applicability') == expected_qa, 'traffic_QA')
            if urb_speed:
                require(item.get('value') is None, 'urban_speed_not_accredited')
            require(item.get('data_origin') == 'observed', 'traffic_origin')
            require(item.get('unit') == ('km/h' if name == 'vmed' else 'percent'), 'traffic_unit')
    require(doc['station_id'] == stable_id('station', source, code), 'station_identity')
    require(doc['channel_id'] == stable_id('channel', source, channel_key), 'channel_identity')
    require(source in catalogs.get('sources', {}), 'catalog_source')
    require(catalogs.get('versions', {}).get(doc['source_version'], {}).get('source_id') == source, 'catalog_version_source')
    station = catalogs.get('stations', {}).get(doc['station_id'], {})
    channel = catalogs.get('channels', {}).get(doc['channel_id'], {})
    require(station.get('source_id') == source and station.get('source_key') == code, 'catalog_station')
    for key in ('source_id', 'station_id', 'measurement_type'):
        require(channel.get(key) == doc[key], 'catalog_channel_' + key)
    require('unit' in channel and channel['unit'] == doc.get('unit'), 'catalog_channel_unit')
    require(channel.get('unit_status') == doc['unit_status'], 'catalog_channel_unit_status')
    require(station.get('zone_id') == doc.get('zone_id'), 'catalog_zone')
    if doc.get('zone_id') is not None:
        require(doc['zone_id'] in catalogs.get('zones', {}), 'catalog_zone_missing')
    require(doc.get('payload_hash') == payload_hash(doc), 'payload_hash')
    return True


class StagingLedger:
    """In-memory review helper, not a persistent ingest service.

    Same source snapshot/channel/original key is idempotent; contradictory
    content is returned for quarantine without replacing the accepted record.
    """
    def __init__(self):
        self.records = {}
        self.quarantine = []

    def accept(self, document, catalogs):
        validate_document(document, catalogs)
        key = staging_key(document)
        previous = self.records.get(key)
        if previous is not None:
            if previous['payload_hash'] == document['payload_hash']:
                return 'duplicate'
            self.quarantine.append(deepcopy(document))
            return 'quarantined'
        self.records[key] = deepcopy(document)
        return 'accepted'
