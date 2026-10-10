"""Seal Phase4 artifacts and verify all previous hashes without rewriting them."""
import csv
import json
import py_compile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from phase4_evaluate import ROOT, OUT, sha


def main():
    checked=0
    for manifest in ['results/phase3/inputs_manifest.csv','results/phase3/outputs_manifest.csv']:
        for r in csv.DictReader((ROOT/manifest).open()):
            p=ROOT/r['path'];assert p.stat().st_size==int(r['bytes']) and sha(p)==r['sha256'],r['path']
            checked+=1
    tests=list(ET.parse(OUT/'tests.xml').getroot().iter('testsuite'))
    count=sum(int(s.attrib['tests']) for s in tests)
    assert count==48
    assert all(int(s.attrib.get(k,0))==0 for s in tests for k in ['failures','errors','skipped'])
    for f in (ROOT/'scripts').glob('phase4*.py'):py_compile.compile(str(f),doraise=True)
    required=['04_final_comparison.md','04_scores.csv','04_selected_dataset.md','04_decision_evidence.md',
              '04_open_risks.md','04_implementation_feasibility.md','04_team_decisions.md']
    assert all((ROOT/name).is_file() for name in required)
    report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'previous_manifest_entries_verified':checked,
        'required_deliverables':7,'tests_passed':count,'failures':0,'errors':0,'skipped':0,
        'prior_files_unchanged':True,'python_compilation_passed':True,'team_approval':False,
        'native_mongodb_executed':False,'remote_changes':False,'phase5_started':False,'all_checks_passed':True}
    (OUT/'final_checks.json').write_text(json.dumps(report,indent=2))
    paths=list(ROOT.glob('04_*'))+list((ROOT/'scripts').glob('phase4*.py'))+[ROOT/'tests/test_phase4.py']+list(OUT.glob('*'))
    with (OUT/'outputs_manifest.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader()
        for path in sorted(set(paths)):
            if path.is_file() and path.name not in ['outputs_manifest.csv','run.log']:
                writer.writerow({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path)})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
