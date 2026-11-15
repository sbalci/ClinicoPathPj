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
    runtime=runtime.resolve();sys.path.insert(0,str(runtime))
    import cpj_runtime,cpj_waffle
    from cpj_plots import figure
    assert Path(cpj_runtime.__file__).resolve()==runtime/'cpj_runtime.py'
    assert Path(cpj_waffle.__file__).resolve()==runtime/'cpj_waffle.py'
    fixtures=json.loads((ROOT/'tests/fixtures/waffle-core.json').read_text())['fixtures']
    checks=configurations=0
    def compare(a,b):
        nonlocal checks
        checks+=1
        if isinstance(b,dict):
            for k,v in b.items():compare(a[k],v)
        elif isinstance(b,list):
            assert len(a)==len(b)
            for v,w in zip(a,b):compare(v,w)
        elif isinstance(b,float):assert abs(a-b)<=2e-12*max(1,abs(b)),(a,b)
        else:assert a==b,(a,b)
    for f in fixtures:
        a=f['inputs'];e=f['expected']
        def factor(codes,levels):return dict(kind='factor',codes=[None if c<0 else c for c in codes],levels=levels)
        columns={'Category':factor(a['codes'],a['levels'])}
        options=dict(groups='Category',rows=f['rows'],flip=f['flip'],showCases=True,show_legend=True)
        if a['weights'] is not None:columns['Count']=dict(kind='number',values=a['weights']);options['counts']='Count'
        if a['facets'] is not None:columns['Panel']=factor(a['facets'],a['facet_levels']);options['facet']='Panel'
        req=dict(analysis='pyjwaffle',columns=columns,options=options,row_ids=[str(i*7+3) for i in range(len(a['codes']))])
        got=cpj_runtime.execute(req);configurations+=1
        compare(got['status'],'ok')
        for k,ref in [('source','n_source'),('complete','n_complete'),('excluded','excluded_missing'),('zero','zero_frequency'),('contributing','n_contributing'),('total','n_total')]:compare(got['tables']['cohort']['rows'][0][k],e[ref])
        payload=json.loads(got['plots']['wafflePlot']['columns']['payload'][0])
        compare(len(payload['panels']),len(e['panels']));compare(payload['rows'],f['rows']);compare(payload['flip'],f['flip'])
        for panel,ref in zip(payload['panels'],e['panels']):compare(panel,{k:v for k,v in ref.items() if k!='retained_indices'})
        compare([r['sourceID'] for r in got['tables']['cases']['rows']],[req['row_ids'][i] for i in e['retained_indices']])
        rows=got['tables']['allocation']['rows'];ref=[c for p in e['panels'] for c in p['cells']]
        compare(len(rows),len(ref))
        for row,c in zip(rows,ref):
            for k,v in [('count',c['count']),('tiles',c['tiles']),('proportion',c['proportion']),('error',c['allocation_error'])]:compare(row[k],v)
        fig=figure(got['plots']['wafflePlot'])
        for axis,panel in zip(fig.axes,e['panels']):
            compare(len(axis.patches),100)
            for rect,tile in zip(axis.patches,panel['geometry']):
                compare(rect.get_x(),tile['xmin']);compare(rect.get_y(),tile['ymin'])
                compare(rect.get_width(),1);compare(rect.get_height(),1)
        for overrides in [dict(showPlot=False,showCases=False),dict(rows=0)]:
            modified=dict(req,options=dict(options,**overrides));result=cpj_runtime.execute(modified);configurations+=1
            compare(result['status'],'input_error' if overrides.get('rows')==0 else 'ok')
            compare(bool(result.get('plots')),False)
    return dict(configurations=configurations,checks=checks,datasets=14,
        scope='Actual packaged runtime and static tile geometry; native/GUI evidence separate')


def check(path):
    path=Path(path)
    version=re.search(r'^Version:\s*(\S+)',(ROOT/'DESCRIPTION').read_text(),re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-waffle-package-') as folder:
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names=z.namelist()
            assert len(names)==len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            prefix='ClinicoPathPj/R/ClinicoPathPj/python/'
            meta=z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$',meta,re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pyjwaffle\s*$',meta,re.M))==1
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
            assert z.read('ClinicoPathPj/data/python_waffle_examples.csv')==(ROOT/'data/python_waffle_examples.csv').read_bytes()
            ui=z.read('ClinicoPathPj/ui/pyjwaffle.js').decode()
            for key in ('groups','counts','facet','subject','rows','flip','showPlot','show_legend','showCases','showExplanations','mytitle','legendtitle'):
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
