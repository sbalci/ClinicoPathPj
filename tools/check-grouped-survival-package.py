"""Execute the actual JMO grouped survival runtime against frozen independent R results."""
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
    import cpj_runtime,cpj_grouped_survival,cpj_grouped_survival_adapter,cpj_grouped_survival_plot,cpj_plots
    fixtures=json.loads((ROOT/'tests/fixtures/grouped-survival-core.json').read_text())['fixtures']
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
            assert a is not None and abs(a-b)<=2e-10*max(1,abs(b)),(a,b)
        else:assert a==b,(a,b)
    for f in fixtures:
        inp=f['inputs'];e=f['expected']
        import numpy as np
        group=cpj_runtime.Factor(np.array(inp['codes'],dtype=int),inp['levels'])
        compare(cpj_grouped_survival.grouped_survival_core(inp['time'],inp['event'],group,
            queries=f['queries'],confidence=f['confidence'],timefix=f['timefix']),e)
        options=dict(elapsedtime='Time',outcome='Status',explanatory='Group',
            outcomeLevel='Event',censorLevel='Censored',
            cutp=','.join(str(v) for v in f['queries']),ciWidth=f['confidence']*100,timefix=f['timefix'],
            showSteps=True,showCases=True,sc=True,ci95=True,censored=True)
        req=dict(analysis='pysurvival',options=options,columns=dict(
            Time=dict(kind='number',values=inp['time']),
            Status=dict(kind='factor',levels=['Censored','Event'],codes=inp['event']),
            Group=dict(kind='factor',levels=inp['levels'],codes=[None if v<0 else v for v in inp['codes']])),
            row_ids=[str(i*7+3) for i in range(len(inp['time']))])
        got=cpj_runtime.execute(req);configurations+=1;compare(got['status'],'ok')
        for k,v in [('source','n_source'),('complete','n_complete'),('excluded','excluded_missing'),
                    ('events','events'),('censored','censored'),('normalized','timefix_changed_rows')]:
            compare(got['tables']['cohort']['rows'][0][k],e[v])
        compare(got['tables']['cohort']['rows'][0]['groups'],len(e['groups']))
        for row,g in zip(got['tables']['groups']['rows'],e['groups']):
            for k in ('n','events','censored','maximum','normalized'):compare(row[k],g[k])
            compare(row['group'],g['label']);compare(row['effective'],g['effective_maximum'])
        for row,g in zip(got['tables']['medians']['rows'],e['groups']):
            compare(row['group'],g['label']);compare({k:row[k] for k in ('estimate','lower','upper')},g['median'])
        compare([r['sourceID'] for r in got['tables']['cases']['rows']],
            [req['row_ids'][i] for i in e['retained_indices']])
        compare([r['effectiveTime'] for r in got['tables']['cases']['rows']],e['effective_times'])
        for table,key in [('steps','curve'),('selectedTimes','selected')]:
            reference=[p for g in e['groups'] for p in g[key]];rows=got['tables'][table]['rows']
            compare(len(rows),len(reference))
            compare([r['group'] for r in rows],[g['label'] for g in e['groups'] for p in g[key]])
            for row,ref in zip(rows,reference):
                for k in ('time','events','censored','survival','lower','upper'):compare(row[k],ref[k])
                compare(row['risk'],ref['n_risk'])
        test=got['tables']['logrank']['rows'][0];ref=e['logrank']
        for key in ('statistic','df','p','status'):compare(test[key],ref[key])
        for i,row in enumerate(got['tables']['logrankGroups']['rows']):
            for key in ('observed','expected','score'):compare(row[key],ref[key][i])
        compare([r['value'] for r in got['tables']['covariance']['rows']],[v for r in ref['variance'] for v in r])
        riskrows=got['tables'].get('riskSets',{}).get('rows',[])
        refs=[(p,i) for p in ref['trace'] for i in range(len(e['groups']))][:1000]
        compare(len(riskrows),len(refs))
        for row,(p,i) in zip(riskrows,refs):
            compare(row['time'],p['time']);compare(row['group'],e['groups'][i]['label'])
            for k,v in [('risk','group_risk'),('events','group_events'),('expected','group_expected')]:compare(row[k],p[v][i])
            compare(row['totalRisk'],p['n_risk']);compare(row['totalEvents'],p['events'])
        state=got['plots']['survivalPlot'];payload=json.loads(state['columns']['payload'][0])
        compare(payload['n'],e['n_complete']);compare(len(payload['series']),len(e['groups']))
        for series,g in zip(payload['series'],e['groups']):
            for key in ('code','label','n','maximum'):compare(series[key],g[key])
            for row,ref in zip(series['points'],g['curve']):compare(row,{k:ref[k] for k in row})
        from unittest.mock import patch
        with patch.object(cpj_grouped_survival,'grouped_survival_core',side_effect=RuntimeError('Rendering must not refit')):
            fig=cpj_plots.figure(state)
        from matplotlib.collections import PolyCollection,PathCollection
        axis=fig.axes[0];scale=max(g['maximum'] for g in e['groups']) or 1
        compare(len(axis.lines),len(e['groups']));rectangles=[];marks=[]
        for line,g in zip(axis.lines,e['groups']):
            points=g['curve'];xs=[0.]+[r['time']/scale for r in points];ys=[1.]+[r['survival'] for r in points]
            if points[-1]['time']<g['maximum']:xs.append(g['maximum']/scale);ys.append(ys[-1])
            compare(list(line.get_xdata()),xs);compare(list(line.get_ydata()),ys);compare(line.get_drawstyle(),'steps-post')
            for j,r in enumerate(points):
                end=points[j+1]['time'] if j+1<len(points) else g['maximum']
                if r['lower'] is not None and end>r['time']:
                    a,b=r['time']/scale,end/scale
                    rectangles.append([[a,r['lower']],[b,r['lower']],[b,r['upper']],[a,r['upper']]])
            groupmarks=[[r['time']/scale,r['survival']] for r in points if r['censored']>0]
            if groupmarks:marks.append(groupmarks)
        compare([p.vertices[:4].tolist() for c in axis.collections if isinstance(c,PolyCollection) for p in c.get_paths()],rectangles)
        compare([c.get_offsets().tolist() for c in axis.collections if isinstance(c,PathCollection)],marks)
        for overrides in (dict(sc=False,showCases=False,showSteps=False),dict(outcomeLevel='Censored')):
            result=cpj_runtime.execute(dict(req,options=dict(options,**overrides)));configurations+=1
            compare(result['status'],'input_error' if 'outcomeLevel' in overrides else 'ok')
            compare(bool(result.get('plots')),False)
            for table in ('steps','cases','covariance','riskSets'):compare(bool(result.get('tables',{}).get(table,{}).get('rows')),False)
    compare(cpj_plots.render(state)['mime'],'image/png')
    for name,module in list(sys.modules.items()):
        if name.startswith('cpj_') and getattr(module,'__file__',None):
            assert Path(module.__file__).resolve().parent==runtime,(name,module.__file__)
    return dict(configurations=configurations,checks=checks,datasets=len({f['id'] for f in fixtures}),
        fixture_sha256=hashlib.sha256((ROOT/'tests/fixtures/grouped-survival-core.json').read_bytes()).hexdigest(),
        scope='Actual packaged grouped computation/native payloads/step-band-censor geometry; native R and GUI acceptance separate')


