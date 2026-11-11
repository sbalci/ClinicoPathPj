"""Execute source ROC engine against blinded R/pROC/literal-kernel fixtures."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_roc import roc_analysis
from cpj_runtime import Factor


def vector(x):return x if isinstance(x,list) else [x]


def check():
    source=ROOT/'tests/fixtures/roc-delong.json';reference=json.loads(source.read_text());rows=[]
    available=unavailable=0
    for fixture in reference['fixtures']:
        e=fixture['expected'];names=list(fixture['markers'])
        markers={name:[float('nan') if v=='NA' else v for v in vector(value)] for name,value in fixture['markers'].items()}
        directions=dict(zip(names,vector(fixture['directions'])))
        ref=Factor(np.asarray(vector(fixture['codes']),dtype=int),fixture['levels'])
        for confidence in (.8,.95,.99):
            got=roc_analysis(ref,markers,fixture['positive'],directions,confidence)
            def record(field,observed,target):
                numeric=isinstance(target,(float,int)) and not isinstance(target,bool)
                diff=abs(observed-target) if numeric and observed is not None else None
                passed=diff<=1e-12 if diff is not None else observed==target
                rows.append(dict(case=fixture['id'],confidence=confidence,field=field,
                                 observed=observed,expected=target,absolute_difference=diff,passed=passed))
            for field in ('n_source','n_complete','n_positive','n_negative','positive','negative','retained_indices'):
                record(field,got[field],e[field])
            if got['covariance'] is None:record('covariance_unavailable',got['covariance'],None)
            else:
                expected=e['covariance']
                for i,row in enumerate(got['covariance']):
                    for j,v in enumerate(row):record(f'covariance_{i}_{j}',v,vector(expected[i])[j])
            for m,expected in zip(got['models'],e['models']):
                name=expected['name'];interval=next(x for x in expected['intervals'] if x['confidence']==confidence)
                record(name+'.name',m['name'],name)
                record(name+'.direction',m['direction'],expected['direction'])
                for field in ('auc','variance'):record(name+'.'+field,m[field],expected[field])
                for field in ('positive_placements','negative_placements'):
                    for i,(a,b) in enumerate(zip(m[field],vector(expected[field]))):record(f'{name}.{field}_{i}',a,b)
                record(name+'.curve_length',len(m['points']),len(expected['points']))
                for i,(a,b) in enumerate(zip(m['points'],expected['points'])):
                    for field in ('cutoff','tp','fp','fn','tn','tpr','fpr'):record(f'{name}.point{i}.{field}',a[field],b[field])
                record(name+'.inference_status',m['inference_status'],interval['status'])
                for field in ('se','raw_lower','raw_upper','lower','upper'):record(name+'.'+field,m[field],interval[field])
                if interval['status']=='ok':available+=1
                else:unavailable+=1;record(name+'.reason',bool(m['inference_reason']),True)
                points=m['points'];area=sum((b['fpr']-a['fpr'])*(a['tpr']+b['tpr'])/2 for a,b in zip(points,points[1:]))
                record(name+'.trapezoid',area,expected['auc_trapezoid'])
            record('comparison_count',len(got['comparisons']),len(e['comparisons']))
            for c,expected in zip(got['comparisons'],e['comparisons']):
                prefix=c['first']+'-'+c['second'];interval=next(x for x in expected['intervals'] if x['confidence']==confidence)
                for field in ('first','second','difference','variance'):record(prefix+'.'+field,c[field],expected[field])
                record(prefix+'.status',c['status'],interval['status'])
                for field in ('se','z','p','lower','upper'):record(prefix+'.'+field,c[field],interval[field])
                if interval['status']=='ok':available+=1
                else:unavailable+=1;record(prefix+'.reason',bool(c['reason']),True)
    failures=[r for r in rows if not r['passed']];out=ROOT/'docs/validation-exports'
    matrix=out/'python-roc-matrix-20261111.csv'
    with matrix.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result=dict(scope='source-only empirical ROC / paired DeLong numerical and policy checks; no native acceptance',
                fixture_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=len(reference['fixtures']),
                cohort_confidence_runs=3*len(reference['fixtures']),available_inference_requests=available,
                unavailable_inference_requests=unavailable,comparisons=len(rows),failures=len(failures),
                tolerance=1e-12,max_absolute_difference=max(r['absolute_difference'] or 0 for r in rows),
                matrix_sha256=hashlib.sha256(matrix.read_bytes()).hexdigest(),first_failures=failures[:20])
    (out/'python-roc-numerical-20261111.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return not failures


if __name__=='__main__':raise SystemExit(not check())
