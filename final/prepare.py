"""Generación analítica nueva: aire 2025–ago2026 + tráfico v2, sin duplicar enero.

Lee el ZIP y el v2 extraído sin modificarlos. Solo escribe una carpeta NUEVA.
No importa datos administrativos ni originales personales de accidentes.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/datasets/scripts')]
from phase5_contract import (base_document, canonical, digest, hourly_endpoint,
                             numeric, payload_hash, stable_id, validate_document)

CONTRACT = 'smartcity-analytics-v1'


def seal(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def flatten(doc, catalogs, source_day):
    station = catalogs['stations'][doc['station_id']]
    row = {'_id': doc['measurement_id'], 'channel_id': doc['channel_id'],
           'station_id': doc['station_id'], 'station_name': station.get('name'),
           'sensor_id': None, 'source_id': doc['source_id'],
           'source_version': doc['source_version'], 'measurement_type': doc['measurement_type'],
           'unit': doc['unit'], 'value': doc['value'],
           'observed_at': doc['observed_at']['$date'], 'original_time': doc['original_time'],
           'source_day': source_day, 'source_year': int(source_day[:4]),
           'source_month': int(source_day[5:7]), 'zone_id': doc['zone_id'],
           'latitude': station.get('latitude'), 'longitude': station.get('longitude'),
           'coordinate_crs': station.get('coordinate_crs'),
           'historical_location_verified': False, 'data_origin': 'observed',
           'input_contract': doc['schema_version'], 'input_payload_hash': doc['payload_hash'],
           'schema_version': CONTRACT, 'raw_reference': doc['raw_reference'],
           'element_type': doc.get('element_type'), 'speed_kmh': None,
           'occupancy_percent': None, 'load_index': None, 'demo_event': False}
    if doc['source_id'] == 'MAD-TRAFFIC':
        measurements = doc['measurements']
        for original, target in (('vmed', 'speed_kmh'), ('ocupacion', 'occupancy_percent'),
                                 ('carga', 'load_index')):
            if measurements[original]['status'] == 'valid':
                row[target] = measurements[original]['value']
        row['demo_event'] = doc['value'] > 2000
    row['record_hash'] = hashlib.sha256(canonical(row).encode()).hexdigest()
    return row
