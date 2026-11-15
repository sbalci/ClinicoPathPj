"""Verify real GUI pie saves, native HTML and PNG against independent R counts."""
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
REF=json.loads(subprocess.check_output(['Rscript','--vanilla',str(ROOT/'tests/reference/pie-example.R')],cwd=ROOT,text=True))
MODES=('percentage','both','off','incomplete','recovered','reopened')


def inspect(html,mode,archive=None):
    tables=base.module.Tables(html).tables
    require(len(tables)==(3 if mode=='off' else 4),'Wrong native table count '+mode)
    if mode=='incomplete':
        require(all(len(t)==3 and all(not c.strip() for c in t[2]) for t in tables),'Stale incomplete rows/notes')
        require('total frequency N=25' not in html,'Stale cohort summary')
    else:
        for value,want in zip(tables[0][2],REF['cohort']):displayed(value,want)
        require(tables[1][2:4]==[['Outcome','Outcome','1'],['Frequency','Frequency','1']],'Wrong role missingness')
        require(len(tables[2])==7,'Wrong declared-category rows')
        for i,row in enumerate(tables[2][2:6]):
            require(row[:2]==[str(i),REF['categories'][i]],'Wrong category order/code')
            for value,want in zip(row[2:5],(REF['counts'][i],REF['total'],REF['proportions'][i])):displayed(value,want)
            require(row[5]==('zero_count' if REF['counts'][i]==0 else 'positive'),'Wrong zero-category status')
        require('including unused or zero-count categories' in tables[2][-1][0],'Missing zero-category disclosure')
        if mode!='off':
            require(len(tables[3])==5,'Wrong contributing source-row count')
            for row,i,label,count in zip(tables[3][2:],REF['source_indices'],REF['source_labels'],REF['source_counts']):
                require(row[:3]==[str(i),'.',label],'Wrong source identity')
                displayed(row[3],count)
    if archive:
        paths=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        blobs=[archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(blobs),'Stale cached PNG')
    else:
        blobs=[base64.b64decode(re.sub(r'\s','',p),validate=True) for p in re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)]
    require(len(blobs)==(0 if mode in ('off','incomplete') else 1),'Wrong plot count '+mode)
    return [base.image_info(b) for b in blobs]


def check():
    report={};tables={};data=[]
    for mode in MODES:
        with zipfile.ZipFile(EXPORTS/f'python-pie-0.3.72-{mode}.omv') as z:
            require(z.testzip() is None,'Corrupt OMV '+mode)
            html=z.read('index.html').decode();report[mode]=inspect(html,mode,z)
            tables[mode]=base.module.Tables(html).tables
            data.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==data[0] for d in data),'GUI lifecycle changed dataset/metadata bytes')
    for mode in ('both','recovered','reopened'):require(tables[mode]==tables['percentage'],'Equivalent tables changed '+mode)
    require(tables['off']==tables['percentage'][:3],'Output-off changed retained frequencies')
    for mode in ('recovered','reopened'):
        require(report[mode][0]['pixel_sha256']==report['both'][0]['pixel_sha256'],'Recovered plot changed '+mode)
    require(report['percentage'][0]['pixel_sha256']!=report['both'][0]['pixel_sha256'],'Plot labels did not change')
    html=(EXPORTS/'python-pie-0.3.72-reopened.html').read_text();report['HTML']=inspect(html,'reopened')
    require(report['HTML'][0]['pixel_sha256']==report['both'][0]['pixel_sha256'],'HTML plot changed')
    png=base.image_info((EXPORTS/'python-pie-0.3.72-plot.png').read_bytes())
    native=base.image_info((EXPORTS/'python-pie-0.3.72-native-source.png').read_bytes())
    require(png['dimensions']==[1300,900],'Unexpected PNG dimensions')
    require(png==native,'Direct PNG differs from independently checked native input example')
    report['directPNG']=png
    chunks=re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    probes=dict(count=html.replace(chunks[2],chunks[2].replace('12.00','99.00',1),1),
        denominator=html.replace(chunks[2],chunks[2].replace('25.0','99.0',1),1),
        identity=html.replace(chunks[3],chunks[3].replace('>No<','>WRONG<',1),1),
        plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed!=html,'No-op corruption '+name)
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):continue
        raise ValueError('Accepted corrupted artifact '+name)
    return dict(scope='Actual native pie saves/exports; full methods and other platforms separate',
                states=report,unchanged_dataset_bytes=True,rejected_corruptions=list(probes))


if __name__=='__main__':
    report=check();(EXPORTS/'python-pie-0.3.72-artifacts-20261114.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
