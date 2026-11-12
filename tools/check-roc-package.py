"""Run independent ROC fixtures through the actual JMO's extracted Python runtime."""
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]


def check(path):
    path=Path(path);fixture=ROOT/'tests/fixtures/roc-delong.json'
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    references=json.loads(fixture.read_text())['fixtures'];count=0
    with tempfile.TemporaryDirectory(prefix='cpj-roc-package-') as folder:
        directory=Path(folder)
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names=z.namelist();assert all(n.startswith('ClinicoPathPj/') and '..' not in Path(n).parts for n in names)
            assert not any(n.endswith('.pyc') for n in names)
            assert 'pyenhancedroc' in z.read('ClinicoPathPj/jamovi.yaml').decode()
            metadata = z.read('ClinicoPathPj/jamovi.yaml').decode()
            archive_version = re.search(r'^version:\s*[\'\"]?([0-9.]+)', metadata, re.M)
            assert archive_version and archive_version.group(1) == version
            assert any(n.endswith('/pyenhancedroc.js') for n in names)
            for member in ('cpj_roc.py','analyses/meddecide/pyenhancedroc.py'):
                assert z.read('ClinicoPathPj/R/ClinicoPathPj/python/'+member)==(ROOT/'inst/python'/member).read_bytes()
            z.extractall(directory)
        runtime=directory/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        for case in references:
            markers=case['markers'];directions=case['directions'] if isinstance(case['directions'],list) else [case['directions']]
            columns={'Reference':dict(kind='factor',codes=[None if c==-1 else c for c in case['codes']],levels=case['levels'])}
            options=dict(reference='Reference',positive=case['positive'],showCases=True,showThresholds=True,showROC=True)
            for i,(name,values) in enumerate(markers.items(),1):
                options['marker'+str(i)]=name;options['direction'+str(i)]=directions[i-1]
                values=values if isinstance(values,list) else [values]
                columns[name]=dict(kind='number',values=[None if x=='NA' else x for x in values])
            request=directory/'request.json';response=directory/'response.json'
            request.write_text(json.dumps(dict(analysis='pyenhancedroc',options=options,columns=columns)))
            subprocess.run([sys.executable,'-B','-s',str(runtime),str(request),str(response)],check=True,capture_output=True,timeout=60)
            got=json.loads(response.read_text());assert got['status']=='ok',(case['id'],got.get('error'))
            assert got['tables']['cohort']['rows'][0]['retained']==case['expected']['n_complete'];count+=1
            for observed,expected in zip(got['tables']['auc']['rows'],case['expected']['models']):
                assert abs(observed['estimate']-expected['auc'])<=1e-12;count+=1
                interval=next(x for x in expected['intervals'] if x['confidence']==.95)
                for key in ('se','lower','upper'):
                    assert (observed[key] is None if interval[key] is None else abs(observed[key]-interval[key])<=1e-12);count+=1
            for observed,expected in zip(got['tables']['comparisons']['rows'],case['expected']['comparisons']):
                assert abs(observed['difference']-expected['difference'])<=1e-12;count+=1
                interval=next(x for x in expected['intervals'] if x['confidence']==.95)
                for key in ('p','se','lower','upper'):
                    assert (observed[key] is None if interval[key] is None else abs(observed[key]-interval[key])<=1e-12);count+=1
            print(case['id'],'passed',flush=True)
        report=dict(scope='actual JMO extracted ROC runtime against independent frozen fixtures; no GUI acceptance',
                    archive=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,
                    CRC='pass',bytecode_members=0,fixtures=len(references),comparisons=count,
                    numerical_tolerance=1e-12,fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                    local_analysis_and_engine_bytes_match=True,native_GUI_qualified=False)
        (ROOT/f'docs/validation-exports/python-roc-{version}-runtime-20261111.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))


if __name__=='__main__':
    version = re.search(r'^Version:\s*(\S+)', (ROOT/'DESCRIPTION').read_text(), re.M).group(1)
    check(sys.argv[1] if len(sys.argv)>1 else ROOT/f'ClinicoPathPj_{version}.jmo')
