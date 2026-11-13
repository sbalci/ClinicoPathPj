"""Compare Python histogram geometry with frozen ggplot2 built-layer references."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_histogram_geometry import histogram_geometry
from cpj_runtime import InputError

FIXTURE = ROOT/'tests/fixtures/histogram-geometry.json'


def verify():
    reference=json.loads(FIXTURE.read_text())
    registry=json.loads((ROOT/'inst/python/registry.json').read_text())
    entry=next(e for e in registry['analyses'] if e['id']=='pyjjhistostats')
    assert reference['baseline_hashes_verified']==entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for name,target in entry['baseline']['files'].items():
            assert hashlib.sha256(archive.extractfile('jjstatsplot/'+name).read()).hexdigest()==target
    checks=configurations=bins=0
    maximum=0.
    def compare(got,want,key):
        nonlocal checks,maximum
        checks+=1
        if want is None or isinstance(want,(str,bool)):
            assert got==want,(key,got,want)
        elif isinstance(want,list):
            assert len(got)==len(want),(key,len(got),len(want))
            for a,b in zip(got,want):compare(a,b,key)
        else:
            assert isinstance(got,(int,float)),(key,got,want)
            if key=='count':assert got==want,(key,got,want)
            error=abs(got-want)
            assert error <= (abs(want)*1e-10 if want else 1e-12),(key,got,want,error)
            maximum=max(maximum,error/max(1,abs(want)))
    for fixture in reference['fixtures']:
        for ref in fixture['runs']:
            if ref['geometry_status']=='error':
                try:histogram_geometry(fixture['values'],width=None if ref['automatic'] else ref['width'])
                except InputError:checks+=1;configurations+=1;continue
                raise AssertionError((fixture['id'],ref.get('error_code'),'must reject'))
            got=histogram_geometry(fixture['values'],width=None if ref['automatic'] else ref['width'])
            for key in ('n_source','n_complete','excluded_missing','retained_indices'):
                compare(got[key],fixture[key],key)
            for key in ('geometry_status','automatic','width','raw_edges','fuzzy_edges'):
                compare(got[key],ref[key],fixture['id']+':'+key)
            assert len(got['bins'])==len(ref['bins']),(fixture['id'],len(got['bins']),len(ref['bins']))
            for actual,expected in zip(got['bins'],ref['bins']):
                for key,value in expected.items():compare(actual[key],value,key)
                bins+=1
            if got['bins']:
                assert sum(b['count'] for b in got['bins'])==got['n_complete']
                assert abs(sum(b['proportion'] for b in got['bins'])-1)<1e-12
            json.dumps(got,allow_nan=False)
            configurations+=1
    return dict(datasets=len(reference['fixtures']),configurations=configurations,bins=bins,
        checks=checks,maximum_scaled_absolute_difference=maximum,
        fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest())


if __name__=='__main__':print(json.dumps(verify(),indent=2))
