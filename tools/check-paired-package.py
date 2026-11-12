"""Exercise the actual JMO paired-test adapter against frozen independent R fixtures."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def check(path):
    path = Path(path)
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    fixture = ROOT/'tests/fixtures/paired-decision.json'
    references = json.loads(fixture.read_text())['fixtures']
    count = 0
    largest_error = 0.

    def compare(got, expected):
        nonlocal count, largest_error
        count += 1
        if expected is None:
            assert got is None, (got, expected)
        elif isinstance(expected, (int, float)):
            assert isinstance(got, (int, float)), (got, expected)
            error = abs(got-expected)
            largest_error = max(largest_error, error)
            assert error <= 1e-12, (got, expected, error)
        else:
            assert got == expected, (got, expected)

    with tempfile.TemporaryDirectory(prefix='cpj-paired-package-') as folder:
        directory = Path(folder)
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            names = archive.namelist()
            assert len(names) == len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') or '/tests/reference/' in n for n in names)
            metadata = archive.read('ClinicoPathPj/jamovi.yaml').decode()
            archive_version = re.search(r'^version:\s*[\'\"]?([0-9.]+)', metadata, re.M)
            assert archive_version and archive_version.group(1) == version
            assert len(re.findall(r'^\s*- name: pydecisioncompare\s*$', metadata, re.M)) == 1
            ui = archive.read('ClinicoPathPj/ui/pydecisioncompare.js').decode()
            for role in ('gold', 'test1', 'test2', 'test3'):
                for suffix in ('Positive', 'Negative'):
                    assert role+suffix in ui
            assert 'difference_intervals' not in ui
            packaged_registry = json.loads(archive.read('ClinicoPathPj/R/ClinicoPathPj/python/registry.json'))
            source_registry = json.loads((ROOT/'inst/python/registry.json').read_text())
            packaged_entry = next(e for e in packaged_registry['analyses'] if e['id'] == 'pydecisioncompare')
            source_entry = next(e for e in source_registry['analyses'] if e['id'] == 'pydecisioncompare')
            qualification_changes = []
            # Desktop evidence is recorded after installing this immutable artifact.
            # Only these two evidence fields may advance without rebuilding its code.
            for key in ('gui', 'platforms'):
                if packaged_entry['coverage'][key] != source_entry['coverage'][key]:
                    qualification_changes.append('pydecisioncompare.coverage.'+key)
                    packaged_entry['coverage'][key] = source_entry['coverage'][key]
            assert packaged_registry == source_registry, 'Packaged registry implementation contract differs from source'
            for member in ('cpj_paired_decision.py', 'cpj_accuracy.py',
                           'analyses/meddecide/pydecisioncompare.py'):
                assert archive.read('ClinicoPathPj/R/ClinicoPathPj/python/'+member) == (ROOT/'inst/python'/member).read_bytes()
            assert archive.read('ClinicoPathPj/data/python_paired_test_examples.csv') == (ROOT/'data/python_paired_test_examples.csv').read_bytes()
            archive.extractall(directory)
        runtime = directory/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        for case in references:
            vector = lambda x: x if isinstance(x, list) else [x]
            encode = lambda x: dict(kind='factor', levels=case['levels'],
                codes=[None if value < 0 else value for value in vector(x)])
            columns = {'Reference': encode(case['reference'])}
            options = dict(gold='Reference', goldPositive=case['positive'], goldNegative=case['negative'],
                referenceType='disease', statComp=True, ci=True, showCases=True,
                excludeIndeterminate=case['exclude'])
            for i, (name, values) in enumerate(case['tests'].items(), 1):
                columns[name] = encode(values)
                options.update({f'test{i}': name, f'test{i}Positive': case['positive'],
                                f'test{i}Negative': case['negative']})
            for method in ('midp', 'asymptotic'):
                options['mcnemarMethod'] = method
                reference = next(r for r in case['expected']['runs'] if r['method'] == method and r['confidence'] == .95)
                request = directory/'request.json'
                response = directory/'response.json'
                row_ids = [str(10+i*3) for i in range(len(vector(case['reference'])))]
                request.write_text(json.dumps(dict(analysis='pydecisioncompare', columns=columns,
                                                   options=options, row_ids=row_ids)))
                subprocess.run([sys.executable, '-B', '-s', str(runtime), str(request), str(response)],
                               check=True, capture_output=True, timeout=60)
                result = json.loads(response.read_text())
                assert result['status'] == 'ok', (case['id'], result.get('error'))
                cohort = result['tables']['cohort']['rows'][0]
                for output, target in (('retained', 'n_complete'), ('missing', 'excluded_missing'),
                                       ('outside', 'excluded_indeterminate')):
                    compare(cohort[output], case['expected'][target])
                for row, (name, model) in zip(result['tables']['counts']['rows'], reference['models'].items()):
                    compare(row['test'], name)
                    for key, value in zip(('pp', 'np', 'pn', 'nn'), model['counts']):
                        compare(row[key], value)
                expected_estimates = [p for model in reference['models'].values() for p in model['proportions']]
                assert len(result['tables']['estimates']['rows']) == len(expected_estimates)
                for row, expected in zip(result['tables']['estimates']['rows'], expected_estimates):
                    for key in ('estimate', 'lower', 'upper'):
                        compare(row[key], expected[key])
                expected_pairs = [(metric, pair[metric]) for pair in reference['pairs']
                                  for metric in ('accuracy', 'sensitivity', 'specificity')]
                assert len(result['tables']['comparisons']['rows']) == len(expected_pairs)
                for row, (metric, expected) in zip(result['tables']['comparisons']['rows'], expected_pairs):
                    for key in ('n', 'difference', 'p'):
                        compare(row[key], expected[key])
                    compare(row['adjusted'], expected.get('p_holm') if metric == 'accuracy' else None)
                    assert 'lower' not in row and 'upper' not in row
                compare([row['sourceID'] for row in result['tables']['cases']['rows']],
                        [row_ids[i] for i in vector(case['expected']['retained_indices'])])
            print(case['id'], 'passed', flush=True)
    report = dict(scope='Actual JMO extracted paired-test runtime; no GUI or clinical qualification',
        archive=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
        CRC='pass', fixtures=len(references), configurations=len(references)*2, checks=count,
        tolerance=1e-12, max_absolute_difference=largest_error,
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        local_analysis_and_engine_bytes_match=True, registry_implementation_contract_matches=True,
        post_build_qualification_fields=qualification_changes,
        native_GUI_qualified=False)
    (ROOT/f'docs/validation-exports/python-paired-{version}-runtime-20261111.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    check(sys.argv[1] if len(sys.argv)>1 else ROOT/f'ClinicoPathPj_{version}.jmo')
