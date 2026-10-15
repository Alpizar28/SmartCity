"""Deterministic fictional administrative fixtures; never physical-inventory evidence."""
import argparse
from datetime import date, timedelta
import json
import random

from phase5_contract import PRIVATE, stable_id

GENERATOR = 'admin-demo-v1'


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
    parser.add_argument('--seed', type=int, default=20261010)
    args = parser.parse_args()
    PRIVATE.mkdir(parents=True, exist_ok=True)
    output = PRIVATE/'synthetic_admin.json'
    text = json.dumps(generate(args.seed), ensure_ascii=False, indent=2)+'\n'
    if output.exists() and output.read_text() != text:
        raise ValueError('Existing demo differs: use another generation, do not overwrite')
    output.write_text(text)
    print(json.dumps({'entities':len(generate(args.seed)), 'observations':0, 'seed':args.seed}))


if __name__ == '__main__':
    main()
