"""Read-only native HTML/PNG/OMV checks using independent source-CSV counts."""
import csv
import json
import runpy
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
Tables = runpy.run_path(str(ROOT / 'tools/check-tree-path-artifacts.py'))['Tables']
saved_columns = runpy.run_path(str(ROOT / 'tools/check-native-core-artifacts.py'))['saved_columns']
rounded_equal = runpy.run_path(str(ROOT / 'tools/check-tree-summary-artifacts.py'))['rounded_equal']


def check():
    with (ROOT / 'data/python_alluvial_examples.csv').open() as handle:
        records = list(csv.DictReader(handle))
    names = list(records[0])
    cohort = [r for r in records if all(r.values())]
    expected = Counter(tuple(r[v] for v in names) for r in cohort)
    parser = Tables()
    parser.feed((EXPORTS / 'python-alluvial-0.3.41-desktop.html').read_text())
    flows = next(t for t in parser.tables if len(t) > 1 and 'Flow ID' in t[1])
    categories = next(t for t in parser.tables if len(t) > 1 and 'Axis' in t[1])
    actual = {}
    for row in flows[2:]:
        entry = dict(zip(flows[1], row))
        key = tuple(json.loads(entry['Category Path (JSON)']))
        actual[key] = int(entry['Rows'])
        rounded_equal(entry['Retained (%)'].replace('%', '').strip(), 100*expected[key]/len(cohort))
    assert actual == expected
    assert [int(r[flows[1].index('Rows')]) for r in flows[2:]] == [12, 5, 2, 1]
    assert len(categories[2:]) == 6
    for row in categories[2:]:
        entry = dict(zip(categories[1], row))
        count = sum(r[entry['Variable']] == entry['Category'] for r in cohort)
        assert int(entry['Rows']) == count
        assert names[int(entry['Axis'])-1] == entry['Variable']
        rounded_equal(entry['Retained (%)'].replace('%', '').strip(), 100*count/len(cohort))
    metadata, labels, columns = saved_columns('python-alluvial-0.3.41-desktop.omv')
    assert metadata['rowCount'] == 22 and metadata['columnCount'] == 3
    for name in names:
        mapping = {r[0]: r[1] for r in labels[name]['labels']}
        restored = ['' if code == -2147483648 else mapping[code] for code in columns[name]]
        assert restored == [r[name] for r in records]
    raw = (EXPORTS / 'python-alluvial-0.3.41-desktop.png').read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    size = struct.unpack('>II', raw[16:24]); assert size == (2200, 1400)
    return dict(status='pass', input_rows=22, retained_complete=20, excluded=2,
                native_path_counts=[12,5,2,1], marginal_categories=6,
                saved_input='all source values and row order retained', png_dimensions=size,
                percentages='independent CSV counts at native display precision')


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
