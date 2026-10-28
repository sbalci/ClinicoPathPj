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
NAMES=['pyjjcorrmat','pyihcheatmap','pybridgecompare','pysvgcutoff','pycheckdata','pyobservablecutoff','pyd3cutoff','pydecision','pydecisioncalculator','pysequentialtests','pychisqposttest','pybenford','pydecisioncurve','pysummarydata','pycategorize','pyagepyramid','pydataquality']


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
            for file in ['cpj_correlation.py','templates/correlation.html','cpj_ihc.py','templates/ihcheatmap.html','cpj_runtime.py','cpj_svg_cutoff.py','cpj_accuracy.py','cpj_registry.py','cpj_plots.py','cpj_descriptive.py','cpj_binning.py','cpj_demographics.py','cpj_quality.py','templates/quality.html','cpj_cutoff.py','cpj_single_quality.py','templates/single-quality.html','cpj_cutoff_analysis.py','templates/bridgecutoff.html','templates/d3cutoff.html','templates/observablecutoff.html','vendor/observable-plot-0.6.17.min.js','vendor/observable-inputs-0.12.0.min.js','vendor/htl-0.3.1.min.js','vendor/observable-plot-LICENSE.txt','vendor/observable-inputs-LICENSE.txt','vendor/htl-LICENSE.txt','vendor/observable-manifest.json','vendor/d3-7.9.0.min.js','vendor/d3-LICENSE.txt','registry.json','font-cache.json']:
                assert archive.read(f'ClinicoPathPj/R/ClinicoPathPj/python/{file}')==(ROOT/'inst/python'/file).read_bytes()
            assert archive.read('ClinicoPathPj/R/ClinicoPathPj/js/pysvgcutoff.js')==(ROOT/'inst/js/pysvgcutoff.js').read_bytes()
            assert archive.read('ClinicoPathPj/data/python_core_examples.omv')==(ROOT/'data/python_core_examples.omv').read_bytes()
            archive.extractall(temp)
        runtime=temp/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        cases=[('pyjjcorrmat',{'a':numeric([1,2,3,4]),'b':numeric([1,2,4,3])},dict(dep=['a','b'])),
          ('pyihcheatmap',{'a':numeric([1,2,3]),'b':numeric([2,4,6])},dict(markers=['a','b'],scaling='zscore',showScatter=True,clusterRows=True,clusterColumns=True,showDendrograms=True,enableSelection=True)),
          ('pybridgecompare',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pysvgcutoff',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pycheckdata',{'x':numeric([0]*10+[100])},dict(var='x',showOutliers=True,showDistribution=True,showInteractive=True)),
          ('pyobservablecutoff',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pyd3cutoff',{'x':numeric([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2')),
          ('pydataquality',{'x':numeric([1,1,None]),'g':factor(['A','A','B'])},dict(vars=['x','g'],check_missing=True,check_duplicates=True,row_level_duplicates=True,showInteractive=True)),
          ('pyagepyramid',{'a':numeric([0,5,65,85]),'g':factor(['F','M','F','M'])},dict(age='a',gender='g',female='F',male='M',age_groups='who')),
          ('pysummarydata',{'x':numeric([1,2,3,4,100])},dict(vars=['x'],distr=True,outliers=True)),
          ('pycategorize',{'x':numeric([1,2,3,4,100])},dict(var='x',method='quantile',nbins=4,showhistogram=True)),
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
            if name=='pyjjcorrmat':
                extended_columns=dict(columns,constant=numeric([2,2,2,2]))
                for method in ['hochberg','hommel','BY']:
                    extended_options=dict(options,dep=['a','b','constant'],padjustmethod=method)
                    request.write_text(json.dumps(dict(analysis=name,columns=extended_columns,options=extended_options)))
                    subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                    adjusted=json.loads(response.read_text())
                    assert adjusted['status']=='ok',adjusted.get('error')
                    rows=adjusted['tables']['correlations']['rows']
                    assert abs(rows[0]['adjusted']-(1 if method=='BY' else .6))<1e-12
                    assert rows[1]['adjusted'] is None and rows[2]['adjusted'] is None
            if name=='pyjjcorrmat':
                partial_columns={'a':numeric([0,-2,0,2]),'b':numeric([0,-2,2,0]),'z':numeric([-1,-1,1,1])}
                request.write_text(json.dumps(dict(analysis=name,columns=partial_columns,options=dict(dep=['a','b','z'],partial=True))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                partial=json.loads(response.read_text())
                assert partial['status']=='ok',partial.get('error')
                row=partial['tables']['correlations']['rows'][0]
                assert abs(row['estimate'])<1e-12 and abs(row['p']-1)<1e-12
                assert row['controls']==1 and row['df']==1 and row['lower'] is None
            if name=='pyihcheatmap':
                assert len(result['tables']['merges']['rows'])==3
                assert result['plots']['rowDendrogram']['kind']=='dendrogram'
                assert result['plots']['markerDendrogram']['kind']=='dendrogram'
                assert '"rowTree": {' in result['htmls']['explorer']
                assert 'tree-branch' in result['htmls']['explorer']
                assert 'Preview rectangle rows' in result['htmls']['explorer']
                assert 'pointercancel' in result['htmls']['explorer']
                assert 'Tab enters/leaves the matrix' in result['htmls']['explorer']
                assert 'aria-describedby=' in result['htmls']['explorer']
                snapshot=re.search(r'"snapshot": "([0-9a-f]{64})"',result['htmls']['explorer'])[1]
                applied_options=dict(options,showSelectionValues=True,selectionDefinition=json.dumps(dict(version=1,rows=['2'],snapshot=snapshot)))
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=applied_options,row_ids=['1','2','3'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                applied=json.loads(response.read_text())
                assert applied['status']=='ok',applied.get('error')
                assert applied['outputs']['selectionFlag']['values']==[0.,1.,0.]
                assert applied['tables']['selectionSummary']['rows'][0]['selected']==1
                values=applied['tables']['selectionValues']['rows']
                assert {v['marker']:v['raw'] for v in values}=={'a':2.,'b':4.}
                assert all(v['sourceRow']=='2' and v['displayed']==0. for v in values)
                assert 'full retained heatmap cohort' in applied['tables']['selectionValues']['notes'][0]
                assert applied['plots']==result['plots']
                assert result['tables']['scatterCohort']['rows'][0]['plotted']==3
                assert len(result['plots']['scatter']['columns']['x'])==3
                assert 'Linked marker scatterplot' in result['htmls']['explorer']
            if name=='pycategorize':
                plot=result['plots']['histogram']
                assert sum(plot['columns']['count'])==5
                assert plot['boundaries']==[r['value'] for r in result['tables']['breakpointsTable']['rows']]
            if name=='pybridgecompare':
                summary=result['texts']['summary'].replace(chr(92),'')
                assert 'Native applied rule: x >= 2' in summary
                assert 'Complete rows: 6; excluded: 0' in summary
                assert 'reselect the analysis heading' in summary
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
