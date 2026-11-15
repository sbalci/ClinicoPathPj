"""Validate source lollipop calculations against frozen independent R fixtures."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_lollipop import lollipop_core
from cpj_runtime import Factor

FIXTURE=ROOT/'tests/fixtures/lollipop-core.json'


def verify(engine=lollipop_core):
    reference=json.loads(FIXTURE.read_text())
    registry=json.loads((ROOT/'inst/python/registry.json').read_text())
    entry=next(e for e in registry['analyses'] if e['id']=='pylollipop')
    assert reference['baseline_hashes']==entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for path,digest in entry['baseline']['files'].items():
            assert hashlib.sha256(archive.extractfile('jjstatsplot/'+path).read()).hexdigest()==digest
    checks=configurations=0
    maximum=0.
    def compare(actual,expected,path):
        nonlocal checks,maximum
        checks+=1
        if isinstance(expected,dict):
            for k,v in expected.items():compare(actual[k],v,path+'.'+k)
        elif isinstance(expected,list):
            assert len(actual)==len(expected),path
            for i,(a,b) in enumerate(zip(actual,expected)):compare(a,b,path+f'[{i}]')
        elif expected is None or isinstance(expected,(str,bool,int)):
            # JSON encodes whole-valued R statistics as ints; statistical fields
            # use the same numeric tolerance, counts/codes/slots remain exact.
            numeric_field=path.rsplit('.',1)[-1] in ('mean','median','sd','minimum','maximum','range',
                'q1','q3','value','stem_start','stem_end','reference_mean')
            if expected is None or isinstance(expected,(str,bool)) or not numeric_field:
                assert actual==expected,(path,actual,expected)
            else:compare_float(actual,expected,path)
        else:compare_float(actual,expected,path)
    def compare_float(actual,expected,path):
        nonlocal maximum
        delta=abs(actual-expected)/max(1.,abs(expected))
        assert delta<=2e-12,(path,actual,expected,delta)
        maximum=max(maximum,delta)
    for fixture in reference['fixtures']:
        a=fixture['inputs']
        for run in fixture['runs']:
            got=engine(a['values'],Factor(np.array(a['codes']),a['levels'],False),
                aggregation=run['aggregation'],sorting=run['sorting'],
                orientation=run['orientation'],baseline=a['baseline'])
            compare(got,run['expected'],fixture['id'])
            json.dumps(got,allow_nan=False)
            configurations+=1
    return dict(datasets=len(reference['fixtures']),configurations=configurations,checks=checks,
        maximum_scaled_difference=maximum,fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source summary/order/ggplot2 stem geometry only; native and clinical acceptance separate')


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
