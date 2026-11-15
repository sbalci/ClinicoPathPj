"""Independent integer allocation and installed R waffle geometry comparisons."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import Factor
from cpj_waffle import waffle_core

FIXTURE = ROOT/'tests/fixtures/waffle-core.json'


def inputs(fixture):
    a = fixture['inputs']
    facet = None if a['facets'] is None else Factor(np.array(a['facets']), a['facet_levels'])
    return dict(group=Factor(np.array(a['codes']), a['levels']), weights=a['weights'],
        facet=facet, rows=fixture['rows'], flip=fixture['flip'])


def verify():
    reference = json.loads(FIXTURE.read_text())
    registry = json.loads((ROOT/'inst/python/registry.json').read_text())
    entry = next(e for e in registry['analyses'] if e['id'] == 'pyjwaffle')
    assert reference['baseline_hashes'] == entry['baseline']['files']
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        for path, digest in entry['baseline']['files'].items():
            assert hashlib.sha256(archive.extractfile('jjstatsplot/'+path).read()).hexdigest() == digest
    checks, maximum, differences, matched = 0, 0., 0, 0

    def compare(actual, expected, key):
        nonlocal checks, maximum
        checks += 1
        if isinstance(expected, dict):
            assert isinstance(actual, dict), key
            for k, value in expected.items():
                compare(actual[k], value, k)
        elif isinstance(expected, list):
            assert len(actual) == len(expected), (key, len(actual), len(expected))
            for a, b in zip(actual, expected):
                compare(a, b, key)
        elif expected is None or isinstance(expected, (str, bool, int)):
            assert actual == expected, (key, actual, expected)
        else:
            delta = abs(actual-expected)
            assert delta <= 2e-12*max(1, abs(expected)), (key, actual, expected)
            maximum = max(maximum, delta/max(1, abs(expected)))

    for fixture in reference['fixtures']:
        got = waffle_core(**inputs(fixture))
        compare(got, fixture['expected'], fixture['id'])
        json.dumps(got, allow_nan=False)
        assert len(got['panels']) == len(fixture['legacy'])
        for panel, baseline in zip(got['panels'], fixture['legacy']):
            allocated = [c['tiles'] for c in panel['cells']]
            assert panel['code'] == baseline['code']
            assert (allocated != baseline['tiles']) == baseline['differs']
            if baseline['differs']:
                differences += 1
                # Truncation may only remove a tile from rounded 29, 57 or 58.
                assert all(old == new or (new in (29,57,58) and old == new-1)
                           for new, old in zip(allocated, baseline['tiles']))
            else:
                matched += 1
                assert baseline['n_tiles'] == 100
    return dict(datasets=len({f['id'] for f in reference['fixtures']}),
        configurations=len(reference['fixtures']), checks=checks,
        baseline_matching_panels=matched, baseline_truncation_panels=differences,
        maximum_scaled_difference=maximum,
        fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        scope='Source allocation/geometry only; no native interface, rendered export or GUI claim')


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
