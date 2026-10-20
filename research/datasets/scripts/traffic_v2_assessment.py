"""Read-only sizing of a PROPOSED traffic v2; does not accept or export observations."""
from collections import Counter
import json
import math
import time

import pandas as pd

from phase5_contract import ROOT, digest
from phase5_prepare import numeric


def assess():
    path=ROOT/'private_results/phase5/traffic_selected.parquet'
    stamp=json.loads((path.parent/'traffic_cache_manifest.json').read_text())
    if digest(path)!=stamp['sha256']:
        raise ValueError('Audited traffic cache hash differs')
    frame=pd.read_parquet(path)
    started=time.perf_counter()
    quality=Counter(frame['error'])
    classes=Counter(frame['tipo_elem'])
    values=frame['intensidad'].map(numeric)
    valid_value=values.notna() & values.ge(0)
    dates=pd.to_datetime(frame['fecha'],errors='coerce')
    january=dates.notna() & dates.dt.year.eq(2025) & dates.dt.month.eq(1)
    official_classes=frame['tipo_elem'].isin(['URB','M30'])
    sample_count=pd.to_numeric(frame['periodo_integracion'],errors='coerce')
    valid_samples=sample_count.notna() & sample_count.map(lambda n:math.isfinite(n) and n>=0 and float(n).is_integer())
    candidates=frame['error'].eq('N') & valid_value & january & official_classes & valid_samples
    selected=frame[candidates]
    distinct=selected[['id','tipo_elem','fecha']].drop_duplicates()
    evidence=json.loads((ROOT/'results/expanded-2025/research_sources.json').read_text())
    dictionary=next(row for row in evidence if row['id']=='traffic_dictionary')
    if digest(ROOT/dictionary['path'])!=dictionary['sha256']:
        raise ValueError('Official traffic documentation changed')
    return {'status':'proposal_only_not_accepted_or_loaded','scope':'January 2025 audited ID modulo 20 stratum',
        'cache_sha256':stamp['sha256'],'source_version':stamp['fingerprint']['original_sha256'],
        'dictionary_url':dictionary['url'],'dictionary_sha256':dictionary['sha256'],
        'selected_rows':len(frame),'quality_flags':dict(quality),'element_types':dict(classes),
        'official_documented_class_candidates':int(candidates.sum()),
        'distinct_candidate_logical_keys':len(distinct),
        'candidate_duplicate_extras':len(selected)-len(distinct),
        'candidates_by_type':dict(Counter(selected['tipo_elem'])),
        'candidate_integration_sample_count_min':int(sample_count[candidates].min()),
        'candidate_integration_sample_count_max':int(sample_count[candidates].max()),
        'undocumented_C30_rows':int(frame['tipo_elem'].eq('C30').sum()),
        'invalid_or_missing_sample_count_rows':int((~valid_samples).sum()),
        'timezone_offset_for_january_if_v2_approved':'Europe/Madrid UTC+01:00; no DST transition in this selected month',
        'candidate_policy':'N flag; finite nonnegative intensity; documented URB/M30; valid January local label; nonnegative integer sample count',
        'not_yet_verified':['new v2 identities and payload conflicts','v2 cross-engine import and replay',
                            'approval of v2 contract and migration','C30 meaning and optional-variable applicability'],
        'accepted_measurements_added':0,'originals_modified':False,'elapsed_seconds':time.perf_counter()-started}


if __name__=='__main__':
    print(json.dumps(assess(),ensure_ascii=False,indent=2))
