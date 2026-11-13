"""Compare the categorical bar source engine with frozen independent R references."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor,InputError
from cpj_barstats import bar_core
FIXTURE=ROOT/'tests/fixtures/barstats-core.json'


def inputs(f):
    a=f['inputs']
    return (Factor(np.array(a['outcome_codes']),a['outcome_levels']),
            Factor(np.array(a['group_codes']),a['group_levels']),a['weights'])


def verify():
    reference=json.loads(FIXTURE.read_text());registry=json.loads((ROOT/'inst/python/registry.json').read_text())
    entry=next(x for x in registry['analyses'] if x['id']=='pyjjbarstats')
    assert reference['baseline_hashes_verified']==entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for p,h in entry['baseline']['files'].items():assert hashlib.sha256(archive.extractfile('jjstatsplot/'+p).read()).hexdigest()==h
    checks=configurations=errors=0;maximum=0.
    def compare(got,want,key):
        nonlocal checks,maximum
        checks+=1
        if isinstance(want,dict):
            assert isinstance(got,dict),key
            for k,v in want.items():compare(got[k],v,k)
        elif isinstance(want,list):
            assert len(got)==len(want),(key,len(got),len(want))
            for a,b in zip(got,want):compare(a,b,key)
        elif want is None or isinstance(want,(str,bool,int)):
            assert got==want,(key,got,want)
        else:
            error=abs(got-want);tol=abs(want)*1e-10 if want else 1e-12
            assert error<=tol,(key,got,want,error,tol)
            maximum=max(maximum,error/max(1,abs(want)))
    for f in reference['fixtures']:
        a,b,w=inputs(f);expected=f['expected']
        if expected['status']=='error':
            try:bar_core(a,b,weights=w,inference=True)
            except InputError:checks+=1;configurations+=1;errors+=1;continue
            raise AssertionError(('Expected refusal',f['id']))
        for inference in (False,True):
            got=bar_core(a,b,weights=w,inference=inference)
            for key,want in expected.items():
                if key=='association_off':continue
                if key=='association' and not inference:want=expected['association_off']
                compare(got[key],want,key)
            json.dumps(got,allow_nan=False);configurations+=1
    return dict(datasets=len(reference['fixtures']),configurations=configurations,expected_refusals=errors,
        checks=checks,maximum_scaled_difference=maximum,fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source core only; native/GUI/package qualification separate')


if __name__=='__main__':print(json.dumps(verify(),indent=2))
