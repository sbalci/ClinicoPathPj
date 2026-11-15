"""Inspect real GUI saves and exports against independent base-R example counts."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
s=importlib.util.spec_from_file_location('waffle_artifact_base',ROOT/'tools/check-estimation-artifacts.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
require,displayed=base.require,base.displayed
REF=json.loads(subprocess.check_output(['Rscript','--vanilla','tests/reference/waffle-example.R'],cwd=ROOT,text=True))
MODES=('default','flip','off','incomplete','recovered','single','reopened')
TITLES=('Source Rows and Frequencies','Missingness by Role','Panel Denominators',
        'Exact Frequencies and Rounded Tile Allocation','Contributing Original Source Rows')


def data_rows(table,width):
    rows=table[2:]
    if rows and len(rows[-1])==1 and rows[-1][0].startswith('Note.'):rows=rows[:-1]
    require(all(len(r)==width for r in rows),'Malformed table row width')
    return rows


def canonical_tables(tables):
    result=[[list(row) for row in table] for table in tables]
    # HTML adds a space before %, whereas the OMV index omits it. Normalize
    # only the two numeric percentage columns; never alter digits or labels.
    for row in result[3][2:]:
        if len(row)==9:
            for k in (4,6):row[k]=re.sub(r'(?<=\d)\s+(?=%$)','',row[k])
    return result


def inspect(html,mode,archive=None):
    require(mode in MODES,'Unknown mode')
    tables=base.module.Tables(html).tables
    cases=mode in ('flip','recovered','single','reopened')
    require(len(tables)==(5 if cases else 4),'Wrong native table count '+mode)
    require([t[0][0] for t in tables]==list(TITLES[:len(tables)]),'Wrong table titles/order')
    require(all(len(t)>=3 for t in tables),'Truncated table')
    if mode=='incomplete':
        require(all(t[2:]==[['']] for t in tables),'Stale incomplete values or notes')
        require('frequency N=1004' not in html,'Stale incomplete narrative')
    else:
        ref=REF['single' if mode=='single' else 'faceted']
        rows=data_rows(tables[0],6);require(len(rows)==1,'Wrong cohort count')
        for actual,expected in zip(rows[0],ref['cohort']):displayed(actual,expected)
        missing=data_rows(tables[1],3)
        expected=[['Categories','Category','1'],['Frequency','Frequency','0']]
        if mode!='single':expected.append(['Panels','Panel','1'])
        require(missing==expected,'Wrong role missingness')
        panels=data_rows(tables[2],5);require(len(panels)==len(ref['panels']),'Wrong retained/inactive panels')
        for actual,panel in zip(panels,ref['panels']):
            require(actual[0]==panel['panel'] and actual[-1]==panel['status'],'Wrong panel label/status')
            for v,k in zip(actual[1:4],('total','sourceRows','tiles')):displayed(v,panel[k])
        cells=data_rows(tables[3],9);require(len(cells)==len(ref['cells']),'Dropped category')
        for actual,cell in zip(cells,ref['cells']):
            require(actual[:2]==[cell['panel'],cell['category']] and actual[-1]==cell['status'],'Wrong category mapping/status')
            for v,k in zip(actual[2:8],('count','denominator','proportion','tiles','represented','error')):displayed(v,cell[k])
        require('Some positive categories receive no tiles' in html,'Missing rare-category warning')
        if cases:
            rows=data_rows(tables[4],5);require(len(rows)==len(ref['cases']),'Wrong source-row count')
            for actual,case in zip(rows,ref['cases']):
                require(actual[:4]==[case['sourceID'],'.',case['category'],case['panel']],'Wrong source mapping')
                displayed(actual[-1],case['frequency'])
    hidden=mode in ('off','incomplete')
    if archive:
        paths=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        blobs=[archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(blobs),'Stale cached image')
    else:
        blobs=[base64.b64decode(re.sub(r'\s','',p),validate=True) for p in
               re.findall(r'<img[^>]*src="data:image/png;base64,([A-Za-z0-9+/=\s]+)"',html)]
    require(len(blobs)==(0 if hidden else 1),'Wrong visible plot count')
    return [base.image_info(b) for b in blobs]


def check():
    images={};tables={};datasets=[]
    for mode in MODES:
        with zipfile.ZipFile(EXPORTS/f'python-waffle-0.3.76-{mode}.omv') as z:
            require(z.testzip() is None,'Corrupt saved file')
            html=z.read('index.html').decode();images[mode]=inspect(html,mode,z)
            tables[mode]=base.module.Tables(html).tables
            datasets.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==datasets[0] for d in datasets),'Source data/metadata changed during option-only checks')
    for mode in ('recovered','reopened'):
        require(tables[mode]==tables['flip'],'Recovered/reopened native tables differ')
        require(images[mode][0]['pixel_sha256']==images['flip'][0]['pixel_sha256'],'Recovered/reopened plot pixels differ')
    require(images['default'][0]['pixel_sha256']!=images['flip'][0]['pixel_sha256'],'Orientation/options did not affect the plot')
    html=(EXPORTS/'python-waffle-0.3.76-reopened.html').read_text()
    exported=inspect(html,'reopened')
    require(canonical_tables(base.module.Tables(html).tables)==canonical_tables(tables['reopened']),
            'HTML tables differ from saved results')
    direct=base.image_info((EXPORTS/'python-waffle-0.3.76-plot.png').read_bytes())
    native=base.image_info(Path('/private/tmp/cpj-waffle-0.3.76-native-reference.png').read_bytes())
    require(direct==native,'Direct PNG differs from full-size native reference')
    require(exported[0]['pixel_sha256']==images['reopened'][0]['pixel_sha256'],
            'HTML and cached image pixels differ')
    cached_native=base.image_info(Path('/private/tmp/cpj-waffle-0.3.76-native-cached-size.png').read_bytes())
    require(cached_native['pixel_sha256']==images['reopened'][0]['pixel_sha256'],
            'Cached image differs from native reference at the same dimensions')
    # Preserve evidence that malformed results cannot pass this checker.
    mutations=[html.replace('899.00','898.00',1),html.replace('1004','1005'),
               html.replace('1000.00','999.00',1),
               re.sub(r'<img(?=[^>]*src="data:image/png;base64,)','<disabled-img',html,count=1)]
    for bad in mutations:
        require(bad!=html,'Mutation did not alter fixture')
        try:inspect(bad,'reopened')
        except ValueError:pass
        else:raise ValueError('Corrupted GUI artifact accepted')
    # Check old-file compatibility without touching the original saved file.
    def old(path):
        with zipfile.ZipFile(path) as z:
            h=z.read('index.html').decode()
            return ({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')},
                    base.module.Tables(h).tables,
                    [base.image_info(z.read(n))['pixel_sha256'] for n in z.namelist() if n.endswith('.png')])
    require(old(EXPORTS/'python-lollipop-0.3.75-reopened.omv')==
            old(EXPORTS/'python-lollipop-0.3.76-compatibility.omv'),'Legacy lollipop data/tables/pixels changed')
    return dict(saved_profiles=len(MODES),corruptions_rejected=4,images=images,
        native_PNG=direct,legacy_lollipop='unchanged data, native tables and cached image pixels',
        data_sha256={k:hashlib.sha256(v).hexdigest() for k,v in datasets[0].items()},
        scope='Scoped macOS GUI synthetic saves/exports; full methods, clinical/accessibility and other platforms separate')


if __name__=='__main__':print(json.dumps(check(),indent=2))
