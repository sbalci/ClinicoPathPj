"""Read-only checks of the synthetic 0.3.36 artifacts saved/exported by native jamovi.

This checks persisted bytes; it does not synthesize GUI lifecycle evidence.
Run from any directory: python3 tools/check-native-core-artifacts.py
"""
import json
import struct
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'docs/validation-exports'
MISSING=-2147483648


def saved_columns(name):
    with zipfile.ZipFile(ROOT/name) as archive:
        assert archive.testzip() is None
        metadata=json.loads(archive.read('metadata.json'))['dataSet']
        labels=json.loads(archive.read('xdata.json'))
        raw=archive.read('data.bin')
    n=metadata['rowCount'];offset=0;columns={}
    for field in metadata['fields']:
        kind='d' if field['type']=='number' else 'i'
        length=struct.calcsize(kind)*n
        columns[field['name']]=struct.unpack('<'+kind*n,raw[offset:offset+length]);offset+=length
    assert offset==len(raw)
    return metadata,labels,columns


def check():
    original,_,original_columns=saved_columns('python-variable-tree-0.3.35-import-failure.omv')
    assert original['rowCount']==38
    assert sum(all(original_columns[v][i]!=MISSING for v in original_columns) for i in range(38))==34
    tree,labels,columns=saved_columns('python-variable-tree-0.3.36-desktop.omv')
    assert tree['rowCount']==38 and tree['columnCount']==3
    assert sum(all(columns[v][i]!=MISSING for v in columns) for i in range(38))==36
    assert 'Type C' in [row[1] for row in labels['Tumor']['labels']]
    outlier,labels,columns=saved_columns('python-outlier-screening-0.3.36-desktop.omv')
    assert outlier['rowCount']==33 and outlier['columnCount']==3
    flags=columns['Univariate screening flag']
    assert flags==(1,)*30+(2,MISSING,MISSING)
    assert next(v for v in outlier['fields'] if v['name']=='Univariate screening flag')['measureType']=='Nominal'
    assert [row[1] for row in labels['Univariate screening flag']['labels']]==['Not flagged','Flagged']
    sizes={}
    for name,expected in [('python-variable-tree-0.3.36-native.png',(2000,1300)),('python-outlier-distributions-0.3.36-native.png',(2000,1600))]:
        raw=(ROOT/name).read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
        size=struct.unpack('>II',raw[16:24]);assert size==expected;sizes[name]=size
    return dict(status='pass',original_tree_complete=34,tree=dict(input=38,complete=36,excluded=2),
                screening=dict(input=33,not_flagged=30,flagged=1,missing=2),png_dimensions=sizes)


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
