"""Recompute and test the whole local audit, preserving a complete execution log."""
import subprocess
import sys

from download import ROOT


def main():
    commands=[
        ['scripts/verify.py'],
        ['scripts/audit.py','all'],
        ['scripts/integrate.py'],
        ['-m','pytest','tests','-q','--basetemp=/tmp/opencode/smartcity-phase2-tests',
         '--junitxml=results/tests.xml'],
        ['scripts/verify.py'],
        ['scripts/build_reports.py'],
    ]
    with (ROOT/'results/offline_run.log').open('w') as log:
        for args in commands:
            command=[sys.executable,*args]
            print(' '.join(args),flush=True)
            log.write('$ '+ ' '.join(command)+'\n');log.flush()
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=300)
            log.write(f'Exit code: {result.returncode}\n');log.flush()
            if result.returncode:
                raise SystemExit(f'Failed {args}; see results/offline_run.log')


if __name__=='__main__':main()
