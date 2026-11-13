"""Compare the histogram/one-sample source helper with frozen independent R oracles."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_histogram import histogram_core, one_sample_core

FIXTURE = ROOT/'tests/fixtures/histogram-core.json'


def verify():
    reference = json.loads(FIXTURE.read_text())
    registry = json.loads((ROOT/'inst/python/registry.json').read_text())
    target = next(e for e in registry['analyses'] if e['id']=='pyjjhistostats')
    hashes = target['baseline']['files']
    assert reference['baseline_hashes_verified'] == hashes
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for name, expected in hashes.items():
            blob = archive.extractfile('jjstatsplot/'+name).read()
            assert hashlib.sha256(blob).hexdigest()==expected, name
    checks, configurations, bins, maximum = 0, 0, 0, 0.
    def compare(got, expected, key):
        nonlocal checks, maximum
        checks += 1
        if expected is None or isinstance(expected, (str, bool)):
            assert got == expected, (key, got, expected)
        elif isinstance(expected, list):
            assert got == expected, (key, got, expected)
        elif key in ('n_source','n_complete','excluded_missing','count','n'):
            assert got == expected, (key, got, expected)
        else:
            assert isinstance(got, (int,float)), (key, got, expected)
            error = abs(got-expected)
            tolerance = (2e-7*max(1,abs(expected)) if key.endswith('_lower') or key.endswith('_upper')
                         else abs(expected)*1e-10 if expected else 1e-12)
            assert error <= tolerance, (key,got,expected,error,tolerance)
            maximum = max(maximum,error/max(1,abs(expected)))
    for f in reference['fixtures']:
        for ref in f['histograms']:
            got = histogram_core(f['values'],breaks=f['breaks'],closure=ref['closure'])
            for key in ('n_source','n_complete','excluded_missing','retained_indices'):
                compare(got[key],f[key],key)
            for key, expected in f['summary'].items(): compare(got['summary'][key],expected,key)
            assert len(got['bins'])==len(ref['rows'])
            for row, expected in zip(got['bins'],ref['rows']):
                for key, value in expected.items():compare(row[key],value,key)
                bins += 1
            assert sum(row['count'] for row in got['bins'])==got['n_complete']
            json.dumps(got,allow_nan=False)
            configurations += 1
        for ref in f['runs']:
            got = one_sample_core(f['values'],reference=ref['reference'],confidence=ref['confidence'])
            for key, value in ref.items():compare(got[key],value,key)
            for key, value in f['summary'].items():compare(got['summary'][key],value,key)
            for key in ('n_source','n_complete','excluded_missing','retained_indices'):
                compare(got[key],f[key],key)
            json.dumps(got,allow_nan=False)
            configurations += 1
    return dict(scope='Source helper only; no menu/native/GUI/automatic binning qualification',
        datasets=len(reference['fixtures']),configurations=configurations,bins=bins,checks=checks,
        maximum_scaled_absolute_difference=maximum,
        fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),baseline_hashes_verified=hashes)


if __name__=='__main__':
    report=verify()
    (ROOT/'docs/validation-exports/python-histogram-core-20261112.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
