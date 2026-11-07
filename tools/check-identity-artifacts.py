"""Check saved subject-audit states against literal synthetic identities/endpoints."""
import base64, csv, json, math, re, runpy, struct, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
BASE=runpy.run_path(str(ROOT/'tools/check-administrative-artifacts.py'))
SUBJECT=['001','001','1','01','S04','S05','S06','S07',None,'S08','S09','S09']


def check():
    with (ROOT/'data/python_first_event_examples.csv').open() as f:
        fixture=list(csv.DictReader(f))
    evidence={}
    for state in ['inputpending','valid','strict','unique','reopened']:
        stem='python-identity-0.3.53-'+state
        metadata,labels,columns=saved_columns(stem+'.omv')
        assert metadata['rowCount']==12 and metadata['columnCount']==12
        with zipfile.ZipFile(EXPORTS/(stem+'.omv')) as z:
            strings=z.read('strings.bin')
        def decoded(name):
            field=next(x for x in metadata['fields'] if x['name']==name)
            if field['type']=='string':
                return [None if x==-2147483648 else strings[x:].split(b'\0',1)[0].decode()
                        for x in columns[name]]
            mapping={r[0]:r[1] for r in labels.get(name,{}).get('labels',[])}
            return [None if math.isnan(x) or x==-2147483648 else mapping.get(x,x)
                    for x in columns[name]]
        for name in fixture[0]:
            want=[r[name] or None for r in fixture]
            if name in ['A time','B time','Expected time']:
                want=[float(v) if v is not None else None for v in want]
            assert decoded(name)==want,(state,name)
        assert decoded('Subject ID')==SUBJECT
        wanted=([None]*12,)*3 if state in ['inputpending','strict'] else (
            BASE['BASE_TIME'],BASE['BASE_STATUS'],BASE['BASE_SOURCE'])
        for name,want in zip(['Composite time','Composite status','Determining component'],wanted):
            assert decoded(name)==want,(state,name,decoded(name))
            field=next(x for x in metadata['fields'] if x['name']==name)
            assert field['columnType']=='Output'
            assert field['measureType']==('Continuous' if name=='Composite time' else 'Nominal')
        evidence[state]={'source_columns_unchanged':'pass','three_outputs_aligned':'pass',
                         'events':wanted[1].count('Event'),'censored':wanted[1].count('Censored')}
    stem='python-identity-0.3.53-reopened'
    text=(EXPORTS/(stem+'.html')).read_text()
    parser=Tables();parser.feed(text)
    audit=next(t for t in parser.tables if t[0]==['Subject Identity Audit'])
    assert [int(v) for v in audit[2]]==[12,11,1,9,2,4]
    repeats=next(t for t in parser.tables if t[0]==['Repeated IDs (First 20)'])
    assert repeats[2:]==[['001','2'],['S09','2']]
    preview=next(t for t in parser.tables if t[0]==['Source-Row First-Event Preview'])
    subject=preview[1].index('Subject ID');count=preview[1].index('Records With This ID')
    assert [r[subject] if r[subject] not in ('','.') else None for r in preview[2:]]==SUBJECT
    assert [None if r[count] in ('','.') else int(r[count]) for r in preview[2:]]==[
        2,2,1,1,1,1,1,1,None,1,2,2]
    images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',text)
    assert len(images)==1
    raw=base64.b64decode(images[0]);assert raw==(EXPORTS/(stem+'.png')).read_bytes()
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    evidence['native_HTML_audit_preview_and_embedded_PNG']='pass'
    evidence['PNG_dimensions']=struct.unpack('>II',raw[16:24])
    return evidence


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
