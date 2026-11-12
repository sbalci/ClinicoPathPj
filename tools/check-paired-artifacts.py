"""Check GUI-saved paired-test tables and images without running serialized analyses."""
import base64
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT/'docs/validation-exports'
sys.path.insert(0, str(ROOT/'inst/python/_vendor'))
from PIL import Image

spec = importlib.util.spec_from_file_location('native_tables', ROOT/'tools/check-summary-service-artifacts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
REFERENCE = next(f for f in json.loads((ROOT/'tests/fixtures/paired-decision.json').read_text())['fixtures']
                 if f['id'] == 'hand_correctness_not_positivity')
RUN = next(r for r in REFERENCE['expected']['runs'] if r['method'] == 'midp' and r['confidence'] == .95)
LABELS = ['Sensitivity', 'Specificity', 'Positive predictive value', 'Negative predictive value', 'Accuracy']
PAIRED_LABELS = ['Accuracy', 'Sensitivity', 'Specificity']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def displayed(value, expected, percent=False):
    value = re.sub(r'\s+', '', value)
    if expected is None:
        require(value == '.', 'Undefined value was populated')
    elif value == '<.001':
        require(0 <= expected < .001, 'Incorrect small p-value')
    else:
        actual = float(value.replace('%', '').replace(' ', ''))/(100 if percent else 1)
        require(abs(actual-expected) <= .00050000001, f'Wrong rounded value: {value} vs {expected}')


def image_info(blob):
    with Image.open(io.BytesIO(blob)) as im:
        require(im.width >= 400 and im.height >= 300, 'Image too small')
        require(im.convert('RGB').getextrema() != ((255, 255),)*3, 'Blank image')
        return dict(sha256=hashlib.sha256(blob).hexdigest(), dimensions=[im.width, im.height],
                    pixel_sha256=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest())


def inspect(html, archive=None):
    tables = module.Tables(html).tables
    require(len(tables) == 7, 'Expected seven native tables')
    require(tables[0][2] == ['20', '16', '3', '1', '8', '8'], 'Wrong cohort')
    require(tables[1][2:6] == [
        ['Reference', 'Reference', 'Positive', 'Negative', '1', '0'],
        ['Test 1', 'Test_A', 'Positive', 'Negative', '1', '0'],
        ['Test 2', 'Test_B', 'Positive', 'Negative', '1', '0'],
        ['Test 3', 'Test_C', 'Positive', 'Negative', '0', '1']], 'Wrong level/exclusion audit')
    require(tables[2][2:] == [['Test_'+name]+[str(v) for v in model['counts']]
                             for name, model in RUN['models'].items()], 'Wrong classification counts')
    estimates = tables[3][2:-1]
    require(len(estimates) == 15, 'Wrong proportion-row count')
    for row, (name, label, target) in zip(estimates,
            [(name, label, p) for name, model in RUN['models'].items()
             for label, p in zip(LABELS, model['proportions'])]):
        require(row[:2] == ['Test_'+name, label], 'Wrong proportion label/order')
        require(int(row[3]) > 0 and abs(int(row[2])/int(row[3])-target['estimate']) < 1e-12,
                'Numerator/denominator mismatch')
        for value, key in zip(row[4:7], ('estimate', 'lower', 'upper')):
            displayed(value, target[key], percent=True)
        require(row[7] == 'Exact per-test interval', 'Wrong interval method label')
    require('not intervals for paired differences' in tables[3][-1][0], 'Missing interval disclosure')
    comparisons = tables[4][2:-1]
    discordances = tables[5][2:]
    require(len(comparisons) == len(discordances) == 9, 'Wrong pair-row count')
    for row, cells, (pair, metric, label) in zip(comparisons, discordances,
            [(pair, metric, label) for pair in RUN['pairs']
             for metric, label in zip(('accuracy', 'sensitivity', 'specificity'), PAIRED_LABELS)]):
        target = pair[metric]
        identity = ['Test_'+pair['first_name'], 'Test_'+pair['second_name'], label]
        require(row[:3] == identity and row[3] == str(target['n']), 'Wrong paired identity/N')
        displayed(row[4], target['difference'], percent=True)
        displayed(row[5], target['p'])
        displayed(row[6], target.get('p_holm') if metric == 'accuracy' else None)
        require(row[7] == 'Mid-p McNemar', 'Wrong McNemar method label')
        require(cells == identity+[str(v) for v in target['counts']]+[str(target['discordant'])],
                'Wrong discordance cells')
    require('p-values are unadjusted' in tables[4][-1][0], 'Missing multiplicity disclosure')
    with (ROOT/'data/python_paired_test_examples.csv').open() as f:
        source = list(csv.DictReader(f))
    require(tables[6][2:] == [[str(i+1)]+[source[i][name] for name in ('Reference', 'Test_A', 'Test_B', 'Test_C')]
                            for i in range(16)], 'Wrong retained source rows')
    if archive is None:
        resources = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)', html)
        require(len(resources) == 1, 'Expected one embedded PNG')
        blob = base64.b64decode(re.sub(r'\s', '', resources[0]), validate=True)
    else:
        resources = re.findall(r'<img[^>]*src="([^"]+\.png)"', html)
        require(len(resources) == 1, 'Expected one cached PNG')
        blob = archive.read(unquote(resources[0]))
    return image_info(blob)


