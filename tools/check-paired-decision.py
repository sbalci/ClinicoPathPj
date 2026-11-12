"""Check the source-only paired engine against independently frozen base-R results."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_paired_decision import mcnemar_discordance, paired_decision
from cpj_runtime import Factor


def vector(value):
    return value if isinstance(value, list) else [value]


def inputs(fixture):
    levels = fixture['levels']
    factor = lambda x: Factor(np.asarray(vector(x), dtype=int), levels)
    return dict(reference=factor(fixture['reference']),
                tests={k: factor(v) for k, v in fixture['tests'].items()},
                reference_levels=(fixture['positive'], fixture['negative']),
                test_levels={k: (fixture['positive'], fixture['negative']) for k in fixture['tests']},
                exclude_indeterminate=fixture['exclude'])


def verify():
    path = ROOT/'tests/fixtures/paired-decision.json'
    reference = json.loads(path.read_text())
    with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
        blob = archive.extractfile('meddecide/R/decisioncompare.b.R').read()
    assert hashlib.sha256(blob).hexdigest() == reference['baseline_backend_sha256']
    checks = 0
    largest_error = 0.

    def compare(got, expected, name):
        nonlocal checks, largest_error
        if isinstance(expected, dict):
            for key, value in expected.items():
                compare(got[key], value, name+'.'+key)
        elif isinstance(expected, list):
            assert len(got) == len(expected), name
            for i, value in enumerate(expected):
                compare(got[i], value, name+f'[{i}]')
        else:
            checks += 1
            if isinstance(expected, (int, float)) and not isinstance(expected, bool):
                assert isinstance(got, (int, float)), (name, got, expected)
                error = abs(got-expected)
                largest_error = max(largest_error, error)
                assert error <= 1e-12, (name, got, expected, error)
            else:
                assert got == expected, (name, got, expected)

    for case in reference['discordance']:
        for method, expected in case['expected'].items():
            compare(mcnemar_discordance(case['b'], case['c'], method), expected,
                    f"discordance({case['b']},{case['c']},{method})")
    for case in reference['fixtures']:
        common = copy.deepcopy(case['expected'])
        runs = common.pop('runs')
        common['retained_indices'] = vector(common['retained_indices'])
        for run in runs:
            got = paired_decision(**inputs(case), method=run['method'], confidence=run['confidence'])
            compare(got, common, case['id']+'.cohort')
            compare(got['models'], run['models'], case['id']+'.models')
            expected_pairs = copy.deepcopy(run['pairs'])
            for pair in expected_pairs:
                pair['accuracy']['p_adjusted'] = pair['accuracy'].pop('p_holm')
            compare(got['pairs'], expected_pairs, case['id']+'.pairs')
            compare(got['holm_family'], run['holm_family'], case['id']+'.Holm family')
            json.dumps(got, allow_nan=False)
    return dict(scope='Source-only numerical agreement; no native/GUI or clinical qualification',
                discordance_cases=len(reference['discordance']), paired_datasets=len(reference['fixtures']),
                checks=checks, failures=0, tolerance=1e-12, max_absolute_difference=largest_error,
                fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                baseline_backend_sha256=reference['baseline_backend_sha256'])


if __name__ == '__main__':
    report = verify()
    out = ROOT/'docs/validation-exports/python-paired-decision-core-20261111.json'
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
