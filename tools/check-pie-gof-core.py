"""Compare source GOF with independent frozen R tests and baseline subtitles."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_pie_gof import pie_gof
from cpj_runtime import Factor

FIXTURE=ROOT/'tests/fixtures/pie-gof-core.json'


def inputs(f):
    a=f['inputs']
    return Factor(np.array(a['codes']),a['levels'],a['ordered']),a['weights']


def verify():
    ref=json.loads(FIXTURE.read_text())
    registry=json.loads((ROOT/'inst/python/registry.json').read_text())
    entry=next(e for e in registry['analyses'] if e['id']=='pyjjpiestats')
    assert ref['baseline_hashes']==entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for path,digest in entry['baseline']['files'].items():
            assert hashlib.sha256(archive.extractfile('jjstatsplot/'+path).read()).hexdigest()==digest
    checks=runs=0;maximum=0.
    def compare(got,want,key):
        nonlocal checks,maximum
        checks+=1
        if isinstance(want,dict):
            for k,v in want.items():compare(got[k],v,k)
        elif isinstance(want,list):
            assert len(got)==len(want),(key,len(got),len(want))
            for a,b in zip(got,want):compare(a,b,key)
        elif (want is None or isinstance(want,(str,bool)) or
              isinstance(want,int) and key not in ('statistic','p','probability','expected',
                  'minimum_expected','pearson_residual','contribution')):
            assert got==want,(key,got,want)
        else:
            error=abs(got-want)
            tolerance=abs(want)*1e-10 if key=='p' and want else 2e-12*max(1,abs(want))
            assert error<=tolerance,(key,got,want,error,tolerance)
            maximum=max(maximum,error/max(1,abs(want)))
    for f in ref['fixtures']:
        a,w=inputs(f)
        for r in f['runs']:
            got=pie_gof(a,weights=w,enabled=True,ratios=r['ratios'])
            compare(got['gof'],r['expected'],f['id']);json.dumps(got,allow_nan=False);runs+=1
        disabled=pie_gof(a,weights=w,ratios='inactive-invalid-ratio')
        compare(disabled['gof']['status'],'disabled','off')
        compare(disabled['gof']['p'],None,'off p');compare(disabled['gof']['rows'],[],'off rows');runs+=1
    return dict(datasets=len(ref['fixtures']),configurations=runs,checks=checks,
        baseline_subtitle_checks=len(ref['subtitle_checks']),maximum_scaled_difference=maximum,
        fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source fixed-null GOF only; no native inference or package/GUI claim')


if __name__=='__main__':print(json.dumps(verify(),indent=2))
