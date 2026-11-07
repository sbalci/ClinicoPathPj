"""Verify synthetic native study-inclusion saves and the GUI-produced HTML export."""
import base64
import csv
import json
import math
from pathlib import Path
import re
import runpy
from statistics import NormalDist
import struct
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
STEM='python-study-inclusion-0.3.57-'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']


def check():
    with (ROOT/'data/python_diagnostic_study_examples.csv').open() as stream:
        fixture=list(csv.DictReader(stream))
    evidence={}
    for state in ['compatible','two','empty','stale','reapplied','reopened']:
        metadata,labels,columns=saved_columns(STEM+state+'.omv')
        assert metadata['rowCount']==12 and metadata['columnCount']==5
        with zipfile.ZipFile(EXPORTS/(STEM+state+'.omv')) as archive:
            assert archive.testzip() is None
            strings=archive.read('strings.bin')
            images=[n for n in archive.namelist() if n.endswith('.png')]
            assert len(images)==(0 if state in ['empty','stale'] else 2),(state,images)
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
                if name=='TP' and state in ['stale','reapplied','reopened']:expected[0]=81
            assert actual==expected,(state,name)
        evidence[state]=dict(rows=12,columns=5,native_images=len(images),expected_raw_data='pass')
    html=(EXPORTS/(STEM+'reopened.html')).read_text();parser=Tables();parser.feed(html)
    table=lambda title:next(t for t in parser.tables if t[0]==[title])
    assert [int(v) for v in table('Study Row Audit')[2]]==[12,8,4,3,1,1]
    inclusion=table('Applied Study Inclusion')[2]
    assert [int(v) for v in inclusion[:3]]==[8,2,6]
    assert inclusion[3]=='Applied to current input'
    studies=[r for r in table('Individual Study Results (Raw Counts)')[2:] if len(r)==12]
    assert [int(r[0]) for r in studies]==[1,7]
    assert [[int(float(v)) for v in r[2:6]] for r in studies]==[[81,10,20,90],[16,2,4,18]]
    payload=json.loads(re.search(r'payload=(\{.*?\}),rows=payload.studies;',html,re.S)[1])
    assert len(payload['studies'])==8 and payload['confidence']==99
    assert payload['inclusion']['included']==['1','7'] and payload['inclusion']['valid'] is True
    z=NormalDist().inv_cdf(.995)
    for row in studies:
        tp,fp,fn,tn=[float(v) for v in row[2:6]];expected=[]
        for x,n in [(tp,tp+fn),(tn,tn+fp)]:
            p=x/n;scale=1+z*z/n;center=(p+z*z/(2*n))/scale
            half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/scale
            expected.extend([p,max(0,center-half),min(1,center+half)])
        shown=[float(v.replace('\u2009','').replace('%','').strip())/100 for v in row[6:12]]
        assert all(abs(a-b)<=.00050001 for a,b in zip(shown,expected))
    images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',html)
    assert len(images)>=2
    for metric,encoded in zip(['sensitivity','specificity'],images[:2]):
        raw=base64.b64decode(encoded)
        assert struct.unpack('>II',raw[16:24])==(1437,1277)
        assert raw==(EXPORTS/(STEM+'reopened-'+metric+'.png')).read_bytes()
    evidence['export']=dict(audit=[12,8,4,3,1,1],inclusion=[8,2,6],source_rows=[1,7],
                            confidence=99,independent_display_intervals='pass',inspector_eligible_rows=8)
    return evidence


if __name__=='__main__':print(json.dumps(check(),indent=2))
