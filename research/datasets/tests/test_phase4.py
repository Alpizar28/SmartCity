"""Read-only acceptance of evidence-based decision artifacts, no engine or network."""
import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
R = ROOT/'results/phase4'


@pytest.mark.parametrize('city', ['Madrid','NYC','London'])
def test_weights_subcriteria_and_totals_reconcile(city):
    rows=list(csv.DictReader((ROOT/'04_scores.csv').open()))
    details=list(csv.DictReader((R/'subscores.csv').open()))
    expected=[20,15,15,10,10,10,10,10]
    values=[]
    for ident,weight in enumerate(expected,1):
        criterion=next(r for r in rows if r['alternative']==city and r['criterion_id']==str(ident))
        sub=[r for r in details if r['alternative']==city and int(r['criterion_id'])==ident]
        assert sum(float(r['subweight']) for r in sub)==weight
        points=sum(float(r['subweight'])*float(r['rating_0_4'])/4 for r in sub)
        assert abs(points-float(criterion['score_points']))<1e-4
        assert all(r['rationale'] and r['evidence'] and r['missing_evidence'] and r['rescore_condition'] for r in sub)
        values.append(points)
    total=next(r for r in rows if r['alternative']==city and r['criterion_id']=='TOTAL')
    summary=json.loads((R/'scores_summary.json').read_text())
    assert abs(sum(values)-float(total['score_points']))<1e-4
    assert float(total['score_points'])==summary['totals'][city]


def test_no_native_credit_or_human_approval_inferred():
    summary=json.loads((R/'scores_summary.json').read_text())
    assert not summary['team_approval'] and not summary['phase5_started']
    details=list(csv.DictReader((R/'subscores.csv').open()))
    native=[r for r in details if r['subcriterion'].startswith('MongoDB nativo')]
    assert len(native)==3 and all(float(r['points'])==0 for r in native)
    checks=json.loads((R/'evidence_checks.json').read_text())
    assert checks['network_requests']==0 and not checks['audit_or_load_repeated']
    assert checks['all_checks_passed']


def test_sensitivity_does_not_require_volume_or_match_percentage():
    s=json.loads((R/'sensitivity.json').read_text())
    assert s['Madrid']['without_volume']>max(s[c]['without_volume'] for c in ['NYC','London'])
    assert s['Madrid']['without_spatial_temporal']>max(s[c]['without_spatial_temporal'] for c in ['NYC','London'])


def test_seven_deliverables_and_all_twenty_query_gap_ids():
    names=['04_final_comparison.md','04_scores.csv','04_selected_dataset.md','04_decision_evidence.md',
           '04_open_risks.md','04_implementation_feasibility.md','04_team_decisions.md']
    for name in names:assert (ROOT/name).stat().st_size>0
    text=(ROOT/'04_implementation_feasibility.md').read_text()
    for prefix in ['PG','MG']:
        for n in range(1,11):assert f'{prefix}{n:02d}' in text
    selected=(ROOT/'04_selected_dataset.md').read_text()
    assert 'MAD-AIR-file' in selected and 'MAD-TRAFFIC-Jan2025' in selected
    assert 'MAD-CRASH-file' in selected and '2026' in selected
    assert 'Condicionada' in selected and 'Pendiente' in selected
