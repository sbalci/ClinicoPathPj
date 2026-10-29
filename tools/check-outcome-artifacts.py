"""Check native saved/HTML outcome artifacts against independent source-row rules."""
import csv
import json
import runpy
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
rounded_equal=runpy.run_path(str(ROOT/'tools/check-tree-summary-artifacts.py'))['rounded_equal']
MISSING=-2147483648


def restored(name,labels,columns):
    mapping={r[0]:r[1] for r in labels[name]['labels']}
    return [None if v==MISSING else mapping[v] for v in columns[name]]


def check():
    with (ROOT/'data/python_outcome_examples.csv').open() as handle:
        records=list(csv.DictReader(handle))
    states=['Alive without disease','Alive with disease','Dead of disease','Dead of other causes']
    evidence={}
    for label,codes in [('competing',[0,0,1,2]),('multistate',[0,1,2,3])]:
        mapping=dict(zip(states,codes))
        expected=[None if not r['Vital status'] else mapping[r['Vital status']] for r in records]
        stem=f'python-outcome-coding-0.3.44-{label}'
        metadata,labels,columns=saved_columns(stem+'.omv')
        assert metadata['rowCount']==13 and metadata['columnCount']==3
        assert restored('Record',labels,columns)==[r['Record'] for r in records]
        assert restored('Vital status',labels,columns)==[r['Vital status'] or None for r in records]
        saved=restored('Recoded survival outcome',labels,columns)
        output_labels=['Censored','Event','Competing'] if label=='competing' else ['0','1','2','3']
        assert saved==[None if v is None else output_labels[v] for v in expected]
        output=next(f for f in metadata['fields'] if f['name']=='Recoded survival outcome')
        assert output['columnType']=='Output' and output['measureType']=='Nominal'
        html=(EXPORTS/(stem+'.html')).read_text();parser=Tables();parser.feed(html)
        frequency=next(t for t in parser.tables if len(t)>1 and 'Coded Rows (%)' in t[1])
        assert len(frequency[2:])==len(output_labels)
        for row in frequency[2:]:
            item=dict(zip(frequency[1],row));code=int(item['Status Code']);n=expected.count(code)
            assert int(item['Count'])==n
            rounded_equal(item['Coded Rows (%)'].replace('%','').strip(),100*n/12)
        preview=next(t for t in parser.tables if len(t)>1 and 'Source Row ID' in t[1])
        assert [row[0] for row in preview[2:]]==[str(i) for i in range(1,14)]
        assert [None if row[1] in ('','.') else int(row[1]) for row in preview[2:]]==expected
        assert 'Input rows: 13; coded: 12; missing outcome: 1' in html
        assert 'data:image/png;base64,' in html
        evidence[label]=dict(input=13,coded=12,missing=1,counts=[expected.count(i) for i in range(len(output_labels))],saved_status='All source rows and missingness agree with independent mapping')
    meta,labels,columns=saved_columns('python-outcome-coding-0.3.44-invalid.omv')
    assert meta['rowCount']==13
    assert all(v==MISSING for v in columns['Recoded survival outcome'])
    assert restored('Vital status',labels,columns)==[r['Vital status'] or None for r in records]
    raw=(EXPORTS/'python-outcome-coding-0.3.44-native.png').read_bytes()
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    size=struct.unpack('>II',raw[16:24]);assert size[0]>0 and size[1]>0
    return dict(status='pass',states=evidence,invalid_output='All 13 saved statuses cleared; source values unchanged',native_png_dimensions=size)


if __name__=='__main__':print(json.dumps(check(),indent=2))
