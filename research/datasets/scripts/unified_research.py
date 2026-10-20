"""Fetch only official documentation, preserving immutable bytes and HTTP provenance."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import requests

from phase5_contract import ROOT, digest

BASE = 'https://datos.madrid.es/dataset/'
RESOURCES = {
    'air_catalog': BASE+'201200-0-calidad-aire-horario',
    'air_downloads': BASE+'201200-0-calidad-aire-horario/downloads',
    'meteo_catalog': BASE+'300352-0-meteorologicos-horarios',
    'traffic_catalog': BASE+'208627-0-transporte-ptomedida-historico',
    'air_dictionary': BASE+'201200-0-calidad-aire-horario/resource/201200-17-calidad-aire-horario/download/201200-17-calidad-aire-horario.pdf',
    'meteo_dictionary': BASE+'300352-0-meteorologicos-horarios/resource/300352-122-meteorologicos-horarios/download/300352-122-meteorologicos-horarios.pdf',
    'traffic_dictionary': BASE+'208627-0-transporte-ptomedida-historico/resource/208627-81-transporte-ptomedida-historico/download/208627-81-transporte-ptomedida-historico.pdf',
}


def main():
    private = ROOT/'raw/sprint1-research'
    out = ROOT/'results/expanded-2025'
    private.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    manifest = out/'research_sources.json'
    rows = json.loads(manifest.read_text()) if manifest.exists() else []
    environment = {k:v for k,v in os.environ.items() if k!='LD_LIBRARY_PATH'}
    for name, url in RESOURCES.items():
        path = private/(name+('.pdf' if url.endswith('.pdf') else '.html'))
        prior = next((row for row in rows if row['id']==name),None)
        if prior:
            path = ROOT/prior['path']
            if digest(path) != prior['sha256']:
                raise ValueError('Documentation changed locally')
            if path.suffix=='.pdf' and not path.with_suffix('.txt').exists():
                subprocess.run(['pdftotext','-layout',str(path),str(path.with_suffix('.txt'))],check=True,env=environment)
            continue
        with requests.get(url, headers={'User-Agent':'SmartCity-academic-reproducibility/1.0'},
                          timeout=90, stream=True) as response:
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                chunks.append(chunk)
                size += len(chunk)
                if size>4_000_000:
                    raise ValueError('Documentation read cap exceeded')
            content = b''.join(chunks)
            if response.status_code != 200:
                raise ValueError('Incomplete or unexpectedly large documentation')
            if url.endswith('.pdf') and not content.startswith(b'%PDF'):
                raise ValueError('Not a PDF')
            if path.exists() and path.read_bytes()!=content:
                path = path.with_name(path.stem+'.'+sha256(content).hexdigest()[:16]+path.suffix)
            if not path.exists():
                path.write_bytes(content)
            rows.append({'id':name,'url':url,'final_url':response.url,'status':response.status_code,
                'retrieved_at':datetime.now(timezone.utc).isoformat(),
                'content_type':response.headers.get('Content-Type'),
                'etag':response.headers.get('ETag'),'last_modified':response.headers.get('Last-Modified'),
                'path':str(path.relative_to(ROOT)), 'bytes':len(content),'sha256':digest(path),
                'publisher':'Ayuntamiento de Madrid','license':'CC BY 4.0 (dataset catalog)'})
        manifest.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
        if path.suffix=='.pdf':
            subprocess.run(['pdftotext','-layout',str(path),str(path.with_suffix('.txt'))],check=True,env=environment)
    print(json.dumps({'downloaded':len(rows),'bytes':sum(r['bytes'] for r in rows)}))


if __name__=='__main__':
    main()
