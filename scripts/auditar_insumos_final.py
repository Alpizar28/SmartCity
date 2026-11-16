"""Audita insumos locales sin extraer el ZIP, cargar motores ni modificar datasets.

Solo usa la biblioteca estándar. El perfil raw NO sustituye una exportación
normalizada ni demuestra procesamiento Spark. El informe no contiene filas privadas.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/datasets/scripts'))
from phase5_contract import hourly_endpoint, local_to_utc


def sha256_stream(stream):
    digest = hashlib.sha256()
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    return digest.hexdigest()


def profile_air(stream):
    """Perfila slots numéricos V y reloj con la conversión contractual existente.

    No aplica catálogos/unidades ni crea IDs: los candidatos no son aceptados ETL.
    Cada fila diaria debe tener clave única; si no, se rechaza el perfil.
    """
    years = {}
    daily_keys = set()
    clocks = {}
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'), delimiter=';')
    required = {'PROVINCIA', 'MUNICIPIO', 'ESTACION', 'MAGNITUD', 'PUNTO_MUESTREO', 'ANO', 'MES', 'DIA'}
    required.update(f'{prefix}{hour:02d}' for prefix in ('H', 'V') for hour in range(1, 25))
    if set(reader.fieldnames or []) != required:
        raise ValueError('Esquema CSV de aire inesperado')
    for row in reader:
        key = tuple(row[name] for name in ('PROVINCIA', 'MUNICIPIO', 'ESTACION',
                    'MAGNITUD', 'PUNTO_MUESTREO', 'ANO', 'MES', 'DIA'))
        if key in daily_keys:
            raise ValueError('Clave diaria duplicada: requiere auditoría de conflictos')
        daily_keys.add(key)
        day = datetime(int(row['ANO']), int(row['MES']), int(row['DIA'])).date().isoformat()
        year = row['ANO']
        stats = years.setdefault(year, {'counts': Counter(), 'months': Counter(),
                                       'min_original_day': day, 'max_original_day': day})
        stats['min_original_day'] = min(stats['min_original_day'], day)
        stats['max_original_day'] = max(stats['max_original_day'], day)
        for hour in range(1, 25):
            stats['counts']['selected_slots'] += 1
            cache_key = (day, hour)
            if cache_key not in clocks:
                try:
                    local_to_utc(hourly_endpoint(day, hour))
                    clocks[cache_key] = 'valid'
                except ValueError as exc:
                    clocks[cache_key] = str(exc)
            clock = clocks[cache_key]
            if clock != 'valid':
                stats['counts'][clock] += 1
                continue
            if row[f'V{hour:02d}'] != 'V':
                stats['counts']['provider_flag'] += 1
                continue
            try:
                value = float(row[f'H{hour:02d}'].strip().replace(',', '.'))
            except ValueError:
                stats['counts']['non_numeric'] += 1
                continue
            if not math.isfinite(value):
                stats['counts']['non_finite'] += 1
                continue
            stats['counts']['candidate_slots'] += 1
            stats['months'][day[:7]] += 1
    return years
