"""Read GUI-saved outputs against literal timelines, without calling the implementation."""
import base64, csv, json, math, re, runpy, struct, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']


def check():
    with (ROOT/'data/python_first_event_examples.csv').open() as f: fixture=list(csv.DictReader(f))
    evidence={}
    for state in ['valid','incomplete','reopened']:
        stem='python-firstevent-0.3.51-'+state
        metadata,labels,columns=saved_columns(stem+'.omv')
        assert metadata['rowCount']==12 and metadata['columnCount']==11
        with zipfile.ZipFile(EXPORTS/(stem+'.omv')) as archive:
            strings=archive.read('strings.bin')
        def decoded(name):
            field=next(x for x in metadata['fields'] if x['name']==name)
            if field['type']=='string':
                return [None if x==-2147483648 else strings[x:].split(b'\x00',1)[0].decode('utf-8') for x in columns[name]]
            mapping={r[0]:r[1] for r in labels.get(name,{}).get('labels',[])}
            return [None if math.isnan(x) or x==-2147483648 else mapping.get(x,x) for x in columns[name]]
        for name in fixture[0]:
            got=decoded(name)
            expected=[row[name] or None for row in fixture]
            if name in ['A time','B time','Expected time']:
                expected=[None if x is None else float(x) for x in expected]
            assert got==expected,(state,name,got,expected)
        for name,reference in [('Composite time','Expected time'),('Composite status','Expected status'),('Determining component','Expected source')]:
            expected=[None]*12 if state=='incomplete' else decoded(reference)
            assert decoded(name)==expected,(state,name,decoded(name),expected)
            field=next(x for x in metadata['fields'] if x['name']==name)
            assert field['columnType']=='Output'
            assert field['measureType']==('Continuous' if name=='Composite time' else 'Nominal')
        evidence[state]={'source_columns_unchanged':'pass','three_saved_columns_aligned':'pass','usable':0 if state=='incomplete' else 9}
    stem='python-firstevent-0.3.51-reopened'
    text=(EXPORTS/(stem+'.html')).read_text()
    parser=Tables();parser.feed(text)
    audit=next(t for t in parser.tables if t[0]==['Row Accounting'])
    assert list(map(int,audit[2]))==[12,9,1,2,3,2]
    counts=next(t for t in parser.tables if t[0]==['Composite Status Counts'])
    assert [int(r[2]) for r in counts[2:]]==[3,6]
    preview=next(t for t in parser.tables if t[0]==['Source-Row First-Event Preview'])
    assert [int(r[0]) for r in preview[2:]]==list(range(1,13))
    for i,row in enumerate(preview[2:]):
        want=fixture[i]['Expected time']
        assert row[5] in ('','.') if not want else float(row[5].replace('−','-'))==float(want)
        want=fixture[i]['Expected status']
        assert row[6] in ('','.') if not want else int(row[6])==int(want=='Event')
    images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',text)
    assert len(images)==1
    raw=base64.b64decode(images[0]);assert raw==(EXPORTS/(stem+'.png')).read_bytes()
    assert struct.unpack('>II',raw[16:24])==(1437,798)
    evidence['native_HTML_tables_and_embedded_PNG']='pass'
    return evidence


if __name__=='__main__':print(json.dumps(check(),indent=2))
