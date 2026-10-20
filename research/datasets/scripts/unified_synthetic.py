"""Deterministic fictional administrative fixtures; never physical-inventory evidence."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import random

from phase5_contract import PRIVATE, ROOT, canonical, digest, stable_id

GENERATOR = 'admin-demo-v1'
ADMIN_GENERATOR = 'admin-demo-v2'
ADMIN_SEED = 20261010


def build_administrative_seed(catalogs, catalogs_sha256, seed=ADMIN_SEED):
    """Create deterministic demo administration tied to real catalog identities.

    These rows are intentionally synthetic and never identify the device that
    produced an observed reading.  Callers must preserve NULL sensor links on
    channels and measurements.
    """
    if not isinstance(catalogs_sha256, str) or len(catalogs_sha256) != 64:
        raise ValueError('catalogs_sha256 must be a SHA-256 hexadecimal string')
    stations = sorted(catalogs.get('stations', {}))
    categories = sorted(catalogs.get('sensor_categories', {}))
    if not categories:
        categories = sorted({row['category_id'] for row in catalogs.get('measurement_types', {}).values()
                             if row.get('category_id')})
    if not stations or not categories:
        raise ValueError('Administrative seed requires catalog stations and sensor categories')
    provenance = {
        'all_fields': 'synthetic',
        'authorization': 'professor-message-2026-10-10',
        'purpose': 'academic_demo_only',
        'physical_inventory_evidence': False,
        'observations_are_synthetic': False,
    }
    organization_id = stable_id('organization', ADMIN_GENERATOR, seed, 1)
    organization = {
        'organization_id': organization_id,
        'name': 'Organización demo 01',
        'responsible_person_or_role': 'Rol administrativo ficticio',
        'evidence_reference': 'synthetic://admin-demo-v2/organizations/1',
        'data_origin': 'synthetic',
        'provenance': dict(provenance),
    }
    users = [{
        'user_id': stable_id('user', ADMIN_GENERATOR, seed, number),
        'name': f'Usuario demo {number:02d}',
        'email': f'user-{number:02d}@example.invalid',
        'consent_reference': f'synthetic://admin-demo-v2/consent/{number}',
        'demo_only': True,
        'data_origin': 'synthetic',
        'provenance': dict(provenance),
    } for number in range(1, len(stations) + 1)]
    sensors = [{
        'sensor_id': stable_id('sensor', ADMIN_GENERATOR, seed, station_id),
        'name': f'Sensor demo {number:02d}',
        'category_id': categories[(number - 1) % len(categories)],
        'station_id': station_id,
        'installation_date': (date(2020, 1, 1) + timedelta(days=(seed + number) % 1800)).isoformat(),
        'administrative_status': 'active' if number % 2 else 'inactive',
        'status_effective_at': '2023-01-01T00:00:00Z',
        'organization_id': organization_id,
        'identity_evidence_reference': f'synthetic://admin-demo-v2/sensors/{number}',
        'data_origin': 'synthetic',
        'provenance': dict(provenance),
    } for number, station_id in enumerate(stations, 1)]
    return {
        'schema_version': 'madrid-draft-v1',
        'generator_version': ADMIN_GENERATOR,
        'seed': seed,
        'catalogs_sha256': catalogs_sha256,
        'provenance': provenance,
        'organizations': [organization],
        'users': users,
        'sensors': sensors,
        'synthetic_measurements': 0,
    }


def write_administrative_seed(private, results, catalog_path, seed=ADMIN_SEED):
    """Seal a catalog-bound administrative demo package without mutating data."""
    private, results, catalog_path = map(Path, (private, results, catalog_path))
    catalogs = json.loads(catalog_path.read_text())
    seed_package = build_administrative_seed(catalogs, digest(catalog_path), seed)
    seed_path = private / 'administrative_seed.json'
    manifest_path = results / 'administrative_manifest.json'
    text = json.dumps(seed_package, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if seed_path.exists() and seed_path.read_text() != text:
        raise ValueError('Existing administrative seed differs; select another generation')
    private.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    if not seed_path.exists():
        seed_path.write_text(text)
    manifest = {
        'administrative_seed_file': seed_path.name,
        'administrative_seed_sha256': digest(seed_path),
        'catalogs_sha256': digest(catalog_path),
        'generator_version': ADMIN_GENERATOR,
        'seed': seed,
        'counts': {key: len(seed_package[key]) for key in ('organizations', 'users', 'sensors')},
        'synthetic_measurements': 0,
        'channels_assigned_to_synthetic_sensors': 0,
    }
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError('Existing administrative manifest differs; select another generation')
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def generate(seed=20261010, count=12):
    if not 1 <= count <= 1000:
        raise ValueError('demo count must be 1..1000')
    rng = random.Random(seed)
    provenance = {'all_fields':'synthetic', 'authorization':'professor-message-2026-10-10',
                  'purpose':'academic_demo_only', 'physical_inventory_evidence':False}
    rows = []
    organization_id = stable_id('demo-organization', GENERATOR, seed)
    user_id = stable_id('demo-user', GENERATOR, seed)
    payloads = [('organization', organization_id, {'name':'Organismo ficticio de demostración',
                 'responsible_person_or_role':'Responsable ficticio'}),
                ('user', user_id, {'name':'Usuario ficticio', 'email':'demo@example.invalid',
                                  'consent_reference':None, 'demo_only':True})]
    for n in range(count):
        payloads.append(('sensor', stable_id('demo-sensor', GENERATOR, seed, n), {
            'name':f'Sensor ficticio {n+1}', 'installation_date':
                (date(2020,1,1)+timedelta(days=rng.randrange(1800))).isoformat(),
            'administrative_status':rng.choice(['active', 'inactive', None]),
            'organization_id':organization_id, 'station_id':None,
            'identity_evidence_reference':None}))
    for kind, ident, payload in payloads:
        rows.append({'entity_id':ident, 'entity_type':kind, 'payload':payload,
                     'data_origin':'synthetic', 'seed':seed, 'generator_version':GENERATOR,
                     'provenance':dict(provenance)})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=ADMIN_SEED)
    parser.add_argument('--generation', help='sealed expanded generation to receive catalog-bound admin rows')
    args = parser.parse_args()
    if args.generation:
        if not args.generation.startswith('expanded-'):
            raise ValueError('Administrative seed requires an expanded generation')
        private = ROOT / 'private_results' / args.generation
        results = ROOT / 'results' / args.generation
        manifest = write_administrative_seed(private, results, private / 'catalogs.json', args.seed)
        print(json.dumps({'generation': args.generation, **manifest}, ensure_ascii=False, indent=2))
        return
    PRIVATE.mkdir(parents=True, exist_ok=True)
    output = PRIVATE/'synthetic_admin.json'
    text = json.dumps(generate(args.seed), ensure_ascii=False, indent=2)+'\n'
    if output.exists() and output.read_text() != text:
        raise ValueError('Existing demo differs: use another generation, do not overwrite')
    output.write_text(text)
    print(json.dumps({'entities':len(generate(args.seed)), 'observations':0, 'seed':args.seed}))


if __name__ == '__main__':
    main()
