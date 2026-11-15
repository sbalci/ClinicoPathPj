"""Inspect the JMO and exercise its extracted categorical-bar runtime against R fixtures."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def runtime_checks(runtime):
    runtime = runtime.resolve()
    sys.path.insert(0, str(runtime))
    import cpj_runtime
    assert Path(cpj_runtime.__file__).resolve() == runtime / 'cpj_runtime.py'
    fixtures = json.loads((ROOT / 'tests/fixtures/barstats-core.json').read_text())['fixtures']
    checks = configurations = 0

    def compare(actual, expected, key):
        nonlocal checks
        checks += 1
        if isinstance(expected, list):
            assert len(actual) == len(expected), key
            for a, b in zip(actual, expected):
                compare(a, b, key)
        elif expected is None or isinstance(expected, (str, bool, int)):
            assert actual == expected, (key, actual, expected)
        else:
            assert abs(actual - expected) <= (abs(expected) * 1e-10 if expected else 1e-12), (key, actual, expected)

    def request(fixture, **options):
        a = fixture['inputs']
        columns = {name: dict(kind='factor', codes=[None if c < 0 else c for c in a[prefix + '_codes']],
                             levels=a[prefix + '_levels'])
                   for name, prefix in [('Outcome', 'outcome'), ('Group', 'group')]}
        opts = dict(dep=['Outcome'], group='Group', **options)
        if a['weights'] is not None:
            columns['Frequency'] = dict(kind='number', values=a['weights'])
            opts['counts'] = 'Frequency'
        return dict(analysis='pyjjbarstats', columns=columns, options=opts,
                    row_ids=[str(10 + 3*i) for i in range(len(a['outcome_codes']))])

    def execute(req):
        nonlocal configurations
        configurations += 1
        result = cpj_runtime.execute(req)
        json.dumps(result, allow_nan=False)
        return result

    for f in fixtures:
        ref = f['expected']
        if ref['status'] == 'error':
            # Invalid numeric encodings may fail at the public transport boundary.
            try:
                got = execute(request(f))
            except cpj_runtime.InputError:
                checks += 1
                continue
            compare(got['status'], 'input_error', f['id'])
            continue
        for enabled in (False, True):
            for scale in ('percentage', 'count'):
                req = request(f, resultssubtitle=enabled, barScale=scale, showCases=True)
                got = execute(req)
                compare(got['status'], 'ok', f['id'])
                tables = got['tables']
                for key, source in [('source', 'n_source'), ('complete', 'n_complete'),
                                    ('excluded', 'excluded_missing'), ('zero', 'zero_frequency'),
                                    ('contributing', 'n_contributing'), ('total', 'n_total')]:
                    compare(tables['cohort']['rows'][0][key], ref[source], key)
                rows = tables['cells']['rows']
                compare(len(rows), len(ref['cells']), 'cell count')
                for actual, cell in zip(rows, ref['cells']):
                    for key in ('count', 'expected', 'group_total', 'group_proportion', 'overall_proportion'):
                        compare(actual[key], cell[key], key)
                    for role in ('outcome', 'group'):
                        compare(actual[role], f['inputs'][role+'_levels'][cell[role]], role)
                compare([r['sourceID'] for r in tables['cases']['rows']],
                        [req['row_ids'][i] for i in ref['retained_indices']], 'source identities')
                columns = got['plots']['barPlot']['columns']
                for key in ('x', 'lower', 'upper'):
                    compare(columns[key], [c[key] for c in ref['geometry'][scale]], key)
                if enabled:
                    assoc = ref['association']
                    compare(tables['association']['rows'][0]['p'], assoc['primary_p'], 'primary p')
                    compare(tables['association']['rows'][0]['method'],
                            'Fisher exact (two-sided)' if assoc['primary_method']=='fisher_exact' else 'Pearson chi-square', 'method')
                    for key, source in [('statistic', 'pearson_statistic'), ('df', 'df'), ('p', 'pearson_p')]:
                        compare(tables['pearson']['rows'][0][key], assoc[source], key)
                    for key, source in [('raw', 'cramers_v_raw'), ('corrected', 'cramers_v_corrected')]:
                        compare(tables['effects']['rows'][0][key], assoc[source], key)
                else:
                    for key in ('association', 'pearson', 'effects'):
                        compare(key in tables, False, key+' off')
    req = request(fixtures[0], showCells=False, showCases=False, showPlot=False)
    got = execute(req)
    for key in ('cells', 'cases', 'association', 'pearson', 'effects'):
        compare(key in got['tables'], False, key+' off')
    compare(bool(got['plots']), False, 'plot off')
    for opts in (dict(paired=True), dict(typestatistics='bayes'), dict(conflevel=.9), dict(barScale='invalid')):
        compare(execute(request(fixtures[0], **opts))['status'], 'input_error', 'unsupported')
    return dict(checks=checks, configurations=configurations, runtime=str(cpj_runtime.__file__))


def check(path):
    path = Path(path)
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-barstats-package-') as folder:
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names = z.namelist()
            assert len(names) == len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            meta = z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$', meta, re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pyjjbarstats\s*$', meta, re.M)) == 1
            for item in ('cpj_barstats.py', 'cpj_barstats_adapter.py', 'cpj_runtime.py', 'cpj_plots.py',
                         'analyses/jjstatsplot/pyjjbarstats.py'):
                assert z.read('ClinicoPathPj/R/ClinicoPathPj/python/'+item) == (ROOT/'inst/python'/item).read_bytes(), item
            assert z.read('ClinicoPathPj/data/python_barstats_examples.csv') == (ROOT/'data/python_barstats_examples.csv').read_bytes()
            ui = z.read('ClinicoPathPj/ui/pyjjbarstats.js').decode()
            for key in ('dep', 'group', 'counts', 'subject', 'resultssubtitle', 'barScale', 'showCells', 'showCases', 'showPlot', 'label', 'digitsperc'):
                assert key in ui, key
            packaged = json.loads(z.read('ClinicoPathPj/R/ClinicoPathPj/python/registry.json'))
            source = json.loads((ROOT/'inst/python/registry.json').read_text())
            for p in packaged['analyses']:
                s = next(e for e in source['analyses'] if e['id']==p['id'])
                assert {k:v for k,v in p.items() if k!='coverage'} == {k:v for k,v in s.items() if k!='coverage'}
                assert p['coverage']['full_parity'] == s['coverage']['full_parity']
            z.extractall(folder)
        runtime = Path(folder)/'ClinicoPathPj/R/ClinicoPathPj/python'
        done = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--runtime', str(runtime)],
                              capture_output=True, text=True, timeout=180)
        assert done.returncode == 0, (done.stdout, done.stderr)
        report = json.loads(done.stdout)
        report.update(package=str(path), version=version, bytes=path.stat().st_size,
                      sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      scope='Actual JMO runtime; desktop and clinical qualification separate')
        return report


if __name__ == '__main__':
    print(json.dumps(runtime_checks(Path(sys.argv[2])) if sys.argv[1]=='--runtime' else check(sys.argv[1]), indent=2))
