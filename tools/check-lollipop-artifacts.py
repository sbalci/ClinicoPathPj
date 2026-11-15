"""Inspect actual GUI lollipop saves/exports against independent base-R CSV results."""
import base64
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
s=importlib.util.spec_from_file_location('estimation_artifacts',ROOT/'tools/check-estimation-artifacts.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
require,displayed=base.require,base.displayed
REF=json.loads(subprocess.check_output(['Rscript','--vanilla',str(ROOT/'tests/reference/lollipop-example.R')],cwd=ROOT,text=True))
MODES=('mean-default','sum-horizontal','sum-off','incomplete','recovered','reopened')


def inspect(html,mode,archive=None):
    require(mode in MODES,'Unknown mode')
    tables=base.module.Tables(html).tables
    hidden=mode in ('sum-off','incomplete')
    require(len(tables)==(4 if hidden else 6),'Wrong table count '+mode)
    require(all(len(t)>=3 for t in tables),'Truncated table')
    if mode=='incomplete':
        require(all(len(t)==3 and all(not c for c in t[2]) for t in tables),'Stale pending values/notes')
        require('6 complete observations' not in html,'Stale narrative')
    else:
        ref=REF['modes']['mean' if mode=='mean-default' else 'sum']
        require(len(tables[0][2])==5,'Wrong cohort width')
        for value,want in zip(tables[0][2],REF['cohort']):displayed(value,want)
        require(tables[1][2:4]==[['Measurement','Value','1'],['Group','Category','1']],'Wrong missingness')
        require(len(tables[2])==5,'Wrong summary row count')
        for row,basis,expected in zip(tables[2][2:4],('Raw complete observations','Plotted values'),(REF['raw'],ref['summary'])):
            require(len(row)==10 and row[0]==basis,'Wrong summary basis/width')
            for value,want in zip(row[1:],expected):displayed(value,want)
        require('not the grand mean' in tables[2][-1][0],'Missing raw/plotted distinction')
        require(tables[3][2:]==[[label,str(n),'retained'] for label,n in zip(REF['categories'],REF['group_counts'])],'Wrong category membership')
        if not hidden:
            require(len(tables[4])==5 and len(tables[5])==8,'Wrong point/source count')
            for j,row in enumerate(tables[4][2:]):
                require(len(row)==6 and row[0:2]==[str(j+1),ref['labels'][j]],'Wrong point order/label')
                for value,want in zip(row[2:],(ref['values'][j],ref['counts'][j],ref['slots'][j],0)):displayed(value,want)
            for j,row in enumerate(tables[5][2:]):
                require(len(row)==5 and row[:2]==[str(REF['source_rows'][j]),REF['source_labels'][j]],'Wrong source identity')
                for value,want in zip(row[2:],(REF['source_values'][j],ref['source_points'][j],ref['source_plotted'][j])):displayed(value,want)
    if archive:
        paths=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        blobs=[archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(blobs),'Stale cached image')
    else:
        blobs=[base64.b64decode(re.sub(r'\s','',p),validate=True) for p in re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)]
    require(len(blobs)==(0 if hidden else 1),'Wrong plot count')
    return [base.image_info(b) for b in blobs]


def check():
    images={};tables={};data=[]
    for mode in MODES:
        with zipfile.ZipFile(EXPORTS/f'python-lollipop-0.3.74-{mode}.omv') as z:
            require(z.testzip() is None,'Corrupt OMV')
            html=z.read('index.html').decode();images[mode]=inspect(html,mode,z)
            tables[mode]=base.module.Tables(html).tables
            data.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==data[0] for d in data),'Dataset/metadata changed during lifecycle')
    for mode in ('recovered','reopened'):
        require(tables[mode]==tables['sum-horizontal'],'Recovered tables changed')
        require(images[mode][0]['pixel_sha256']==images['sum-horizontal'][0]['pixel_sha256'],'Recovered image changed')
    require(tables['sum-off']==tables['sum-horizontal'][:4],'Output off changed summaries')
    require(images['mean-default'][0]['pixel_sha256']!=images['sum-horizontal'][0]['pixel_sha256'],'Aggregation/orientation did not change image')
    html=(EXPORTS/'python-lollipop-0.3.74-reopened.html').read_text();images['HTML']=inspect(html,'reopened')
    require(base.module.Tables(html).tables==tables['reopened'],'HTML tables changed')
    require(images['HTML'][0]['pixel_sha256']==images['reopened'][0]['pixel_sha256'],'HTML image changed')
    png=base.image_info((EXPORTS/'python-lollipop-0.3.74-plot.png').read_bytes())
    native=base.image_info((EXPORTS/'python-lollipop-0.3.74-native-reference.png').read_bytes())
    require(png['dimensions']==[1300,900] and png==native,'Native exported PNG disagrees with independently checked CSV render')
    images['directPNG']=png
    chunks=re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    probes=dict(raw_mean=html.replace(chunks[2],chunks[2].replace('30.7','99.7',1),1),
        point_value=html.replace(chunks[4],chunks[4].replace('104.0','999.0',1),1),
        identity=html.replace(chunks[5],chunks[5].replace('Treatment A','WRONG',1),1),
        plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed!=html,'No-op corruption '+name)
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):continue
        raise ValueError('Accepted corrupted artifact '+name)
    return dict(scope='Actual native GUI lollipop saves/exports; clinical/full-method/platform gates separate',
        states=images,unchanged_dataset_bytes=True,rejected_corruptions=list(probes))


if __name__=='__main__':
    r=check();(EXPORTS/'python-lollipop-0.3.74-artifacts-20261115.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