def check():
    report = {}
    datasets = []
    tables = []
    for mode in ('valid', 'recovered', 'reopened'):
        path = EXPORTS/f'python-paired-0.3.66-{mode}.omv'
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, 'Saved OMV CRC failed')
            html = archive.read('index.html').decode()
            report[mode] = inspect(html, archive)
            report[mode]['omv_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            datasets.append({n: archive.read(n) for n in ('data.bin', 'metadata.json', 'xdata.json')})
            tables.append(module.Tables(html).tables)
    require(all(t == tables[0] for t in tables), 'Equivalent-input saved tables changed')
    require(len({report[m]['pixel_sha256'] for m in ('valid', 'recovered', 'reopened')}) == 1,
            'Equivalent-input saved plot changed')
    with zipfile.ZipFile(EXPORTS/'python-paired-0.3.66-incomplete.omv') as archive:
        require(archive.testzip() is None, 'Incomplete OMV CRC failed')
        html = archive.read('index.html').decode()
        pending = module.Tables(html).tables
        require(len(pending) == 7 and all(len(t) == 3 and all(not c.strip() for c in t[2]) for t in pending),
                'Incomplete state retained computed rows')
        require(not any(n.endswith('.png') for n in archive.namelist()), 'Incomplete state retained cached plot')
        require('Choose which level of Test_B' in html, 'Missing level guidance')
        datasets.append({n: archive.read(n) for n in ('data.bin', 'metadata.json', 'xdata.json')})
    require(all(d == datasets[0] for d in datasets), 'Lifecycle changed dataset bytes/metadata')
    html = (EXPORTS/'python-paired-0.3.66-recovered.html').read_text()
    report['HTML'] = inspect(html)
    require(report['HTML']['pixel_sha256'] == report['reopened']['pixel_sha256'], 'HTML image pixels changed')
    report['native_PNG'] = image_info((EXPORTS/'python-paired-0.3.66-native-plot.png').read_bytes())
    report['source_rendered_PNG'] = image_info((EXPORTS/'python-paired-native-example-20261111.png').read_bytes())
    require(report['native_PNG']['dimensions'] == report['source_rendered_PNG']['dimensions'] and
            report['native_PNG']['pixel_sha256'] == report['source_rendered_PNG']['pixel_sha256'],
            'Same-resolution native export changed from source render')
    probes = {'count': html.replace('>16<', '>15<', 1),
              'estimate': html.replace('62.5', '52.5', 1),
              'paired_p': html.replace('.031', '.931', 1),
              'missing_plot': re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+', '', html, count=1)}
    for name, changed in probes.items():
        require(changed != html, 'No-op corruption probe '+name)
        try:
            inspect(changed)
        except (ValueError, IndexError):
            continue
        raise ValueError('Accepted corrupted artifact: '+name)
    report.update(scope='GUI-saved/recalculated/exported artifacts; no clinical or cross-platform qualification',
                  equivalent_tables_and_saved_plot_pixels_identical=True, source_bytes_and_metadata_unchanged=True,
                  incomplete_tables_and_plot_cleared=True, corruption_probes_rejected=list(probes))
    (EXPORTS/'python-paired-0.3.66-artifacts-20261111.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    check()
