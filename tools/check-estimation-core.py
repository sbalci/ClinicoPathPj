"""Check source estimation against frozen base-R references, without a native port."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import Factor
from cpj_estimation import between_estimation, within_estimation


def inputs(case):
    if case['design'] == 'paired':
        return dict(first=case['a'], second=case['b'])
    return dict(values=case['values'], group=Factor(np.array(case['codes'], dtype=int), case['levels']),
                first_level=case['first'], second_level=case['second'])


def verify():
    fixture = ROOT/'tests/fixtures/estimation-core.json'
    references = json.loads(fixture.read_text())
    registry = json.loads((ROOT/'inst/python/registry.json').read_text())
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for name in ('jjbetweenstats', 'jjwithinstats'):
            entry = next(e for e in registry['analyses'] if e['id'] == 'py'+name)
            for path, target in entry['baseline']['files'].items():
                assert hashlib.sha256(archive.extractfile('jjstatsplot/'+path).read()).hexdigest() == target
            assert entry['baseline']['files']['R/'+name+'.b.R'] == references['baseline'][name+'_backend_sha256']
    checks, configs, maximum_relative = 0, 0, 0.

    def compare(got, expected, location):
        nonlocal checks, maximum_relative
        if isinstance(expected, dict):
            for key, value in expected.items():
                if key != 'runs': compare(got[key], value, location+'.'+key)
        elif isinstance(expected, list):
            assert len(got) == len(expected), location
            for i, value in enumerate(expected): compare(got[i], value, location+f'[{i}]')
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            checks += 1
            assert isinstance(got, (int, float)), (location, got, expected)
            error = abs(got-expected)
            if location.endswith('.p'):
                assert error <= 1e-12, (location, got, expected)
            elif expected == 0:
                assert got == 0, (location, got, expected)
            else:
                relative = error/abs(expected)
                maximum_relative = max(maximum_relative, relative)
                assert relative <= 1e-11, (location, got, expected, relative)
        else:
            checks += 1
            assert got == expected, (location, got, expected)

    for case in references['fixtures']:
        for run in case['expected']['runs']:
            call = within_estimation if case['design'] == 'paired' else between_estimation
            kwargs = {} if case['design'] == 'paired' else dict(equal_variances=run['method'] == 'student')
            result = call(**inputs(case), confidence=run['confidence'], **kwargs)
            compare(result, case['expected'], case['id']+'.cohort')
            compare(result, run, case['id']+'.'+run['method'])
            json.dumps(result, allow_nan=False)
            configs += 1
    return dict(scope='Source-only raw mean estimation; no native/GUI, standardized-effect or full-baseline qualification',
        datasets=len(references['fixtures']), configurations=configs, checks=checks, failures=0,
        maximum_relative_difference=maximum_relative, relative_tolerance=1e-11,
        p_absolute_tolerance=1e-12, exact_zero_targets=True,
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest())


if __name__ == '__main__':
    report = verify()
    (ROOT/'docs/validation-exports/python-estimation-core-20261111.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
