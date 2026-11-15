"""Execute the actual JMO survival runtime against frozen independent R results."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]


def runtime_checks(runtime):
    runtime=Path(runtime).resolve();sys.path.insert(0,str(runtime))
    import cpj_runtime,cpj_kaplan_meier,cpj_kaplan_meier_adapter,cpj_kaplan_meier_plot,cpj_plots
    for m in (cpj_runtime,cpj_kaplan_meier,cpj_kaplan_meier_adapter,cpj_kaplan_meier_plot,cpj_plots):
        assert Path(m.__file__).resolve().parent==runtime,m.__file__
    fixtures=json.loads((ROOT/'tests/fixtures/kaplan-meier-core.json').read_text())['fixtures']
    checks=configurations=0
    def compare(a,b):
        nonlocal checks
        checks+=1
        if isinstance(b,dict):
            for k,v in b.items():compare(a[k],v)
        elif isinstance(b,list):
            assert len(a)==len(b),(len(a),len(b))
            for v,w in zip(a,b):compare(v,w)
        elif isinstance(b,float):
            assert a is not None and abs(a-b)<=2e-12*max(1e-12,abs(b)),(a,b)
        else:assert a==b,(a,b)
    for f in fixtures:
        inp=f['inputs'];e=f['expected']
        compare(cpj_kaplan_meier.kaplan_meier_core(**inp,queries=f['queries'],
            confidence=f['confidence'],timefix=f['timefix']),e)
        options=dict(elapsedtime='Time',outcome='Status',outcomeLevel='Event',censorLevel='Censored',
            cutp=','.join(str(v) for v in f['queries']),ciWidth=f['confidence']*100,timefix=f['timefix'],
            person_time=True,showSteps=True,showCases=True,sc=True,ci95=True,censored=True)
        req=dict(analysis='pysinglearm',options=options,columns=dict(
            Time=dict(kind='number',values=inp['time']),
            Status=dict(kind='factor',levels=['Censored','Event'],codes=inp['event'])),
            row_ids=[str(i*7+3) for i in range(len(inp['time']))])
        got=cpj_runtime.execute(req);configurations+=1;compare(got['status'],'ok')
        for k,v in [('source','n_source'),('complete','n_complete'),('excluded','excluded_missing'),
                    ('events','events'),('censored','censored'),('normalized','timefix_changed_rows')]:
            compare(got['tables']['cohort']['rows'][0][k],e[v])
        for row,median in zip(got['tables']['medians']['rows'],[e['median'],e['reverse']['median']]):
            compare({k:row[k] for k in ('estimate','lower','upper')},median)
        compare([r['sourceID'] for r in got['tables']['cases']['rows']],
            [req['row_ids'][i] for i in e['retained_indices']])
        compare([r['effectiveTime'] for r in got['tables']['cases']['rows']],e['effective_times'])
        for table,reference in [('steps',e['curve']),('selectedTimes',e['selected'])]:
            rows=got['tables'][table]['rows'];compare(len(rows),len(reference))
            for row,ref in zip(rows,reference):
                for k in ('time','events','censored','survival','lower','upper'):compare(row[k],ref[k])
                compare(row['risk'],ref['n_risk'])
        rate=got['tables']['personTime']['rows'][0]
        for k,v in [('exposure','person_time'),('estimate','estimate'),('lower','lower'),('upper','upper')]:compare(rate[k],e['rate'][v])
        state=got['plots']['survivalPlot'];payload=json.loads(state['columns']['payload'][0])
        compare(payload['n'],e['n_complete']);compare(payload['maximum'],e['max_time'])
        for row,ref in zip(payload['points'],e['curve']):compare(row,{k:ref[k] for k in row})
        fig=cpj_plots.figure(state);axis=fig.axes[0];scale=e['max_time'] or 1
        xs=[0.]+[r['time']/scale for r in e['curve']];ys=[1.]+[r['survival'] for r in e['curve']]
        if e['curve'][-1]['time']<e['max_time']:xs.append(1.);ys.append(ys[-1])
        compare(list(axis.lines[0].get_xdata()),xs);compare(list(axis.lines[0].get_ydata()),ys)
        compare(axis.lines[0].get_drawstyle(),'steps-post')
        for overrides in (dict(sc=False,showCases=False,showSteps=False,person_time=False),dict(outcomeLevel='Censored')):
            result=cpj_runtime.execute(dict(req,options=dict(options,**overrides)));configurations+=1
            compare(result['status'],'input_error' if 'outcomeLevel' in overrides else 'ok')
            compare(bool(result.get('plots')),False)
    compare(cpj_plots.render(state)['mime'],'image/png')
    return dict(configurations=configurations,checks=checks,datasets=len({f['id'] for f in fixtures}),
        fixture_sha256=hashlib.sha256((ROOT/'tests/fixtures/kaplan-meier-core.json').read_bytes()).hexdigest(),
        scope='Actual packaged survival computation/native table payloads and step geometry; native R/GUI qualification separate')


def check(path):
    path=Path(path);version=re.search(r'^Version:\s*(\S+)',(ROOT/'DESCRIPTION').read_text(),re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-singlearm-package-') as folder:
        with ZipFile(path) as z:
            assert z.testzip() is None
            names=z.namelist();assert len(names)==len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            prefix='ClinicoPathPj/R/ClinicoPathPj/python/'
            meta=z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$',meta,re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pysinglearm\s*$',meta,re.M))==1
            packaged=json.loads(z.read(prefix+'registry.json'));source=json.loads((ROOT/'inst/python/registry.json').read_text())
            assert [e['id'] for e in packaged['analyses']]==[e['id'] for e in source['analyses']]
            for p,s in zip(packaged['analyses'],source['analyses']):
                assert {k:v for k,v in p.items() if k!='coverage'}=={k:v for k,v in s.items() if k!='coverage'}
                assert p['coverage']['full_parity']==s['coverage']['full_parity']
            sources={e['source'] for e in source['analyses'] if e.get('source')}
            assert {n[len(prefix):] for n in names if n.startswith(prefix+'analyses/') and n.endswith('.py')}==sources
            for item in sources|{p.name for p in (ROOT/'inst/python').glob('cpj*.py')}:
                assert z.read(prefix+item)==(ROOT/'inst/python'/item).read_bytes(),item
            assert z.read('ClinicoPathPj/data/python_singlearm_examples.csv')==(ROOT/'data/python_singlearm_examples.csv').read_bytes()
            ui=z.read('ClinicoPathPj/ui/pysinglearm.js').decode()
            for key in ('elapsedtime','outcome','outcomeLevel','censorLevel','timetypeoutput','cutp','sc','ci95','censored','timefix'):assert key in ui,key
            for p in (ROOT/'data').glob('*.omv'):
                assert p.name in meta,p.name
                assert z.read('ClinicoPathPj/data/'+p.name)==p.read_bytes(),p.name
            z.extractall(folder)
        done=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--runtime',
            str(Path(folder)/'ClinicoPathPj/R/ClinicoPathPj/python')],capture_output=True,text=True,timeout=300)
        assert done.returncode==0,(done.stdout,done.stderr)
        report=json.loads(done.stdout);report.update(version=version,package=str(path),bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        return report


if __name__=='__main__':
    print(json.dumps(runtime_checks(sys.argv[2]) if sys.argv[1]=='--runtime' else check(sys.argv[1]),indent=2))
