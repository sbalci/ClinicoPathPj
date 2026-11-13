"""Check actual raw and standardized estimation JMO runtime against independent R results."""
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
    fixture = ROOT/'tests/fixtures/estimation-core.json'
    references = json.loads(fixture.read_text())['fixtures']
    checks, configurations, maximum_relative = 0, 0, 0.
    standardized_configs, gating_configs, maximum_standardized = 0, 0, 0.
    standardized_fixture = ROOT/'tests/fixtures/standardized-effects.json'
    standardized_references = {f['id']: f for f in json.loads(standardized_fixture.read_text())['fixtures']}
    welch_fixture = ROOT/'tests/fixtures/welch-standardized-effects.json'
    welch_references = {f['id']: f for f in json.loads(welch_fixture.read_text())['fixtures']}
    qualification_changes = []

    def compare(got, expected):
        nonlocal checks, maximum_relative
        checks += 1
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            assert isinstance(got, (int, float)), (got, expected)
            error = abs(got-expected)
            if expected == 0:
                assert got == 0, (got, expected)
            else:
                maximum_relative = max(maximum_relative, error/abs(expected))
                assert error <= abs(expected)*1e-11, (got, expected)
        else:
            assert got == expected, (got, expected)

    def compare_standardized(got, expected, interval=False):
        nonlocal checks, maximum_standardized
        checks += 1
        if expected is None or isinstance(expected, str):
            assert got == expected, (got, expected)
        else:
            assert isinstance(got, (int, float)), (got, expected)
            error = abs(got-expected)
            tolerance = 2e-7*max(1,abs(expected)) if interval else abs(expected)*1e-10
            assert error <= tolerance, (got, expected, error, tolerance)
            maximum_standardized = max(maximum_standardized, error/max(1,abs(expected)))

    with tempfile.TemporaryDirectory(prefix='cpj-estimation-package-') as folder:
        directory = Path(folder)
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            names = archive.namelist()
            assert len(names) == len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') or '/tests/reference/' in n for n in names)
            metadata = archive.read('ClinicoPathPj/jamovi.yaml').decode()
            packaged_version = re.search(r'^version:\s*[\'\"]?([0-9.]+)', metadata, re.M)
            assert packaged_version and packaged_version.group(1) == version
            for name in ('pyjjbetweenstats', 'pyjjwithinstats'):
                assert len(re.findall(r'^\s*(?:- )?name: '+name+r'\s*$', metadata, re.M)) == 1
                ui = archive.read('ClinicoPathPj/ui/'+name+'.js').decode()
                for binding in ('conflevel', 'showCases', 'showPlot', 'showStandardized'):
                    assert binding in ui
                assert archive.read('ClinicoPathPj/R/ClinicoPathPj/python/analyses/jjstatsplot/'+name+'.py') == (ROOT/'inst/python/analyses/jjstatsplot'/ (name+'.py')).read_bytes()
            for member in ('cpj_estimation.py', 'cpj_estimation_adapter.py', 'cpj_standardized.py', 'cpj_welch_standardized.py', 'cpj_runtime.py'):
                assert archive.read('ClinicoPathPj/R/ClinicoPathPj/python/'+member) == (ROOT/'inst/python'/member).read_bytes()
            packaged = json.loads(archive.read('ClinicoPathPj/R/ClinicoPathPj/python/registry.json'))
            source = json.loads((ROOT/'inst/python/registry.json').read_text())
            # Only coverage evidence can advance after qualifying this immutable archive;
            # full_parity, baseline, source, methods and option/output contracts cannot.
            for name in ('pyjjbetweenstats', 'pyjjwithinstats', 'pyjjhistostats'):
                p = next(e for e in packaged['analyses'] if e['id'] == name)
                s = next(e for e in source['analyses'] if e['id'] == name)
                for key in ('numerical', 'gui', 'platforms'):
                    if p['coverage'][key] != s['coverage'][key]:
                        qualification_changes.append(name+'.coverage.'+key)
                        p['coverage'][key] = s['coverage'][key]
            assert packaged == source, 'Packaged registry implementation differs from source'
            assert archive.read('ClinicoPathPj/data/python_estimation_examples.csv') == (ROOT/'data/python_estimation_examples.csv').read_bytes()
            archive.extractall(directory)
        runtime = directory/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        for case in references:
            paired = case['design'] == 'paired'
            number = lambda x: dict(kind='number', values=x)
            if paired:
                columns = dict(First=number(case['a']), Second=number(case['b']))
                options = dict(dep1='First', dep2='Second')
            else:
                columns = dict(Outcome=number(case['values']), Group=dict(kind='factor', levels=case['levels'], codes=[None if c<0 else c for c in case['codes']]))
                options = dict(dep=['Outcome'], group='Group', firstLevel=case['first'], secondLevel=case['second'])
            options.update(conflevel=.95, showCases=True, showPlot=True)
            row_ids = [str(10+3*i) for i in range(case['expected']['n_source'])]
            for ref in (r for r in case['expected']['runs'] if r['confidence'] == .95):
                if not paired: options['varequal'] = ref['method'] == 'student'
                request, response = directory/'request.json', directory/'response.json'
                request.write_text(json.dumps(dict(analysis='pyjjwithinstats' if paired else 'pyjjbetweenstats', columns=columns, options=options, row_ids=row_ids)))
                subprocess.run([sys.executable, '-B', '-s', str(runtime), str(request), str(response)], check=True, capture_output=True, timeout=60)
                result = json.loads(response.read_text())
                assert result['status'] == 'ok', (case['id'], result.get('error'))
                tables = result['tables']
                cohort = tables['cohort']['rows'][0]
                compare(cohort['retained'], case['expected']['n_complete'])
                compare(cohort['excluded'], case['expected']['excluded_missing'])
                for row, key in zip(tables['descriptives']['rows'], ('first','second')):
                    for column in ('n','mean','sd'): compare(row[column], case['expected']['summaries'][key][column])
                row = tables['contrast']['rows'][0]
                for key in ('difference','stderr','df','statistic','p','lower','upper','status'):
                    # Tiny p-values retain relative agreement in packaged execution.
                    compare(row[key], ref[key])
                compare([r['sourceID'] for r in tables['cases']['rows']], [row_ids[i] for i in case['expected']['retained_indices']])
                plot = result['plots']['differencePlot']
                for key, column in (('difference','estimate'), ('lower','lower'), ('upper','upper')):
                    compare(plot['columns'][column], [row[key]])
                compare(plot['reference'], 0)
                configurations += 1
            baseline = result
            assert not any(name in baseline['tables'] for name in ('standardizer','standardized','hedges'))
            assert 'standardizedPlot' not in baseline['plots']
            options['showStandardized'] = True
            request.write_text(json.dumps(dict(analysis='pyjjwithinstats' if paired else 'pyjjbetweenstats', columns=columns, options=options, row_ids=row_ids)))
            subprocess.run([sys.executable, '-B', '-s', str(runtime), str(request), str(response)], check=True, capture_output=True, timeout=60)
            result = json.loads(response.read_text())
            assert result['status'] == 'ok', (case['id'], result.get('error'))
            for name in ('cohort','missing','descriptives','contrast','cases'):
                compare(result['tables'][name], baseline['tables'][name])
            compare(result['plots']['differencePlot'], baseline['plots']['differencePlot'])
            expected = next(r for r in standardized_references[case['id']]['runs'] if r['confidence'] == .95)
            std = result['tables']['standardized']['rows'][0]
            model = result['tables']['standardizer']['rows'][0]
            hedges = result['tables']['hedges']['rows'][0]
            for column,key in (('sd','standardizer_sd'),('df','df')):
                compare_standardized(model[column],expected[key])
            for column,key in (('estimate','cohens_d'),('lower','delta_lower'),('upper','delta_upper')):
                compare_standardized(std[column],expected[key], interval=column in ('lower','upper'))
            compare_standardized(std['status'],expected['status'])
            compare(std['metric'],'Cohen d_z' if paired else 'Cohen d')
            compare(model['denominator'],'Within-row difference SD' if paired else 'Sample-size-weighted pooled SD')
            compare(hedges['metric'],'Hedges g_z (point only)' if paired else 'Hedges g (point only)')
            for column,key in (('estimate','hedges_g'),('correction','correction')):
                compare_standardized(hedges[column],expected[key])
            assert 'lower' not in hedges and 'upper' not in hedges
            if expected['cohens_d'] is None:
                assert 'standardizedPlot' not in result['plots']
            else:
                plot = result['plots']['standardizedPlot']
                for column in ('estimate','lower','upper'):
                    compare(plot['columns'][column],[std[column]])
                compare(plot['reference'],0)
            standardized_configs += 1
            if not paired:
                options['varequal'] = False
                request.write_text(json.dumps(dict(analysis='pyjjbetweenstats', columns=columns, options=options, row_ids=row_ids)))
                subprocess.run([sys.executable, '-B', '-s', str(runtime), str(request), str(response)], check=True, capture_output=True, timeout=60)
                result = json.loads(response.read_text())
                assert result['status'] == 'ok', (case['id'], result.get('error'))
                assert not any(name in result['tables'] for name in ('standardizer','standardized','hedges'))
                assert 'standardizedPlot' not in result['plots']
                welch = next(r for r in case['expected']['runs'] if r['confidence'] == .95 and r['method'] == 'welch')
                for key in ('difference','stderr','df','statistic','p','lower','upper','status'):
                    compare(result['tables']['contrast']['rows'][0][key],welch[key])
                expected_point = next(r for r in welch_references[case['id']]['runs'] if r['confidence'] == .95)
                point = result['tables']['welchEffect']['rows'][0]
                model = result['tables']['welchStandardizer']['rows'][0]
                for observed, key in ((point['estimate'],'d_rms'),(model['sd'],'standardizer_sd'),
                                      (model['welch_df'],'welch_df'),(model['sd_moment_df'],'sd_moment_df')):
                    compare_standardized(observed,expected_point[key])
                compare(point['status'],'degenerate' if expected_point['status']=='degenerate' else 'point_only')
                compare(point['first'],case['first']); compare(point['second'],case['second'])
                assert set(point)=={'first','second','estimate','status'}
                assert set(model)=={'denominator','sd','welch_df','sd_moment_df'}
                gating_configs += 1
            print(case['id'], 'raw/standardized passed', flush=True)
    report = dict(scope='Actual JMO extracted estimation runtime; GUI and clinical qualification separate',
        archive=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
        CRC='pass', datasets=len(references), raw_configurations=configurations,
        standardized_configurations=standardized_configs, Welch_point_configurations=gating_configs,
        configurations=configurations+standardized_configs+gating_configs, checks=checks,
        relative_tolerance=1e-11, maximum_relative_difference=maximum_relative,
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        standardized_fixture_sha256=hashlib.sha256(standardized_fixture.read_bytes()).hexdigest(),
        Welch_fixture_sha256=hashlib.sha256(welch_fixture.read_bytes()).hexdigest(),
        maximum_standardized_scaled_difference=maximum_standardized, standardized_interval_tolerance=2e-7,
        source_bytes_match=True, registry_implementation_matches=True,
        post_build_qualification_fields=qualification_changes, native_GUI_qualified=False)
    (ROOT/f'docs/validation-exports/python-estimation-{version}-runtime-20261112.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    check(sys.argv[1] if len(sys.argv)>1 else ROOT/f'ClinicoPathPj_{version}.jmo')
