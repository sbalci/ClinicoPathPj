"""Read-only checks of native 0.3.60 service-comparison persistence/export artifacts."""
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs/validation-exports'


class Text(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts = []
        self.feed(html)

    def handle_data(self, data):
        self.parts.append(data)


def check():
    baseline = ROOT / 'python-bridge-comparison-0.3.8-validation.omv'
    with zipfile.ZipFile(baseline) as archive:
        original = {name: archive.read(name) for name in ('data.bin', 'xdata.json')}
    results = []
    for suffix, cutoff in [('cutoff4', 4), ('reopened', 3)]:
        path = ROOT / f'python-pj-service-0.3.60-{suffix}.omv'
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for name, raw in original.items():
                assert archive.read(name) == raw, (suffix, name)
            metadata = json.loads(archive.read('metadata.json'))['dataSet']
            assert (metadata['rowCount'], metadata['columnCount']) == (6, 3)
            assert '02 pybridgecompare/analysis' in archive.namelist()
            html = archive.read('index.html').decode()
            text = re.sub(r'\s+', ' ', ' '.join(Text(html).parts))
            assert ('Applied Cutoff Classification Classification Count '
                    'True positive 2 False positive 1 False negative 1 True negative 2') in text
            assert f'Measurement &gt;= {cutoff}.0' in html or f'Measurement >= {cutoff}.0' in text
            assert 'Pj 1.5.0; runner: processx; checkpoint enabled; shared call timeout.' in text
            if suffix == 'reopened':
                assert 'Running cancellation requires Pj 1.5.0' in text
                assert 'no checkpoint callback' not in text
            pngs = [name for name in archive.namelist() if name.endswith('.png')]
            assert len(pngs) == 2
            for name in pngs:
                assert archive.read(name).startswith(b'\x89PNG\r\n\x1a\n')
        results.append(dict(file=path.name, cutoff=cutoff, rows=6, native_pngs=2,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    exported = ROOT / 'python-pj-service-0.3.60-reopened.html'
    html = exported.read_text()
    text = ' '.join(Text(html).parts)
    assert 'Pj 1.5.0; runner: processx; checkpoint enabled; shared call timeout.' in text
    assert 'Running cancellation requires Pj 1.5.0' in text
    assert len(re.findall('data:image/png;base64,', html)) == 2
    return dict(status='pass', saved_files=results, native_html=exported.name,
                source_data_unchanged=True, scope='Persisted artifacts; not independent GUI or cleanup evidence')


def check_system_artifacts():
    with zipfile.ZipFile(ROOT / 'python-pj-service-0.3.60-reopened.omv') as archive:
        original = {name: archive.read(name) for name in ('data.bin', 'xdata.json')}
    files = []
    alias = "System Python currently resolves to jamovi's bundled interpreter."
    for suffix in ['startup-error', 'alias-error', 'recovered']:
        path = ROOT / f'python-system-0.3.61-{suffix}.omv'
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for name, raw in original.items():
                assert archive.read(name) == raw
            text = re.sub(r'\s+', ' ', ' '.join(Text(archive.read('index.html').decode()).parts))
            pngs = [name for name in archive.namelist() if name.endswith('.png')]
            if suffix == 'startup-error':
                assert 'No module named' in text and 'encodings' in text
                assert not pngs
            elif suffix == 'alias-error':
                assert alias in text and not pngs
            else:
                assert alias not in text
                assert 'Route: pj;' in text and 'checkpoint enabled; shared call timeout.' in text
                assert ('Applied Cutoff Classification Classification Count '
                        'True positive 2 False positive 1 False negative 1 True negative 2') in text
                assert 'Measurement >= 4.0' in text and len(pngs) == 2
        files.append(dict(file=path.name, native_pngs=len(pngs)))
    html = (ROOT / 'python-system-0.3.61-recovered.html').read_text()
    assert len(re.findall('data:image/png;base64,', html)) == 2
    assert 'checkpoint enabled; shared call timeout.' in ' '.join(Text(html).parts)
    return dict(status='pass', files=files, source_data_unchanged=True,
                native_system_calculation_qualified=False, bundled_recovery_verified=True)


if __name__ == '__main__':
    report = check()
    report['system_isolation'] = check_system_artifacts()
    print(json.dumps(report, indent=2))
