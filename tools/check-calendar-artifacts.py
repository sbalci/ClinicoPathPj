"""Read-only calendar/standardized native artifact checks independent of the Python engine."""
import csv,json,math,runpy
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
rounded_equal=runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']


def check():
    with (ROOT/'data/python_calendar_interval_examples.csv').open() as f:source=list(csv.DictReader(f))
    calendar=[1.,1.,1+1/31,12.,28/29,None]
    evidence={}
    for basis in ['standardized','calendar']:
        stem='python-calendar-0.3.47-'+basis
        m,l,c=saved_columns(stem+'.omv')
        assert m['rowCount']==6 and m['columnCount']==4
        for name in source[0]:
            mapping={row[0]:row[1] for row in l[name]['labels']}
            values=[None if v==-2147483648 else mapping[v] for v in c[name]]
            assert values==[r[name] or None for r in source],name
        want=calendar if basis=='calendar' else [((date.fromisoformat(r['End date'])-date.fromisoformat(r['Start date'])).days/30.4375) if r['End date'] else None for r in source]
        got=[None if math.isnan(v) else v for v in c['Calculated interval']]
        for a,b in zip(got,want):
            if b is None:assert a is None
            else:assert math.isclose(a,b,abs_tol=1e-12)
        field=next(f for f in m['fields'] if f['name']=='Calculated interval')
        assert field['columnType']=='Output' and field['measureType']=='Continuous'
        assert f'basis: {basis}' in field['description']
        evidence[basis]={'used':5,'values':got,'basis_metadata':'pass'}
    old=saved_columns('python-interval-0.3.46-excluded.omv')
    new=saved_columns('python-calendar-0.3.47-legacy.omv')
    assert old[0]['rowCount']==new[0]['rowCount']==12
    for name,values in old[2].items():
        assert len(values)==len(new[2][name])
        for a,b in zip(values,new[2][name]):assert a==b or isinstance(a,float) and math.isnan(a) and math.isnan(b)
    evidence['legacy']={'all_source_and_saved_values_unchanged':'pass'}
    parser=Tables();parser.feed((EXPORTS/'python-calendar-0.3.47-calendar.html').read_text())
    summary=next(t for t in parser.tables if len(t)>1 and 'Summed Record-Time' in t[1])
    s=dict(zip(summary[1],summary[2]));assert int(s['N'])==5 and s['Unit']=='months'
    rounded_equal(s['Summed Record-Time'],sum(calendar[:-1]));rounded_equal(s['Mean'],sum(calendar[:-1])/5)
    preview=next(t for t in parser.tables if len(t)>1 and 'Disposition' in t[1])
    assert len(preview[2:])==6
    for i,row in enumerate(preview[2:]):
        r=dict(zip(preview[1],row));assert r['Source Row ID']==str(i+1)
        if calendar[i] is None:assert r['Used Interval'] in ('.','')
        else:rounded_equal(r['Used Interval'],calendar[i])
    evidence['html']={'summary_and_six_source_rows':'pass'}
    return evidence

if __name__=='__main__':print(json.dumps(check(),indent=2))
