"""Verify GUI-saved interval2 fixtures against literal endpoint expectations."""
import base64, json, math, re, runpy, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
saved_columns = runpy.run_path(str(ROOT/'tools/check-native-core-artifacts.py'))['saved_columns']
Tables = runpy.run_path(str(ROOT/'tools/check-tree-path-artifacts.py'))['Tables']
LEFT = [1,None,1,1,None,None,-3,0,4,None]
RIGHT = [1,3,None,4,None,None,-1,0,4,0]
KINDS = ['Exact','Left-censored','Right-censored','Interval-censored',None,None,
         'Interval-censored','Exact','Exact','Left-censored']


def check():
    evidence = {}
    for state in ['valid','incomplete','same-column','reopened']:
        stem = 'python-interval-censoring-0.3.50-' + state
        metadata, labels, columns = saved_columns(stem+'.omv')
        assert metadata['rowCount'] == 10 and metadata['columnCount'] == 6
        original_left = [1,None,1,1,None,5,-3,0,4,None]
        original_right = [1,3,None,4,None,2,-1,0,4,0]
        def numeric(name):
            return [None if math.isnan(x) or x == -2147483648 else x for x in columns[name]]
        assert numeric('Left endpoint') == original_left
        assert numeric('Right endpoint') == original_right
        left, right, kinds = LEFT, RIGHT, KINDS
        if state == 'incomplete':
            left = right = kinds = [None]*10
        elif state == 'same-column':
            left = right = original_left
            kinds = ['Exact' if x is not None else None for x in left]
        assert numeric('Prepared interval left') == left, state
        assert numeric('Prepared interval right') == right, state
        name = 'Prepared censoring type'
        mapping = {r[0]:r[1] for r in labels[name]['labels']}
        actual = [None if x == -2147483648 else mapping[x] for x in columns[name]]
        assert actual == kinds, (state,actual)
        fields = {f['name']:f for f in metadata['fields']}
        for name in ['Prepared interval left','Prepared interval right','Prepared censoring type']:
            assert fields[name]['columnType'] == 'Output'
        assert fields['Prepared interval left']['measureType'] == 'Continuous'
        assert fields['Prepared interval right']['measureType'] == 'Continuous'
        assert fields['Prepared censoring type']['measureType'] == 'Nominal'
        evidence[state] = {'source_bounds_and_saved_alignment':'pass',
                           'informative':sum(x is not None for x in kinds)}
    stem = 'python-interval-censoring-0.3.50-reopened'
    text = (EXPORTS/(stem+'.html')).read_text()
    parser = Tables(); parser.feed(text)
    audit = next(t for t in parser.tables if t[0] == ['Endpoint Accounting'])
    assert list(map(int,audit[2])) == [10,8,1,1,0,1]
    counts = next(t for t in parser.tables if t[0] == ['Informative Censoring Types'])
    assert [int(r[2]) for r in counts[2:]] == [1,3,2,2]
    assert [float(re.sub(r'[^0-9.]','',r[3])) for r in counts[2:]] == [12.5,37.5,25,25]
    preview = next(t for t in parser.tables if t[0] == ['Source-Row Endpoint Preview'])
    assert [int(r[0]) for r in preview[2:]] == list(range(1,11))
    images = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',text)
    assert len(images) == 1
    raw = base64.b64decode(images[0])
    assert raw == (EXPORTS/(stem+'.png')).read_bytes()
    assert struct.unpack('>II',raw[16:24]) == (1437,798)
    evidence['native_HTML_and_embedded_PNG'] = 'pass'
    return evidence


if __name__ == '__main__':
    print(json.dumps(check(),indent=2))
