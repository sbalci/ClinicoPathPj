"""Read-only native OMV/HTML checks against independent date arithmetic."""
import csv,json,math,runpy
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
rounded_equal=runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']


def check():
    with (ROOT/'data/python_interval_examples.csv').open() as f: records=list(csv.DictReader(f))
    evidence={}
    for state in ['days','landmark','negative','excluded']:
        m,labels,cols=saved_columns('python-interval-0.3.46-'+state+'.omv')
        assert m['rowCount']==12 and m['columnCount']==5
        for name in records[0]:
            mapping={x[0]:x[1] for x in labels[name]['labels']}
            got=[None if v==-2147483648 else mapping[v] for v in cols[name]]
            assert got==[r[name] or None for r in records],(state,name)
        expected=[]
        source='End with reversal' if state in ['negative','excluded'] else 'End date'
        for r in records:
            v=(date.fromisoformat(r[source])-date.fromisoformat(r['Start date'])).days if r[source] and r['Start date'] else None
            if state=='negative':v=None
            elif state=='landmark':v=v-6 if v is not None and v>=6 else None
            elif state=='excluded' and v is not None and v<0:v=None
            expected.append(v)
        got=[None if math.isnan(v) else v for v in cols['Calculated interval']]
        assert got==expected,(state,got,expected)
        field=next(f for f in m['fields'] if f['name']=='Calculated interval')
        assert field['columnType']=='Output' and field['measureType']=='Continuous'
        if state!='negative':assert 'Unit: days;' in field['description']
        evidence[state]={'used':sum(v is not None for v in expected),'total':sum(v for v in expected if v is not None) if any(v is not None for v in expected) else None,'saved_alignment':'pass'}
    parser=Tables();parser.feed((EXPORTS/'python-interval-0.3.46-excluded.html').read_text())
    summary=next(t for t in parser.tables if len(t)>1 and 'Summed Record-Time' in t[1])
    s=dict(zip(summary[1],summary[2]));assert int(s['N'])==9 and s['Unit']=='days'
    rounded_equal(s['Summed Record-Time'],861);rounded_equal(s['Mean'],861/9)
    preview=next(t for t in parser.tables if len(t)>1 and 'Disposition' in t[1])
    assert len(preview[2:])==12
    for i,row in enumerate(preview[2:]):
        r=dict(zip(preview[1],row));assert r['Source Row ID']==str(i+1)
        v=[0,1,2,6,None,30,31,60,365,366,None,None][i]
        if v is None:assert r['Used Interval'] in ('','.')
        else:rounded_equal(r['Used Interval'],v)
    assert dict(zip(preview[1],preview[6]))['Disposition']=='Excluded negative interval'
    evidence['html']={'summary_and_12_source_rows':'pass'}
    return evidence

if __name__=='__main__':print(json.dumps(check(),indent=2))
