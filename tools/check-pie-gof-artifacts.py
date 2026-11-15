"""Check real saved/exported GOF artifacts independently of the Python calculation."""
import base64
import argparse
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
REF=json.loads(subprocess.check_output(['Rscript','--vanilla',str(ROOT/'tests/reference/pie-gof-example.R')],cwd=ROOT,text=True))
MODES=('legacy','equal','custom','invalid','off','expectedoff','incomplete','recovered','reopened')


def inspect(html,mode,archive=None):
    require(mode in MODES,'Unknown qualification mode '+mode)
    tables=base.module.Tables(html).tables
    disabled=mode in ('legacy','off')
    empty=mode in ('invalid','incomplete')
    require(len(tables)==(4 if disabled else 5 if mode=='expectedoff' else 6),'Wrong table count '+mode)
    require(all(len(t)>=3 for t in tables),'Truncated table '+mode)
    if empty:
        require(all(len(t)==3 and all(not c.strip() for c in t[2]) for t in tables),'Stale rows/notes '+mode)
        require('total frequency N=25' not in html,'Stale cohort summary '+mode)
        if mode=='invalid':require('duplicate' in html.lower(),'Missing duplicate-ratio explanation')
    else:
        require(tables[0][2]==['6','4','2','1','3','25.0'],'Wrong cohort '+mode)
        require(tables[1][2:4]==[['Outcome','Outcome','1'],['Frequency','Frequency','1']],'Wrong role missingness')
        require(len(tables[2])==7,'Wrong declared category count')
        common=REF['equal']
        for i,row in enumerate(tables[2][2:6]):
            require(len(row)==6,'Wrong observed row width')
            require(row[:2]==[str(i),common['categories'][i]],'Wrong category order/code')
            for value,want in zip(row[2:5],(common['observed'][i],25,common['observed'][i]/25)):displayed(value,want)
            require(row[5]==('zero_count' if common['observed'][i]==0 else 'positive'),'Wrong zero-category status')
        if not disabled:
            ref=REF['equal' if mode=='equal' else 'custom']
            row=tables[3][2]
            require(len(row)==8,'Wrong test row width')
            require(row[0]=='Pearson chi-square goodness of fit','Wrong test')
            require(row[1]==('Equal probabilities' if mode=='equal' else 'Custom labelled ratios'),'Wrong null')
            for value,key in zip(row[2:7],('statistic','df','p','minimum','small')):displayed(value,ref[key])
            require(row[7]==('Asymptotic approximation' if mode=='equal' else 'Sparse approximation'),'Wrong sparse status')
            require('A large p-value does not establish equivalence' in tables[3][-1][0],'Missing inference assumption')
            if mode!='expectedoff':
                require(len(tables[4])==7,'Wrong expected mapping count')
                for i,row in enumerate(tables[4][2:6]):
                    require(len(row)==7,'Wrong expected row width')
                    require(row[:2]==[str(i),ref['categories'][i]],'Wrong null category mapping')
                    for value,key in zip(row[2:],('observed','probability','expected','residual','contribution')):
                        displayed(value,ref[key][i])
        cases=tables[-1][2:]
        require(len(cases)==3,'Wrong contributing cases')
        for row,identifier,label,count in zip(cases,('1','2','3'),('No','Yes','Other'),(12,8,5)):
            require(len(row)==4,'Wrong source row width')
            require(row[:3]==[identifier,'.',label],'Wrong original source identity')
            displayed(row[3],count)
    if archive:
        paths=re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        blobs=[archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(blobs),'Stale cached plot')
    else:
        blobs=[base64.b64decode(re.sub(r'\s','',p),validate=True) for p in re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)]
    require(len(blobs)==(0 if empty else 1),'Wrong plot count '+mode)
    return [base.image_info(b) for b in blobs]


def inspect_export(html,saved_tables,saved_image):
    images=inspect(html,'reopened')
    def canonical(tables):
        # Native HTML export inserts whitespace before %; preserve all digits,
        # signs, labels and other cell text, including significant precision.
        return [[[re.sub(r'\s+(?=%$)','',c) if re.fullmatch(r'[+\-−]?(?:\d+(?:\.\d*)?|\.\d+)\s*%',c) else c
                  for c in row] for row in t] for t in tables]
    require(canonical(base.module.Tables(html).tables)==canonical(saved_tables),'HTML tables differ from saved analysis')
    require(images[0]['pixel_sha256']==saved_image['pixel_sha256'],'HTML plot changed')
    return images


def check(version='0.3.73'):
    require(isinstance(version,str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',version) is not None,'Invalid package version')
    images={};tables={};data=[]
    for mode in MODES:
        with zipfile.ZipFile(EXPORTS/f'python-pie-gof-{version}-{mode}.omv') as z:
            require(z.testzip() is None,'Corrupt OMV '+mode)
            html=z.read('index.html').decode();images[mode]=inspect(html,mode,z)
            tables[mode]=base.module.Tables(html).tables
            data.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==data[0] for d in data),'Lifecycle changed dataset/metadata bytes')
    for mode in ('equal','custom','off','expectedoff','recovered','reopened'):
        require(tables[mode][:3]==tables['legacy'][:3],'Descriptives changed '+mode)
        require(images[mode][0]['pixel_sha256']==images['legacy'][0]['pixel_sha256'],'Inference changed plot '+mode)
    for mode in ('recovered','reopened'):require(tables[mode]==tables['custom'],'Custom inference changed '+mode)
    html=(EXPORTS/f'python-pie-gof-{version}-reopened.html').read_text()
    images['HTML']=inspect_export(html,tables['reopened'],images['reopened'][0])
    png=base.image_info((EXPORTS/f'python-pie-gof-{version}-plot.png').read_bytes())
    previous=base.image_info((EXPORTS/'python-pie-0.3.72-plot.png').read_bytes())
    require(png==previous,'Native export differs from qualified descriptive PNG')
    images['directPNG']=png
    chunks=re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    probes=dict(statistic=html.replace(chunks[3],chunks[3].replace('2.93','9.99',1),1),
        probability=html.replace(chunks[4],chunks[4].replace('40.0','90.0',1),1),
        support=html.replace(chunks[4],chunks[4].replace('>Zero<','>WRONG<',1),1),
        plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed!=html,'No-op corruption '+name)
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):continue
        raise ValueError('Accepted corrupted artifact '+name)
    return dict(scope='Actual native GOF saves/exports; clinical/full-method/other-platform gates separate',
        states=images,unchanged_dataset_bytes=True,rejected_corruptions=list(probes))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default='0.3.73',help='Version prefix of the actual GUI-created artifacts')
    args=parser.parse_args()
    r=check(args.version);(EXPORTS/f'python-pie-gof-{args.version}-artifacts.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
