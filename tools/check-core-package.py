"""Inspect and smoke-test a built ClinicoPathPj package in jamovi's bundled Python.

    PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
      /Applications/jamovi.app/Contents/MacOS/python -B tools/check-core-package.py
"""
import json
import io
import base64
import struct
import csv
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
VERSION=re.search(r'^Version: (.+)$',(ROOT/'DESCRIPTION').read_text(),re.M)[1]
REGISTRY=json.loads((ROOT/'inst/python/registry.json').read_text())
NAMES=['pydiagnosticmeta','pyfirstevent','pyintervalcensoring','pytimeinterval','pydatetimeconverter','pyoutcomeorganizer','pytableone','pycrosstable','pyalluvial','pyvartree','pyoutlierdetection','pyvenn','pyjjcorrmat','pyihcheatmap','pybridgecompare','pysvgcutoff','pycheckdata','pyobservablecutoff','pyd3cutoff','pydecision','pydecisioncalculator','pysequentialtests','pychisqposttest','pybenford','pydecisioncurve','pysummarydata','pycategorize','pyagepyramid','pydataquality']


def numeric(x):return dict(kind='number',values=x)
def factor(x):
    levels=sorted({y for y in x if y is not None})
    return dict(kind='factor',levels=levels,codes=[None if y is None else levels.index(y) for y in x])


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
            assert 'python_set_intersection_examples.csv' in manifest
            assert 'python_diagnostic_study_examples.omv' in manifest
            assert archive.read('ClinicoPathPj/data/python_diagnostic_study_examples.omv')==(ROOT/'data/python_diagnostic_study_examples.omv').read_bytes()
            assert 'python_first_event_identity.omv' in manifest
            assert archive.read('ClinicoPathPj/data/python_first_event_identity.omv')==(ROOT/'data/python_first_event_identity.omv').read_bytes()
            assert 'python_first_event_examples.omv' in manifest
            assert archive.read('ClinicoPathPj/data/python_first_event_examples.omv')==(ROOT/'data/python_first_event_examples.omv').read_bytes()
            assert 'python_interval_censoring_examples.omv' in manifest
            assert archive.read('ClinicoPathPj/data/python_interval_censoring_examples.omv')==(ROOT/'data/python_interval_censoring_examples.omv').read_bytes()
            assert 'python_composite_outcome_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_composite_outcome_examples.csv')==(ROOT/'data/python_composite_outcome_examples.csv').read_bytes()
            assert 'python_numeric_date_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_numeric_date_examples.csv')==(ROOT/'data/python_numeric_date_examples.csv').read_bytes()
            assert 'python_calendar_interval_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_calendar_interval_examples.csv')==(ROOT/'data/python_calendar_interval_examples.csv').read_bytes()
            assert 'python_interval_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_interval_examples.csv')==(ROOT/'data/python_interval_examples.csv').read_bytes()
            assert 'python_datetime_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_datetime_examples.csv')==(ROOT/'data/python_datetime_examples.csv').read_bytes()
            assert 'python_table_one_examples.omv' in manifest
            assert archive.read('ClinicoPathPj/data/python_table_one_examples.omv')==(ROOT/'data/python_table_one_examples.omv').read_bytes()
            assert 'python_cross_table_examples.omv' in manifest
            assert archive.read('ClinicoPathPj/data/python_cross_table_examples.omv')==(ROOT/'data/python_cross_table_examples.omv').read_bytes()
            with zipfile.ZipFile(io.BytesIO(archive.read('ClinicoPathPj/data/python_cross_table_examples.omv'))) as example:
                typed=json.loads(example.read('metadata.json'))['dataSet']
                assert typed['rowCount']==25 and typed['columnCount']==4
                fields={v['name']:v for v in typed['fields']}
                assert fields['Age']['measureType']==fields['Code']['measureType']=='Continuous'
                source=list(csv.DictReader((ROOT/'data/python_cross_table_examples.csv').open()))
                raw=example.read('data.bin');labels=json.loads(example.read('xdata.json'));offset=0
                for field in typed['fields']:
                    kind='d' if field['type']=='number' else 'i';length=struct.calcsize(kind)*25
                    values=struct.unpack('<'+kind*25,raw[offset:offset+length]);offset+=length
                    if field['name'] in ('Group','Marker'):
                        mapping={row[0]:row[1] for row in labels[field['name']]['labels']}
                        assert ['' if v==-2147483648 else mapping[v] for v in values]==[r[field['name']] for r in source]
                    else:
                        assert all(v==float(r[field['name']]) if r[field['name']] else v==-2147483648 or v!=v for v,r in zip(values,source))
                assert offset==len(raw)
            assert 'python_alluvial_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_alluvial_examples.csv')==(ROOT/'data/python_alluvial_examples.csv').read_bytes()
            assert 'python_tree_reference_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_tree_reference_examples.csv')==(ROOT/'data/python_tree_reference_examples.csv').read_bytes()
            assert 'python_tree_node_summary_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_tree_node_summary_examples.csv')==(ROOT/'data/python_tree_node_summary_examples.csv').read_bytes()
            assert 'python_variable_tree_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_variable_tree_examples.csv')==(ROOT/'data/python_variable_tree_examples.csv').read_bytes()
            assert 'python_outlier_screening_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_outlier_screening_examples.csv')==(ROOT/'data/python_outlier_screening_examples.csv').read_bytes()
            assert 'python_set_intersection_unequal_examples.csv' in manifest
            assert archive.read('ClinicoPathPj/data/python_set_intersection_unequal_examples.csv')==(ROOT/'data/python_set_intersection_unequal_examples.csv').read_bytes()
            assert archive.read('ClinicoPathPj/data/python_set_intersection_examples.csv')==(ROOT/'data/python_set_intersection_examples.csv').read_bytes()
            assert all(n.startswith('py') for n in re.findall(r'^    name: (\w+)$',manifest,re.M))
            for name in NAMES:
                assert f'name: {name}\n' in manifest
                entry=next(e for e in REGISTRY['analyses'] if name==e['id'] or name in e.get('aliases',[]))
                member='ClinicoPathPj/R/ClinicoPathPj/python/'+entry['source']
                assert archive.read(member)==(ROOT/'inst/python'/entry['source']).read_bytes()
                assert f"name: {entry['id']}\n" in manifest
            for file in ['cpj_study_inclusion.py','cpj_study_inspector.py','templates/diagnostic-studies.html','cpj_diagnostic_studies.py','cpj_identity.py','cpj_firstevent.py','cpj_censoring.py','cpj_intervals.py','cpj_datetime.py','cpj_outcomes.py','cpj_tableone.py','cpj_crosstable.py','cpj_alluvial.py','templates/alluvial.html','cpj_tree.py','cpj_outliers.py','cpj_sets.py','templates/sets.html','cpj_correlation.py','templates/correlation.html','cpj_ihc.py','templates/ihcheatmap.html','cpj_runtime.py','cpj_svg_cutoff.py','cpj_accuracy.py','cpj_registry.py','cpj_plots.py','cpj_descriptive.py','cpj_binning.py','cpj_demographics.py','cpj_quality.py','templates/quality.html','cpj_cutoff.py','cpj_single_quality.py','templates/single-quality.html','cpj_cutoff_analysis.py','templates/bridgecutoff.html','templates/d3cutoff.html','templates/observablecutoff.html','vendor/observable-plot-0.6.17.min.js','vendor/observable-inputs-0.12.0.min.js','vendor/htl-0.3.1.min.js','vendor/observable-plot-LICENSE.txt','vendor/observable-inputs-LICENSE.txt','vendor/htl-LICENSE.txt','vendor/observable-manifest.json','vendor/d3-7.9.0.min.js','vendor/d3-LICENSE.txt','registry.json','font-cache.json']:
                assert archive.read(f'ClinicoPathPj/R/ClinicoPathPj/python/{file}')==(ROOT/'inst/python'/file).read_bytes()
            assert archive.read('ClinicoPathPj/R/ClinicoPathPj/js/pysvgcutoff.js')==(ROOT/'inst/js/pysvgcutoff.js').read_bytes()
            assert archive.read('ClinicoPathPj/data/python_core_examples.omv')==(ROOT/'data/python_core_examples.omv').read_bytes()
            archive.extractall(temp)
        runtime=temp/'ClinicoPathPj/R/ClinicoPathPj/python/cpj_runtime.py'
        cases=[('pyfirstevent',{'ta':numeric([2,8,None]),'tb':numeric([8,2,4]),'sa':dict(kind='factor',levels=['N','Y'],codes=[1,1,1]),'sb':dict(kind='factor',levels=['N','Y'],codes=[0,0,0])},dict(timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',showReport=True,showPlot=True)),('pyintervalcensoring',{'a':numeric([1,None,1,5,None]),'b':numeric([1,3,None,2,None])},dict(left='a',right='b',showReport=True,showPlot=True)),('pytimeinterval',{'a':factor(['2024-01-01']*4),'b':factor(['2024-01-01','2024-01-07','2024-01-11',None])},dict(dx_date='a',fu_date='b',output_unit='days',use_landmark=True,landmark_time=6)),('pydatetimeconverter',{'x':factor(['2024-02-29','2023-02-29',None,'2021-01-01'])},dict(datetime_var='x',show_quality_metrics=True,extract_year=True)),('pyoutcomeorganizer',{'y':factor(['N','N','X','O',None])},dict(outcome='y',multievent=True,analysistype='compete',awod='N',dod='X',dooc='O',visualization=True,diagnostics=True)),('pytableone',{'x':numeric([1,2,None,4]),'g':factor(['A','B',None,'B']),'empty':numeric([None]*4)},dict(vars=['x','g','empty'],showSummary=True,showReportSentence=True)),('pycrosstable',{'g':factor(['A']*5+['B']*5),'x':numeric(list(range(1,11)))},dict(vars=['x'],group='g',cont='median',p_adjust='holm')),('pyalluvial',{'a':factor(['A']*9+['B']),'b':factor(['X']*10)},dict(vars=['a','b'],showFlowTable=True,showCategories=True)),('pyvartree',{'a':dict(kind='factor',levels=['X','Y'],codes=[0,0,1,None]),'b':factor(['P','Q','P','Q'])},dict(vars=['a','b'],showPlot=True)),('pyoutlierdetection',{'x':numeric([0,1,2,3,4,20,None])},dict(vars=['x'],method='iqr',showRows=True,showPlot=True,showFlaggedValues=True,showDistribution=True)),('pyvenn',{'a':{'kind':'factor','levels':['N','Y'],'codes':[0,1,0,1,None]},'b':{'kind':'factor','levels':['N','Y'],'codes':[0,0,1,1,1]}},dict(var1='a',var2='b',var1true='Y',var2true='Y',showMembershipTable=True)),
          ('pyjjcorrmat',{'a':numeric([1,2,3,4]),'b':numeric([1,2,4,3])},dict(dep=['a','b'])),
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
        cases.append(('pydiagnosticmeta',dict(study=dict(kind='text',values=['S1','S2','S3']),tp=numeric([8,0,None]),fp=numeric([1,2,1]),fn=numeric([2,5,1]),tn=numeric([9,8,1])),dict(study='study',true_positives='tp',false_positives='fp',false_negatives='fn',true_negatives='tn',show_explorer=True)))
        results=[]
        for name,columns,options in cases:
            request=temp/'request.json';response=temp/'response.json'
            payload=dict(analysis=name,columns=columns,options=options)
            if name=='pyfirstevent':payload['row_ids']=['2','8','20']
            if name=='pyintervalcensoring':payload['row_ids']=['2','8','20','40','51']
            if name=='pyoutcomeorganizer':payload['row_ids']=['1','3','8','12','20']
            if name=='pytimeinterval':payload['row_ids']=['2','5','9','20']
            if name=='pydatetimeconverter':payload['row_ids']=['2','5','9','20']
            request.write_text(json.dumps(payload))
            subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
            result=json.loads(response.read_text())
            assert result['status']=='ok',(name,result.get('error'))
            assert result['tables'],name
            if name=='pydiagnosticmeta':
                assert result['tables']['cohort']['rows'][0]['retained']==2
                assert result['tables']['cohort']['rows'][0]['excluded']==1
                assert [r['sensitivity'] for r in result['tables']['studies']['rows']]==[.8,0]
                assert result['plots']['sensitivityPlot']['columns']['estimate']==[.8,0]
                assert 'No continuity correction' in result['texts']['summary']
                assert 'Linked study inspector' in result['htmls']['explorer']
                assert len(result['plots'])==2
                inclusion_options=dict(options,enable_inclusion=True)
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=inclusion_options)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                initial=json.loads(response.read_text());assert initial['status']=='ok',initial.get('error')
                snapshot=re.search(r'"snapshot": "([0-9a-f]{64})"',initial['htmls']['explorer'])[1]
                inclusion_options['inclusionDefinition']=json.dumps(dict(version=1,rows=['2'],snapshot=snapshot))
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=inclusion_options)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                applied=json.loads(response.read_text());assert applied['status']=='ok',applied.get('error')
                assert applied['tables']['inclusion']['rows'][0]['included']==1
                assert [r['sourceID'] for r in applied['tables']['studies']['rows']]==['2']
                assert applied['plots']['sensitivityPlot']['columns']['estimate']==[0]
                inclusion_options['inclusionDefinition']=json.dumps(dict(version=1,rows=[],snapshot=snapshot))
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=inclusion_options)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                empty=json.loads(response.read_text());assert empty['status']=='ok',empty.get('error')
                assert not empty['tables']['studies']['rows'] and not empty['plots']
                assert 'explorer' in empty['htmls']
                changed=dict(columns,tp=numeric([9,0,None]))
                request.write_text(json.dumps(dict(analysis=name,columns=changed,options=inclusion_options)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                stale=json.loads(response.read_text());assert stale['status']=='ok',stale.get('error')
                assert 'Input changed' in stale['tables']['inclusion']['rows'][0]['status']
                assert not stale['tables']['studies']['rows'] and not stale['plots']
            if name=='pyfirstevent':
                assert result['outputs']['timeOut']['values']==[2,2,None]
                assert result['outputs']['statusOut']['values']==[1,0,None]
                assert result['outputs']['sourceOut']['values']==[1,0,None]
                assert result['outputs']['timeOut']['row_ids']==['2','8','20']
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=dict(options,use_admin=True,admin_cutoff='1'),row_ids=['2','8','20'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                adjusted=json.loads(response.read_text());assert adjusted['status']=='ok'
                assert adjusted['outputs']['timeOut']['values']==[1,1,None]
                assert adjusted['outputs']['statusOut']['values']==[0,0,None]
                assert adjusted['outputs']['sourceOut']['values']==[4,4,None]
                assert adjusted['tables']['adminAudit']['rows'][0]['shortened']==2
                id_columns=dict(columns,subject=dict(kind='text',values=['001','001',None]))
                request.write_text(json.dumps(dict(analysis=name,columns=id_columns,options=dict(options,audit_subject=True,subject='subject'),row_ids=['2','8','20'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                identified=json.loads(response.read_text());assert identified['status']=='ok'
                assert identified['tables']['identityAudit']['rows'][0]['repeatedRows']==2
                assert identified['outputs']['timeOut']['values']==result['outputs']['timeOut']['values']
                assert identified['outputs']['identityOut']['values']==[2,2,0]
                assert identified['outputs']['identityOut']['row_ids']==['2','8','20']
                assert identified['outputs']['identityOut']['levels']==['Unknown ID','Unique ID','Repeated ID']
                assert result['outputs']['identityOut']['values']==[None]*3


            if name=='pyintervalcensoring':
                assert result['outputs']['leftOut']['values']==[1,None,1,None,None]
                assert result['outputs']['rightOut']['values']==[1,3,None,None,None]
                assert result['outputs']['kindOut']['values']==[1,2,0,None,None]
                assert result['outputs']['leftOut']['row_ids']==['2','8','20','40','51']
                assert result['tables']['cohort']['rows'][0]['retained']==3
                request.write_text(json.dumps(dict(analysis=name,columns={'a':numeric(['-Infinity',1]),'b':numeric([3,'Infinity'])},options=dict(left='a',right='b'),row_ids=['2','8'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                opened=json.loads(response.read_text());assert opened['status']=='ok'
                assert opened['outputs']['leftOut']['values']==[None,1]
                assert opened['outputs']['rightOut']['values']==[3,None]
                assert opened['outputs']['kindOut']['values']==[2,0]
            if name=='pytimeinterval':
                assert result['outputs']['calculated_time']['values']==[None,0,4,None]
                assert result['outputs']['calculated_time']['title']=='Calculated interval'
                assert result['outputs']['calculated_time']['row_ids']==['2','5','9','20']
                assert result['tables']['statistics']['rows'][0]['total']==4
                assert result['tables']['cohort']['rows'][0]['used']==2
                request.write_text(json.dumps(dict(analysis=name,columns={'a':factor(['2024-01-31','2023-01-31']), 'b':factor(['2024-02-29','2023-02-28'])}, options=dict(dx_date='a',fu_date='b',time_basis='calendar'),row_ids=['2','9'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                calendar_result=json.loads(response.read_text())
                assert calendar_result['status']=='ok'
                assert calendar_result['outputs']['calculated_time']['values']==[1,1]
                assert 'basis: calendar' in calendar_result['outputs']['calculated_time']['description']
                request.write_text(json.dumps(dict(analysis=name,columns={'a':numeric([20240131,20240229,None]),'b':numeric([20240229,20240301,20240301])},options=dict(dx_date='a',fu_date='b',time_format='packed_ymd',output_unit='days'),row_ids=['2','8','20'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                packed=json.loads(response.read_text());assert packed['status']=='ok'
                assert packed['outputs']['calculated_time']['values']==[29,1,None]
                assert 'Format: packed_ymd' in packed['outputs']['calculated_time']['description']
            if name=='pydatetimeconverter':
                assert result['outputs']['corrected_datetime_numeric']['values']==[1709164800.,None,None,1609459200.]
                assert result['outputs']['year_out']['values']==[2024,None,None,2021]
                assert result['outputs']['corrected_datetime_numeric']['title']=='Unix epoch seconds (UTC)'
                assert all(v.get('title','').strip() for v in result['outputs'].values())
                q=result['tables']['quality']['rows'][0]
                assert (q['parsed'],q['invalid'],q['missing'])==(2,1,1)
                request.write_text(json.dumps(dict(analysis=name,columns={'x':numeric([20240229,20230229,None,20000229])},options=dict(datetime_var='x',datetime_format='packed_ymd'),row_ids=['2','5','9','20'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                packed=json.loads(response.read_text());assert packed['status']=='ok'
                assert packed['outputs']['corrected_datetime_numeric']['values']==[1709164800.,None,None,951782400.]
            if name=='pyoutcomeorganizer':
                assert [v['n'] for v in result['tables']['frequencies']['rows']]==[2,1,1]
                assert result['outputs']['addOutcome']['values']==[0,0,1,2,None]
                assert result['outputs']['addOutcome']['levels']==['Censored','Event','Competing']
                request.write_text(json.dumps(dict(analysis=name,columns={'y':numeric([0,1,None]),'r':factor(['N',None,'Y'])},options=dict(outcome='y',recurrence='r',recurrenceLevel='Y',analysistype='rfs',diagnostics=True),row_ids=['2','8','20'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                composite=json.loads(response.read_text());assert composite['status']=='ok'
                assert composite['outputs']['addOutcome']['values']==[0,1,1]
                assert composite['outputs']['addOutcome']['row_ids']==['2','8','20']
                assert composite['tables']['compositeAudit']['rows'][0]['overrides']==2
            if name=='pytableone':
                assert result['tables']['cohort']['rows'][0]['retained']==4
                assert result['tables']['cohort']['rows'][0]['omitted']==1
                assert abs(result['tables']['continuous']['rows'][0]['mean']-7/3)<1e-12
                assert result['tables']['categories']['rows'][0]['level']=='B'
                assert result['tables']['categories']['rows'][0]['n']==2
                assert 'retained records' in result['texts']['report']
            if name=='pycrosstable':
                assert result['tables']['cohort']['rows'][0]['n']==10
                summary=result['tables']['continuous']['rows'][0]
                assert summary['mean']==5.5 and summary['median']==5.5
                test=result['tables']['tests']['rows'][0]
                assert test['method']=='Wilcoxon exact' and abs(test['p']-2/252)<1e-12
                assert abs(test['adjusted']-test['p'])<1e-12
                tied_columns={'g':factor(['A']*6+['B']*6),'x':numeric([1,2,2,3,4,5,2,3,4,4,6,8])}
                request.write_text(json.dumps(dict(analysis=name,columns=tied_columns,options=dict(vars=['x'],group='g',numericMode='continuous'))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                tied=json.loads(response.read_text());assert tied['status']=='ok',tied.get('error')
                test=tied['tables']['tests']['rows'][0]
                assert test['method']=='Wilcoxon exact (ties)' and abs(test['p']-178/924)<1e-12
            if name=='pyalluvial':
                assert [r['n'] for r in result['tables']['flows']['rows']]==[9,1]
                drawing=json.loads(result['plots']['flowPlot']['columns']['payload'][0])
                assert [r['n'] for r in drawing['ribbons']]==[9,1]
                assert 'Highlighted flow' in result['htmls']['explorer']
                request.write_text(json.dumps(dict(operation='render_plot',plot=result['plots']['flowPlot'],settings=dict(width=1100,height=700))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                rendered=json.loads(response.read_text());assert rendered['status']=='ok',rendered.get('error')
                png=base64.b64decode(rendered['asset']['png']);assert struct.unpack('>II',png[16:24])==(1100,700)
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
            if name=='pyjjcorrmat':
                ranked_columns={'a':numeric([1,1,2,3,5,8]),'b':numeric([5,2,2,8,4,9]),'z':numeric([1,3,2,5,4,7])}
                request.write_text(json.dumps(dict(analysis=name,columns=ranked_columns,options=dict(dep=['a','b','z'],partial=True,typestatistics='nonparametric'))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                ranked=json.loads(response.read_text())
                assert ranked['status']=='ok',ranked.get('error')
                row=ranked['tables']['correlations']['rows'][0]
                assert abs(row['estimate']-.1601592641029556)<1e-12
                assert abs(row['p']-.7969540733546533)<1e-12
                assert row['controls']==1 and row['df']==3 and row['lower'] is None and row['upper'] is None
            if name=='pyjjcorrmat':
                split_columns={'a':numeric([1,2,4,3,1,2,3,4,99]),'b':numeric([1,2,3,4,4,3,2,1,99]),'g':{'kind':'factor','levels':['unused','A','B'],'codes':[1,1,1,1,2,2,2,2,None]}}
                request.write_text(json.dumps(dict(analysis=name,columns=split_columns,options=dict(dep=['a','b'],grvar='g'))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                split=json.loads(response.read_text())
                assert split['status']=='ok',split.get('error')
                rows=split['tables']['correlations']['rows'];assert [r['group'] for r in rows]==['A','B']
                assert abs(rows[0]['estimate']-.8)<1e-12 and abs(rows[1]['estimate']+1)<1e-12
                assert len(split['tables']['cohorts']['rows'])==2
                assert len(split['plots']['matrix']['columns']['value'])==8 and 'Inspect group' in split['htmls']['explorer']
            if name=='pyvartree':
                nodes=result['tables']['nodes']['rows']
                assert nodes[0]['n']==3 and sum(v['n'] for v in nodes if v['leaf']=='Yes')==3
                assert '<details open>' in result['htmls']['explorer']
                assert sum(result['plots']['leafPlot']['columns']['value'])==3
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=dict(options,showPaths=True))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                paths=json.loads(response.read_text());assert paths['status']=='ok',paths.get('error')
                assert paths['tables']==result['tables'] and paths['plots']==result['plots']
                summary_columns=dict(columns,score=numeric([1,3,9,100]))
                request.write_text(json.dumps(dict(analysis=name,columns=summary_columns,options=dict(options,showNodeSummary=True,summaryvar='score',summarylocation='allnodes'))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                summary=json.loads(response.read_text());assert summary['status']=='ok',summary.get('error')
                assert summary['tables']['nodes']==result['tables']['nodes'] and summary['plots']==result['plots']
                stats=summary['tables']['nodeSummary']['rows'];assert len(stats)==6
                assert (stats[0]['nodeN'],stats[0]['valid'],stats[0]['missing'])==(3,3,0)
                assert abs(stats[0]['mean']-13/3)<1e-12 and abs(stats[0]['sd']-(52/3)**.5)<1e-12
                request.write_text(json.dumps(dict(operation='render_plot',plot=result['plots']['leafPlot'],settings=dict(width=1000,height=650))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                rendered=json.loads(response.read_text());assert rendered['status']=='ok',rendered.get('error')
                png=base64.b64decode(rendered['asset']['png']);assert struct.unpack('>II',png[16:24])==(1000,650)
                with (temp/'ClinicoPathPj/data/python_variable_tree_examples.csv').open() as handle:
                    records=list(csv.DictReader(handle))
                example_columns={}
                for variable in ['Tumor','Grade','Stage']:
                    labels=list(dict.fromkeys(r[variable] for r in records if r[variable]))
                    example_columns[variable]=dict(kind='factor',levels=labels,codes=[labels.index(r[variable]) if r[variable] else None for r in records])
                request.write_text(json.dumps(dict(analysis=name,columns=example_columns,options=dict(vars=['Tumor','Grade','Stage'],showPlot=True))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                example=json.loads(response.read_text());assert example['status']=='ok',example.get('error')
                nodes=example['tables']['nodes']['rows'];assert nodes[0]['n']==36 and len(nodes)==15
                assert [v['n'] for v in nodes if v['leaf']=='Yes']==[12,6,4,5,7,2]
                with (temp/'ClinicoPathPj/data/python_tree_node_summary_examples.csv').open() as handle:
                    records=list(csv.DictReader(handle))
                summary_columns={}
                for variable in ['Tumor','Grade']:
                    labels=list(dict.fromkeys(r[variable] for r in records if r[variable]))
                    summary_columns[variable]=dict(kind='factor',levels=labels,codes=[labels.index(r[variable]) if r[variable] else None for r in records])
                summary_columns['MarkerScore']=numeric([float(r['MarkerScore']) if r['MarkerScore'] else None for r in records])
                request.write_text(json.dumps(dict(analysis=name,columns=summary_columns,options=dict(vars=['Tumor','Grade'],showNodeSummary=True,summaryvar='MarkerScore',summarylocation='allnodes'))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                example=json.loads(response.read_text());assert example['status']=='ok',example.get('error')
                root_stats=example['tables']['nodeSummary']['rows'][0]
                assert (root_stats['nodeN'],root_stats['valid'],root_stats['missing'],root_stats['mean'])==(7,4,3,18.5)
                assert abs(root_stats['sd']-(227/3)**.5)<1e-12
                with (temp/'ClinicoPathPj/data/python_tree_reference_examples.csv').open() as handle:
                    records=list(csv.DictReader(handle))
                reference_columns={}
                for variable in ['Tumor','Grade','MarkerStatus']:
                    labels=list(dict.fromkeys(r[variable] for r in records if r[variable]))
                    reference_columns[variable]=dict(kind='factor',levels=labels,codes=[labels.index(r[variable]) if r[variable] else None for r in records])
                reference_columns['MarkerScore']=numeric([float(r['MarkerScore']) if r['MarkerScore'] else None for r in records])
                opts=dict(vars=['Tumor','Grade'],showNodeSummary=True,summaryvar='MarkerScore',summarylocation='allnodes',pct=True,percvar='MarkerStatus',percvarLevel='Positive')
                request.write_text(json.dumps(dict(analysis=name,columns=reference_columns,options=opts)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                reference=json.loads(response.read_text());assert reference['status']=='ok',reference.get('error')
                root=reference['tables']['referenceSummary']['rows'][0]
                assert (root['nodeN'],root['valid'],root['missing'],root['matches'],root['percent'])==(7,4,3,2,.5)
                assert reference['tables']['nodeSummary']['rows'][0]['mean']==18.5
                assert 'MarkerStatus=Positive' in reference['htmls']['explorer'] and 'MarkerScore:' in reference['htmls']['explorer']
            if name=='pyoutlierdetection':
                c=result['plots']['distributionPlot']['columns']
                assert c['value'][0]==0 and c['value'][-1]==20 and len(c['value'])==101
                assert c['lower']==[-3.]*101 and c['upper']==[8.]*101
                request.write_text(json.dumps(dict(operation='render_plot',plot=result['plots']['distributionPlot'],settings=dict(width=1000,height=800))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                rendered=json.loads(response.read_text());assert rendered['status']=='ok',rendered.get('error')
                png=base64.b64decode(rendered['asset']['png']);assert struct.unpack('>II',png[16:24])==(1000,800)
                assert result['tables']['variables']['rows'][0]['flagged']==1
                detail=result['tables']['flaggedValues']['rows'][0]
                assert (detail['row'],detail['value'],detail['lower'],detail['upper'])==('6',20.,-3.,8.)
                assert result['tables']['rowPreview']['rows'][-1]['status']=='Excluded: missing/nonfinite'
                with (temp/'ClinicoPathPj/data/python_outlier_screening_examples.csv').open() as handle:
                    panels=list(csv.DictReader(handle))
                example_columns={v:numeric([float(r[v]) if r[v] else None for r in panels]) for v in ['Marker_A','Marker_B']}
                for method in ['zscore_robust','zscore','iqr']:
                    request.write_text(json.dumps(dict(analysis=name,columns=example_columns,options=dict(vars=['Marker_A','Marker_B'],method=method,showFlaggedValues=True))))
                    subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                    example=json.loads(response.read_text());assert example['status']=='ok',example.get('error')
                    assert [r['flagged'] for r in example['tables']['variables']['rows']]==[1,1]
                    assert [r['n'] for r in example['tables']['variables']['rows']]==[31,31]
                    assert [(r['row'],r['variable'],r['value']) for r in example['tables']['flaggedValues']['rows']]==[('31','Marker_A',200.),('31','Marker_B',-100.)]

            if name=='pyvenn':
                assert [r['n'] for r in result['tables']['intersections']['rows']]==[1,1,1,1]
                assert result['tables']['membershipTable']['rows'][-1]['status'].startswith('Excluded')
                request.write_text(json.dumps(dict(analysis=name,columns=columns,options=dict(options,showSetMatrix=True),row_ids=['2','5','9','12','15'])))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                saved=json.loads(response.read_text());assert saved['status']=='ok',saved.get('error')
                assert saved['outputs']['membershipGroups']['values']==[0,1,2,3,None]
                assert saved['outputs']['membershipGroups']['measure_type']=='nominal'
                matrix=saved['plots']['intersectionMatrix'];assert matrix['kind']=='setmatrix'
                assert matrix['columns']['count']==[1]*4
                request.write_text(json.dumps(dict(operation='render_plot',plot=matrix,settings=dict(width=900,height=600))))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                rendered=json.loads(response.read_text());assert rendered['status']=='ok',rendered.get('error')
                png=base64.b64decode(rendered['asset']['png']);assert struct.unpack('>II',png[16:24])==(900,600)
                with (temp/'ClinicoPathPj/data/python_set_intersection_unequal_examples.csv').open() as handle:
                    panels=list(csv.DictReader(handle))
                labels=['Negative','Positive'];variables=['Marker_A','Marker_B','Marker_C','Marker_D']
                unequal_columns={v:dict(kind='factor',levels=labels,codes=[labels.index(r[v]) if r[v] else None for r in panels]) for v in variables}
                unequal_options={f'var{i+1}':v for i,v in enumerate(variables)}
                unequal_options.update({f'var{i+1}true':'Positive' for i in range(4)})
                unequal_options.update(showSetMatrix=True,showZero=True)
                request.write_text(json.dumps(dict(analysis=name,columns=unequal_columns,options=unequal_options)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                unequal=json.loads(response.read_text());assert unequal['status']=='ok',unequal.get('error')
                assert unequal['plots']['intersectionMatrix']['columns']['count']==[12,8,6,10,4,5,3,2,3,1,2,1,1,0,1,1]
                unequal_options['patternOrder']='frequency'
                request.write_text(json.dumps(dict(analysis=name,columns=unequal_columns,options=unequal_options)))
                subprocess.run([sys.executable,'-B',str(runtime),str(request),str(response)],check=True,timeout=70)
                ordered=json.loads(response.read_text());assert ordered['status']=='ok',ordered.get('error')
                expected=sorted(enumerate([12,8,6,10,4,5,3,2,3,1,2,1,1,0,1,1]),key=lambda pair:(-pair[1],pair[0]))
                signatures=[''.join(str((i>>j)&1) for j in range(4)) for i,count in expected]
                assert ordered['plots']['intersectionMatrix']['columns']['pattern']==signatures
                assert [r['pattern'] for r in ordered['tables']['intersections']['rows']]==signatures


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
