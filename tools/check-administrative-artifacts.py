"""Check native saved administrative states against literal synthetic endpoints."""
import base64,csv,json,math,re,runpy,struct,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
BASE_TIME=[2,2,2,2,5,5,5,0,None,None,None,3]
BASE_STATUS=['Event','Censored','Censored','Event','Event','Event','Event','Event',None,None,None,'Censored']
BASE_SOURCE=['Component A','Censored','Censored','Component B','Component A','Component B','Both components','Component A',None,None,None,'Censored']
CUT2_TIME=[2,2,2,2,2,2,2,0,None,None,None,2]
CUT2_STATUS=['Event','Censored','Censored','Event','Censored','Censored','Censored','Event',None,None,None,'Censored']
CUT2_SOURCE=['Component A','Censored','Censored','Component B','Administrative cutoff','Administrative cutoff','Administrative cutoff','Component A',None,None,None,'Administrative cutoff']
ZERO_TIME=[0,0,0,0,0,0,0,0,None,None,None,0]
ZERO_STATUS=['Censored']*7+['Event',None,None,None,'Censored']
ZERO_SOURCE=['Administrative cutoff']*7+['Component A',None,None,None,'Administrative cutoff']


def check():
    with (ROOT/'data/python_first_event_examples.csv').open() as f:fixture=list(csv.DictReader(f))
    evidence={}
    for state in ['disabled','cutoff2','pending','zero','reopened','freshoutputs']:
        stem='python-admin-0.3.52-'+state
        metadata,labels,columns=saved_columns(stem+'.omv')
        assert metadata['rowCount']==12 and metadata['columnCount']==11
        with zipfile.ZipFile(EXPORTS/(stem+'.omv')) as z:strings=z.read('strings.bin')
        def decoded(name):
            field=next(x for x in metadata['fields'] if x['name']==name)
            if field['type']=='string':return [None if x==-2147483648 else strings[x:].split(b'\0',1)[0].decode() for x in columns[name]]
            mapping={r[0]:r[1] for r in labels.get(name,{}).get('labels',[])}
            return [None if math.isnan(x) or x==-2147483648 else mapping.get(x,x) for x in columns[name]]
        for name in fixture[0]:
            want=[r[name] or None for r in fixture]
            if name in ['A time','B time','Expected time']:want=[float(v) if v is not None else None for v in want]
            assert decoded(name)==want,(state,name)
        want=(BASE_TIME,BASE_STATUS,BASE_SOURCE) if state=='disabled' else (ZERO_TIME,ZERO_STATUS,ZERO_SOURCE) if state=='zero' else ([None]*12,)*3 if state=='pending' else (CUT2_TIME,CUT2_STATUS,CUT2_SOURCE)
        for name,values in zip(['Composite time','Composite status','Determining component'],want):
            assert decoded(name)==values,(state,name,decoded(name),values)
            field=next(x for x in metadata['fields'] if x['name']==name)
            assert field['columnType']=='Output'
            assert field['measureType']==('Continuous' if name=='Composite time' else 'Nominal')
        if state=='disabled':assert len(labels['Determining component']['labels'])==4
        if state in ['cutoff2','zero','reopened','freshoutputs']:
            assert len(labels['Determining component']['labels'])==5
            desc=next(x for x in metadata['fields'] if x['name']=='Composite time')['description']
            assert 'Minimum component event/follow-up duration' in desc
            assert ('Administrative cutoff 2.0' in desc) == (state=='freshoutputs')
        evidence[state]={'source_columns_unchanged':'pass','three_saved_columns_aligned':'pass','events':want[1].count('Event'),'censored':want[1].count('Censored')}
    stem='python-admin-0.3.52-reopened';text=(EXPORTS/(stem+'.html')).read_text()
    parser=Tables();parser.feed(text)
    audit=next(t for t in parser.tables if t[0]==['Administrative Censoring Audit'])
    assert [float(v) for v in audit[2]]==[2,4,3,1,2]
    counts=next(t for t in parser.tables if t[0]==['Composite Status Counts'])
    assert [int(r[2]) for r in counts[2:]]==[6,3]
    preview=next(t for t in parser.tables if t[0]==['Source-Row First-Event Preview'])
    assert [int(r[0]) for r in preview[2:]]==list(range(1,13))
    def number(x):return None if x in ('','.') else float(x.replace('−','-'))
    assert [number(r[5]) for r in preview[2:]]==CUT2_TIME
    assert [number(r[9]) for r in preview[2:]]==BASE_TIME
    assert [number(r[10]) for r in preview[2:]]==[None if v is None else int(v=='Event') for v in BASE_STATUS]
    assert [number(r[11]) for r in preview[2:]]==[0,0,0,0,1,1,1,0,None,None,None,1]
    images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',text);assert len(images)==1
    raw=base64.b64decode(images[0]);assert raw==(EXPORTS/(stem+'.png')).read_bytes()
    assert struct.unpack('>II',raw[16:24])==(1437,798)
    evidence['native_HTML_audit_preview_and_embedded_PNG']='pass'
    evidence['existing_dataset_descriptions']='Retain the older dataset text; current cutoff is in the saved analysis audit, not automatically refreshed dataset descriptions. Recreating the generated columns refreshes descriptions; freshoutputs fixture verifies this.'
    return evidence


if __name__=='__main__':print(json.dumps(check(),indent=2))
