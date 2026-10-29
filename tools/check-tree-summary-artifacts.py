"""Independently check native 0.3.39 node-summary export against its synthetic CSV."""
import csv
import json
import math
import runpy
import statistics
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
Tables=runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
saved_columns=runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']


def rounded_equal(text,value):
    if value is None:
        assert text in ('','.');return
    number=Decimal(text.replace('\u2009',''))
    tolerance=.5*10**number.as_tuple().exponent+1e-12
    assert math.isclose(float(number),value,rel_tol=0,abs_tol=tolerance),(text,value)


def check():
    with (ROOT/'data/python_tree_node_summary_examples.csv').open() as handle:
        records=list(csv.DictReader(handle))
    cohort=[r for r in records if r['Tumor'] and r['Grade']]
    parser=Tables();parser.feed((EXPORTS/'python-tree-summary-0.3.39-allnodes.html').read_text())
    nodes=next(t for t in parser.tables if len(t)>1 and 'Parent ID' in t[1])
    stats=next(t for t in parser.tables if len(t)>1 and 'Node Rows' in t[1])
    nh=nodes[1];sh=stats[1]
    indexed={int(row[nh.index('Node ID')]):dict(zip(nh,row)) for row in nodes[2:]}
    assert len(indexed)==len(stats[2:])==8 and len(cohort)==7
    for row in stats[2:]:
        record=dict(zip(sh,row));node=int(record['Node ID']);cursor=indexed[node];path=[]
        while cursor['Parent ID']!='.':
            path.append((cursor['Variable'],cursor['Category']));cursor=indexed[int(cursor['Parent ID'])]
        rows=[r for r in cohort if all(r[v]==label for v,label in path)]
        values=[float(r['MarkerScore']) for r in rows if r['MarkerScore']]
        assert int(record['Node Rows'])==len(rows)
        assert int(record['Valid'])==len(values)
        assert int(record['Missing'])==len(rows)-len(values)
        rounded_equal(record['Mean'],statistics.mean(values) if values else None)
        rounded_equal(record['SD'],statistics.stdev(values) if len(values)>1 else None)
    for location in ['leaves','allnodes']:
        metadata,_,columns=saved_columns(f'python-tree-summary-0.3.39-{location}.omv')
        assert metadata['rowCount']==8 and metadata['columnCount']==3
        scores=columns['MarkerScore']
        for actual,row in zip(scores,records):
            if row['MarkerScore']:assert actual==float(row['MarkerScore'])
            else:assert actual==-2147483648 or math.isnan(actual)
    original=saved_columns('python-variable-tree-paths-0.3.37-compact.omv')
    compatible=saved_columns('python-tree-summary-0.3.39-compatibility.omv')
    assert compatible[0]['rowCount']==original[0]['rowCount']==38
    assert compatible[1]==original[1] and compatible[2]==original[2]
    return dict(status='pass',nodes=8,input=8,categorical_complete=7,root_valid=4,root_missing=3,
                root_mean=18.5,root_sample_sd=math.sqrt(227/3),
                export_precision='compared at each native displayed rounding precision',saved_input_scores='unchanged',old_categorical_input_and_labels='unchanged')


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
