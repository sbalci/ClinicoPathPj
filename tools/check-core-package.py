"""Inspect and smoke-test a built ClinicoPathPj package in jamovi's bundled Python.

    PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
      /Applications/jamovi.app/Contents/MacOS/python -B tools/check-core-package.py
"""
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
VERSION=re.search(r'^Version: (.+)$',(ROOT/'DESCRIPTION').read_text(),re.M)[1]
REGISTRY=json.loads((ROOT/'inst/python/registry.json').read_text())
NAMES=['pysvgcutoff','pycheckdata','pyobservablecutoff','pyd3cutoff','pydecision','pydecisioncalculator','pysequentialtests','pychisqposttest','pybenford','pydecisioncurve','pysummarydata','pycategorize','pyagepyramid','pydataquality']


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
            assert f'version: {VERSION}' in manifest
            assert 'python_core_examples.omv' in manifest
            assert all(n.startswith('py') for n in re.findall(r'^    name: (\w+)$',manifest,re.M))
            for name in NAMES:
                assert f'name: {name}\n' in manifest
                entry=next(e for e in REGISTRY['analyses'] if name==e['id'] or name in e.get('aliases',[]))
                member='ClinicoPathPj/R/ClinicoPathPj/python/'+entry['source']
                assert archive.read(member)==(ROOT/'inst/python'/entry['source']).read_bytes()
                assert f"name: {entry['id']}\n" in manifest
            for file in ['cpj_runtime.py','cpj_svg_cutoff.py','cpj_accuracy.py','cpj_registry.py','cpj_plots.py','cpj_descriptive.py','cpj_binning.py','cpj_demographics.py','cpj_quality.py','templates/quality.html','cpj_cutoff.py','cpj_single_quality.py','templates/single-quality.html','cpj_cutoff_analysis.py','templates/d3cutoff.html','templates/observablecutoff.html','vendor/observable-plot-0.6.17.min.js','vendor/observable-inputs-0.12.0.min.js','vendor/htl-0.3.1.min.js','vendor/observable-plot-LICENSE.txt','vendor/observable-inputs-LICENSE.txt','vendor/htl-LICENSE.txt','vendor/observable-manifest.json','vendor/d3-7.9.0.min.js','vendor/d3-LICENSE.txt','registry.json','font-cache.json']:
                assert archive.read(f'ClinicoPathPj/R/ClinicoPathPj/python/{file}')==(ROOT/'inst/python'/file).read_bytes()
            assert archive.read('ClinicoPathPj/R/ClinicoPathPj/js/pysvgcutoff.js')==(ROOT/'inst/js/pysvgcutoff.js').read_bytes()
            assert archive.read('ClinicoPathPj/data/python_core_examples.omv')==(ROOT/'data/python_core_examples.omv').read_bytes()
            archive.extractall(temp)
        runtime=temp/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        cases=[('pysvgcutoff',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pycheckdata',{'x':numeric([0]*10+[100])},dict(var='x',showOutliers=True,showDistribution=True,showInteractive=True)),
          ('pyobservablecutoff',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pyd3cutoff',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pydataquality',{'x':numeric([1,1,None]),'g':factor(['A','A','B'])},dict(vars=['x','g'],check_missing=True,check_duplicates=True,row_level_duplicates=True,showInteractive=True)),
          ('pyagepyramid',{'a':numeric([0,5,65,85]),'g':factor(['F','M','F','M'])},dict(age='a',gender='g',female='F',male='M',age_groups='who')),
          ('pysummarydata',{'x':numeric([1,2,3,4,100])},dict(vars=['x'],distr=True,outliers=True)),
          ('pycategorize',{'x':numeric([1,2,3,4,100])},dict(var='x',method='quantile',nbins=4)),
          ('pydecisioncalculator',{},{}),('pysequentialtests',{},{}),
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
        print(json.dumps(dict(package=str(path),integrity='ok',module='ClinicoPathPj',version=VERSION,analyses=results),indent=2))


if __name__=='__main__':
    check(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/f'ClinicoPathPj_{VERSION}.jmo')
