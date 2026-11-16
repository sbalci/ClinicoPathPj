"""Compare the source grouped core to independently frozen survival-package outputs."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor
from cpj_grouped_survival import grouped_survival_core
import numpy as np
FIXTURE=ROOT/'tests/fixtures/grouped-survival-core.json'


def verify():
    ref=json.loads(FIXTURE.read_text());registry=json.loads((ROOT/'inst/python/registry.json').read_text())
    entry=next(e for e in registry['analyses'] if e['id']=='pysurvival')
    assert entry['baseline']['files']==ref['baseline_hashes']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for path,digest in ref['baseline_hashes'].items():
            assert hashlib.sha256(archive.extractfile('jsurvival/'+path).read()).hexdigest()==digest
    checks=0;maximum=0.
    def compare(a,b,key):
        nonlocal checks,maximum
        checks+=1
        if isinstance(b,dict):
            for k,v in b.items():compare(a[k],v,key+'.'+k)
        elif isinstance(b,list):
            assert len(a)==len(b),(key,len(a),len(b))
            for i,(x,y) in enumerate(zip(a,b)):compare(x,y,key+f'[{i}]')
        elif isinstance(b,float):
            assert a is not None,(key,a,b)
            delta=abs(a-b)/max(1,abs(b));maximum=max(maximum,delta)
            assert delta<=2e-10,(key,a,b,delta)
        else:assert a==b,(key,a,b)
    for f in ref['fixtures']:
        a=f['inputs'];group=Factor(np.array(a['codes'],dtype=int),a['levels'])
        result=grouped_survival_core(a['time'],a['event'],group,queries=f['queries'],
            confidence=f['confidence'],timefix=f['timefix'])
        compare(result,f['expected'],f['id']+str(f['timefix']))
        json.dumps(result,allow_nan=False)
    return dict(datasets=len({f['id'] for f in ref['fixtures']}),configurations=len(ref['fixtures']),
        checks=checks,maximum_scaled_difference=maximum,tolerance=2e-10,
        fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source grouped KM/log CI/risk sets/log-rank only; no native/package/GUI acceptance')

if __name__=='__main__':print(json.dumps(verify(),indent=2))
