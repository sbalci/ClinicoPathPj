"""Check native CCC saved/exported results without executing archive contents."""
import base64
import csv
import hashlib
import io
import sys
import importlib.util
import json
import re
import struct
import zipfile
from urllib.parse import unquote
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT/'docs/validation-exports'
# Use reviewed Pillow already bundled for the native static renderer.
sys.path.insert(0, str(ROOT/'inst/python/_vendor'))
from PIL import Image
spec = importlib.util.spec_from_file_location('summary_artifacts', ROOT/'tools/check-summary-service-artifacts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(html, archive=None):
    tables = module.Tables(html).tables
    require(len(tables) == 3, 'Expected three native CCC tables')
    require(tables[0] == [['CCC Paired Observation Audit'],
            ['Supplied Rows','Complete Pairs','Excluded Rows','First Only Missing','Second Only Missing','Both Missing'],
            ['15','12','3','1','1','1']], 'Wrong paired audit')
    require(tables[1][:5] == [['Concordance Point Estimates'], ['Quantity','Estimate'],
            ['Lin concordance correlation (CCC)','0.969'],
            ['Pearson correlation (precision)','0.973'],
            ['Bias correction factor (Cb)','0.996']], 'Wrong displayed coefficients')
    require(len(tables[1]) == 6 and 'intervals and p-values are unavailable' in tables[1][5][0],
            'Missing inference limitation')
    with (ROOT/'data/python_concordance_examples.csv').open() as stream:
        source = list(csv.DictReader(stream))
    expected = [['Complete Independent CCC Pairs'],
                ['Source Row ID','Case','First Measurement','Second Measurement']]
    expected += [[str(i+1),r['Case'],f"{float(r['Method_A']):.1f}",f"{float(r['Method_B']):.1f}"]
                 for i,r in enumerate(source) if r['Method_A'] and r['Method_B']]
    require(tables[2] == expected, 'Wrong retained source pairs or identities')
    if archive is None:
        images = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)', html)
        require(len(images) == 1, 'Expected exactly one exported PNG image')
        png = base64.b64decode(re.sub(r'\s','',images[0]), validate=True)
    else:
        images = re.findall(r'<img[^>]*src="([^"]+\.png)"', html)
        require(len(images) == 1, 'Expected exactly one saved PNG resource')
        png = archive.read(unquote(images[0]))
    require(png[:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG signature')
    width, height = struct.unpack('>II', png[16:24])
    require(width >= 400 and height >= 300, 'Unexpected native plot dimensions')
    return png, [width,height]


def pixel_hash(png):
    with Image.open(io.BytesIO(png)) as image:
        return hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()


def check():
    report = {}
    saved = []
    for suffix in ('comparison','reopened','live-recalculated'):
        path = EXPORTS/f'python-concordance-0.3.63-{suffix}.omv'
        with zipfile.ZipFile(path) as z:
            require(z.testzip() is None, 'Bad OMV CRC')
            require(all(i.file_size < 16*1024*1024 for i in z.infolist()), 'Oversized OMV member')
            png, dims = inspect(z.read('index.html').decode(), z)
            resources = [n for n in z.namelist() if n.endswith('.png')]
            require(len(resources)==1 and z.read(resources[0])==png, 'Cached plot differs from result image')
            saved.append({name:z.read(name) for name in ('data.bin','metadata.json','xdata.json')})
            report[suffix] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                 png_sha256=hashlib.sha256(png).hexdigest(), pixel_sha256=pixel_hash(png), dimensions=dims)
    require(all(item == saved[0] for item in saved[1:]),
            'Save/reopen/recalculation changed source bytes or metadata')
    report['HTML'] = {}
    for suffix in ('reopened', 'live-recalculated'):
        path = EXPORTS/f'python-concordance-0.3.63-{suffix}.html'
        html = path.read_text()
        png, dims = inspect(html)
        require(pixel_hash(png)==report[suffix]['pixel_sha256'],
                'Exported plot differs from saved plot: '+suffix)
        report['HTML'][suffix] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    png_sha256=hashlib.sha256(png).hexdigest(), pixel_sha256=pixel_hash(png),dimensions=dims)
    require(len({report[suffix]['pixel_sha256'] for suffix in
                 ('comparison','reopened','live-recalculated')})==1,
            'Live recalculation changed the equivalent-input plot')
    report['saved_exported_plot_pixels_identical'] = True
    changes = {
        'wrong_CCC': html.replace('0.969','0.869',1),
        'wrong_source_case': html.replace('S01','T01',1),
        'missing_plot': re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1),
        'missing_table': re.sub(r'<table\b.*?</table>','',html,count=1,flags=re.S)
    }
    for name, changed in changes.items():
        require(changed != html, 'No-op corruption probe: '+name)
        try:
            inspect(changed)
        except ValueError:
            continue
        raise ValueError('Accepted corruption: '+name)
    report['corruption_probes_rejected'] = list(changes)
    report['source_bytes_and_metadata_unchanged'] = True
    report['scope'] = 'native saved/exported and live-recalculated artifacts; GUI actions independently observed; not clinical acceptance'
    (EXPORTS/'python-concordance-artifacts-20261111.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    check()
