"""Verify native GUI saves/exports against survival::survfit and hand-counted rows."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'
s=importlib.util.spec_from_file_location('singlearm_artifact_base',ROOT/'tools/check-estimation-artifacts.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
require,displayed=base.require,base.displayed
REF=json.loads(subprocess.check_output(['Rscript','--vanilla','tests/reference/singlearm-example.R'],cwd=ROOT,text=True))
MODES=('default','plotted','off','incomplete','invalid','recovered','reopened')
TITLES=('Retained Cohort','Event Definition and Time Scale','Missingness by Role',
        'Survival and Follow-up Medians','Estimates at Requested Times','Person-Time Event Rate',
        'Kaplan–Meier Steps','Retained Original Source Rows')


def records(table):
    rows=table[2:]
    return [r for r in rows if not(len(r)==1 and r[0].startswith('Note.'))]


def canonical_tables(tables):
    # HTML adds a space before %, while the OMV index omits it. Normalize
    # numeric percentage cells only, preserving every digit, label and unit.
    return [[[re.sub(r"(?<=\d)\s+(?=%$)","",cell)
              if re.fullmatch(r"[-−0-9.]+\s*%",cell) else cell
              for cell in row] for row in table] for table in tables]


def inspect(html,mode,archive=None):
    require(mode in MODES,'Unknown profile')
    tables=base.module.Tables(html).tables
    extended=mode in ('plotted','incomplete','invalid','recovered','reopened')
    expected=list(TITLES if extended else TITLES[:5])
    require([t[0][0] for t in tables]==expected,'Wrong native table titles/order')
    if mode in ('incomplete','invalid'):
        require(all(records(t)==[['']] for t in tables),'Stale invalid/incomplete native table')
        require('9 complete pairs' not in html,'Stale cohort narrative')
    else:
        require(records(tables[0])==[[str(v) for v in REF['cohort']]],'Wrong complete-pair cohort')
        mapping=records(tables[1])[0]
        require(mapping[:4]==['Status','Event','Censored','months'],'Wrong explicit event/unit mapping')
        for v in mapping[-2:]:displayed(v,60)
        require(records(tables[2])==[['Elapsed time','Months','1'],['Outcome','Status','1']],'Wrong overlapping missingness')
        medians=records(tables[3]);expected_medians=REF['medians'][:1 if mode=='off' else 2]
        require(len(medians)==len(expected_medians),'Wrong follow-up toggle')
        for row,ref in zip(medians,expected_medians):
            for v,k in zip(row[1:4],('median','0.95LCL','0.95UCL')):displayed(v,ref[k])
            displayed(row[4],.95);require(row[5]=='months','Wrong median units')
        selected=records(tables[4]);require(len(selected)==3,'Wrong horizon count')
        for row,ref,ce,cc in zip(selected,REF['selected'],[2,4,4],[2,3,5]):
            require(row[1]=='months','Wrong horizon units')
            for v,k in zip([row[0]]+row[2:5],('time','risk','events','censored')):displayed(v,ref[k])
            displayed(row[5],ce);displayed(row[6],cc)
            for v,k in zip(row[7:10],('survival','lower','upper')):displayed(v,ref[k])
        if extended:
            for v,k in zip(records(tables[5])[0][:5],('events','exposure','estimate','lower','upper')):displayed(v,REF['rate'][k])
            steps=records(tables[6]);require(len(steps)==len(REF['steps']),'Wrong KM step count')
            for row,ref in zip(steps,REF['steps']):
                for v,k in zip(row,('time','risk','events','censored','survival','se','lower','upper')):displayed(v,ref[k])
            cases=records(tables[7]);require(len(cases)==9,'Wrong source case count')
            for row,ref in zip(cases,REF['cases']):
                require(row[:2]==[ref['sourceID'],ref['subject']],'Changed source/subject identity')
                displayed(row[2],ref['time']);displayed(row[3],ref['time'])
                require(row[4]==ref['label'],'Wrong original status');displayed(row[5],ref['event'])
    if archive is None:
        blobs=[base64.b64decode(re.sub(r'\s','',x),validate=True) for x in
            re.findall(r'<img\b[^>]*\bsrc="data:image/png;base64,([A-Za-z0-9+/=\s]+)"',html)]
    else:
        blobs=[archive.read(unquote(x)) for x in re.findall(r'<img[^>]*src="([^"]+\.png)"',html)]
    require(len(blobs)==int(mode in ('plotted','recovered','reopened')),'Missing or stale plot')
    return [base.image_info(b) for b in blobs]


def check():
    report={};datasets=[];tables={}
    for mode in MODES:
        with ZipFile(EXPORTS/f'python-singlearm-0.3.77-{mode}.omv') as z:
            require(z.testzip() is None,'OMV CRC failure');html=z.read('index.html').decode()
            report[mode]=inspect(html,mode,z);tables[mode]=base.module.Tables(html).tables
            datasets.append({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')})
    require(all(d==datasets[0] for d in datasets),'Lifecycle changed source data or metadata')
    require(tables['plotted']==tables['recovered']==tables['reopened'],'Equivalent input tables changed')
    require(report['plotted']==report['recovered']==report['reopened'],'Equivalent cached plot pixels changed')
    html=(EXPORTS/'python-singlearm-0.3.77-reopened.html').read_text();exported=inspect(html,'reopened')
    require(canonical_tables(base.module.Tables(html).tables)==canonical_tables(tables['reopened']),
            'Native HTML and saved tables differ')
    require([(p['dimensions'],p['pixel_sha256']) for p in exported]==
            [(p['dimensions'],p['pixel_sha256']) for p in report['reopened']],
            'Native HTML and cached images differ')
    direct=base.image_info((EXPORTS/'python-singlearm-0.3.77-plot.png').read_bytes())
    reference=base.image_info(Path('/private/tmp/cpj-singlearm-0.3.77-native-reference.png').read_bytes())
    require(direct==reference,'Direct native PNG differs at matching resolution')
    cached=base.image_info(Path('/private/tmp/cpj-singlearm-0.3.77-native-cached-size.png').read_bytes())
    require((cached['dimensions'],cached['pixel_sha256'])==
            (report['reopened'][0]['dimensions'],report['reopened'][0]['pixel_sha256']),
            'Cached PNG differs at matching resolution')
    mutations=[html.replace('>11<','>10<',1),
               html.replace('>216<','>217<'),
               html.replace('>36.0<','>37.0<',1),
               re.sub(r'<img(?=[^>]*src="data:image/png;base64,)','<disabled-img',html,count=1)]
    for changed in mutations:
        require(changed!=html,'No-op corruption probe')
        try:inspect(changed,'reopened')
        except (ValueError,IndexError):pass
        else:raise ValueError('Corrupted native artifact accepted')
    def legacy(path):
        with ZipFile(path) as z:
            require(z.testzip() is None,'Legacy archive CRC failure')
            return ({k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')},
                    base.module.Tables(z.read('index.html').decode()).tables,
                    [base.image_info(z.read(n)) for n in z.namelist() if n.endswith('.png')])
    require(legacy(ROOT/'data/python_waffle_examples.omv')==
            legacy(EXPORTS/'python-waffle-0.3.77-compatibility.omv'),
            'Prior-version waffle source data, native tables or cached images changed')
    report.update(legacy_waffle='0.3.76 source data, native tables and cached PNG unchanged',saved_profiles=len(MODES),corruptions_rejected=len(mutations),native_PNG=direct,
        scope='Bounded macOS arm64 GUI synthetic lifecycle/export; no full method/clinical/other-platform qualification')
    return report

if __name__=='__main__':print(json.dumps(check(),indent=2))
