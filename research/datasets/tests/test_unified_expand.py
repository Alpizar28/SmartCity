"""Multi-month, duplicate, DST, interruption and sealed-generation regressions."""
import csv
import json

import pytest

import unified_expand as expand
from phase5_contract import digest


def daily(month,day,value='7'):
    row={'PROVINCIA':'28','MUNICIPIO':'079','ESTACION':'4','MAGNITUD':'8',
         'PUNTO_MUESTREO':'28079004_8_8','ANO':'2025','MES':str(month),'DIA':str(day)}
    for hour in range(1,25):
        row[f'H{hour:02d}']=value
        row[f'V{hour:02d}']='V'
    return row


@pytest.fixture
def workspace(tmp_path,monkeypatch):
    monkeypatch.setattr(expand,'ROOT',tmp_path)
    def inputs(rows):
        path=tmp_path/'raw.csv'
        with path.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        names=['MAD-AIR-file','MAD-METEO-file','MAD-TRAFFIC-Jan2025','air-inventory','meteo-inventory','traffic-inventory']
        resources={name:{'path':'raw.csv','sha256':digest(path) if n==0 else str(n)*64} for n,name in enumerate(names)}
        monkeypatch.setattr(expand,'sources',lambda:resources)
        monkeypatch.setattr(expand,'metadata',lambda r:{'MAD-AIR':{}})
        monkeypatch.setattr(expand,'configuration',lambda r,y,m:{'year':y,'months':sorted(set(m)),
            'code_hashes':{},'snapshot':digest(path)})
        return resources
    return inputs


def exported(generation):
    private,out=expand.generation_paths(generation)
    return [json.loads(line) for line in (private/'accepted.extjsonl').read_text().splitlines()],json.loads((out/'preparation.json').read_text())


def test_month_boundary_preserves_source_month_and_h24(workspace):
    workspace([daily(1,31),daily(2,1)])
    result=expand.prepare('expanded-test',2025,[1,2,2])
    docs,report=exported('expanded-test')
    assert result['accepted']==48 and len({d['_id'] for d in docs})==48
    endpoint=next(d for d in docs if d['source_key'][-2:] == ['2025-01-31','H24'])
    assert endpoint['original_time']=='2025-02-01T00:00:00'
    assert endpoint['observed_at']=={'$date':'2025-01-31T23:00:00Z'}
    assert report['by_month']['2025-01']['accepted']==24
    assert report['by_month']['2025-02']['accepted']==24
    assert expand.prepare('expanded-test',2025,[1,2])['idempotent_reuse']


def test_dst_quarantines_gap_and_ambiguous_without_fold(workspace):
    workspace([daily(3,30),daily(10,26)])
    result=expand.prepare('expanded-dst',2025,[3,10])
    docs,report=exported('expanded-dst')
    assert result['accepted']==46 and result['quarantined']==2
    private,_=expand.generation_paths('expanded-dst')
    rejected=[json.loads(line) for line in (private/'quarantine.extjsonl').read_text().splitlines()]
    assert {d['reason'] for d in rejected}=={'nonexistent_local_time','ambiguous_local_time_requires_publisher_fold'}
    assert all(d['observed_at'] is None for d in rejected)


def test_duplicate_physical_rows_not_double_counted(workspace):
    workspace([daily(1,1),daily(1,1)])
    result=expand.prepare('expanded-duplicates',2025,[1])
    assert result['accepted']==24 and result['duplicates']==24
    docs,_=exported('expanded-duplicates')
    assert len(docs)==24


def test_conflicting_payload_blocks_completed_generation(workspace):
    workspace([daily(1,1),daily(1,1,value='8')])
    with pytest.raises(ValueError,match='conflict'):
        expand.prepare('expanded-conflict',2025,[1])
    private,out=expand.generation_paths('expanded-conflict')
    assert not (out/'preparation.json').exists()
    assert (private/'conflicts.extjsonl.partial').stat().st_size>0
    assert not (private/'accepted.extjsonl').exists()


def test_interrupted_process_replays_only_unsealed_generation(workspace):
    workspace([daily(1,1)])
    with pytest.raises(RuntimeError,match='interruption'):
        expand.prepare('expanded-restart',2025,[1],interrupt_after=5)
    private,out=expand.generation_paths('expanded-restart')
    assert not (out/'preparation.json').exists()
    with pytest.raises(FileNotFoundError):
        expand.verify_generation('expanded-restart')
    expand.prepare('expanded-restart',2025,[1])
    docs,report=exported('expanded-restart')
    assert len(docs)==24 and report['resumed_by_deterministic_replay']
    assert report['duplicates']==0


def test_changed_interrupted_fingerprint_is_blocked(workspace):
    workspace([daily(1,1)])
    with pytest.raises(RuntimeError):
        expand.prepare('expanded-changed',2025,[1],interrupt_after=1)
    with pytest.raises(ValueError,match='fingerprint'):
        expand.prepare('expanded-changed',2025,[1,2])


def test_tampering_and_generation_path_escape_rejected(workspace):
    workspace([daily(1,1)])
    expand.prepare('expanded-tamper',2025,[1])
    private,_=expand.generation_paths('expanded-tamper')
    with (private/'accepted.extjsonl').open('a') as stream:
        stream.write('{}\n')
    with pytest.raises(ValueError,match='Changed generation'):
        expand.verify_generation('expanded-tamper')
    with pytest.raises(ValueError):
        expand.generation_paths('../../other')


def test_dry_run_does_not_write(workspace):
    workspace([daily(1,1)])
    assert expand.prepare('expanded-dry',2025,[1],dry_run=True)['writes'] is False
    private,out=expand.generation_paths('expanded-dry')
    assert not private.exists() and not out.exists()
