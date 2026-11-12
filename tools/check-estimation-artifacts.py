"""Validate GUI-saved estimation tables and plots against independent R fixtures."""
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
FIXTURES = json.loads((ROOT/'tests/fixtures/estimation-core.json').read_text())['fixtures']
with (ROOT/'data/python_estimation_examples.csv').open() as f:
    SOURCE = list(csv.DictReader(f))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def displayed(value, expected):
    value = re.sub(r'\s+', '', value).replace('−', '-')
    if expected is None:
        require(value == '.', 'Undefined value was populated')
        return
    if '%' in value:
        expected *= 100
        value = value.replace('%', '')
    if value == '<.001':
        require(0 <= expected < .001, 'Incorrect small p-value')
        return
    decimals = len(value.split('.')[1]) if '.' in value else 0
    tolerance = .5*10**(-decimals) + 1e-12
    require(abs(float(value)-expected) <= tolerance, f'Wrong rounded value {value} vs {expected}')


def image_info(blob):
    with Image.open(io.BytesIO(blob)) as im:
        require(im.width >= 400 and im.height >= 250, 'Image too small')
        require(im.convert('RGB').getextrema() != ((255, 255),)*3, 'Blank image')
        return dict(sha256=hashlib.sha256(blob).hexdigest(), dimensions=[im.width, im.height],
                    pixel_sha256=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest())


def inspect(html, archive=None):
    tables = module.Tables(html).tables
    require(len(tables) == 10, 'Expected ten native tables')
    for paired, offset, fixture_name in ((False,0,'hand_unequal_variance'), (True,5,'paired_missing_alignment')):
        case = next(f for f in FIXTURES if f['id'] == fixture_name)
        target = case['expected']
        run = next(r for r in target['runs'] if r['confidence'] == .95 and r['method'] == ('paired_t' if paired else 'welch'))
        require(tables[offset][2] == (['13','5','8'] if paired else ['13','13','0']), 'Wrong retained cohort')
        expected_missing = [['First measurement','FirstMeasurement','7'],['Second measurement','SecondMeasurement','6']] if paired else [['Outcome','Outcome','0'],['Group','IndependentGroup','0']]
        require(tables[offset+1][2:4] == expected_missing, 'Wrong role missingness')
        names = ['FirstMeasurement','SecondMeasurement'] if paired else ['First','Second']
        for row,key,label,name in zip(tables[offset+2][2:4], ('first','second'), ('First','Second'), names):
            require(row[:2] == [label,name], 'Wrong contrast role/label')
            require(row[2] == str(target['summaries'][key]['n']), 'Wrong descriptive N')
            for value,column in zip(row[3:], ('mean','sd')): displayed(value,target['summaries'][key][column])
        row = tables[offset+3][2]
        require(row[:2] == names, 'Wrong contrast orientation')
        require(row[2] == ('Paired t-test' if paired else 'Welch independent t-test'), 'Wrong method')
        for value,key in zip(row[3:10], ('difference','stderr','df','statistic','p','lower','upper')): displayed(value,run[key])
        displayed(row[10],.95)
        require(row[11] == 'ok', 'Wrong inference status')
        require('does not establish equivalence' in tables[offset+3][-1][0], 'Missing interpretation boundary')
        cases = tables[offset+4][2:]
        indices = target['retained_indices']
        require(len(cases) == len(indices), 'Wrong source-row count')
        for row,i in zip(cases,indices):
            require(row[:2] == [str(i+1),SOURCE[i]['Subject']], 'Changed source/subject identity')
            if paired:
                for value,key in zip(row[2:4], ('FirstMeasurement','SecondMeasurement')): displayed(value,float(SOURCE[i][key]))
                displayed(row[4],float(SOURCE[i]['FirstMeasurement'])-float(SOURCE[i]['SecondMeasurement']))
            else:
                require(row[2] == SOURCE[i]['IndependentGroup'], 'Changed group label')
                displayed(row[3],float(SOURCE[i]['Outcome']))
    if archive is None:
        resources = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)
        require(len(resources) == 2, 'Expected two embedded plots')
        blobs = [base64.b64decode(re.sub(r'\s','',x),validate=True) for x in resources]
    else:
        resources = re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        require(len(resources) == 2, 'Expected two cached plots')
        blobs = [archive.read(unquote(x)) for x in resources]
    return [image_info(b) for b in blobs]


