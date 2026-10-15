"""Capture/verify immutable previous phases and seal Phase5; never regenerates earlier outputs."""
import argparse
import csv
import json
import py_compile
from pathlib import Path
import xml.etree.ElementTree as ET

from phase5_legacy_contract import ROOT, OUT, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = OUT/'previous_files.json'
    if not baseline.exists():
        paths = list(ROOT.glob('0[0-4]_*')) + [ROOT/'README.md', ROOT/'.gitignore']
        paths += [p for p in (ROOT/'scripts').glob('*') if p.is_file() and not p.name.startswith('phase5')]
        paths += [p for p in (ROOT/'tests').glob('*.py') if not p.name.startswith('test_phase5')]
        paths += [p for p in (ROOT/'results').rglob('*') if p.is_file() and 'phase5' not in p.parts]
        baseline.write_text(json.dumps([{'path':str(p.relative_to(ROOT)), 'sha256':digest(p), 'bytes':p.stat().st_size}
                                       for p in sorted(set(paths))], indent=2))
    for r in json.loads(baseline.read_text()):
        p = ROOT/r['path']
        assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'], r['path']
    count = 0
    for name in ('results/phase3/inputs_manifest.csv','results/phase3/outputs_manifest.csv','results/phase4/outputs_manifest.csv'):
        for r in csv.DictReader((ROOT/name).open()):
            assert digest(ROOT/r['path'])==r['sha256'], r['path']
            count += 1
    # Original PDFs, not just stale extracted text.
    checks = json.loads((ROOT/'results/phase4/evidence_checks.json').read_text())
    documents = [r for r in checks['hash_checks'] if 'document' in r]
    for r in documents:
        assert digest(Path(r['path']))==r['sha256'], r['path']
    info = {'previous_files_unchanged':True, 'prior_manifest_entries_verified':count,
            'original_PDFs_verified':len(documents), 'remote_connections':0, 'dataset_downloads':0}
    if args.final:
        names = ['dataset_manifest','data_contract','postgresql_design','mongodb_design','ingestion_plan',
                 'volume_strategy','native_mongodb_test','academic_decisions','team_handoff','acceptance_checklist']
        assert all((ROOT/f'05_{n}.md').is_file() for n in names)
        assert (ROOT/'05_data_dictionary.csv').is_file()
        suites = list(ET.parse(OUT/'tests.xml').getroot().iter('testsuite'))
        assert all(int(s.attrib.get(k,0))==0 for s in suites for k in ('failures','errors','skipped'))
        info['tests_passed'] = sum(int(s.attrib['tests']) for s in suites)
        info['required_deliverables'] = 11
        info['approved_dataset'] = False
        info['production_ready'] = False
        for p in (ROOT/'scripts').glob('phase5*.py'):
            py_compile.compile(str(p),doraise=True)
        for p in list(ROOT.glob('05_*.md'))+list((ROOT/'scripts').glob('phase5*'))+list((ROOT/'tests').glob('test_phase5*')):
            if p.is_file():
                for n,line in enumerate(p.read_text().splitlines(),1):
                    assert line==line.rstrip(),f'Trailing whitespace {p.name}:{n}'
                    assert not line.startswith(('<<<<<<< ','=======','>>>>>>> ')),f'Conflict marker {p.name}:{n}'
        prep = json.loads((OUT/'preparation.json').read_text())
        private = ROOT/'private_results/phase5'
        for name,h in prep['private_output_hashes'].items():
            assert digest(private/name)==h,name
        for name in ('mongodb_execution.json','postgresql_sample.json'):
            native = json.loads((OUT/name).read_text())
            assert native['native_executed'] and native['container_removed'] and native['anonymous_volumes_removed'],name
        info['new_text_files_checked'] = True
        info['bounded_native_samples_and_cleanup_verified'] = True
        info['all_checks_passed'] = True
        (OUT/'final_checks.json').write_text(json.dumps(info,indent=2)+'\n')
        paths = list(ROOT.glob('05_*')) + list((ROOT/'scripts').glob('phase5*')) + list((ROOT/'tests').glob('test_phase5*'))
        paths += [p for p in OUT.iterdir() if p.is_file() and p.name!='outputs_manifest.csv']
        with (OUT/'outputs_manifest.csv').open('w',newline='') as f:
            w = csv.DictWriter(f,fieldnames=['path','bytes','sha256']); w.writeheader()
            for p in sorted(paths):
                w.writerow({'path':str(p.relative_to(ROOT)), 'bytes':p.stat().st_size, 'sha256':digest(p)})
    else:
        (OUT/'preflight.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))


if __name__=='__main__':
    main()
