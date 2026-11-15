"""Inspect the JMO and exercise its extracted descriptive pie runtime against R fixtures."""
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
    sys.path.insert(0,str(runtime))
    import cpj_runtime
    from cpj_plots import figure
    assert Path(cpj_runtime.__file__).resolve()==runtime/'cpj_runtime.py'
    fixtures=json.loads((ROOT/'tests/fixtures/pie-core.json').read_text())['fixtures']
    checks=configurations=0
    def compare(actual,expected,key):
        nonlocal checks
        checks+=1
        if isinstance(expected,list):
            assert len(actual)==len(expected),key
            for a,b in zip(actual,expected):compare(a,b,key)
        elif expected is None or isinstance(expected,(str,bool,int)):
            assert actual==expected,(key,actual,expected)
        else:assert abs(actual-expected)<=2e-12*max(1,abs(expected)),(key,actual,expected)
    def request(f,**opts):
        a=f['inputs']
        cols={'Outcome':dict(kind='factor',codes=[None if c<0 else c for c in a['codes']],levels=a['levels'])}
        options=dict(dep='Outcome',**opts)
        if a['weights'] is not None:
            cols['Frequency']=dict(kind='number',values=a['weights']);options['counts']='Frequency'
        return dict(analysis='pyjjpiestats',columns=cols,options=options,row_ids=[str(7*i+3) for i in range(len(a['codes']))])
    def run(req):
        nonlocal configurations
        configurations+=1
        got=cpj_runtime.execute(req);json.dumps(got,allow_nan=False)
        return got
    for f in fixtures:
        ref=f['expected']
        for label in ('percentage','counts','both'):
            for digits in (0,2):
                req=request(f,label=label,digitsperc=digits,showCases=True)
                got=run(req);compare(got['status'],'ok',f['id'])
                for k,v in [('source','n_source'),('complete','n_complete'),('excluded','excluded_missing'),('zero','zero_frequency'),('contributing','n_contributing'),('total','n_total')]:
                    compare(got['tables']['cohort']['rows'][0][k],ref[v],k)
                rows=got['tables']['frequencies']['rows'];compare(len(rows),len(ref['cells']),'categories')
                for actual,c in zip(rows,ref['cells']):
                    for k,v in [('category','label'),('code','code'),('count','count'),('proportion','proportion')]:compare(actual[k],c[v],k)
                    compare(actual['denominator'],ref['n_total'],'denominator')
                compare([r['sourceID'] for r in got['tables']['cases']['rows']],[req['row_ids'][i] for i in ref['retained_indices']],'identities')
                state=got['plots']['piePlot'];columns=state['columns']
                for k in ('lower','upper'):compare(columns[k],[c[k] for c in ref['cells']],k)
                expected_labels=[]
                for c in ref['cells']:
                    count=f'{c["count"]:,}';percent=f'{100*c["proportion"]:.{digits}f}%'
                    expected_labels.append((percent if label=='percentage' else count if label=='counts' else count+'\n('+percent+')') if c['count'] else None)
                compare(columns['annotation'],expected_labels,'annotations')
                fig=figure(state,width=650,height=450)
                positive=[c for c in ref['cells'] if c['count']>0]
                compare(len(fig.axes[0].patches),len(positive),'visible slices')
                for wedge,c in zip(fig.axes[0].patches,positive):
                    compare(wedge.theta1,90-360*c['upper'],'clockwise end')
                    compare(wedge.theta2,90-360*c['lower'],'clockwise start')
                compare([t.get_text() for t in fig.axes[0].get_legend().get_texts()],[c['label'] for c in ref['cells']],'legend')
                fig.clear()
    off=run(request(fixtures[0],showPlot=False,showCases=False))
    compare(bool(off['plots']),False,'plot off');compare('cases' in off['tables'],False,'cases off')
    for opts in (dict(group='Outcome'),dict(typestatistics='bayes'),dict(resultssubtitle=True,customRatios=True,ratio='1,2'),dict(digitsperc=3)):
        compare(run(request(fixtures[0],**opts))['status'],'input_error','unsupported')
    gof_fixtures=json.loads((ROOT/'tests/fixtures/pie-gof-core.json').read_text())['fixtures']
    for f in gof_fixtures:
        for r in f['runs']:
            req=request(f,resultssubtitle=True,customRatios=r['ratios'] is not None,
                ratio=json.dumps(r['ratios']) if r['ratios'] is not None else '')
            got=run(req);compare(got['status'],'ok',f['id'])
            row=got['tables']['gof']['rows'][0]
            for key in ('statistic','df','p'):
                expected=r['expected'][key]
                compare(row[key],None if expected is None else float(expected),key)
            expected_rows=got['tables']['expected']['rows']
            compare([c['category'] for c in expected_rows],[c['label'] for c in r['expected']['rows']],'null support')
            compare([c['expected'] for c in expected_rows],[float(c['expected']) for c in r['expected']['rows']],'expected counts')
    return dict(checks=checks,configurations=configurations,runtime=str(cpj_runtime.__file__))


def check(path):
    path = Path(path)
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-pie-package-') as folder:
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names = z.namelist()
            assert len(names) == len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            meta = z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$', meta, re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pyjjpiestats\s*$', meta, re.M)) == 1
            for item in ('cpj_pie.py', 'cpj_pie_gof.py', 'cpj_pie_adapter.py', 'cpj_runtime.py', 'cpj_plots.py',
                         'analyses/jjstatsplot/pyjjpiestats.py'):
                assert z.read('ClinicoPathPj/R/ClinicoPathPj/python/'+item) == (ROOT/'inst/python'/item).read_bytes(), item
            assert z.read('ClinicoPathPj/data/python_pie_examples.csv') == (ROOT/'data/python_pie_examples.csv').read_bytes()
            ui = z.read('ClinicoPathPj/ui/pyjjpiestats.js').decode()
            for key in ('dep', 'counts', 'subject', 'showCases', 'showPlot', 'label', 'digitsperc', 'resultssubtitle', 'customRatios', 'ratio', 'showExpected'):
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
