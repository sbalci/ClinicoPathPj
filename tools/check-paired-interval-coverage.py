"""Exact, prespecified coverage profile for the source-only paired interval engine."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.special import gammaln, xlogy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_paired_interval import newcombe_interval


def enumerate_counts(n):
    return np.array([(a, b, c, n-a-b-c) for a in range(n+1)
                     for b in range(n-a+1) for c in range(n-a-b+1)], dtype=np.int64)


def profile(sizes=(5, 10, 20, 50)):
    source = ROOT/'tests/fixtures/paired-difference-coverage.json'
    reference = json.loads(source.read_text())
    assert reference['nominal_tolerance'] == .02 and reference['endpoint_tolerance'] == 1e-12
    assert hashlib.sha256((ROOT/'tests/reference/paired-difference-coverage.R').read_bytes()).hexdigest() == reference['reference_sha256']
    rows, tables = [], []
    for n in sizes:
        cells = enumerate_counts(n)
        assert len(cells) == math.comb(n+3, 3) and np.all(cells.sum(axis=1) == n)
        constants = gammaln(n+1)-gammaln(cells+1).sum(axis=1)
        tables.append(dict(n=n,table_count=len(cells),
                           counts_sha256=hashlib.sha256(cells.astype('<i8').tobytes()).hexdigest()))
        for confidence in (.8, .95, .99):
            bounds = np.array([(r['lower'],r['upper']) for r in
                               (newcombe_interval(x,confidence) for x in cells)])
            assert np.isfinite(bounds).all() and np.all(bounds[:,0] <= bounds[:,1])
            for expected in reference['rows']:
                if expected['n'] != n or expected['confidence'] != confidence:
                    continue
                probabilities = np.asarray(expected['probabilities'])
                assert np.all(probabilities >= 0) and abs(probabilities.sum()-1) < 1e-15
                mass = np.exp(constants+xlogy(cells,probabilities).sum(axis=1))
                total = float(mass.sum())
                assert abs(total-1) <= 1e-12
                truth = float(probabilities[1]-probabilities[2])
                covered = (bounds[:,0] <= truth+1e-12) & (bounds[:,1] >= truth-1e-12)
                coverage = float(mass[covered].sum())
                width = float(mass @ (bounds[:,1]-bounds[:,0]))
                for value, target in ((coverage,expected['coverage']), (width,expected['mean_width']),
                                      (total,expected['mass_sum']), (truth,expected['true_difference'])):
                    assert abs(value-target) <= 1e-12, (expected['scenario'],n,confidence,value,target)
                passed = coverage >= confidence-.02-1e-12
                assert passed == expected['screen_pass']
                rows.append(dict(n=n,confidence=confidence,scenario=expected['scenario'],
                                 true_difference=truth,coverage=coverage,mean_width=width,
                                 mass_sum=total,screen_pass=passed))
        print(f'Checked exact coverage for n={n}: {len(cells)} tables',flush=True)
    return dict(scope='Prespecified exact coverage profile; not universal coverage or clinical qualification',
                endpoint_tolerance=1e-12,screen_tolerance=.02,profiles=len(rows),
                passed=sum(r['screen_pass'] for r in rows),failed=sum(not r['screen_pass'] for r in rows),
                tables=tables,rows=rows,
                reference_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_paired_interval.py').read_bytes()).hexdigest())


if __name__ == '__main__':
    report = profile()
    out = ROOT/'docs/validation-exports/python-paired-interval-coverage-20261111.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('profiles','passed','failed','reference_sha256','engine_sha256')},indent=2))
