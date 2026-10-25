"""Inspect and smoke-test a built ClinicoPathPj package in jamovi's bundled Python.

    PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
      /Applications/jamovi.app/Contents/MacOS/python -B tools/check-core-package.py
"""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
NAMES=['pydecision','pydecisioncalculator','pysequentialtests','pychisqposttest','pybenford','pydecisioncurve']


def numeric(x):return dict(kind='number',values=x)
def factor(x):
    levels=sorted(set(x))
    return dict(kind='factor',levels=levels,codes=[levels.index(y) for y in x])


def check(path):
    with tempfile.TemporaryDirectory(prefix='cpj-package-check-') as directory:
        temp=Path(directory)
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            names=archive.namelist()
            assert {p.split('/')[0] for p in names}=={'ClinicoPathPj'}
            manifest=archive.read('ClinicoPathPj/jamovi.yaml').decode()
            assert 'version: 0.2.0' in manifest
            assert 'python_core_examples.omv' in manifest
            for name in NAMES:
                assert f'name: {name}\n' in manifest
                member=f'ClinicoPathPj/R/ClinicoPathPj/python/analyses/{name}.py'
                assert archive.read(member)==(ROOT/'inst/python/analyses'/f'{name}.py').read_bytes()
            for file in ['cpj_runtime.py','cpj_accuracy.py']:
                assert archive.read(f'ClinicoPathPj/R/ClinicoPathPj/python/{file}')==(ROOT/'inst/python'/file).read_bytes()
            assert archive.read('ClinicoPathPj/data/python_core_examples.omv')==(ROOT/'data/python_core_examples.omv').read_bytes()
            archive.extractall(temp)
        runtime=temp/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        cases=[('pydecisioncalculator',{},{}),('pysequentialtests',{},{}),
          ('pydecision',{'r':factor(['N','P']),'t':factor(['N','P'])},dict(reference='r',test='t',referencePositive='P',testPositive='P')),
          ('pychisqposttest',{'r':factor(['a','a','b','b']),'c':factor(['x','y','x','y'])},dict(rows='r',cols='c')),
          ('pybenford',{'x':numeric([.3,1,20,333,4444,55555])},dict(measurement='x')),
          ('pydecisioncurve',{'r':factor(['N','P']),'p':numeric([.1,.9])},dict(outcome='r',positive='P',models=['p']))]
        results=[]
        for name,columns,options in cases:
            request=temp/'request.json';response=temp/'response.json'
            request.write_text(json.dumps(dict(analysis=name,columns=columns,options=options)))
            subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
            result=json.loads(response.read_text())
            assert result['status']=='ok',(name,result.get('error'))
            assert result['tables'],name
            if name=='pydecision':
                assert [r['n'] for r in result['tables']['counts']['rows']]==[1,0,0,1]
            if name=='pydecisioncalculator':
                assert abs(result['tables']['accuracy']['rows'][0]['estimate']-90/110)<1e-12
            if name=='pydecisioncurve':
                assert len(result['plots']['netBenefitPlot']['columns']['x'])==138
            results.append(dict(analysis=name,status='ok',tables=list(result['tables']),plots=list(result['plots'])))
        print(json.dumps(dict(package=str(path),integrity='ok',module='ClinicoPathPj',version='0.2.0',analyses=results),indent=2))


if __name__=='__main__':
    check(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'ClinicoPathPj_0.2.0.jmo')
