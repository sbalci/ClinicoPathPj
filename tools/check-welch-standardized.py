"""Independent R/package numeric comparisons and fixed-draw coverage replay."""
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


def verify():
    paths = [ROOT/'tests/fixtures'/name for name in ('welch-standardized-effects.json',
             'welch-standardized-coverage.json', 'welch-standardized-coverage.csv')]
    references = json.loads(paths[0].read_text())
    checks, maximum, configs = 0, 0., 0
    def compare(got, expected, key):
        nonlocal checks, maximum
        checks += 1
        if expected is None or isinstance(expected, str):
            assert got == expected, (key, got, expected)
        else:
            tolerance = (2e-7*max(1, abs(expected)) if key in
                ('ncp_lower', 'ncp_upper', 'delta_lower', 'delta_upper') else abs(expected)*1e-10)
            assert isinstance(got, (int, float)), (key, got, expected)
            error = abs(got-expected)
            assert math.isfinite(got) and error <= tolerance, (key, got, expected, error, tolerance)
            maximum = max(maximum, error/max(1, abs(expected)))
    for f in references['fixtures']:
        for ref in f['runs']:
            got = between_welch_standardized(f['values'], Factor(np.array(f['codes']), f['levels']),
                f['first'], f['second'], standardizer='rms_variance',
                interval='welch_nct_plugin', confidence=ref['confidence'])
            for key, value in ref.items():
                if key != 'confidence':
                    try: compare(got['standardized'][key], value, key)
                    except AssertionError as error: raise AssertionError((f['id'], ref['confidence'], error)) from error
            json.dumps(got, allow_nan=False)
            configs += 1
    coverage = json.loads(paths[1].read_text())
    draws = np.genfromtxt(paths[2], delimiter=',', names=True)
    reports, max_cdf_error, audited = [], 0., 0
    for p in coverage['profiles']:
        x = draws[draws['profile'] == p['id']]
        n1, n2 = p['n1'], p['n2']
        v1, v2 = p['sigma1']**2*x['q1']/(n1-1), p['sigma2']**2*x['q2']/(n2-1)
        difference = (p['delta']*math.sqrt((p['sigma1']**2+p['sigma2']**2)/2)
            + math.sqrt(p['sigma1']**2/n1+p['sigma2']**2/n2)*x['z'])
        se, sd = np.sqrt(v1/n1+v2/n2), np.sqrt((v1+v2)/2)
        statistic = difference/se
        df = (v1/n1+v2/n2)**2/((v1/n1)**2/(n1-1)+(v2/n2)**2/(n2-1))
        probabilities = nct.cdf(statistic, df, p['delta']*sd/se)
        error = float(np.max(np.abs(probabilities-x['R_probability'])))
        assert error < 2e-9, (p['id'], error)
        max_cdf_error = max(max_cdf_error, error)
        supported = (df >= 2) & (df <= 100_000) & (np.abs(statistic) <= 40)
        included = supported & (probabilities >= .025) & (probabilities <= .975)
        successes = int(np.sum(included))
        assert successes == p['successes'] and int(np.sum(~supported)) == p['unsupported']
        assert len(x) == p['N']
        tail = .05/(2*len(coverage['profiles']))
        lower = float(beta.ppf(tail, successes, len(x)-successes+1)) if successes else 0.
        upper = float(beta.ppf(1-tail, successes+1, len(x)-successes)) if successes < len(x) else 1.
        compare(lower, p['lower'], 'coverage_lower'); compare(upper, p['upper'], 'coverage_upper')
        status = 'fail' if upper < .925 else 'pass' if lower >= .925 else 'inconclusive'
        assert status == p['status']
        # Independently reconstruct observations with the drawn means/variances;
        # audit the actual engine's inverted limits, not only a CDF shortcut.
        for i in (0, 1, len(x)-2, len(x)-1):
            a = np.full(n1, difference[i], dtype=float); b = np.zeros(n2)
            a[:2] += np.array([-1, 1])*math.sqrt(v1[i]*(n1-1)/2)
            b[:2] += np.array([-1, 1])*math.sqrt(v2[i]*(n2-1)/2)
            result = between_welch_standardized(np.concatenate([a, b]),
                Factor(np.array([0]*n1+[1]*n2), ['First', 'Second']), 'First', 'Second',
                standardizer='rms_variance', interval='welch_nct_plugin')['standardized']
            got_included = (result['status'] == 'ok' and
                result['delta_lower'] <= p['delta'] <= result['delta_upper'])
            assert got_included == bool(included[i]), (p['id'], i, result)
            audited += 1
        reports.append(p)
    return dict(scope='Source-only; no native/GUI/release qualification', datasets=len(references['fixtures']),
        configurations=configs, numeric_checks=checks, maximum_scaled_absolute_difference=maximum,
        package_cross_checks=references['package_cross_checks'],
        coverage_draws=len(draws), maximum_R_SciPy_probability_difference=max_cdf_error,
        full_engine_interval_audits=audited, profiles=reports,
        hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__ == '__main__':
    report = verify()
    (ROOT/'docs/validation-exports/python-welch-standardized-20261112.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
