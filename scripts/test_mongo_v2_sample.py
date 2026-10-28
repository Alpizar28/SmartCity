#!/usr/bin/env python3
"""Smoke test nativo Mongo v2 antes de repetir la carga masiva; usa datos locales."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/datasets/scripts'))
from unified_full_load import container, command


def main():
    source = ROOT / 'research/datasets/private_results/expanded-v2-2025-01'
    with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='smartcity-v2-mongo-smoke-') as tmp:
        target = Path(tmp)
        documents, seen = [], set()
        with (source / 'accepted.extjsonl').open() as stream:
            for line in stream:
                doc = json.loads(line)
                kind = ('air' if doc['source_id'] == 'MAD-AIR' else
                        'high' if doc['value'] > 2000 and doc['zone_id'] else 'traffic')
                if kind not in seen:
                    documents.append(doc)
                    seen.add(kind)
                if len(seen) == 3:
                    break
        if seen != {'air', 'traffic', 'high'}:
            raise ValueError('Faltan casos reales para la prueba pequeña')
        (target / 'accepted.extjsonl').write_text(''.join(json.dumps(d, ensure_ascii=False) + '\n' for d in documents))
        prep = json.loads((source / 'preparation.json').read_text())
        prep.update(accepted=3, expected_events=1, expected_alerts_with_zone=1)
        (target / 'preparation.json').write_text(json.dumps(prep))
        for name in ['incidents.extjsonl', 'administrative_seed.json']:
            (target / name).write_bytes((source / name).read_bytes())
        report = {}
        with container('mongodb', 'mongo:7.0.16', target, report) as name:
            for filename in ['cargar_mongodb_v2.js', 'consultas_mongodb_v2.js']:
                command(['cp', str(ROOT / 'sprint1/basico' / filename), name + ':/tmp/' + filename])
            try:
                output = command(['exec', name, 'mongosh', '--quiet',
                    'mongodb://127.0.0.1:27017/smartcity_v2_' + uuid.uuid4().hex[:12],
                    '/tmp/cargar_mongodb_v2.js']).stdout
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, file=sys.stderr)
                raise
            result = json.loads(next(line for line in output.splitlines()
                                     if line.startswith('V2_MONGO_RESULT=')).split('=', 1)[1])
            if len(result['results']) != 10 or result['events'] != 1 or result['alerts'] != 1:
                raise ValueError('Las consultas/eventos/alertas no coinciden con la muestra')
        if not report['container_removed'] or not report['anonymous_volumes_removed']:
            raise ValueError('No se limpiaron los recursos propios')
        print('Mongo v2 native sample: PASS (3 readings, 10 queries, 1 event, 1 alert; not volume evidence)')


if __name__ == '__main__':
    main()
