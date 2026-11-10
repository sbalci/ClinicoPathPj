"""Read-only checks of GUI-produced age-pyramid persistence/export artifacts."""
import hashlib
import json
import re
import struct
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
EXPECTED = [('0-4', 2, 1, 3), ('5-9', 1, 2, 3), ('10-14', 1, 3, 4),
            ('15-19', 1, 0, 1), ('20-24', 2, 2, 4), ('65-69', 0, 1, 1),
            ('85+', 1, 1, 2), ('Total', 8, 10, 18)]


class Tables(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tables = []
        self.parts = []
        self.rows = None
        self.row = None
        self.cell = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'table': self.rows = []
        elif tag == 'tr' and self.rows is not None: self.row = []
        elif tag in ('th', 'td') and self.row is not None: self.cell = []

    def handle_data(self, data):
        self.parts.append(data)
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.cell is not None:
            self.row.append(re.sub(r'\s+', ' ', ''.join(self.cell)).strip())
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == 'table' and self.rows is not None:
            self.tables.append(self.rows)
            self.rows = None


def validate_html(html):
    parsed = Tables(html)
    populations = []
    for table in parsed.tables:
        rows = []
        for row in table:
            if len(row) >= 4 and row[0] in {r[0] for r in EXPECTED}:
                rows.append((row[0], *map(int, row[1:4])))
        if rows: populations.append(rows)
    assert populations == [EXPECTED, EXPECTED], populations
    text = re.sub(r'\s+', ' ', ' '.join(parsed.parts))
    assert 'Age Pyramid via Pj' in text
    assert 'Pj 1.5.0; runner: processx; checkpoint enabled; shared call timeout.' in text
    assert 'Python stopped' not in text
    return text


def label_contract(raw):
    document = json.loads(raw)
    for column in document.values():
        for i, row in enumerate(column.get('labels', [])):
            # This jamovi writer adds two false flags to jmvReadWrite's four fields.
            assert len(row) in (4, 6) and all(value is False for value in row[4:])
            column['labels'][i] = row[:4]
    return document


def check():
    with zipfile.ZipFile(ROOT/'data/python_age_pyramid_service_examples.omv') as source:
        original = {name: source.read(name) for name in ('data.bin', 'xdata.json', 'strings.bin')}
    records = []
    for suffix in ('comparison', 'reopened'):
        filename = f'python-age-pyramid-0.3.62-{suffix}.omv'
        path = EXPORTS / filename
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for name, raw in original.items():
                actual = archive.read(name)
                assert (label_contract(actual) == label_contract(raw) if name.endswith('.json')
                        else actual == raw), (suffix, name)
            metadata = json.loads(archive.read('metadata.json'))['dataSet']
            assert (metadata['rowCount'], metadata['columnCount']) == (22, 3)
            for member in ('02 pyagepyramid/analysis', '04 pyagepyramidpj/analysis'):
                assert b'ClinicoPathPj' in archive.read(member)
            validate_html(archive.read('index.html').decode())
            pngs = [n for n in archive.namelist() if n.endswith('.png')]
            assert len(pngs) == 2
            dimensions = {}
            for name in pngs:
                raw = archive.read(name)
                assert raw.startswith(b'\x89PNG\r\n\x1a\n')
                dimensions[name] = struct.unpack('>II', raw[16:24])
                assert min(dimensions[name]) > 0
            html = (EXPORTS / filename.replace('.omv', '.html')).read_text()
            validate_html(html)
            assert len(re.findall('data:image/png;base64,', html)) == 2
        records.append(dict(file=filename, rows=22, columns=3, native_pngs=dimensions,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return dict(status='pass', saved_files=records, source_data_unchanged=True,
                expected_female=8, expected_male=10, expected_retained=18,
                scope='Persisted native GUI artifacts; independent numerical/GUI observations are separate')


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
