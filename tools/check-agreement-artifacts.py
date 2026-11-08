"""Read-only checks of synthetic agreement files saved/exported through jamovi."""
import base64
import csv
import json
import math
from pathlib import Path
import re
import runpy
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
STEM = 'python-agreement-0.3.58-'
saved_columns = runpy.run_path(str(ROOT / 'tools/check-native-core-artifacts.py'))['saved_columns']
Tables = runpy.run_path(str(ROOT / 'tools/check-tree-path-artifacts.py'))['Tables']


def check():
    with (ROOT / 'data/python_agreement_examples.csv').open() as stream:
        fixture = list(csv.DictReader(stream))
    evidence = {}
    for state in ['valid', 'reopened']:
        name = STEM + state + '.omv'
        metadata, labels, columns = saved_columns(name)
        assert metadata['rowCount'] == 12 and metadata['columnCount'] == 3
        with zipfile.ZipFile(EXPORTS / name) as archive:
            assert archive.testzip() is None
            strings = archive.read('strings.bin')
            images = [n for n in archive.namelist() if n.endswith('.png')]
            assert len(images) == 1
        for field in metadata['fields']:
            key = field['name']
            if field['type'] == 'string':
                actual = [None if v == -2147483648 else strings[v:].split(b'\0', 1)[0].decode()
                          for v in columns[key]]
                expected = [r[key] or None for r in fixture]
            else:
                mapping = {r[0]: r[1] for r in labels.get(key, {}).get('labels', [])}
                actual = [None if math.isnan(v) or v == -2147483648 else mapping.get(v, v)
                          for v in columns[key]]
                expected = [float(r[key]) if r[key] else None for r in fixture]
            assert actual == expected, (state, key)
        evidence[state] = dict(rows=12, columns=3, native_images=1, original_data='pass')
    html = (EXPORTS / (STEM + 'reopened.html')).read_text()
    parser = Tables()
    parser.feed(html)
    table = lambda title: next(t for t in parser.tables if t[0] == [title])
    assert list(map(int, table('Paired Observation Audit')[2])) == [12, 8, 4, 1, 2, 1]
    expected = [[0, -2.86, 2.86], [3.42], [-6.71, -11.82, -1.59], [6.71, 1.59, 11.82]]
    for row, values in zip(table('Bland-Altman Estimates')[2:6], expected):
        assert list(map(float, row[1:1 + len(values)])) == values
    pairs = table('Complete Independent Pairs')[2:]
    assert [int(r[0]) for r in pairs] == list(range(1, 9))
    assert [r[1] for r in pairs] == [r['Case'] for r in fixture[:8]]
    assert [float(r[5]) for r in pairs] == [1, 2, -1, 3, -5, 1, -5, 4]
    images = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)', html)
    assert len(images) == 1
    raw = base64.b64decode(images[0])
    assert struct.unpack('>II', raw[16:24]) == (1277, 958)
    assert raw == (EXPORTS / (STEM + 'reopened.png')).read_bytes()
    evidence['export'] = dict(audit=[12, 8, 4, 1, 2, 1], source_rows=list(range(1, 9)),
                              rounded_estimates='pass', png_dimensions=[1277, 958])
    return evidence


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
