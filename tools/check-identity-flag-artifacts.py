"""Check desktop-saved 0.3.54 identity flags without invoking the analysis engine."""
import base64, json, math, re, runpy, struct, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
BASE=runpy.run_path(str(ROOT/'tools/check-administrative-artifacts.py'))
FLAGS=['Repeated ID','Repeated ID','Unique ID','Unique ID','Unique ID','Unique ID',
       'Unique ID','Unique ID','Unknown ID','Unique ID','Repeated ID','Repeated ID']


def decoded(path):
    metadata,labels,columns=saved_columns(path.name)
    with zipfile.ZipFile(path) as z:
        strings=z.read('strings.bin')
    result={}
    for field in metadata['fields']:
        name=field['name'];mapping={r[0]:r[1] for r in labels.get(name,{}).get('labels',[])}
        if field['type']=='string':
            result[name]=[None if v==-2147483648 else strings[v:].split(b'\0',1)[0].decode()
                          for v in columns[name]]
        else:
            result[name]=[None if math.isnan(v) or v==-2147483648 else mapping.get(v,v)
                          for v in columns[name]]
    return metadata,labels,result


def check():
    old_meta,_,original=decoded(EXPORTS/'python-identity-0.3.53-reopened.omv')
    sources=[f['name'] for f in old_meta['fields'] if f['columnType']!='Output']
    result={}
    for state in ['valid','strict','unique','disabled','pending','reopened']:
        path=EXPORTS/('python-identity-flags-0.3.54-'+state+'.omv')
        meta,labels,columns=decoded(path)
        assert meta['rowCount']==12 and meta['columnCount']==13
        for source in sources:
            assert columns[source]==original[source],(state,source)
        flag=next(f for f in meta['fields'] if f['name']=='Subject identity flag')
        assert flag['columnType']=='Output' and flag['measureType']=='Nominal'
        want=[None]*12 if state in ['disabled','strict','pending'] else ['Unique ID']*12 if state=='unique' else FLAGS
        assert columns['Subject identity flag']==want,(state,columns['Subject identity flag'])
        expected=([None]*12,)*3 if state in ['strict','pending'] else (
            BASE['BASE_TIME'],BASE['BASE_STATUS'],BASE['BASE_SOURCE'])
        for name,values in zip(['Composite time','Composite status','Determining component'],expected):
            assert columns[name]==values,(state,name)
        result[state]=dict(source_columns_unchanged=True,identity_flags_aligned=True,
                           endpoint_outputs_aligned=True)
    html=(EXPORTS/'python-identity-flags-0.3.54-reopened.html').read_text()
    parser=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']()
    parser.feed(html)
    audit=next(t for t in parser.tables if t[0]==['Subject Identity Audit'])
    assert [int(v) for v in audit[2]]==[12,11,1,9,2,4]
    counts=next(t for t in parser.tables if t[0]==['Composite Status Counts'])
    assert [int(r[2]) for r in counts[2:]]==[3,6]
    assert 'optional saved identity flag' in html and 'Unknown ID' in html
    images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',html)
    assert len(images)==1
    raw=base64.b64decode(images[0])
    assert raw==(EXPORTS/'python-identity-flags-0.3.54-reopened.png').read_bytes()
    assert struct.unpack('>II',raw[16:24])==(1437,798)
    result['native_HTML_and_embedded_PNG']='pass'
    return result


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
