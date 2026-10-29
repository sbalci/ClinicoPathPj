"""Read-only validation of native 0.3.37 compact/full-path exports and OMV files."""
import csv
import json
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.table=[]
        if self.table is not None and tag=='tr':self.row=[]
        if self.row is not None and tag in ['td','th']:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ['td','th'] and self.cell is not None:
            self.row.append(''.join(self.cell).strip());self.cell=None
        if tag=='tr' and self.row is not None:self.table.append(self.row);self.row=None
        if tag=='table' and self.table is not None:self.tables.append(self.table);self.table=None


def table(kind):
    parser=Tables();parser.feed((EXPORTS/f'python-variable-tree-paths-0.3.37-{kind}.html').read_text())
    return next(t[1:] for t in parser.tables if len(t)>1 and 'Node ID' in t[1])


def check():
    compact=table('compact');expanded=table('expanded')
    assert len(compact)==len(expanded)==16  # header and all 15 nodes
    assert 'Branch Path' not in compact[0]
    assert 'Branch Path' in expanded[0]
    path_column=expanded[0].index('Branch Path')
    assert [[v for j,v in enumerate(row) if j!=path_column] for row in expanded]==compact
    with (ROOT/'data/python_variable_tree_examples.csv').open() as handle:
        cohort=[row for row in csv.DictReader(handle) if all(row.values())]
    assert len(cohort)==36
    count_column=expanded[0].index('Count')
    paths=[]
    for row in expanded[1:]:
        path=json.loads(row[path_column]);paths.append(row[path_column])
        count=sum(all(record[name]==level for name,level in path) for record in cohort)
        assert int(row[count_column])==count
    for kind in ['compact','expanded']:
        with zipfile.ZipFile(EXPORTS/f'python-variable-tree-paths-0.3.37-{kind}.omv') as archive:
            assert archive.testzip() is None
            metadata=json.loads(archive.read('metadata.json'))['dataSet']
            assert metadata['rowCount']==38 and metadata['columnCount']==3
            analysis=archive.read(next(n for n in archive.namelist() if 'pyvartree' in n and n.endswith('/analysis')))
            assert all(path.encode('utf-8') in analysis for path in paths)
    return dict(status='pass',nodes=15,complete=36,compact_columns=9,expanded_columns=10,
                native_export_counts='independent CSV-prefix agreement',all_paths_retained_in_both_OMV=True)


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
