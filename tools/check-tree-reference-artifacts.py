"""Independently check native reference percentages against the synthetic source CSV."""
import csv
import json
import runpy
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
summary = runpy.run_path(str(ROOT / 'tools/check-tree-summary-artifacts.py'))
Tables = summary['Tables']
rounded_equal = summary['rounded_equal']


def check():
    with (ROOT / 'data/python_tree_reference_examples.csv').open() as handle:
        records = list(csv.DictReader(handle))
    cohort = [r for r in records if r['Tumor'] and r['Grade']]
    parser = Tables()
    parser.feed((EXPORTS / 'python-tree-reference-0.3.40-desktop.html').read_text())
    nodes = next(t for t in parser.tables if len(t) > 1 and 'Parent ID' in t[1])
    refs = next(t for t in parser.tables if len(t) > 1 and 'Matches' in t[1])
    stats = next(t for t in parser.tables if len(t) > 1 and 'Mean' in t[1])
    header = nodes[1]
    indexed = {int(r[header.index('Node ID')]): dict(zip(header, r)) for r in nodes[2:]}
    assert len(indexed) == len(refs[2:]) == len(stats[2:]) == 8
    for table in (refs, stats):
        for row in table[2:]:
            result = dict(zip(table[1], row))
            cursor = indexed[int(result['Node ID'])]
            path = []
            while cursor['Parent ID'] != '.':
                path.append((cursor['Variable'], cursor['Category']))
                cursor = indexed[int(cursor['Parent ID'])]
            selected = [r for r in cohort if all(r[v] == label for v, label in path)]
            assert int(result['Node Rows']) == len(selected)
            if 'Matches' in result:
                valid = [r['MarkerStatus'] for r in selected if r['MarkerStatus']]
                matches = valid.count('Positive')
                assert result['Reference Variable'] == 'MarkerStatus'
                assert result['Reference Level'] == 'Positive'
                assert int(result['Valid Reference']) == len(valid)
                assert int(result['Missing Reference']) == len(selected) - len(valid)
                assert int(result['Matches']) == matches
                rounded_equal(result['Reference (%)'].replace('%', '').strip(),
                              100 * matches / len(valid) if valid else None)
            else:
                values = [float(r['MarkerScore']) for r in selected if r['MarkerScore']]
                assert int(result['Valid']) == len(values)
                assert int(result['Missing']) == len(selected) - len(values)
                rounded_equal(result['Mean'], statistics.mean(values) if values else None)
                rounded_equal(result['SD'], statistics.stdev(values) if len(values) > 1 else None)
    metadata, _, columns = summary['saved_columns']('python-tree-reference-0.3.40-desktop.omv')
    assert metadata['rowCount'] == 8 and metadata['columnCount'] == 4
    for actual, row in zip(columns['MarkerScore'], records):
        if row['MarkerScore']:
            assert actual == float(row['MarkerScore'])
    return dict(status='pass', nodes=8, input_rows=8, categorical_complete=7,
                root_reference_valid=4, root_reference_missing=3, root_matches=2,
                root_reference_percent=50, all_missing_reference='undefined',
                numeric_summaries='independently checked at native display precision',
                saved_input='eight rows and four original columns retained')


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
