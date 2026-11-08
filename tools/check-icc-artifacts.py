"""Read-only checks of native synthetic ICC saves and HTML export, version 0.3.59."""
import csv
import json
import math
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
STEM='python-icc-0.3.59-'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']


def tables(html):
    parser=Tables();parser.feed(html)
    return {t[0][0]:t for t in parser.tables}


def check():
    with (ROOT/'data/python_icc_examples.csv').open() as stream:
        fixture=list(csv.DictReader(stream))
    evidence={}
    for state in ['icc21','icc2k','pending','icc31','reopened']:
        path=STEM+state+'.omv'
        metadata,labels,columns=saved_columns(path)
        assert metadata['rowCount']==8 and metadata['columnCount']==4
        with zipfile.ZipFile(EXPORTS/path) as archive:
            assert archive.testzip() is None
            strings=archive.read('strings.bin')
            content=archive.read('index.html').decode()
            assert not any(n.endswith('.png') for n in archive.namelist())
        for field in metadata['fields']:
            name=field['name']
            if field['type']=='string':
                actual=[None if v==-2147483648 else strings[v:].split(b'\0',1)[0].decode()
                        for v in columns[name]]
                expected=[r[name] or None for r in fixture]
            else:
                mapping={r[0]:r[1] for r in labels.get(name,{}).get('labels',[])}
                actual=[None if math.isnan(v) or v==-2147483648 else mapping.get(v,v) for v in columns[name]]
                expected=[float(r[name]) if r[name] else None for r in fixture]
            assert actual==expected,(state,name)
        t=tables(content)
        row=t['Intraclass Correlation'][2]
        if state=='pending':
            assert row==[''] and t['ICC Complete-Case Audit'][2]==['']
            assert t['Retained Independent ICC Cases'][2]==['']
        else:
            assert list(map(int,t['ICC Complete-Case Audit'][2]))==[8,6,2,3]
            assert t['Retained Independent ICC Cases'][2:]==[[str(i+1),r['Case']] for i,r in enumerate(fixture[:6])]
            if state=='icc2k':
                assert row[1:]==['0.963','.','.','0.950']
                assert 'Do not choose a different model solely' in content
            elif state=='icc21':
                assert row[1:]==['0.898','0.585','0.984','0.950']
            else:
                assert row[1:]==['0.938','0.770','0.990','0.950']
        evidence[state]=dict(rows=8,columns=4,unchanged_source_data=True,
                             displayed_icc=row[1:] if state!='pending' else None)
    with zipfile.ZipFile(EXPORTS/(STEM+'compatibility.omv')) as current, \
         zipfile.ZipFile(EXPORTS/'python-agreement-0.3.58-reopened.omv') as original:
        assert current.testzip() is None
        assert current.read('data.bin')==original.read('data.bin')
        assert current.read('strings.bin')==original.read('strings.bin')
        t=tables(current.read('index.html').decode())
        assert t['Paired Observation Audit'][2]==['12','8','4','1','2','1']
        assert t['Bland-Altman Estimates'][2][1]=='0.00'
        assert t['Bland-Altman Estimates'][5][1]=='6.71'
        assert len([n for n in current.namelist() if n.endswith('.png')])==1
    exported=tables((EXPORTS/(STEM+'reopened.html')).read_text())
    assert exported['Intraclass Correlation'][2][1:]==['0.938','0.770','0.990','0.950']
    assert exported['Retained Independent ICC Cases'][2:]==[[str(i+1),r['Case']] for i,r in enumerate(fixture[:6])]
    evidence['legacy_compatibility']=dict(original_source_data=True,audit=[12,8,4,1,2,1],native_plot=1)
    evidence['native_html_export']='matches saved ICC(3,1), cohort and retained source cases'
    return evidence


if __name__=='__main__':print(json.dumps(check(),indent=2))
