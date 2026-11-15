"""Check real GUI saves/exports against independent base-R categorical references."""
import base64
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT/'docs/validation-exports'
spec = importlib.util.spec_from_file_location('estimation_artifacts', ROOT/'tools/check-estimation-artifacts.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
require, displayed = base.require, base.displayed
REF = json.loads(subprocess.check_output(['Rscript','--vanilla',str(ROOT/'tests/reference/barstats-example.R')],cwd=ROOT,text=True))
MODES = ('percentage','count','off','incomplete','recovered','reopened')


def inspect(html, mode, archive=None):
    tables = base.module.Tables(html).tables
    require(len(tables)==(4 if mode=='off' else 9), 'Wrong table count '+mode)
    if mode=='incomplete':
        require(all(len(t)==3 and all(not c.strip() for c in t[2]) for t in tables),
                'Incomplete result retained computed rows or notes')
        require('also choose: Outcome' in html, 'Missing required-input message')
    else:
        require(tables[0][2]==['7','5','2','1','4','50.0'], 'Wrong source/frequency cohort')
        require(tables[1][2:5]==[['Outcome','Outcome','1'],['Group','Group','0'],['Frequency','Frequency','1']], 'Wrong missingness')
        for row, group, total in zip(tables[2][2:], REF['groups'], REF['totals']):
            require(row[0]==group, 'Wrong group label'); displayed(row[1],total)
        if mode!='off':
            for i, row in enumerate(tables[3][2:6]):
                require(row[:2]==[REF['outcomes'][i%2],REF['groups'][i//2]], 'Wrong cell orientation')
                for value, want in zip(row[2:], (REF['counts'][i],REF['expected'][i],REF['totals'][i//2],REF['group_proportions'][i],REF['overall_proportions'][i])):
                    displayed(value,want)
            require(len(tables[4])==2 or tables[4][2:]==[['']], 'Unexpected removed levels')
            require(tables[5][2][0]=='Pearson chi-square' and tables[5][2][2]=='approximation', 'Wrong primary test')
            displayed(tables[5][2][1],REF['p'])
            for value,key in zip(tables[6][2],('statistic','df','p')): displayed(value,REF[key])
            for value,key in zip(tables[7][2][:2],('raw','corrected')): displayed(value,REF[key])
            require(tables[7][2][2]=='points_only', 'Unlabelled effect points')
            require('No confidence intervals' in tables[7][-1][0], 'Missing interval omission')
            for i,row in enumerate(tables[8][2:]):
                require(row[:4]==[str(i+1),'.',REF['outcomes'][i%2],REF['groups'][i//2]], 'Wrong source identities')
                displayed(row[4],REF['counts'][i])
        else: require(len(tables[3])==2 or tables[3][2:]==[['']], 'Unexpected removed levels in off state')
    if archive:
        paths = re.findall(r'<img[^>]*src="([^"]+\.png)"',html)
        blobs = [archive.read(unquote(p)) for p in paths]
        require(len([n for n in archive.namelist() if n.endswith('.png')])==len(blobs), 'Stale cached PNG')
    else:
        blobs = [base64.b64decode(re.sub(r'\s','',p),validate=True) for p in re.findall(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)',html)]
    require(len(blobs)==(0 if mode in ('off','incomplete') else 1), 'Wrong plot count '+mode)
    return [base.image_info(b) for b in blobs]


def check():
    report, tables, data = {}, {}, []
    for mode in MODES:
        with zipfile.ZipFile(EXPORTS/f'python-barstats-0.3.71-{mode}.omv') as z:
            require(z.testzip() is None, 'Invalid OMV '+mode)
            html = z.read('index.html').decode()
            report[mode] = inspect(html,mode,z)
            tables[mode] = base.module.Tables(html).tables
            data.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==data[0] for d in data), 'Lifecycle changed dataset/metadata bytes')
    for mode in ('percentage','recovered','reopened'):
        require(tables[mode]==tables['count'], 'Equivalent numerical tables changed '+mode)
    for mode in ('recovered','reopened'):
        require(report[mode][0]['pixel_sha256']==report['count'][0]['pixel_sha256'], 'Recovered count plot changed '+mode)
    require(report['percentage'][0]['pixel_sha256']!=report['count'][0]['pixel_sha256'], 'Scale/labels did not change plot')
    html = (EXPORTS/'python-barstats-0.3.71-reopened.html').read_text()
    report['HTML'] = inspect(html,'reopened')
    require(report['HTML'][0]['pixel_sha256']==report['count'][0]['pixel_sha256'], 'HTML plot changed')
    png = base.image_info((EXPORTS/'python-barstats-0.3.71-plot.png').read_bytes())
    source = base.image_info((EXPORTS/'python-barstats-0.3.71-native-source.png').read_bytes())
    require(png['dimensions']==[1300,900], 'Unexpected PNG export dimensions')
    require(png==source, 'Direct PNG differs from independently checked native source example')
    report['directPNG'] = png
    chunks = re.findall(r'<table\b[^>]*>.*?</table>',html,re.S)
    probes = dict(count=html.replace(chunks[3],chunks[3].replace('12.00','99.00',1),1),
                  denominator=html.replace(chunks[2],chunks[2].replace('20.0','99.0',1),1),
                  effect=html.replace(chunks[7],chunks[7].replace('0.535','0.999',1),1),
                  plot=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=\s]+','',html,count=1))
    for name,changed in probes.items():
        require(changed!=html, 'No-op corruption '+name)
        try: inspect(changed,'reopened')
        except (ValueError,IndexError): continue
        raise ValueError('Accepted corrupted artifact '+name)
    return dict(scope='Actual native saves and exports; full methods and other platforms separate',
                states=report,unchanged_dataset_bytes=True,rejected_corruptions=list(probes))


if __name__=='__main__':
    report = check()
    (EXPORTS/'python-barstats-0.3.71-artifacts-20261114.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
