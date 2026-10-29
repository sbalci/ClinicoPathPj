"""Read-only native HTML/OMV checks against source fixtures and independent UTC arithmetic."""
import csv
import json
import math
import runpy
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
rounded_equal=runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']
MISSING=-2147483648
NAMES=['Unix epoch seconds (UTC)','Standardized UTC datetime labels','Year (UTC)','Week (Jan-1 blocks) (UTC)']


def values(name,labels,columns):
    mapping={v[0]:v[1] for v in labels.get(name,{}).get('labels',[])}
    return [None if v==MISSING or isinstance(v,float) and math.isnan(v) else mapping.get(v,v) for v in columns[name]]


def check_sources(metadata,labels,columns,records):
    assert metadata['rowCount']==12 and metadata['columnCount']==8
    assert values('Record',labels,columns)==[r['Record'] for r in records]
    assert values('Calendar text',labels,columns)==[r['Calendar text'] or None for r in records]
    for name in ('Excel serial','Unix seconds'):
        for actual,row in zip(values(name,labels,columns),records):
            if row[name]:assert float(actual)==float(row[name])
            else:assert actual is None
    fields={f['name']:f for f in metadata['fields']}
    for name in NAMES:assert fields[name]['columnType']=='Output'
    assert all(f['name'].strip() and not f['name'].startswith(' (') for f in metadata['fields'])


def check():
    with (ROOT/'data/python_datetime_examples.csv').open() as handle:records=list(csv.DictReader(handle))
    utc=timezone.utc;epoch=datetime(1970,1,1,tzinfo=utc);evidence={}
    for state in ('calendar','excel'):
        source='Calendar text' if state=='calendar' else 'Excel serial'
        expected=[];statuses=[]
        for row in records:
            raw=row[source]
            if not raw:date=None;status='Missing'
            else:
                try:
                    date=(datetime.strptime(raw,'%Y-%m-%d').replace(tzinfo=utc) if state=='calendar'
                          else datetime(1899,12,30,tzinfo=utc)+timedelta(seconds=round(float(raw)*86400)))
                    status='Parsed'
                except ValueError:date=None;status='Invalid'
            expected.append(date);statuses.append(status)
        stem=f'python-datetime-0.3.45-{state}'
        metadata,labels,columns=saved_columns(stem+'.omv');check_sources(metadata,labels,columns,records)
        expected_epoch=[None if d is None else (d-epoch).total_seconds() for d in expected]
        actual=values(NAMES[0],labels,columns)
        for got,want in zip(actual,expected_epoch):
            if want is None:assert got is None
            else:assert float(got)==want
        assert values(NAMES[1],labels,columns)==[None if d is None else d.isoformat().replace('+00:00','Z') for d in expected]
        assert values(NAMES[2],labels,columns)==[None if d is None else d.year for d in expected]
        assert values(NAMES[3],labels,columns)==[None if d is None else (d.timetuple().tm_yday-1)//7+1 for d in expected]
        parser=Tables();parser.feed((EXPORTS/(stem+'.html')).read_text())
        quality=next(t for t in parser.tables if len(t)>1 and 'Success Among Nonmissing (%)' in t[1])
        q=dict(zip(quality[1],quality[2]));parsed=statuses.count('Parsed');invalid=statuses.count('Invalid');missing=statuses.count('Missing')
        assert [int(q[k]) for k in ('Input Rows','Parsed','Invalid','Missing or Blank')]==[12,parsed,invalid,missing]
        rounded_equal(q['Success Among Nonmissing (%)'].replace('%','').strip(),100*parsed/(12-missing))
        preview=next(t for t in parser.tables if len(t)>1 and 'Source Row ID' in t[1])
        assert len(preview[2:])==12
        for i,row in enumerate(preview[2:]):
            r=dict(zip(preview[1],row));assert r['Source Row ID']==str(i+1);assert r['Status']==statuses[i]
            if expected[i] is None:assert r['UTC Datetime'] in ('','.');continue
            assert r['UTC Datetime']==expected[i].isoformat().replace('+00:00','Z')
            assert int(r['Year'])==expected[i].year
            assert int(r['Week (Jan-1 blocks, not ISO)'])==(expected[i].timetuple().tm_yday-1)//7+1
        evidence[state]=dict(parsed=parsed,invalid=invalid,missing=missing,
            saved_output='Four named columns match independent UTC/calendar arithmetic on every source row',
            source='All 12 original profiles, four input columns and row order preserved')
    metadata,labels,columns=saved_columns('python-datetime-0.3.45-unparsed.omv')
    check_sources(metadata,labels,columns,records)
    assert all(v is None for name in NAMES for v in values(name,labels,columns))
    return dict(status='pass',states=evidence,unparsed='All four saved outputs missing for all 12 rows; original values unchanged')


if __name__=='__main__':print(json.dumps(check(),indent=2))
