"""Read-only native saved-file and HTML checks against the nine-pair truth table."""
import base64,csv,json,re,runpy,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
rounded_equal=runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']
OR=[0,1,None,1,1,1,None,1,None];TTP=[0,1,None,0,1,None,0,1,None]

def decoded(name,labels,columns):
    mapping={x[0]:x[1] for x in labels.get(name,{}).get('labels',[])}
    return [None if v==-2147483648 else mapping.get(v,v) for v in columns[name]]


def check():
    with (ROOT/'data/python_composite_outcome_examples.csv').open() as f:source=list(csv.DictReader(f))
    evidence={}
    for state,want in [('rfs',OR),('incomplete',[None]*9),('ttp',TTP),('rfs-reopened',OR)]:
        stem='python-composite-0.3.49-'+state
        m,l,c=saved_columns(stem+'.omv');assert m['rowCount']==9 and m['columnCount']==5
        for name in source[0]:
            got=decoded(name,l,c)
            expected=[row[name] or None for row in source]
            assert [str(v) if v is not None else None for v in got]==expected,(state,name,got)
        got=[None if v is None else int(v) for v in decoded('Recoded survival outcome',l,c)]
        assert got==want,(state,got)
        field=next(f for f in m['fields'] if f['name']=='Recoded survival outcome')
        assert field['columnType']=='Output' and field['measureType']=='Nominal'
        if state!='incomplete':assert 'Endpoint status only' in field['description']
        evidence[state]={'known':sum(v is not None for v in want),'events':want.count(1),'unknown':want.count(None),'source_and_saved_alignment':'pass'}
        if state in ['ttp','rfs-reopened']:
            text=(EXPORTS/(stem+'.html')).read_text();parser=Tables();parser.feed(text)
            frequencies=next(t for t in parser.tables if len(t)>1 and 'Count' in t[1] and 'Coded Rows (%)' in t[1])
            rows=[dict(zip(frequencies[1],r)) for r in frequencies[2:]]
            assert [int(r['Count']) for r in rows]==[want.count(0),want.count(1)]
            for i,r in enumerate(rows):rounded_equal(r['Coded Rows (%)'].replace('%','').strip(),100*want.count(i)/6)
            audit=next(t for t in parser.tables if len(t)>1 and 'Known Event Despite Unknown Component' in t[1])
            row=dict(zip(audit[1],audit[2]));assert int(row['Known Event Despite Unknown Component'])==(0 if state=='ttp' else 2)
            components=next(t for t in parser.tables if len(t)>1 and 'Component Code' in t[1])
            assert len(components[2:])==(2 if state=='ttp' else 4)
            preview=next(t for t in parser.tables if len(t)>1 and 'Status Rule' in t[1])
            assert len(preview[2:])==9
            for i,r in enumerate(preview[2:]):
                row=dict(zip(preview[1],r));assert row['Source Row ID']==str(i+1)
                if want[i] is None:assert row['Status Code'] in ('.','')
                else:assert int(row['Status Code'])==want[i]
            images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',text);assert len(images)==1
            raw=base64.b64decode(images[0]);assert raw==(EXPORTS/(stem+'.png')).read_bytes()
            assert struct.unpack('>II',raw[16:24])==(1277,798)
            evidence[state]['native_HTML_and_embedded_PNG']='pass'
    return evidence

if __name__=='__main__':print(json.dumps(check(),indent=2))
