"""Check curated workbook manifests without modifying saved data, options or results."""
import csv
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    root=Path(root);data=root/'data'
    with (data/'saved-analysis-examples.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
    assert rows,'No curated workbooks registered'
    assert len({r['file'] for r in rows})==len(rows),'Duplicate curated workbook'
    report=[]
    for row in rows:
        name=row['file'];assert re.fullmatch(r'python_[a-z0-9_]+_examples\.omv',name),name
        assert re.fullmatch(r'\d+\.\d+\.\d+',row['saved_module_version']),name
        p=data/name;blob=p.read_bytes();digest=hashlib.sha256(blob).hexdigest()
        assert digest==row['sha256'],name+' checksum mismatch'
        analyses=row['analyses'].split(',')
        assert all(re.fullmatch(r'py[A-Za-z0-9]+',n) for n in analyses),name
        with ZipFile(p) as z:
            assert z.testzip() is None,name+' CRC failure'
            names=z.namelist();assert len(names)==len(set(names)),name+' duplicate members'
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names),name
            for required in ('data.bin','metadata.json','xdata.json','index.html'):assert required in names,(name,required)
            entries=[n for n in names if n.endswith('/analysis')]
            for analysis in analyses:
                matched=[n for n in entries if n.split('/')[-2].endswith(' '+analysis)]
                assert len(matched)==1,(name,analysis,matched)
                assert analysis.encode() in z.read(matched[0]),(name,analysis)
        report.append(dict(file=name,analyses=analyses,bytes=len(blob),sha256=digest))
    return dict(workbooks=len(rows),analyses=sum(len(r['analyses']) for r in report),entries=report,
        scope='Curated ZIP integrity, manifest hashes and saved analysis presence; numerical and GUI evidence separate')


if __name__=='__main__':print(json.dumps(verify(),indent=2))
