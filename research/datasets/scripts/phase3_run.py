"""Reproduce Phase3 without rewriting Phase0/1/2; fixed local disposable SQL runner."""
import subprocess
import sys
from datetime import datetime, timezone

from download import ROOT


def main():
    result=ROOT/'results/phase3';result.mkdir(parents=True,exist_ok=True)
    commands=[
        ['scripts/phase3_validate.py'],['scripts/phase3_enrich.py'],['scripts/phase3_postgres.py'],
        ['-m','pytest','tests/test_audit.py','tests/test_saved_evidence.py','-q',
         '--basetemp=/tmp/opencode/smartcity-phase3-legacy','--junitxml=results/phase3/legacy_tests.xml'],
        ['-m','pytest','tests/test_phase3.py','-q','--basetemp=/tmp/opencode/smartcity-phase3-tests',
         '--junitxml=results/phase3/tests.xml'],['scripts/phase3_reports.py'],['scripts/phase3_finalize.py'],
    ]
    with (result/'run.log').open('w') as log:
        log.write('UTC '+datetime.now(timezone.utc).isoformat()+'\n')
        for args in commands:
            print(' '.join(args),flush=True)
            command=[sys.executable,*args];log.write('$ '+' '.join(command)+'\n');log.flush()
            p=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=300)
            log.write(f'Exit code: {p.returncode}\n');log.flush()
            if p.returncode:raise SystemExit('Failed Phase3 stage; see results/phase3/run.log')


if __name__=='__main__':main()
