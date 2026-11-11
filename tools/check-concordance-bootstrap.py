"""Compare the source bootstrap engine with independently frozen paired-index R fixtures."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_bootstrap import bootstrap_concordance_interval


def decode(values):
    if not isinstance(values,list):values=[values]
    return [float('nan') if v in ('NA','NaN') else v for v in values]


def check():
    path=ROOT/'tests/fixtures/concordance-bootstrap.json';reference=json.loads(path.read_text())
    rows=[];available=unavailable=0
    for fixture in reference['fixtures']:
        e=fixture['expected'];x,y=decode(fixture['x']),decode(fixture['y'])
        for interval in e['intervals']:
            confidence=interval['confidence']
            r=bootstrap_concordance_interval(x,y,confidence,resamples=fixture['resamples'],
                                             indices=fixture['indices'],return_distribution=True)
            def record(field,observed,expected):
                if expected=='NA':expected=None
                numeric=isinstance(expected,(float,int)) and not isinstance(expected,bool)
                difference=abs(observed-expected) if numeric and observed is not None else None
                passed=difference<=1e-12 if difference is not None else observed==expected
                rows.append(dict(case=fixture['id'],confidence=confidence,field=field,
                                 observed=observed,expected=expected,absolute_difference=difference,passed=passed))
            record('status',r['status'],interval['policy_status'])
            record('estimate',r['estimate'],e['point'])
            record('n_complete',r['n_complete'],e['n_complete'])
            record('retained_indices',r['point']['retained_indices'],e['retained_indices'])
            record('lower',r['lower'],interval['policy_lower'])
            record('upper',r['upper'],interval['policy_upper'])
            early=e['point']=='NA' or abs(e['point'])==1
            if early:
                record('not_resampled',r['resamples_evaluated'],0)
            else:
                record('evaluated',r['resamples_evaluated'],fixture['resamples'])
                record('undefined_resamples',r['undefined_resamples'],e['n_undefined'])
                for i,(got,target) in enumerate(zip(r['distribution'],e['distribution'])):
                    record(f'draw_{i}',got,target)
                record('distribution_length',len(r['distribution']),len(e['distribution']))
            if interval['policy_status']=='ok':
                available+=1;record('se',r['se'],e['raw_bootstrap_se'])
            else:
                unavailable+=1;record('se_unavailable',r['se'],None)
                record('reason_present',bool(r['reason']),True)
    failures=[r for r in rows if not r['passed']]
    out=ROOT/'docs/validation-exports'
    matrix=out/'python-concordance-bootstrap-matrix-20261111.csv'
    with matrix.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result=dict(scope='source-only paired percentile CCC bootstrap numerical/policy parity; not coverage',
                fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cases=len(reference['fixtures']),
                interval_runs=available+unavailable,available=available,unavailable=unavailable,
                comparisons=len(rows),failures=len(failures),tolerance=1e-12,
                max_absolute_difference=max(r['absolute_difference'] or 0 for r in rows),
                matrix_sha256=hashlib.sha256(matrix.read_bytes()).hexdigest(),first_failures=failures[:20])
    (out/'python-concordance-bootstrap-numerical-20261111.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return not failures


if __name__=='__main__':raise SystemExit(not check())
