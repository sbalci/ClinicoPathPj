"""Validate native GUI histogram saves, HTML and PNG against independent R results."""
import base64
import csv
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXPORTS=ROOT/'docs/validation-exports'
spec=importlib.util.spec_from_file_location('estimation_artifacts',ROOT/'tools/check-estimation-artifacts.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
require,displayed=base.require,base.displayed
with (ROOT/'data/python_histogram_examples.csv').open() as f:SOURCE=list(csv.DictReader(f))
REF=json.loads(subprocess.check_output(['Rscript','--vanilla',str(ROOT/'tests/reference/histogram-example.R')],cwd=ROOT,text=True))
MODES=('valid','custom','off','incomplete','recovered','reopened')


def inspect(html,mode,archive=None):
    tables=base.module.Tables(html).tables
    require(len(tables)==(3 if mode=='off' else 7),'Wrong native table count '+mode)
    if mode=='incomplete':
        require(all(len(t)==3 and all(not c.strip() for c in t[2]) for t in tables),
                'Incomplete result retained computed rows or notes')
    else:
        require(tables[0][2]==['22','20','2'],'Wrong retained cohort')
        summary=REF['summary']
        for value,key in zip(tables[1][2],('n','mean','sd','minimum','q1','median','q3','maximum')):
            displayed(value,summary[key])
        require(tables[2][2][0]=='Manual width','Wrong width rule')
        displayed(tables[2][2][1],2);require(tables[2][2][2:]==['10','ok'],'Wrong binning audit')
        require('Right-closed counting with ggplot2 edge fuzz' in tables[2][-1][0],'Missing membership disclosure')
        if mode!='off':
            counts=[5,7,4,1,1,1,0,0,0,1]
            for i,row in enumerate(tables[3][2:12]):
                for value,want in zip(row,(2*i-1,2*i+1,counts[i],counts[i]/20,counts[i]/40)):
                    displayed(value,want)
            require(len(tables[3])==13,'Wrong number of bin rows')
            reference,confidence=(1,.9) if mode=='custom' else (0,.95)
            ref=next(r for r in REF['runs'] if r['reference']==reference and r['confidence']==confidence)
            for value,key in zip(tables[4][2][:6],('reference','difference','stderr','df','statistic','p')):
                displayed(value,ref[key])
            require(tables[4][2][6]=='ok','Wrong Student status')
            require('does not establish equivalence' in tables[4][-1][0],'Missing interpretation boundary')
            for row,prefix,label,estimate in zip(tables[5][2:4],('mean_','difference_'),('Mean','Mean minus reference'),(summary['mean'],ref['difference'])):
                require(row[0]==label,'Wrong confidence target')
                for value,want in zip(row[1:],(estimate,ref[prefix+'lower'],ref[prefix+'upper'],confidence)):
                    displayed(value,want)
            cases=tables[6][2:];require(len(cases)==20,'Wrong retained case count')
            for i,row in enumerate(cases):
                require(row[:2]==[str(i+1),SOURCE[i]['Case']],'Wrong original row/subject identity')
                displayed(row[2],float(SOURCE[i]['Measurement']))
    if archive:
        paths=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        blobs=[archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(blobs),'Unused stale cached PNG')
    else:
        blobs=[base64.b64decode(re.sub(r'\s','',p),validate=True) for p in re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)]
    require(len(blobs)==(0 if mode in ('off','incomplete') else 1),'Wrong plot count '+mode)
    return [base.image_info(b) for b in blobs]


def check():
    report={};tables={};data=[]
    for mode in MODES:
        with zipfile.ZipFile(EXPORTS/f'python-histogram-0.3.70-{mode}.omv') as z:
            require(z.testzip() is None,'Invalid saved archive '+mode)
            html=z.read('index.html').decode();report[mode]=inspect(html,mode,z)
            tables[mode]=base.module.Tables(html).tables
            data.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==data[0] for d in data),'GUI lifecycle changed dataset/metadata bytes')
    for mode in ('recovered','reopened'):
        require(tables[mode]==tables['valid'],'Equivalent tables changed '+mode)
    for mode in ('custom','recovered','reopened'):
        require(report[mode][0]['pixel_sha256']==report['valid'][0]['pixel_sha256'],'Equivalent plot pixels changed '+mode)
    require(tables['off']==tables['valid'][:3],'Optional-result off changed retained core')
    html=(EXPORTS/'python-histogram-0.3.70-reopened.html').read_text()
    report['HTML']=inspect(html,'reopened')
    require(report['HTML'][0]['pixel_sha256']==report['valid'][0]['pixel_sha256'],'HTML plot pixels changed')
    png=base.image_info((EXPORTS/'python-histogram-0.3.70-plot.png').read_bytes())
    require(png['dimensions']==[1200,900],'Unexpected native PNG dimensions')
    # jamovi caches a viewport-sized 958x718 image but Export uses the native
    # 600x450 logical default at 2x. Compare each image at its own exact resolution.
    source_png=base.image_info((EXPORTS/'python-histogram-source.png').read_bytes())
    require(png==source_png,'Direct PNG differs from the independently rendered native source example')
    report['sourcePNG']=source_png
    report['directPNG']=png
    chunks=re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    probes=dict(count=html.replace(chunks[3],chunks[3].replace('>7<','>99<',1),1),
                confidence=html.replace(chunks[5],chunks[5].replace('95.0','80.0',1),1),
                identity=html.replace('H001','WRONG',1),
                plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed!=html,'No-op corruption '+name)
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):continue
        raise ValueError('Accepted corrupted artifact '+name)
    return dict(scope='Native saved/exported histogram artifacts; full methods/clinical/platform gates separate',
        states=report,unchanged_dataset_bytes=True,rejected_corruptions=list(probes))


if __name__=='__main__':
    report=check();(EXPORTS/'python-histogram-0.3.70-artifacts-20261113.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
