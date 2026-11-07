"""Read-only checks of the linked inspector's synthetic desktop saves and export."""
import base64,csv,json,math,re,runpy,struct,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']


def check():
    with (ROOT/'data/python_diagnostic_study_examples.csv').open() as f:
        fixture=list(csv.DictReader(f))
    evidence={}
    for state in ['compatible','explorer','disabled','pending','strict','excluded','reopened']:
        stem='python-study-inspector-0.3.56-'+state
        metadata,labels,columns=saved_columns(stem+'.omv')
        assert metadata['rowCount']==12 and metadata['columnCount']==5
        with zipfile.ZipFile(EXPORTS/(stem+'.omv')) as z:strings=z.read('strings.bin')
        for field in metadata['fields']:
            name=field['name']
            if field['type']=='string':
                got=[None if v==-2147483648 else strings[v:].split(b'\0',1)[0].decode()
                     for v in columns[name]]
            else:
                mapping={r[0]:r[1] for r in labels.get(name,{}).get('labels',[])}
                got=[None if math.isnan(v) or v==-2147483648 else mapping.get(v,v)
                     for v in columns[name]]
            want=[r[name] or None for r in fixture]
            if name!='Study':want=[None if v is None else float(v) for v in want]
            if state=='excluded' and name=='TP':want=[1.5]*12
            assert got==want,(state,name)
        evidence[state]='pass: source inputs unchanged' if state!='excluded' else 'pass: earlier synthetic TP=1.5 exclusion inputs retained'
    stem='python-study-inspector-0.3.56-reopened'
    html=(EXPORTS/(stem+'.html')).read_text();parser=Tables();parser.feed(html)
    audit=next(t for t in parser.tables if t[0]==['Study Row Audit'])
    assert [int(v) for v in audit[2]]==[12,8,4,3,1,1]
    study=next(t for t in parser.tables if t[0]==['Individual Study Results (Raw Counts)'])
    assert [int(r[0]) for r in study[2:]]==list(range(1,9))
    assert [float(r[2]) for r in study[2:]]==[80,45,0,12,1,18,16,9]
    assert 'Linked study inspector' in html or 'Linked Study Inspector' in html
    images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',html)
    assert len(images)>=2
    dimensions={}
    for metric,encoded in zip(['sensitivity','specificity'],images[:2]):
        raw=base64.b64decode(encoded)
        assert raw==(EXPORTS/(stem+'-'+metric+'.png')).read_bytes()
        dimensions[metric]=struct.unpack('>II',raw[16:24])
        assert dimensions[metric]==(1437,1277)
    evidence['native_HTML_audit_and_static_counterparts']=dimensions
    return evidence


if __name__=='__main__':print(json.dumps(check(),indent=2))
