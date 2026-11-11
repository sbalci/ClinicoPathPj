"""Execute the CCC prototype against frozen independent R reference fixtures."""
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'inst/python'))
from cpj_concordance import concordance
from cpj_runtime import InputError


def check():
    path = ROOT / 'tests/fixtures/concordance-points.json'
    fixtures = json.loads(path.read_text())
    records = []
    estimates = refused = 0
    for case in fixtures['cases'] + fixtures['degenerate_cases']:
        x = [float('nan') if v is None else v for v in case['x']]
        y = [float('nan') if v is None else v for v in case['y']]
        if case['n_complete'] < 3:
            try:
                concordance(x, y)
            except InputError:
                refused += 1
                records.append(dict(case=case['id'], claim='minimum_pairs', observed='InputError',
                                    expected='InputError', absolute_difference=None, passed=True))
                continue
            raise AssertionError('Unsupported pair count was accepted: ' + case['id'])
        result = concordance(x, y)
        estimates += 1
        for key in ('ccc', 'precision', 'bias_correction'):
            actual, expected = result[key], case['expected'][key]
            difference = None if actual is None or expected is None else abs(actual-expected)
            passed = actual is expected if difference is None else difference <= 1e-12
            records.append(dict(case=case['id'], claim=key, observed=actual, expected=expected,
                                absolute_difference=difference, passed=passed))
        for key in ('n_input', 'n_complete', 'missing_x', 'missing_y', 'missing_either',
                    'missing_both', 'retained_indices'):
            records.append(dict(case=case['id'], claim=key, observed=result[key], expected=case[key],
                                absolute_difference=None, passed=result[key] == case[key]))
    differences = [row['absolute_difference'] for row in records
                   if row['absolute_difference'] is not None]
    report = dict(date='2026-11-10', status='pass' if all(r['passed'] for r in records) else 'fail',
                  supported_datasets=estimates, explicitly_refused_datasets=refused,
                  comparisons=len(records), tolerance=1e-12,
                  max_absolute_coefficient_difference=max(differences),
                  reference_metadata=fixtures['metadata'],
                  fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_concordance.py').read_bytes()).hexdigest(),
                  scope='Point-estimate engine prototype; no native analysis/UI/CI qualification')
    return report, records


if __name__ == '__main__':
    report, records = check()
    folder = ROOT / 'docs/validation-exports'
    (folder/'python-concordance-points-20261110.json').write_text(json.dumps(report, indent=2)+'\n')
    with (folder/'python-concordance-points-matrix-20261110.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({key: value for key, value in report.items()
                      if key != 'reference_metadata'}, indent=2))
    raise SystemExit(report['status'] != 'pass')
