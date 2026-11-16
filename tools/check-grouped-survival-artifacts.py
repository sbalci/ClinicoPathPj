"""Check GUI-saved grouped tables and static exports against independent R values."""
import base64
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'
s=importlib.util.spec_from_file_location('grouped_artifact_base',ROOT/'tools/check-estimation-artifacts.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
require,displayed=base.require,base.displayed
REF=json.loads(subprocess.check_output(['Rscript','--vanilla','tests/reference/grouped-survival-example.R'],cwd=ROOT,text=True))
with (ROOT/'data/python_grouped_survival_examples.csv').open() as f:SOURCE=list(csv.DictReader(f))
MODES=('default','plotted','off','incomplete','invalid','recovered','reopened')
TITLES=('Retained Cohort','Event Definition and Time Scale','Missingness by Role','Group Follow-up and Counts',
    'Overall Log-Rank Test','Log-Rank Group Contributions','Log-Rank Covariance Audit',
    'Pooled Event-Time Risk Sets (First 1,000 Group Rows)','Group Survival Medians',
    'Estimates at Requested Times','Kaplan–Meier Steps','Retained Original Source Rows')


def records(table):return [r for r in table[2:] if not(len(r)==1 and r[0].startswith('Note.'))]


def canonical_tables(tables):
    return [[[re.sub(r'(?<=\d)\s+(?=%$)','',cell) if re.fullmatch(r'[-−0-9.]+\s*%',cell) else cell
        for cell in row] for row in table] for table in tables]


def inspect(html,mode,archive=None):
    require(mode in MODES,'Unknown profile')
    tables=base.module.Tables(html).tables;extended=mode in ('plotted','incomplete','invalid','recovered','reopened')
    expected=list(TITLES if extended else [t for i,t in enumerate(TITLES) if i not in (6,7,10,11)])
    require([t[0][0] for t in tables]==expected,'Wrong native tables or order')
    byname={t[0][0]:records(t) for t in tables}
    if mode in ('incomplete','invalid'):
        require(all(rows==[['']] for rows in byname.values()),'Stale invalid/incomplete native table')
        require('9 complete subjects' not in html,'Stale cohort narrative')
    else:
        row=byname[TITLES[0]][0]
        for v,key in zip(row,('source','complete','excluded','events','censored')):displayed(v,REF['cohort'][key])
        displayed(row[5],0);displayed(row[6],3)
        require(byname[TITLES[1]][0]==['Status','Event','Censored','months','Origin of supplied elapsed times','Group'],'Wrong explicit roles or unit')
        require(byname[TITLES[2]]==[['Elapsed time','Months','1'],['Outcome','Status','1'],['Group','Group','1']],'Wrong missing-role counts')
        groups={g['label']:g for g in REF['groups']}
        require(len(byname[TITLES[3]])==len(groups),'Wrong group count')
        for row in byname[TITLES[3]]:
            g=groups[row[0]]
            for v,k in zip(row[1:5],('n','events','censored','maximum')):displayed(v,g[k])
            displayed(row[5],g['maximum']);displayed(row[6],0)
        test=byname[TITLES[4]][0];require(test[0]=='Unweighted log-rank (rho = 0)' and test[-1]=='available','Wrong test/method availability')
        for v,k in zip(test[1:4],('statistic','df','p')):displayed(v,REF['logrank'][k])
        for row in byname[TITLES[5]]:
            label=row[0]
            displayed(row[1],REF['logrank']['observed'][label]);displayed(row[2],REF['logrank']['expected'][label])
            displayed(row[3],REF['logrank']['observed'][label]-REF['logrank']['expected'][label]);require(row[4]=='Yes','Wrong eligible contrast')
        require(len(byname[TITLES[8]])==3,'Wrong median group count')
        for row in byname[TITLES[8]]:
            for value,key in zip(row[1:4],('median','0.95LCL','0.95UCL')):displayed(value,groups[row[0]]['median'][key])
            displayed(row[4],.95);require(row[5]=='months','Wrong median unit')
        selected=byname[TITLES[9]];require(len(selected)==5,'Wrong group-specific horizon support')
        for row in selected:
            g=groups[row[0]];ref=next(p for p in g['selected'] if abs(float(row[1])-p['time'])<1e-10)
            require(row[2]=='months','Wrong horizon unit')
            for value,key in zip(row[3:6],('risk','events','censored')):displayed(value,ref[key])
            retained=[r for r in SOURCE if r['Group']==g['label'] and r['Months'] and r['Status'] and float(r['Months'])<=ref['time']]
            displayed(row[6],sum(r['Status']=='Event' for r in retained));displayed(row[7],sum(r['Status']=='Censored' for r in retained))
            for value,key in zip(row[8:11],('survival','lower','upper')):displayed(value,ref[key])
        if extended:
            labels=[g['label'] for g in REF['groups']]
            covariance=byname[TITLES[6]];require(len(covariance)==9,'Wrong covariance dimensions')
            for row in covariance:displayed(row[2],REF['logrank']['variance'][labels.index(row[0])][labels.index(row[1])])
            complete=[r for r in SOURCE if all(r[k] for k in ('Months','Status','Group'))]
            risks=byname[TITLES[7]];require(len(risks)==12,'Wrong pooled risk audit size')
            for row in risks:
                t=float(row[0]);label=row[1];at=[r for r in complete if float(r['Months'])>=t]
                events=[r for r in at if float(r['Months'])==t and r['Status']=='Event']
                risk=sum(r['Group']==label for r in at)
                for value,number in zip(row[2:],(risk,sum(r['Group']==label for r in events),len(events)*risk/len(at),len(at),len(events))):displayed(value,number)
            steps=byname[TITLES[10]];require(len(steps)==9,'Wrong group KM steps')
            for row in steps:
                ref=next(r for r in groups[row[0]]['steps'] if r['time']==float(row[1]))
                for value,key in zip(row[1:],('time','risk','events','censored','survival','se','lower','upper')):displayed(value,ref[key])
            cases=byname[TITLES[11]];require(len(cases)==9,'Wrong retained source rows')
            for row,i in zip(cases,range(9)):
                source=SOURCE[i]
                require(row[:3]==[source['Group'],str(i+1),source['Subject']],'Changed source/subject/group identity')
                for value in row[3:5]:displayed(value,float(source['Months']))
                require(row[5]==source['Status'],'Changed outcome label');displayed(row[6],int(source['Status']=='Event'))
    if archive is None:
        blobs=[base64.b64decode(re.sub(r'\s','',x),validate=True) for x in re.findall(r'<img\b[^>]*\bsrc="data:image/png;base64,([A-Za-z0-9+/=\s]+)"',html)]
    else:blobs=[archive.read(unquote(x)) for x in re.findall(r'<img[^>]*src="([^"]+\.png)"',html)]
    require(len(blobs)==int(mode in ('plotted','recovered','reopened')),'Missing or stale plot')
    return [base.image_info(b) for b in blobs]


def check():
    report={};datasets=[];tables={}
    for mode in MODES:
        with ZipFile(EXPORTS/f'python-grouped-survival-0.3.78-{mode}.omv') as z:
            require(z.testzip() is None,'OMV CRC failure');html=z.read('index.html').decode()
            report[mode]=inspect(html,mode,z);tables[mode]=base.module.Tables(html).tables
            datasets.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==datasets[0] for d in datasets),'Lifecycle changed source data/metadata')
    require(tables['plotted']==tables['recovered']==tables['reopened'],'Equivalent input tables changed')
    require(report['plotted']==report['recovered']==report['reopened'],'Equivalent cached plot changed')
    html=(EXPORTS/'python-grouped-survival-0.3.78-reopened.html').read_text();images=inspect(html,'reopened')
    require(canonical_tables(base.module.Tables(html).tables)==canonical_tables(tables['reopened']),'HTML and saved native tables differ')
    require([(p['dimensions'],p['pixel_sha256']) for p in images]==[(p['dimensions'],p['pixel_sha256']) for p in report['reopened']],'HTML/cached pixels differ')
    direct=base.image_info((EXPORTS/'python-grouped-survival-0.3.78-plot.png').read_bytes())
    native=base.image_info(Path('/private/tmp/cpj-grouped-0.3.78-native-reference.png').read_bytes())
    require(direct==native,'Direct native PNG differs at matching resolution')
    cached=base.image_info(Path('/private/tmp/cpj-grouped-0.3.78-native-cached-size.png').read_bytes())
    require((cached['dimensions'],cached['pixel_sha256'])==(report['reopened'][0]['dimensions'],report['reopened'][0]['pixel_sha256']),'Cached native PNG differs at matching resolution')
    mutations=[html.replace('>12<','>13<',1),html.replace('>8.12<','>9.12<',1),html.replace('>S01<','>S99<',1),
        re.sub(r'<img(?=[^>]*src="data:image/png;base64,)','<disabled-img',html,count=1)]
    for changed in mutations:
        require(changed!=html,'No-op corruption probe')
        try:inspect(changed,'reopened')
        except (ValueError,IndexError,KeyError,StopIteration):pass
        else:raise ValueError('Corrupted native artifact accepted')
    def legacy(path):
        with ZipFile(path) as archive:
            require(archive.testzip() is None,'Legacy OMV CRC failure')
            return ({k:archive.read(k) for k in ('data.bin','metadata.json','xdata.json')},
                base.module.Tables(archive.read('index.html').decode()).tables,
                [base.image_info(archive.read(n)) for n in archive.namelist() if n.endswith('.png')])
    require(legacy(EXPORTS/'python-singlearm-0.3.77-reopened.omv')==
            legacy(EXPORTS/'python-singlearm-0.3.78-compatibility.omv'),
            'Prior single-cohort source data, native tables or cached PNG changed')
    report.update(legacy_singlearm='0.3.77 data, native tables and cached PNG unchanged after fresh-engine rerun/save',saved_profiles=len(MODES),corruptions_rejected=len(mutations),native_PNG=direct,
        scope='Bounded macOS arm64 synthetic native lifecycle/export; full methods/clinical/other-platform gates pending')
    return report


if __name__=='__main__':print(json.dumps(check(),indent=2))
