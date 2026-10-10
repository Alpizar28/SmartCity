"""Read-only input integrity and final deliverable validation with reproducible hashes."""
import csv
import json
import py_compile
from datetime import datetime, timezone

from download import ROOT
from phase3_validate import OUT, sha


def main():
    for row in csv.DictReader((OUT/'inputs_manifest.csv').open()):
        path=ROOT/row['path']
        assert path.stat().st_size==int(row['bytes']) and sha(path)==row['sha256'],row['path']
    required=['03_postgresql_matrix.md','03_mongodb_matrix.md','03_integration_gaps.md',
              '03_data_origin_matrix.csv','03_spark_future_matrix.md','03_dashboard_coverage.md',
              '03_feasibility_report.md','03_tests_report.md']
    for name in required:assert (ROOT/name).is_file() and (ROOT/name).stat().st_size>0
    for path in (ROOT/'scripts').glob('phase3*.py'):py_compile.compile(str(path),doraise=True)
    matrix=list(csv.DictReader((ROOT/'03_compliance_matrix.csv').open()))
    for city in ['Madrid','NYC','London']:
        for technology,prefix in [('PostgreSQL','PG'),('MongoDB','MG'),('Spark','SP')]:
            rows=[r for r in matrix if r['alternative']==city and r['technology']==technology]
            assert len(rows)==10 and {r['id'] for r in rows}=={f'{prefix}{i:02d}' for i in range(1,11)}
    origins=list(csv.DictReader((ROOT/'03_data_origin_matrix.csv').open()))
    assert {r['data_origin'] for r in origins}=={'observed','derived','synthetic','unavailable','unverified'}
    assert all(int(r['synthetic_rows_generated'])==0 for r in origins)
    native=json.loads((OUT/'postgres_execution.json').read_text())
    assert native['native_executed'] and native['container_removed'] and native['anonymous_volumes_removed']
    checks={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'required_deliverables':len(required),
        'compliance_matrix_rows':len(matrix),'origin_matrix_rows':len(origins),'all_prior_inputs_unchanged':True,
        'native_postgresql_executed':True,'container_and_anonymous_volumes_removed':True,
        'python_compilation_passed':True,'all_checks_passed':True}
    (OUT/'final_checks.json').write_text(json.dumps(checks,indent=2))
    paths=list(ROOT.glob('03_*'))+list((ROOT/'scripts').glob('phase3*'))+[ROOT/'tests/test_phase3.py']
    paths+=list(OUT.glob('*'))
    with (OUT/'outputs_manifest.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader()
        for path in sorted(set(paths)):
            # Runner appends its exit code after this process; do not hash a live log.
            if path.is_file() and path.name not in ['outputs_manifest.csv','run.log']:
                writer.writerow({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path)})
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
