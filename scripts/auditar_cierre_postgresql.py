#!/usr/bin/env python3
"""Read the private JP ZIP in place. Standard library only; never extract originals.

Hashes the six v2 outputs and seven originals; independently checks all accepted
identities, references and PG01--PG10 summaries against the historical SQL report.
Only an aggregate report is written (exclusive creation), never private rows.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import math
from pathlib import Path, PurePosixPath
import sqlite3
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/datasets/scripts'))
from phase5_contract import canonical, digest, local_to_utc, payload_hash, stable_id
from unified_synthetic import build_administrative_seed

PREFIX = 'research/datasets/private_results/expanded-v2-2025-01/'
HISTORICAL = ROOT / 'research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_members(archive):
    names = archive.namelist()
    require(len(names) == len(set(names)), 'Duplicate ZIP members')
    for item in archive.infolist():
        path = PurePosixPath(item.filename)
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename,
                'Unsafe ZIP member')
        require((item.external_attr >> 16) & 0o170000 != 0o120000, 'ZIP symlink')


def validate_historical(preparation, historical):
    require(historical.get('status') == 'PASS', 'Historical SQL report is not PASS')
    require(historical.get('generation') == preparation['generation']
            and historical.get('contract') == preparation['contract'], 'Historical generation/contract')
    require(historical.get('shared_server_modified') is False, 'Historical server scope')
    pg = historical['postgresql']
    require(pg.get('count') == pg.get('metadata_verified') == preparation['accepted'], 'Historical volume/metadata')
    require(pg.get('count_by_source') == {s: c['accepted'] for s,c in preparation['by_source'].items()}, 'Historical sources')
    require(pg.get('sensor_links') == 0 and pg.get('replay_verified') is True, 'Historical links/replay')
    require(pg.get('container_removed') is True and pg.get('anonymous_volumes_removed') is True, 'Historical cleanup')


def administrative_results(catalogs, admin):
    sensors = admin['sensors']
    cats = {t['category_id']: t['name'] for t in catalogs['measurement_types'].values()}
    bycat = Counter(s['category_id'] for s in sensors)
    bystation = Counter(s['station_id'] for s in sensors)
    locations = {s: stable_id('location', s, 'current-inventory') for s in bystation}
    bystate = Counter(s['administrative_status'] for s in sensors)
    byorg = Counter(s['organization_id'] for s in sensors)
    byyear = Counter(int(s['installation_date'][:4]) for s in sensors if s['installation_date'])
    byzone = Counter()
    for s in sensors:
        zone = catalogs['stations'][s['station_id']]['zone_id']
        if zone is not None:
            byzone[zone] += 1
    ranks = {count: rank for rank, count in enumerate(sorted(set(byzone.values()), reverse=True), 1)}
    channels = Counter(c['station_id'] for c in catalogs['channels'].values())
    return {
        'PG01': [dict(category_id=k, category_name=cats[k], sensor_count=v) for k, v in sorted(bycat.items())],
        'PG02': [dict(station_id=k, location_id=locations[k], location_name=catalogs['stations'][k]['name'],
                      sensor_count=v) for k, v in sorted(bystation.items())],
        'PG03': [dict(administrative_status=k, sensor_count=v) for k, v in sorted(bystate.items())],
        'PG04': [dict(organization_id=o['organization_id'], name=o['name'], sensor_count=byorg[o['organization_id']])
                 for o in sorted(admin['organizations'], key=lambda x: x['organization_id'])],
        'PG05': sorted([dict(location_id=locations[k], name=catalogs['stations'][k]['name'], sensor_count=v)
                        for k, v in bystation.items()], key=lambda x: (-x['sensor_count'], x['location_id'])),
        'PG06': [dict(installation_year=k, sensor_count=v) for k, v in sorted(byyear.items())],
        'PG07': [],
        'PG08': [dict(zone_id=k, name=catalogs['zones'][k]['name'], sensor_count=v, zone_rank=ranks[v])
                 for k, v in sorted(byzone.items(), key=lambda x: (-x[1], x[0]))],
        'PG10': [dict(station_id=k, channel_count=channels[k]) for k in sorted(catalogs['stations'])],
    }


def audit(path):
    result = {'status': 'FAIL', 'base_commit': 'b77e5497fa28f8c2b483b06e2e593d96b7bd0a5d',
              'started_at': datetime.now(timezone.utc).isoformat(), 'archive_name': path.name,
              'archive_bytes': path.stat().st_size, 'generation': 'expanded-v2-2025-01',
              'contract': 'madrid-draft-v2', 'shared_server_modified': False,
              'scope': 'v2 outputs, source hashes, accepted rows and historical PostgreSQL evidence; not a new massive SQL load',
              'files_verified': {}, 'source_hashes': {}}
    with zipfile.ZipFile(path) as z:
        safe_members(z)
        manifest = {f['path']: f for f in json.loads(z.read('DATASET_COMPLETO_manifest.json'))['files']}
        prep = json.loads(z.read(PREFIX + 'preparation.json'))
        historical = json.loads(HISTORICAL.read_text())
        require(prep['generation'] == result['generation'] and prep['contract'] == result['contract'], 'Generation')
        validate_historical(prep, historical)
        for name, expected in prep['code_hashes'].items():
            require(digest(ROOT / name) == expected, 'Preparation code changed: ' + name)
        for name, expected in historical['source_hashes'].items():
            if not name.endswith('.js'):
                require(digest(ROOT / name) == expected, 'SQL execution code changed: ' + name)
        ddl = 'research/datasets/scripts/phase5_postgresql.sql'
        require(z.read(ddl) == (ROOT / ddl).read_bytes(), 'Archived/current DDL mismatch')
        result['source_hashes'] = {n: digest(ROOT / n) for n in
            [*prep['code_hashes'], *(n for n in historical['source_hashes'] if not n.endswith('.js')),
             ddl, 'sprint1/postgres/queries.sql', 'sprint1/postgres/contract_v2.sql',
             str(HISTORICAL.relative_to(ROOT)), str(Path(__file__).relative_to(ROOT))]}

        def verify(name, expected=None):
            h, size = sha256(), 0
            with z.open(name) as f:
                for block in iter(lambda: f.read(1 << 20), b''):
                    h.update(block)
                    size += len(block)
            entry = manifest[name]
            require(h.hexdigest() == entry['sha256'] and size == entry['bytes'], 'Archive manifest: ' + name)
            require(expected is None or h.hexdigest() == expected, 'Preparation hash: ' + name)
            result['files_verified'][name] = {'bytes': size, 'sha256': h.hexdigest()}

        verify(PREFIX + 'preparation.json')
        for name, expected in prep['output_hashes'].items():
            if name != 'accepted.extjsonl':
                verify(PREFIX + name, expected)
        for name, expected in prep['source_hashes'].items():
            verify('research/datasets/' + name, expected)
        verify('research/datasets/raw/sprint1-v2/traffic_dictionary.pdf',
               '17562978ce1b7930c6c720db37f055cb3459e30b8cec50d2a671682b215b9de9')
        catalogs = json.loads(z.read(PREFIX + 'catalogs.json'))
        admin = json.loads(z.read(PREFIX + 'administrative_seed.json'))
        expected_admin = build_administrative_seed(catalogs, prep['output_hashes']['catalogs.json'])
        expected_admin['schema_version'] = 'madrid-draft-v2'
        require(admin == expected_admin, 'Administrative seed not reproducible')
        require(all(c['sensor_id'] is None for c in catalogs['channels'].values()), 'Unexpected physical links')
        require(all(c['catalog_basis'] == 'observations' for c in catalogs['channels'].values()), 'Catalog basis changed')
        for s in catalogs['stations'].values():
            require(s['station_id'] == stable_id('station', s['source_id'], s['source_key']), 'Station identity')
        for c in catalogs['channels'].values():
            require(c['channel_id'] == stable_id('channel', c['source_id'], c['station_id'], c['source_key']), 'Channel identity')
        # Bounded inventory of every catalog/metadata description supplied by JP.
        # Only field names/counts are retained, never person-level raw records.
        result['catalog_search'] = []
        for name in z.namelist():
            if name.endswith('.json') and any(token in name for token in
                    ('catalogs.json', '-META-schema_quality.json', 'administrative_manifest.json')):
                verify(name)
                obj = json.loads(z.read(name))
                sensor_fields = Counter()
                def walk(value):
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if k == 'sensor_id':
                                sensor_fields['nonnull' if v is not None else 'null'] += 1
                            walk(v)
                    elif isinstance(value, list):
                        for v in value:
                            walk(v)
                walk(obj)
                result['catalog_search'].append({'path': name, 'top_level_fields': list(obj) if isinstance(obj,dict) else [],
                                                 'sensor_id_fields': dict(sensor_fields)})
        result['catalog_counts'] = {k: len(v) for k, v in catalogs.items() if isinstance(v, dict)}
        result['administration'] = {'counts': {k: len(admin[k]) for k in ('sensors', 'users', 'organizations')},
            'generator': admin['generator_version'], 'seed': admin['seed'], 'origin': 'synthetic',
            'reproduced_exactly': True, 'physical_sensor_channel_links': 0}
        result['official_headers'] = {}
        for name in prep['source_hashes']:
            if 'inventory' in name or name in ('raw/MAD-AIR-file.attempt1.bin', 'raw/MAD-TRAFFIC-META-file.attempt1.bin'):
                with z.open('research/datasets/' + name) as f:
                    result['official_headers'][name] = f.readline().decode('utf-8-sig').strip()
        # The traffic original is itself a ZIP. Only this 93 MB original is held
        # briefly in memory to inspect its CSV header, never extracted or executed.
        with zipfile.ZipFile(io.BytesIO(z.read('research/datasets/raw/MAD-TRAFFIC-Jan2025.record89.bin'))) as traffic:
            safe_members(traffic)
            for name in traffic.namelist():
                if name.lower().endswith('.csv'):
                    with traffic.open(name) as f:
                        result['official_headers']['traffic_zip/' + name] = f.readline().decode('utf-8-sig').strip()

        counts, activity, ids = Counter(), {}, set()
        h, bytes_read = sha256(), 0
        # Reuse the original ledger read-only, copying only its 408 MB into a
        # temporary owned directory; no multi-GB extraction or source mutation.
        with tempfile.TemporaryDirectory(prefix='smartcity-audit-', dir='/tmp/opencode') as tmp:
            ledger_path = Path(tmp) / 'identities.sqlite'
            with z.open(PREFIX + 'identities.sqlite') as src, ledger_path.open('xb') as dst:
                for block in iter(lambda: src.read(1 << 20), b''):
                    dst.write(block)
            with sqlite3.connect(f'file:{ledger_path}?mode=ro', uri=True) as ledger:
                require(ledger.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Ledger integrity')
                require(ledger.execute('SELECT count(*) FROM identities').fetchone()[0] == prep['accepted'], 'Ledger count')
                with z.open(PREFIX + 'accepted.extjsonl') as f:
                    for line in f:
                        h.update(line)
                        bytes_read += len(line)
                        d = json.loads(line)
                        c = catalogs['channels'][d['channel_id']]
                        s = catalogs['stations'][d['station_id']]
                        t = catalogs['measurement_types'][d['measurement_type']]
                        require(d['schema_version'] == d['catalog_version'] == 'madrid-draft-v2', 'Contract')
                        require(d['data_origin'] == 'observed' and d['sensor_id'] is None, 'Origin/sensor')
                        require(isinstance(d['value'], (int,float)) and not isinstance(d['value'],bool)
                                and math.isfinite(d['value']), 'Value domain')
                        if d['source_id'] == 'MAD-AIR':
                            require(d['quality_flag']=='V' and d['timestamp_status']=='documented_local'
                                    and d['integration_sample_count'] is None, 'Air v2 acceptance')
                        else:
                            require(d['source_id']=='MAD-TRAFFIC' and d['quality_flag']=='N'
                                    and d['timestamp_status']=='publisher_confirmed_local'
                                    and d['timestamp_role']=='publisher_label' and d['interval_minutes']==15
                                    and type(d['integration_sample_count']) is int and d['integration_sample_count']>0
                                    and d['element_type'] in ('URB','M30') and d['value']>=0, 'Traffic v2 acceptance')
                        require(d['zone_scope'] == ('unknown' if d['zone_id'] is None else
                                'current_inventory_not_historically_verified'), 'Zone scope')
                        require(c['station_id'] == d['station_id'] and c['measurement_type'] == d['measurement_type'], 'Channel')
                        require(c['source_id'] == s['source_id'] == t['source_id'] == d['source_id'], 'Source')
                        require(t['unit'] == d['unit'] and t['unit_status'] == d['unit_status'] and s['zone_id'] == d['zone_id'], 'Unit/zone')
                        require(catalogs['source_versions'][d['source_version']]['source_id'] == d['source_id'], 'Version source')
                        utc = local_to_utc(datetime.fromisoformat(d['original_time'])).isoformat().replace('+00:00', 'Z')
                        require(d['observed_at'] == {'$date': utc}, 'Clock')
                        ident = stable_id('measurement', d['channel_id'], utc, d['timestamp_role'])
                        require(d['_id'] == d['measurement_id'] == ident and ident not in ids, 'Identity/duplicate')
                        ids.add(ident)
                        require(d['payload_hash'] == payload_hash(d) and d['source_version'] == d['raw_reference']['sha256'], 'Payload')
                        natural = canonical([d['channel_id'], d['observed_at'], d['timestamp_role']])
                        require(ledger.execute('SELECT signature,natural_key FROM identities WHERE id=?', (ident,)).fetchone()
                                == (d['payload_hash'], natural), 'Ledger membership')
                        counts[d['source_id']] += 1
                        a = activity.setdefault(d['channel_id'], [0, utc, utc])
                        a[0] += 1
                        a[1], a[2] = min(a[1], utc), max(a[2], utc)
                identity_hash = sha256()
                for ident, signature in ledger.execute('SELECT id,signature FROM identities ORDER BY id'):
                    identity_hash.update((canonical([ident, signature]) + '\n').encode())
        require(h.hexdigest() == prep['output_hashes']['accepted.extjsonl'] == manifest[PREFIX + 'accepted.extjsonl']['sha256'], 'Accepted hash')
        require(bytes_read == manifest[PREFIX + 'accepted.extjsonl']['bytes'], 'Accepted size')
        result['files_verified'][PREFIX + 'accepted.extjsonl'] = {'bytes': bytes_read, 'sha256': h.hexdigest()}
        require(dict(counts) == {s: v['accepted'] for s, v in prep['by_source'].items()}, 'Counts by source')
        require(identity_hash.hexdigest() == historical['postgresql']['ids_payload_sha256'], 'Historical identity fingerprint')
        expected = administrative_results(catalogs, admin)
        expected['PG09'] = [dict(channel_id=k, readings=a[0], first_observed_at=a[1].replace('Z', '+00:00'),
            last_observed_at=a[2].replace('Z', '+00:00')) for k, a in sorted(activity.items(), key=lambda x: (-x[1][0], x[0]))]
        result['query_checks'] = {}
        for key, rows in sorted(expected.items()):
            saved = historical['postgresql']['results'][key]
            require(saved['total'] == len(rows) and saved['sample'] == rows[:5], 'Historical result differs: ' + key)
            result['query_checks'][key] = {'rows': len(rows), 'historical_total_and_sample_match': True,
                                         'independent_result_sha256': sha256(canonical(rows).encode()).hexdigest()}
        result.update(status='PASS', accepted=sum(counts.values()), by_source=dict(counts), duplicates=0,
            accepted_rows_references_checked=sum(counts.values()), ids_payload_sha256=identity_hash.hexdigest(),
            physical_accreditation='BLOCKED: no independently identified device or dated device-channel mapping',
            historical_report=str(HISTORICAL.relative_to(ROOT)), finished_at=datetime.now(timezone.utc).isoformat())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paquete', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    if args.salida.exists():
        parser.error('--salida ya existe: elegir otro nombre, no reemplazar evidencia')
    try:
        report = audit(args.paquete)
    except Exception as error:
        report = {'status': 'FAIL', 'error': str(error)}
    with args.salida.open('x') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write('\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report['status'] == 'PASS' else 1)