def check():
    report, datasets, valid_tables = {}, [], []
    for mode in ('valid','recovered','reopened'):
        path = EXPORTS/f'python-estimation-0.3.67-{mode}.omv'
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, 'OMV CRC failed')
            html = archive.read('index.html').decode()
            report[mode] = inspect(html,archive)
            valid_tables.append(module.Tables(html).tables)
            datasets.append({n:archive.read(n) for n in ('data.bin','metadata.json','xdata.json')})
    require(all(t == valid_tables[0] for t in valid_tables), 'Equivalent-input saved tables changed')
    require(report['valid'] == report['recovered'] == report['reopened'], 'Equivalent-input saved plot pixels changed')
    for mode,offset,remaining in (('incomplete',5,0), ('independent-incomplete',0,5)):
        with zipfile.ZipFile(EXPORTS/f'python-estimation-0.3.67-{mode}.omv') as archive:
            require(archive.testzip() is None, 'Incomplete CRC failed')
            html = archive.read('index.html').decode()
            tables = module.Tables(html).tables
            require(len(tables) == 10, 'Incomplete table structure changed')
            require(all(len(t) == 3 and all(not cell.strip() for cell in t[2]) for t in tables[offset:offset+5]), 'Stale incomplete computed rows')
            require(tables[remaining:remaining+5] == valid_tables[0][remaining:remaining+5], 'Unaffected analysis changed')
            images = [n for n in archive.namelist() if n.endswith('.png')]
            require(len(images) == 1, 'Stale incomplete plot')
            require(image_info(archive.read(images[0])) == report['valid'][0 if remaining == 0 else 1], 'Unaffected image changed')
            datasets.append({n:archive.read(n) for n in ('data.bin','metadata.json','xdata.json')})
    require(all(d == datasets[0] for d in datasets), 'Lifecycle changed dataset bytes/metadata')
    html = (EXPORTS/'python-estimation-0.3.67-recovered.html').read_text()
    report['HTML'] = inspect(html)
    require([(p['dimensions'], p['pixel_sha256']) for p in report['HTML']] ==
            [(p['dimensions'], p['pixel_sha256']) for p in report['valid']], 'HTML plot pixels changed')
    for i,name in enumerate(('independent','paired')):
        exported = image_info((EXPORTS/f'python-estimation-0.3.67-{name}-plot.png').read_bytes())
        source = image_info((EXPORTS/f'python-estimation-{name}-native-20261112.png').read_bytes())
        require(exported == source, 'Native PNG differs from same-resolution source '+name)
        report[name+'_PNG'] = exported
    probes = dict(cohort=html.replace('>13<','>12<',1), estimate=html.replace('>0.875<','>0.975<',1),
                  p=html.replace('>.700<','>.900<',1), missing_plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed != html,'No-op corruption probe '+name)
        try: inspect(changed)
        except (ValueError,IndexError): continue
        raise ValueError('Accepted corrupted artifact '+name)
    report.update(scope='Local macOS arm64 GUI artifacts; no clinical or cross-platform qualification',
        independent_R_tables_agree_at_display_precision=True, same_input_tables_and_plot_pixels_identical=True,
        both_incomplete_states_clear_only_affected_analysis=True, dataset_bytes_and_metadata_unchanged=True,
        corruption_probes_rejected=list(probes))
    (EXPORTS/'python-estimation-0.3.67-artifacts-20261112.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    check()