def check(path):
    path=Path(path);version=re.search(r'^Version:\s*(\S+)',(ROOT/'DESCRIPTION').read_text(),re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-grouped-survival-package-') as folder:
        with ZipFile(path) as z:
            assert z.testzip() is None
            names=z.namelist();assert len(names)==len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            prefix='ClinicoPathPj/R/ClinicoPathPj/python/'
            meta=z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$',meta,re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pysurvival\s*$',meta,re.M))==1
            packaged=json.loads(z.read(prefix+'registry.json'));source=json.loads((ROOT/'inst/python/registry.json').read_text())
            assert [e['id'] for e in packaged['analyses']]==[e['id'] for e in source['analyses']]
            for p,s in zip(packaged['analyses'],source['analyses']):
                assert {k:v for k,v in p.items() if k!='coverage'}=={k:v for k,v in s.items() if k!='coverage'}
                assert p['coverage']['full_parity']==s['coverage']['full_parity']
            sources={e['source'] for e in source['analyses'] if e.get('source')}
            assert {n[len(prefix):] for n in names if n.startswith(prefix+'analyses/') and n.endswith('.py')}==sources
            for item in sources|{p.name for p in (ROOT/'inst/python').glob('cpj*.py')}:
                assert z.read(prefix+item)==(ROOT/'inst/python'/item).read_bytes(),item
            assert z.read('ClinicoPathPj/data/python_grouped_survival_examples.csv')==(ROOT/'data/python_grouped_survival_examples.csv').read_bytes()
            ui=z.read('ClinicoPathPj/ui/pysurvival.js').decode()
            for key in ('elapsedtime','outcome','explanatory','outcomeLevel','censorLevel','timetypeoutput','cutp','sc','ci95','censored','timefix'):assert key in ui,key
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
