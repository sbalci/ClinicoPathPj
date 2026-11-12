"""Check paired-difference intervals against pinned R and MPFR references."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_paired_interval import newcombe_interval
from cpj_paired_decision import paired_decision


def verify():
    source = ROOT/'tests/fixtures/paired-difference-intervals.json'
    reference = json.loads(source.read_text())
    frozen = ROOT/'tests/reference/frozen/paired-intervals'
    manifest = reference['provenance']
    for name, digest in manifest['independent']['files'].items():
        assert hashlib.sha256((frozen/name).read_bytes()).hexdigest() == digest, name
    assert hashlib.sha256((frozen/'meddecide-paired-proportions.R').read_bytes()).hexdigest() == manifest['baseline']['sha256']
    assert hashlib.sha256((ROOT/'tests/reference/paired-difference-intervals.R').read_bytes()).hexdigest() == reference['reference_code_sha256']
    paired_path = ROOT/'tests/fixtures/paired-decision.json'
    assert hashlib.sha256(paired_path.read_bytes()).hexdigest() == reference['paired_fixture_sha256']
    checks = 0
    maximum = 0.

    def compare(actual, expected, label):
        nonlocal checks, maximum
        checks += 1
        if isinstance(expected, (int, float)):
            assert actual is not None, label
            error = abs(actual-expected)
            maximum = max(maximum, error)
            assert error <= 1e-12, (label, actual, expected, error)
        else:
            assert actual == expected, (label, actual, expected)

    indexed = {}
    for fixture in reference['fixtures']:
        indexed[fixture['id']] = fixture
        for run in fixture['runs']:
            result = newcombe_interval(fixture['cells'], run['confidence'])
            for key, expected in run['expected'].items():
                compare(result[key], expected, fixture['id']+'.'+key)
            for key, expected in zip(('counts0', 'counts1', 'counts2', 'counts3'), fixture['cells']):
                compare(result['counts'][int(key[-1])], expected, fixture['id']+'.'+key)
            if run['independent'] is not None:
                for key in ('estimate', 'lower', 'upper'):
                    compare(result[key], run['independent'][key], fixture['id']+'.independent.'+key)
                    compare(result[key], float(run['mpfr'][key+'_mpfr']) if key != 'estimate'
                            else run['mpfr'][key], fixture['id']+'.MPFR256.'+key)
            if run['baseline_95'] is not None:
                for key, target in [('estimate', 'diff'), ('lower', 'lower'), ('upper', 'upper')]:
                    compare(result[key], run['baseline_95'][target], fixture['id']+'.baseline95.'+key)
            json.dumps(result, allow_nan=False)

    loader = importlib.util.spec_from_file_location('paired_fixture_inputs', ROOT/'tools/check-paired-decision.py')
    helper = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(helper)
    for case in json.loads(paired_path.read_text())['fixtures']:
        for confidence in (.8, .95, .99):
            for method in ('midp', 'asymptotic', 'exact'):
                args = helper.inputs(case)
                original = paired_decision(**args, confidence=confidence, method=method)
                expanded = paired_decision(**args, confidence=confidence, method=method, difference_intervals=True)
                restored = copy.deepcopy(expanded)
                restored['interval_method'] = original['interval_method']
                for pair in restored['pairs']:
                    for metric in ('accuracy', 'sensitivity', 'specificity'):
                        row = pair[metric]
                        fixture = indexed['/'.join((case['id'], pair['first_name'], pair['second_name'], metric))]
                        expected = next(r['expected'] for r in fixture['runs'] if r['confidence'] == confidence)
                        for key in ('lower', 'upper'):
                            compare(row[key], expected[key], fixture['id']+'.adapter.'+key)
                        compare(row['interval_status'], 'absent_class' if row['n'] == 0 else 'ok', fixture['id']+'.adapter.status')
                        for key in ('lower', 'upper', 'interval_phi', 'interval_status', 'interval_method'):
                            row.pop(key)
                assert restored == original, 'Opt-in intervals changed points, p-values or cohort'
                json.dumps(expanded, allow_nan=False)
    return dict(scope='Source-only paired limits; no native/GUI or coverage qualification',
                count_tables=len(reference['fixtures']), confidence_runs=sum(len(f['runs']) for f in reference['fixtures']),
                checks=checks, failures=0, tolerance=1e-12, max_absolute_difference=maximum,
                fixture_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                interval_engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_paired_interval.py').read_bytes()).hexdigest(),
                opt_in_preserves_points_pvalues_and_cohort=True)


if __name__ == '__main__':
    report = verify()
    (ROOT/'docs/validation-exports/python-paired-intervals-numerical-20261111.json').write_text(
        json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
