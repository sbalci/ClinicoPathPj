"""Inspect saved GUI summary examples without executing their contents.

This verifies persisted display values and source data. Numerical agreement and
desktop actions are separate evidence; the display rounds sample SD to 3.54.
"""
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
EXPECTED = [['Summary'],
            ['Input rows', 'N', 'Missing', 'Mean', 'Sample SD', 'Median', 'Minimum', 'Maximum'],
            ['6', '5', '1', '4.00', '3.54', '3.00', '1.00', '10.0']]
LIMIT = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Tables(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tables, self.parts = [], []
        self.rows = self.row = self.cell = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.rows = []
        elif tag == 'tr' and self.rows is not None:
            self.row = []
        elif tag in ('th', 'td') and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        self.parts.append(data)
        if self.cell is not None:
            self.cell.append(data)

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


def inspect_html(html):
    parsed = Tables(html)
    require(parsed.tables == [EXPECTED, EXPECTED], 'Expected two identical native summaries')
    text = re.sub(r'\s+', ' ', ' '.join(parsed.parts))
    for marker in ('Own Python Summary Example', 'Pj Service Summary Example',
                   'ClinicoPathPj launches its own Python subprocess.',
                   'no editor opens.',
                   'Pj 1.5.0; runner: processx; checkpoint enabled; shared call timeout.'):
        require(marker in text, 'Missing execution-route detail: ' + marker)
    require('Python stopped' not in text, 'Unexpected execution failure')
    times = re.findall(r'Route: (processx|pj); backend elapsed: ([0-9.]+) s\.', text)
    require([route for route, _ in times] == ['processx', 'pj'], 'Missing route timings')
    return {route: float(seconds) for route, seconds in times}


def read(archive, name):
    require(archive.getinfo(name).file_size <= LIMIT, 'Oversized archive member: ' + name)
    return archive.read(name)


def negative_probes(html):
    probes = {
        'wrong_mean': html.replace('4.00', '9.00', 1),
        'wrong_sd': html.replace('3.54', '9.54', 1),
        'missing_table': re.sub(r'<table\b.*?</table>', '', html, count=1, flags=re.S),
        'missing_service_identity': html.replace(
            'Pj 1.5.0; runner: processx; checkpoint enabled; shared call timeout.',
            'unverified service'),
    }
    for name, changed in probes.items():
        require(changed != html, 'Probe did not alter the fixture: ' + name)
        try:
            inspect_html(changed)
        except ValueError:
            continue
        raise ValueError('Corrupted HTML was accepted: ' + name)
    return list(probes)


def check():
    with zipfile.ZipFile(ROOT / 'data/python_service_examples.omv') as source:
        original = {name: read(source, name) for name in ('data.bin', 'xdata.json')}
        metadata = json.loads(read(source, 'metadata.json'))['dataSet']
    records = []
    for suffix in ('comparison', 'reopened'):
        path = EXPORTS / f'python-summary-service-0.3.62-{suffix}.omv'
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, 'Archive CRC check failed')
            require(len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate members')
            for name, expected in original.items():
                actual = read(archive, name)
                if name == 'xdata.json':
                    # jmvReadWrite emits [] for this numeric-only fixture; the
                    # jamovi writer emits {}. Neither contains factor labels.
                    require(json.loads(expected) == [] and json.loads(actual) == {},
                            'Unexpected labels in the numeric-only source data')
                else:
                    require(actual == expected, 'Source data changed: ' + name)
            require(json.loads(read(archive, 'metadata.json'))['dataSet'] == metadata,
                    'Source dataset metadata changed')
            for name in ('pyservicedirect', 'pyservicepj'):
                members = [m for m in archive.namelist()
                           if re.fullmatch(r'\d+ ' + name + '/analysis', m)]
                require(len(members) == 1, 'Expected one saved ' + name + ' analysis')
                raw = read(archive, members[0])
                require(b'ClinicoPathPj' in raw and b'Measurement' in raw,
                        'Missing host identity or selected variable')
            times = inspect_html(read(archive, 'index.html').decode())
        html_path = path.with_suffix('.html')
        html = html_path.read_text()
        require(inspect_html(html) == times, 'Export differs from saved timings')
        records.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            html_sha256=hashlib.sha256(html_path.read_bytes()).hexdigest(),
                            backend_seconds=times))
    require(all(records[0]['backend_seconds'][route] != records[1]['backend_seconds'][route]
                for route in ('processx', 'pj')), 'Expected fresh timings after both reruns')
    return dict(status='pass', source_data_unchanged=True, rows=6, columns=1,
                label_normalization='Empty jmvReadWrite [] to empty jamovi {}; no labels',
                saved_files=records, native_tables_per_file=2,
                negative_html_probes_rejected=negative_probes(html),
                scope='Persisted display/data checks; GUI observations and numerical oracles separate',
                performance_benchmark=False)


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
