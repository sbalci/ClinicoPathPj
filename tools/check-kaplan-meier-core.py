"""Compare the source survival engine with frozen independent R references."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_kaplan_meier import kaplan_meier_core

FIXTURE=ROOT/'tests/fixtures/kaplan-meier-core.json'


def inputs(f):
    return dict(time=f['inputs']['time'],event=f['inputs']['event'],queries=f['queries'],
        confidence=f['confidence'],timefix=f['timefix'])


def verify():
    reference=json.loads(FIXTURE.read_text())
    registry=json.loads((ROOT/'inst/python/registry.json').read_text())
    entry=next(e for e in registry['analyses'] if e['id']=='pysinglearm')
    assert reference['baseline_hashes']==entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for path,digest in entry['baseline']['files'].items():
            assert hashlib.sha256(archive.extractfile('jsurvival/'+path).read()).hexdigest()==digest
    checks=0;maximum=0.;relative=0.

    def compare(actual,expected,key):
        nonlocal checks,maximum,relative
        checks+=1
        if isinstance(expected,dict):
            assert isinstance(actual,dict),key
            for k,v in expected.items():compare(actual[k],v,key+'.'+k)
        elif isinstance(expected,list):
            assert len(actual)==len(expected),(key,len(actual),len(expected))
            for i,(a,b) in enumerate(zip(actual,expected)):compare(a,b,key+f'[{i}]')
        elif expected is None or isinstance(expected,(str,bool,int)):
            assert actual==expected,(key,actual,expected)
        else:
            assert actual is not None,key
            delta=abs(actual-expected)
            assert delta<=2e-12*max(1e-12,abs(expected)),(key,actual,expected)
            maximum=max(maximum,delta/max(1,abs(expected)))
            relative=max(relative,delta/max(1e-12,abs(expected)))

    for f in reference['fixtures']:
        result=kaplan_meier_core(**inputs(f))
        compare(result,f['expected'],f['id'])
        json.dumps(result,allow_nan=False)
    return dict(datasets=len({f['id'] for f in reference['fixtures']}),
        configurations=len(reference['fixtures']),checks=checks,
        maximum_scaled_difference=maximum,maximum_relative_difference=relative,
        fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source KM/log-log/median/reverse-KM/Poisson core only; no native, package or GUI acceptance')


if __name__=='__main__':print(json.dumps(verify(),indent=2))
