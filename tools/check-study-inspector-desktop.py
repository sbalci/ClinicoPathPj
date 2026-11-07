"""Read-only verification of the bounded-study desktop save and native exports."""
import csv
import json
import math
import re
from pathlib import Path
import runpy
from statistics import NormalDist
import struct
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
STEM = 'python-study-inspector-0.3.56-'
saved_columns = runpy.run_path(str(ROOT / 'tools/check-native-core-artifacts.py'))['saved_columns']
Tables = runpy.run_path(str(ROOT / 'tools/check-tree-path-artifacts.py'))['Tables']


def wilson(successes, total):
    """Independent score-interval formula, separate from the production helper."""
    z = NormalDist().inv_cdf(0.975)
    p = successes / total
    scale = 1 + z*z/total
    center = (p + z*z/(2*total)) / scale
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / scale
    return p, max(0, center-half), min(1, center+half)


def check():
    generated = runpy.run_path(str(ROOT / 'data-raw/generate-study-inspector-maximum.py'))['rows']()
    with (EXPORTS / (STEM + 'maximum.csv')).open() as stream:
        source = list(csv.DictReader(stream))
    expected = [{'Study': r[0], **dict(zip(['TP','FP','FN','TN'], r[1:]))} for r in generated]
    assert source == [{k: str(v) for k,v in row.items()} for row in expected]
    metadata, labels, columns = saved_columns(STEM + 'maximum.omv')
    assert metadata['rowCount'] == 200 and metadata['columnCount'] == 5
    with zipfile.ZipFile(EXPORTS / (STEM + 'maximum.omv')) as archive:
        assert archive.testzip() is None
        strings = archive.read('strings.bin')
        assert len([n for n in archive.namelist() if n.endswith('.png')]) == 2
    for field in metadata['fields']:
        name = field['name']
        if field['type'] == 'string':
            actual = [strings[v:].split(b'\0',1)[0].decode() for v in columns[name]]
        else:
            mapping = {r[0]: r[1] for r in labels.get(name, {}).get('labels', [])}
            actual = [mapping.get(v,v) for v in columns[name]]
        assert actual == [r[name] for r in expected], name
    html = (EXPORTS / (STEM + 'maximum.html')).read_text()
    parser = Tables(); parser.feed(html)
    audit = next(t for t in parser.tables if t[0] == ['Study Row Audit'])
    assert [int(v) for v in audit[2]] == [200,200,0,75,0,0]
    study = next(t for t in parser.tables if t[0] == ['Individual Study Results (Raw Counts)'])
    assert len(study[2:]) == 200
    for i,(row,want) in enumerate(zip(study[2:], expected), 1):
        assert int(row[0]) == i and row[1] == want['Study']
        assert [float(v) for v in row[2:6]] == [want[k] for k in ['TP','FP','FN','TN']]
        calculated = (*wilson(want['TP'], want['TP']+want['FN']),
                      *wilson(want['TN'], want['TN']+want['FP']))
        # Native HTML rounds percentages to one decimal; this is a display-level comparison.
        displayed = [float(v.replace('\u2009','').replace('%','').strip())/100 for v in row[6:12]]
        assert all(abs(a-b) <= 0.00050001 for a,b in zip(displayed,calculated)), i
    payload = json.loads(re.search(r'payload=(\{.*?\}),rows=payload.studies;', html, re.S)[1])
    assert payload['confidence'] == 95 and len(payload['studies']) == 200
    for i,(row,want) in enumerate(zip(payload['studies'],expected),1):
        assert row['sourceID'] == str(i) and row['study'] == want['Study']
        assert [row[k] for k in ['tp','fp','fn','tn']] == [want[k] for k in ['TP','FP','FN','TN']]
        calculated = (*wilson(want['TP'], want['TP']+want['FN']),
                      *wilson(want['TN'], want['TN']+want['FP']))
        actual = [row[k] for k in ['sensitivity','seLower','seUpper','specificity','spLower','spUpper']]
        assert all(abs(a-b) < 1e-12 for a,b in zip(actual,calculated)), i
    assert 'first 20 retained source rows' in html
    png = (EXPORTS / (STEM + 'direct-specificity.png')).read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    dimensions = struct.unpack('>II', png[16:24])
    assert dimensions == (1800,1600)
    offset = 8; chunks = []; compressed = bytearray()
    while offset < len(png):
        length = struct.unpack('>I',png[offset:offset+4])[0]
        kind = png[offset+4:offset+8]; payload = png[offset+8:offset+8+length]
        checksum = struct.unpack('>I',png[offset+8+length:offset+12+length])[0]
        assert zlib.crc32(kind+payload) & 0xffffffff == checksum
        if kind == b'IDAT': compressed.extend(payload)
        chunks.append(kind); offset += length+12
    assert chunks[-1] == b'IEND' and zlib.decompress(compressed)
    return {'saved_source_rows':200, 'native_export_rows':200,
            'audit':[200,200,0,75,0,0], 'independent_display_comparisons':1200,
            'independent_payload_comparisons':1200, 'payload_tolerance':1e-12,
            'percentage_tolerance':0.05, 'percentage_tolerance_unit':'percentage points',
            'direct_png_dimensions':dimensions, 'direct_png_integrity':'CRC and decompression pass',
            'saved_native_png_resources':2}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
