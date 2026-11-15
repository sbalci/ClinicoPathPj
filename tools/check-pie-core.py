"""Compare the source pie engine with frozen independent R/polar-build fixtures."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor
from cpj_pie import pie_core

FIXTURE = ROOT/'tests/fixtures/pie-core.json'


def inputs(fixture):
    a = fixture['inputs']
    return Factor(np.array(a['codes']),a['levels'],a['ordered']), a['weights']


def verify():
    reference = json.loads(FIXTURE.read_text())
    registry = json.loads((ROOT/'inst/python/registry.json').read_text())
    entry = next(e for e in registry['analyses'] if e['id']=='pyjjpiestats')
    assert reference['baseline_hashes']==entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for path, digest in entry['baseline']['files'].items():
            assert hashlib.sha256(archive.extractfile('jjstatsplot/'+path).read()).hexdigest()==digest
    checks = 0
    maximum = 0.

    def compare(actual, expected, key):
        nonlocal checks, maximum
        checks += 1
        if isinstance(expected, dict):
            assert isinstance(actual,dict), key
            for k,v in expected.items(): compare(actual[k],v,k)
        elif isinstance(expected,list):
            assert len(actual)==len(expected), (key,len(actual),len(expected))
            for a,b in zip(actual,expected): compare(a,b,key)
        elif expected is None or isinstance(expected,(str,bool,int)):
            assert actual==expected, (key,actual,expected)
        else:
            delta=abs(actual-expected)
            assert delta<=2e-12*max(1,abs(expected)), (key,actual,expected)
            maximum=max(maximum,delta/max(1,abs(expected)))

    for fixture in reference['fixtures']:
        factor, weights = inputs(fixture)
        got = pie_core(factor,weights=weights)
        compare(got,fixture['expected'],fixture['id'])
        json.dumps(got,allow_nan=False)
    return dict(datasets=len(reference['fixtures']),checks=checks,
        maximum_scaled_difference=maximum,fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source counts and geometry only; no inference, native UI, renderer or package/GUI claim')


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
