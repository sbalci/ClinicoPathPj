"""Inspect and execute the immutable JMO's actual histogram runtime."""
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
    assert Path(cpj_runtime.__file__).resolve()==runtime/'cpj_runtime.py'
    checks=configurations=0
    def compare(got,want,key):
        nonlocal checks
        checks+=1
        if want is None or isinstance(want,(str,bool,list)):
            assert got==want,(key,got,want)
        else:
            assert isinstance(got,(int,float)),(key,got,want)
            tol=2e-7*max(1,abs(want)) if key.endswith(('_lower','_upper')) else abs(want)*1e-10 if want else 1e-12
            assert abs(got-want)<=tol,(key,got,want,tol)
    def run(values,**opts):
        nonlocal configurations
        configurations+=1
        response=cpj_runtime.execute(dict(analysis='pyjjhistostats',
            columns={'Measurement':dict(kind='number',values=values)},
            options=dict(dep=['Measurement'],**opts),row_ids=[str(10+3*i) for i in range(len(values))]))
        json.dumps(response,allow_nan=False)
        return response
    core=json.loads((ROOT/'tests/fixtures/histogram-core.json').read_text())['fixtures']
    for f in core:
        for ref in f['runs']:
            extra=dict(changebinwidth=True,binwidth=1e15) if f['id']=='offset_degenerate' else {}
            got=run(f['values'],resultssubtitle=True,enableOneSampleTest=True,testValue=ref['reference'],
                conflevel=ref['confidence'],showCases=True,**extra)
            compare(got['status'],'ok',f['id']+':status')
            row=got['tables']['meanTest']['rows'][0]
            for key in ('reference','difference','stderr','df','statistic','p','status'):compare(row[key],ref[key],key)
            for i,prefix in enumerate(('mean_','difference_')):
                limits=got['tables']['meanLimits']['rows'][i]
                for key in ('lower','upper'):compare(limits[key],ref[prefix+key],prefix+key)
                compare(limits['confidence'],ref['confidence'],'confidence')
            for key,value in f['summary'].items():compare(got['tables']['descriptives']['rows'][0][key],value,key)
            compare([r['sourceID'] for r in got['tables']['cases']['rows']],
                [str(10+3*i) for i in f['retained_indices']],'source IDs')
    geometry=json.loads((ROOT/'tests/fixtures/histogram-geometry.json').read_text())['fixtures']
    for f in geometry:
        for ref in f['runs']:
            got=run(f['values'],changebinwidth=not ref['automatic'],binwidth=ref['width'] if not ref['automatic'] else 1.1,showBins=True)
            if ref['geometry_status']=='error':compare(got['status'],'input_error',f['id']);continue
            compare(got['status'],'ok',f['id'])
            compare(got['tables']['binning']['rows'][0]['status'],ref['geometry_status'],'geometry_status')
            rows=got['tables'].get('bins',{}).get('rows',[])
            compare(len(rows),len(ref['bins']),'bin count')
            for actual,expected in zip(rows,ref['bins']):
                for key in ('lower','upper','count','proportion','density'):compare(actual[key],expected[key],key)
            if ref['bins']:
                for key in ('lower','upper','count'):
                    compare(got['plots']['histogramPlot']['columns'][key],[r[key] for r in rows],key)
            else:compare('histogramPlot' in got['plots'],False,'plot unavailable')
            compare('meanTest' in got['tables'],False,'default inference off')
    # Public default/custom-null and optional-result gates, separate from oracle loops.
    values=[0,1,2,4,8,None]
    for supplied,enabled,expected in [(100,False,0),(.75,True,.75)]:
        got=run(values,resultssubtitle=True,enableOneSampleTest=enabled,testValue=supplied)
        compare(got['tables']['meanTest']['rows'][0]['reference'],expected,'custom null')
    got=run(values,showPlot=False,showCases=False,showBins=False)
    for key in ('meanTest','meanLimits','cases','bins'):compare(key in got['tables'],False,key+' off')
    compare(bool(got['plots']),False,'plot off')
    for opts in [dict(changebinwidth=True,binwidth=0),dict(resultssubtitle=True,conflevel=1),dict(typestatistics='robust')]:
        compare(run(values,**opts)['status'],'input_error','refused request')
    return dict(checks=checks,configurations=configurations,runtime=str(Path(cpj_runtime.__file__)),
        geometry_configurations=54,student_configurations=210)


def check(path):
    path=Path(path)
    version=re.search(r'^Version:\s*(\S+)',(ROOT/'DESCRIPTION').read_text(),re.M).group(1)
    with tempfile.TemporaryDirectory(prefix='cpj-histogram-package-') as folder:
        directory=Path(folder)
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names=z.namelist();assert len(names)==len(set(names))
            assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') or '/tests/reference/' in n for n in names)
            meta=z.read('ClinicoPathPj/jamovi.yaml').decode()
            assert re.search(r'^version:\s*[\'\"]?'+re.escape(version)+r'[\'\"]?\s*$',meta,re.M)
            assert len(re.findall(r'^\s*(?:- )?name: pyjjhistostats\s*$',meta,re.M))==1
            for item in ('cpj_histogram.py','cpj_histogram_geometry.py','cpj_histogram_adapter.py','cpj_runtime.py','analyses/jjstatsplot/pyjjhistostats.py'):
                assert z.read('ClinicoPathPj/R/ClinicoPathPj/python/'+item)==(ROOT/'inst/python'/item).read_bytes(),item
            assert z.read('ClinicoPathPj/data/python_histogram_examples.csv')==(ROOT/'data/python_histogram_examples.csv').read_bytes()
            ui=z.read('ClinicoPathPj/ui/pyjjhistostats.js').decode()
            for key in ('changebinwidth','binwidth','resultssubtitle','enableOneSampleTest','testValue','conflevel','showBins','showCases','showPlot','centralityline'):
                assert key in ui,key
            packaged=json.loads(z.read('ClinicoPathPj/R/ClinicoPathPj/python/registry.json'))
            source=json.loads((ROOT/'inst/python/registry.json').read_text())
            # Coverage evidence may advance after this immutable archive is qualified.
            for p in packaged['analyses']:
                s=next(e for e in source['analyses'] if e['id']==p['id'])
                assert {k:v for k,v in p.items() if k!='coverage'}=={k:v for k,v in s.items() if k!='coverage'}
                assert p['coverage']['full_parity']==s['coverage']['full_parity']
            z.extractall(directory)
        runtime=directory/'ClinicoPathPj/R/ClinicoPathPj/python'
        done=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--runtime',str(runtime)],
            capture_output=True,text=True,timeout=180)
        assert done.returncode==0,(done.stdout,done.stderr)
        report=json.loads(done.stdout)
        report.update(package=str(path),version=version,bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scope='Actual JMO runtime; desktop and clinical qualification separate')
        return report


if __name__=='__main__':
    report=runtime_checks(Path(sys.argv[2])) if sys.argv[1]=='--runtime' else check(sys.argv[1])
    print(json.dumps(report,indent=2))
