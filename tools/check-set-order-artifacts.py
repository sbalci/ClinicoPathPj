"""Independent CSV checks of native 0.3.38 set-order exports and saved outputs."""
import csv
import json
import runpy
import struct
import zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
MISSING=-2147483648
VARIABLES=['Marker_A','Marker_B','Marker_C','Marker_D']


def saved(name):
    with zipfile.ZipFile(EXPORTS/name) as archive:
        assert archive.testzip() is None
        metadata=json.loads(archive.read('metadata.json'))['dataSet']
        labels=json.loads(archive.read('xdata.json'));raw=archive.read('data.bin')
    n=metadata['rowCount'];columns={};offset=0
    for field in metadata['fields']:
        assert field['type']=='integer'
        columns[field['name']]=struct.unpack('<'+'i'*n,raw[offset:offset+4*n]);offset+=4*n
    assert n==62 and offset==len(raw)
    decoded={name:[None if v==MISSING else {r[0]:r[1] for r in labels[name]['labels']}[v] for v in values]
             for name,values in columns.items()}
    return columns,labels,decoded


def check():
    with (ROOT/'data/python_set_intersection_unequal_examples.csv').open() as handle:
        records=list(csv.DictReader(handle))
    expected=[None if any(not r[v] for v in VARIABLES) else ''.join('1' if r[v]=='Positive' else '0' for v in VARIABLES) for r in records]
    counts=Counter(v for v in expected if v is not None)
    canonical=[''.join(str((code>>j)&1) for j in range(4)) for code in range(16)]
    frequency=sorted(canonical,key=lambda p:(-counts[p],canonical.index(p)))
    original=saved('python-set-matrix-unequal-0.3.30-desktop.omv')
    for order,patterns in [('membership',canonical),('frequency',frequency)]:
        columns,labels,decoded=saved(f'python-set-order-0.3.38-{order}.omv')
        assert columns==original[0] and labels==original[1]
        assert decoded['Set membership pattern']==expected
        assert all(decoded[v]==[r[v] or None for r in records] for v in VARIABLES)
        parser=Tables();parser.feed((EXPORTS/f'python-set-order-0.3.38-{order}.html').read_text())
        table=next(t for t in parser.tables if len(t)>1 and 'Pattern' in t[1] and 'Rows' in t[1])
        header=table[1];rows=table[2:];pi=header.index('Pattern');ni=header.index('Rows')
        assert [r[pi] for r in rows]==patterns
        assert [int(r[ni]) for r in rows]==[counts[p] for p in patterns]
        assert sum(int(r[ni]) for r in rows)==60
        sets=next(t for t in parser.tables if len(t)>1 and 'Members' in t[1])
        h=sets[1]
        for j,row in enumerate(sets[2:]):
            assert row[h.index('Variable')]==VARIABLES[j]
            assert int(row[h.index('Members')])==sum(r[VARIABLES[j]]=='Positive' for r in records if all(r[v] for v in VARIABLES))
            assert int(row[h.index('Missing in Input')])==sum(not r[VARIABLES[j]] for r in records)
    png=(EXPORTS/'python-set-order-0.3.38-frequency.png').read_bytes()
    assert png[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',png[16:24])==(1800,1200)
    return dict(status='pass',input=62,complete=60,excluded=2,patterns=16,
                frequency_order=frequency,frequency_counts=[counts[p] for p in frequency],
                saved_codes_and_labels_unchanged=True,original_fixture='0.3.30',native_matrix_png=[1800,1200])


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
