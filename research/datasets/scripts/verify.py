"""Validate hashes, sizes, budget, prior documents and derived artifact manifests."""
import csv
import hashlib
import json
from pathlib import Path

from download import ROOT


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(1<<20):h.update(b)
    return h.hexdigest()


def main():
    rows=list(csv.DictReader((ROOT/'02_download_manifest.csv').open()))
    used=sum(int(r['bytes_downloaded']) for r in rows)
    assert used<=1_000_000_000
    verified=0
    for r in rows:
        p=ROOT/r['path']
        if p.exists():
            assert p.stat().st_size==int(r['bytes_downloaded']),(r['id'],'size')
            assert sha(p)==r['sha256'],(r['id'],'sha256')
            verified+=1
        else:
            assert int(r['bytes_downloaded'])==0
    old={p.name:sha(p) for p in sorted(ROOT.glob('0[01]_*')) if p.is_file()}
    baseline=ROOT/'results/prior_files_hashes.json'
    if baseline.exists():assert json.loads(baseline.read_text())==old,'Earlier phases changed'
    else:baseline.write_text(json.dumps(old,indent=2))
    artifacts=[]
    for p in sorted((ROOT/'raw').rglob('*')):
        if p.is_file() and (p.suffix=='.csv' or p.name=='EPA-2023-assembled.zip'):
            artifacts.append({'path':str(p.relative_to(ROOT)),'file_bytes':p.stat().st_size,
                              'sha256':sha(p),'kind':'assembled from range responses' if p.suffix=='.zip' else 'complete CRC-verified LCL member'})
    with (ROOT/'02_artifact_manifest.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['path','file_bytes','sha256','kind']);w.writeheader();w.writerows(artifacts)
    result={'http_attempt_records':len(rows),'files_hash_verified':verified,'downloaded_entity_bytes':used,
            'budget_bytes':1_000_000_000,'remaining_bytes':1_000_000_000-used,'prior_phase_files':len(old),
            'derived_raw_artifacts':len(artifacts),'all_checks_passed':True}
    (ROOT/'results/verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
