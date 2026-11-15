"""Inspect and execute the actual JMO; fixtures come from independent frozen R."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def runtime_checks(runtime):
    runtime=runtime.resolve()
    sys.path.insert(0,str(runtime))
    import cpj_runtime
    import cpj_lollipop
    from cpj_plots import figure
    assert Path(cpj_runtime.__file__).resolve()==runtime/'cpj_runtime.py'
    assert Path(cpj_lollipop.__file__).resolve()==runtime/'cpj_lollipop.py'
    fixtures=json.loads((ROOT/'tests/fixtures/lollipop-core.json').read_text())['fixtures']
    checks=configurations=0
    maximum=0.
    def compare(actual,expected,path,exact=False):
        nonlocal checks,maximum
        checks+=1
        if expected is None or isinstance(expected,(str,bool)) or exact:
            assert actual==expected,(path,actual,expected)
        else:
            assert actual is not None,(path,actual,expected)
            delta=abs(actual-expected)/max(1.,abs(expected))
            assert delta<=2e-12,(path,actual,expected)
            maximum=max(maximum,delta)
    def request(f,**options):
        a=f['inputs']
        return dict(analysis='pylollipop',columns={
            'Value':dict(kind='number',values=a['values']),
            'Group':dict(kind='factor',codes=[None if c<0 else c for c in a['codes']],levels=a['levels'])},
            row_ids=[str(7*i+3) for i in range(len(a['values']))],
            options=dict(dep='Value',group='Group',baseline=a['baseline'],**options))
    def run(req):
        nonlocal configurations
        configurations+=1
        got=cpj_runtime.execute(req);json.dumps(got,allow_nan=False)
        return got
    for f in fixtures:
        for run_ref in f['runs']:
            e=run_ref['expected']
            req=request(f,aggregation=run_ref['aggregation'],sortBy=run_ref['sorting'],
                orientation=run_ref['orientation'],showMean=True,showCases=True,showValues=True)
            got=run(req);compare(got['status'],'ok',f['id'])
            for actual,key in zip(got['tables']['descriptives']['rows'],('raw_summary','plotted_summary')):
                for field,value in e[key].items():compare(actual[field],value,key+'.'+field,field=='n')
            cases=got['tables']['cases']['rows'];compare(len(cases),len(e['retained_indices']),'case count',True)
            for actual,i in zip(cases,e['retained_indices']):
                compare(actual['sourceID'],req['row_ids'][i],'source identity')
                compare(actual['value'],f['inputs']['values'][i],'raw measurement')
            state=got['plots']['lollipopPlot'];columns=state['columns']
            compare(state['reference'],e['reference_mean'],'plotted reference')
            compare(len(columns['value']),len(e['points']),'point count',True)
            for i,p in enumerate(e['points']):
                for col,key in [('label','label'),('slot','slot'),('value','value'),('baseline','stem_start')]:
                    compare(columns[col][i],p[key],col,col=='slot')
            fig=figure(state)
            ax=fig.axes[0];horizontal=run_ref['orientation']=='horizontal'
            segments=ax.collections[0].get_segments();offsets=ax.collections[1].get_offsets()
            compare(len(segments),len(e['points']),'stems',True)
            compare(len(offsets),len(e['points']),'markers',True)
            for segment,offset,p in zip(segments,offsets,e['points']):
                endpoints=[[p['stem_start'],p['slot']],[p['stem_end'],p['slot']]] if horizontal else [[p['slot'],p['stem_start']],[p['slot'],p['stem_end']]]
                for actual,want in zip(segment,endpoints):
                    for v,w in zip(actual,want):compare(float(v),w,'stem coordinates')
                for v,w in zip(offset,endpoints[1]):compare(float(v),w,'point coordinates')
            labels=ax.get_yticklabels() if horizontal else ax.get_xticklabels()
            compare([t.get_text() for t in labels],e['axis_levels'],'axis labels',True)
            compare(len(ax.lines),1,'one reference line',True)
            line=ax.lines[0].get_xdata() if horizontal else ax.lines[0].get_ydata()
            for v in line:compare(float(v),e['reference_mean'],'oriented mean line')
            fig.clear()
    off=run(request(fixtures[0],showPlot=False,showPoints=False,showCases=False))
    compare(bool(off['plots']),False,'plot off')
    for table in ('points','cases'):compare(table in off['tables'],False,'table off')
    defaults=run(request(fixtures[0]))
    compare(defaults['plots']['lollipopPlot']['reference'],None,'mean default off')
    for options in (dict(aggregation='bogus'),dict(useHighlight=True),dict(showPlot='yes'),dict(dep='Group')):
        req=request(fixtures[0]);req['options'].update(options)
        compare(run(req)['status'],'input_error','invalid options')
    return dict(checks=checks,configurations=configurations,maximum_scaled_difference=maximum,
        runtime=str(cpj_runtime.__file__),datasets=len(fixtures),
        fixture_sha256=hashlib.sha256((ROOT/'tests/fixtures/lollipop-core.json').read_bytes()).hexdigest())


def check(path):
    path=Path(path)
    version=re.search(r'^Version:\s*(\S+)',(ROOT/'DESCRIPTION').read_text(),re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-lollipop-package-') as folder:
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names=z.namelist()
            assert len(names)==len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            prefix='ClinicoPathPj/R/ClinicoPathPj/python/'
            meta=z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$',meta,re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pylollipop\s*$',meta,re.M))==1
            packaged=json.loads(z.read(prefix+'registry.json'))
            source=json.loads((ROOT/'inst/python/registry.json').read_text())
            assert {e['id'] for e in packaged['analyses']}=={e['id'] for e in source['analyses']}
            for p in packaged['analyses']:
                s=next(e for e in source['analyses'] if e['id']==p['id'])
                assert {k:v for k,v in p.items() if k!='coverage'}=={k:v for k,v in s.items() if k!='coverage'}
                assert p['coverage']['full_parity']==s['coverage']['full_parity']
            sources={e['source'] for e in source['analyses'] if e.get('source')}
            assert {n[len(prefix):] for n in names if n.startswith(prefix+'analyses/') and n.endswith('.py')}==sources
            for item in sources|{p.name for p in (ROOT/'inst/python').glob('cpj*.py')}:
                assert z.read(prefix+item)==(ROOT/'inst/python'/item).read_bytes(),item
            assert z.read('ClinicoPathPj/data/python_lollipop_examples.csv')==(ROOT/'data/python_lollipop_examples.csv').read_bytes()
            ui=z.read('ClinicoPathPj/ui/pylollipop.js').decode()
            for key in ('dep','group','aggregation','sortBy','orientation','baseline','showPlot','showMean','showValues','showPoints','showCases'):
                assert key in ui,key
            z.extractall(folder)
        done=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--runtime',
            str(Path(folder)/'ClinicoPathPj/R/ClinicoPathPj/python')],capture_output=True,text=True,timeout=300)
        assert done.returncode==0,(done.stdout,done.stderr)
        report=json.loads(done.stdout)
        report.update(version=version,package=str(path),bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            scope='Actual JMO runtime and rendered geometry; desktop/clinical/platform acceptance separate')
        return report


if __name__=='__main__':
    print(json.dumps(runtime_checks(Path(sys.argv[2])) if sys.argv[1]=='--runtime' else check(sys.argv[1]),indent=2))
