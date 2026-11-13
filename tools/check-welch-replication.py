"""Replay independently frozen R replication/sensitivity, without changing estimator."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import beta, nct

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import Factor
from cpj_welch_standardized import between_welch_standardized

MANIFEST = ROOT/'tests/fixtures/welch-standardized-replication.json'
DRAWS = ROOT/'tests/fixtures/welch-standardized-replication.csv.gz'
SOURCE_PATHS = {'inst/python/cpj_welch_standardized.py', 'inst/python/cpj_estimation.py',
                'inst/python/cpj_standardized.py', 'tests/fixtures/welch-standardized-effects.json',
                'tests/fixtures/welch-standardized-coverage.json',
                'tests/fixtures/welch-standardized-coverage.csv'}


def load_draws():
    with gzip.open(DRAWS, 'rt', newline='') as stream:
        reader = csv.DictReader(stream)
        names = ['profile', 'replicate', 'mean1', 'mean2', 'var1', 'var2', 'R_probability']
        assert reader.fieldnames == names
        rows = [tuple(row[name] for name in names) for row in reader]
    return np.array(rows, dtype=[('profile', 'U80')]+[(name, 'f8') for name in names[1:]])


def coverage_bounds(successes, total, profiles=17):
    """Prespecified simultaneous binomial bounds; all replicates in denominator."""
    if (type(successes) is not int or type(total) is not int or type(profiles) is not int
            or not 0 <= successes <= total or total < 1 or profiles < 1):
        raise ValueError('Use integer binomial counts and a positive family size.')
    tail = .05/(2*profiles)
    lower = float(beta.ppf(tail, successes, total-successes+1)) if successes else 0.
    upper = float(beta.ppf(1-tail, successes+1, total-successes)) if successes < total else 1.
    status = 'fail' if upper < .925 else 'pass' if lower >= .925 else 'inconclusive'
    return lower, upper, status


def verify(manifest=None, draws=None):
    references = json.loads(MANIFEST.read_text()) if manifest is None else manifest
    if draws is None:
        draws = load_draws()
    assert references['schema_version'] == 1
    assert set(references['source_hashes']) == SOURCE_PATHS
    for name, expected in references['source_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    profiles = references['profiles']
    assert len(profiles) == 17 and len(draws) == 84000
    assert len({p['id'] for p in profiles}) == 17
    expected_designs = [('replication', 'normal', 20, 5, 0, 20000)]
    expected_designs += [('small_sample', 'normal', n1, n2, delta, 4000)
        for n1, n2 in ((2, 2), (2, 5), (5, 2), (3, 3)) for delta in (0, 1.5)]
    expected_designs += [('sensitivity', dist, n1, n2, delta, 4000)
        for dist in ('lognormal', 'student_t5') for n1, n2 in ((5, 20), (20, 5))
        for delta in (0, 1.5)]
    for p, expected in zip(profiles, expected_designs):
        assert tuple(p[k] for k in ('kind', 'distribution', 'n1', 'n2', 'delta', 'N')) == expected
        assert p['sigma1'] == 1 and p['sigma2'] == 4
    assert references['domain'] == dict(df_min=2, df_max=100000, abs_t_max=40)
    maximum_cdf_error, maximum_numeric_error, checks, audits = 0., 0., 0, 0
    def compare(got, expected, key):
        nonlocal checks, maximum_numeric_error
        checks += 1
        if expected is None or isinstance(expected, str):
            assert got == expected, (key, got, expected)
            return
        assert isinstance(got, (float, int)) and math.isfinite(got), (key, got)
        error = abs(got-expected)
        tolerance = (2e-7*max(1, abs(expected)) if key in
                     ('ncp_lower', 'ncp_upper', 'delta_lower', 'delta_upper')
                     else 1e-10*abs(expected) if expected else 1e-12)
        assert error <= tolerance, (key, got, expected, error, tolerance)
        maximum_numeric_error = max(maximum_numeric_error, error/max(1, abs(expected)))
    reports = []
    for p in profiles:
        x = draws[draws['profile'] == p['id']]
        n1, n2 = p['n1'], p['n2']
        assert len(x) == p['N']
        assert np.array_equal(x['replicate'], np.arange(1, p['N']+1)), p['id']
        assert all(np.all(np.isfinite(x[k])) for k in x.dtype.names if k != 'profile'), p['id']
        assert np.all(x['var1'] > 0) and np.all(x['var2'] > 0), p['id']
        se = np.sqrt(x['var1']/n1+x['var2']/n2)
        rms = np.sqrt((x['var1']+x['var2'])/2)
        difference = x['mean1']-x['mean2']
        statistic = difference/se
        u, v = x['var1']/n1, x['var2']/n2
        df = (u+v)**2/(u*u/(n1-1)+v*v/(n2-1))
        # Study deltas are nonnegative; R and SciPy CDFs are compared per dataset.
        nc = p['delta']*rms/se
        probabilities = nct.cdf(statistic, df, nc)
        assert np.all(np.isfinite(probabilities)), p['id']
        error = float(np.max(np.abs(probabilities-x['R_probability'])))
        assert error <= 2e-9, (p['id'], error)
        maximum_cdf_error = max(maximum_cdf_error, error)
        supported = ((df >= 2) & (df <= 100000) & (np.abs(statistic) <= 40)
            & (se >= 10*np.finfo(float).eps*np.maximum(np.abs(x['mean1']), np.abs(x['mean2']))))
        included = supported & (probabilities >= .025) & (probabilities <= .975)
        available, successes = int(np.sum(supported)), int(np.sum(included))
        assert available == p['available'] and len(x)-available == p['unsupported'], p['id']
        assert successes == p['successes'], p['id']
        compare(successes/len(x), p['coverage'], 'coverage')
        compare(successes/available if available else None, p['available_coverage'], 'available_coverage')
        lower, upper, status = coverage_bounds(successes, len(x), len(profiles))
        compare(lower, p['lower'], 'lower'); compare(upper, p['upper'], 'upper')
        compare(status, p['status'], 'status')
        reports.append(p)
    for sample in references['selected']:
        p = next(p for p in profiles if p['id'] == sample['profile'])
        a, b = sample['a'], sample['b']
        assert len(a) == p['n1'] and len(b) == p['n2']
        row = draws[(draws['profile'] == p['id']) & (draws['replicate'] == sample['replicate'])]
        assert len(row) == 1
        for got, key in ((float(np.mean(a)), 'mean1'), (float(np.mean(b)), 'mean2'),
                         (float(np.var(a, ddof=1)), 'var1'), (float(np.var(b, ddof=1)), 'var2')):
            compare(got, float(row[key][0]), key)
        result = between_welch_standardized(a+b,
            Factor(np.array([0]*len(a)+[1]*len(b)), ['First', 'Second']), 'First', 'Second',
            standardizer='rms_variance', interval='welch_nct_plugin')
        raw, std = result['raw'], result['standardized']
        for key, expected in sample['expected'].items():
            target = raw if key in ('difference', 'stderr', 'df') else std
            compare(target[key], expected, key)
        got_included = (std['status'] == 'ok' and std['delta_lower'] <= p['delta'] <= std['delta_upper'])
        expected_included = (sample['expected']['status'] == 'ok'
            and .025 <= float(row['R_probability'][0]) <= .975)
        assert got_included == expected_included, (p['id'], sample['replicate'])
        json.dumps(result, allow_nan=False)
        audits += 1
    return dict(scope='Source-only independent replication/sensitivity; no native qualification',
        profiles=reports, draws=len(draws), selected_original_dataset_audits=audits,
        numerical_checks=checks, maximum_scaled_absolute_difference=maximum_numeric_error,
        maximum_R_SciPy_CDF_difference=maximum_cdf_error,
        passed=sum(p['status'] == 'pass' for p in reports),
        failed=sum(p['status'] == 'fail' for p in reports),
        inconclusive=sum(p['status'] == 'inconclusive' for p in reports),
        fixture_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (MANIFEST, DRAWS)})


if __name__ == '__main__':
    result = verify()
    (ROOT/'docs/validation-exports/python-welch-replication-20261112.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'profiles'}, indent=2))
    for p in result['profiles']:
        print(p['id'], p['label'], p['status'], p['coverage'], 'available:', p['available'])
