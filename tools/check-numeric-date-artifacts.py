"""Read-only OMV/HTML checks using independent datetime arithmetic and source CSV."""
import csv,json,math,runpy
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
rounded_equal=runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']


def decoded(name,labels,columns):
    mapping={v[0]:v[1] for v in labels.get(name,{}).get('labels',[])}
    return [None if v==-2147483648 or isinstance(v,float) and math.isnan(v) else mapping.get(v,v) for v in columns[name]]


def check():
    with (ROOT/'data/python_numeric_date_examples.csv').open() as f:records=list(csv.DictReader(f))
    expected={'packed':[29,30,1,31,365,None],'malformed':[29,30,1,31,None,None],
              'rejected':[None]*6,'excel':[29,30,1,31,365,None],'combined':[29,30,1,31,365,None]}
    evidence={}
    for state,want in expected.items():
        m,l,c=saved_columns('python-numeric-dates-0.3.48-'+state+'.omv')
        assert m['rowCount']==6
        for name in records[0]:
            got=decoded(name,l,c)
            for a,row in zip(got,records):
                if not row[name]:assert a is None
                elif name=='Record':assert a==row[name]
                else:assert float(a)==float(row[name])
        actual=decoded('Calculated interval',l,c)
        assert actual==want,(state,actual)
        field=next(x for x in m['fields'] if x['name']=='Calculated interval')
        assert field['columnType']=='Output' and field['measureType']=='Continuous'
        if state!='rejected':
            fmt='packed_ymd' if state in ['packed','malformed'] else 'excel_serial'
            assert f'Format: {fmt}' in field['description']
        evidence[state]={'used':sum(v is not None for v in want),'sum_days':sum(v for v in want if v is not None) if state!='rejected' else None,'source_and_saved_alignment':'pass'}
        if state=='combined':
            dates=[]
            for r in records:
                try:d=datetime.strptime(r['Malformed packed end'],'%Y%m%d').replace(tzinfo=timezone.utc)
                except ValueError:d=None
                dates.append(d)
            assert decoded('Unix epoch seconds (UTC)',l,c)==[None if d is None else d.timestamp() for d in dates]
            assert decoded('Standardized UTC datetime labels',l,c)==[None if d is None else d.isoformat().replace('+00:00','Z') for d in dates]
            assert len(m['fields'])==13
    parser=Tables();parser.feed((EXPORTS/'python-numeric-dates-0.3.48-combined.html').read_text())
    summary=next(t for t in parser.tables if len(t)>1 and 'Summed Record-Time' in t[1])
    row=dict(zip(summary[1],summary[2]));assert row['Unit']=='days' and int(row['N'])==5
    rounded_equal(row['Summed Record-Time'],456);rounded_equal(row['Mean'],91.2)
    quality=next(t for t in parser.tables if len(t)>1 and 'Input Rows' in t[1] and 'Parsed' in t[1])
    row=dict(zip(quality[1],quality[2]));assert [int(row[k]) for k in ['Input Rows','Parsed','Invalid','Missing or Blank']]==[6,5,1,0]
    preview=next(t for t in parser.tables if len(t)>1 and 'UTC Datetime' in t[1])
    assert len(preview[2:])==6
    assert [dict(zip(preview[1],r))['Status'] for r in preview[2:]]==['Parsed']*4+['Invalid','Parsed']
    evidence['HTML']={'native_summary_quality_and_six_conversion_rows':'pass'}
    return evidence

if __name__=='__main__':print(json.dumps(check(),indent=2))
