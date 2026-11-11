"""Execute empirical-moment CCC prototype against blinded R/MPFR references."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_empirical import empirical_concordance_interval
from cpj_runtime import InputError


def decode(values):
    values=values if isinstance(values,list) else [values]
    tokens={'NA':float('nan'),'NaN':float('nan'),'Inf':float('inf'),'-Inf':float('-inf')}
    return [tokens.get(v,v) if isinstance(v,str) else v for v in values]


def finite(value):
    return isinstance(value,(int,float)) and math.isfinite(value)


def check():
    path=ROOT/'tests/fixtures/concordance-empirical.json'
    reference=json.loads(path.read_text())
    rows=[];available=unavailable=refused=0
    for fixture in reference['fixtures']:
        expected=fixture['expected'];mp=expected.get('mpfr256',{})
        x,y=decode(fixture['x']),decode(fixture['y'])
        for confidence in (.8,.9,.95,.975,.99):
            for method,key in [('empirical-z','atanh'),('empirical-normal','normal')]:
                def record(field,observed,target,oracle):
                    numeric=finite(target) and not isinstance(target,bool)
                    diff=abs(observed-target) if numeric and observed is not None else None
                    passed=diff<=1e-12 if diff is not None else observed==target
                    rows.append(dict(case=fixture['id'],confidence=confidence,method=method,
                                     field=field,observed=observed,expected=target,oracle=oracle,
                                     absolute_difference=diff,passed=passed))
                if expected['policy']!='eligible':
                    try:
                        empirical_concordance_interval(x,y,confidence,method)
                    except InputError:
                        record('input_refused',True,True,'frozen domain contract');refused+=1
                    else:
                        record('input_refused',False,True,'frozen domain contract')
                    continue
                got=empirical_concordance_interval(x,y,confidence,method)
                supported=(finite(mp['point']) and abs(mp['point'])<1
                           and finite(mp['variance']) and mp['variance']>0)
                record('status',got['status'],'ok' if supported else 'unavailable','R/MPFR domain')
                record('n_complete',got['n_complete'],expected['n'],'R complete-pair audit')
                if not supported:
                    unavailable+=1
                    for field in ('lower','upper','variance','se','transformed_se'):
                        record(field,got[field],None,'explicit unavailable contract')
                    record('reason_present',bool(got['reason']),True,'explicit unavailable contract')
                    continue
                available+=1
                interval=next(v for v in mp['intervals'] if v['confidence']==confidence)
                for field,target in [('estimate',mp['point']),('variance',mp['variance']),
                                     ('se',mp['se']),('lower',interval[key][0]),('upper',interval[key][1])]:
                    record(field,got[field],target,'independent R MPFR256 raw-moment delta')
                if key=='atanh':
                    record('transformed_se',got['transformed_se'],mp['transformed_se'],'R MPFR256')
                record('mean_influence',got['mean_influence'],0.,'centered influence identity')
                record('variance_divisor',got['variance_divisor'],'n^2','frozen contract')
    target=ROOT/'docs/validation-exports/python-concordance-empirical-matrix-20261111.csv'
    with target.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    failures=[v for v in rows if not v['passed']]
    differences=[v['absolute_difference'] for v in rows if v['absolute_difference'] is not None]
    result=dict(scope='source-only empirical-moment CCC numerical/domain checks; not coverage qualification',
                fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cases=len(reference['fixtures']),
                available=available,unavailable=unavailable,refused=refused,comparisons=len(rows),
                failures=len(failures),max_absolute_difference=max(differences),tolerance=1e-12,
                matrix_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),first_failures=failures[:20])
    (target.parent/'python-concordance-empirical-numerical-20261111.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return not failures


if __name__=='__main__':raise SystemExit(not check())
