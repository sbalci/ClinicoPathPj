"""Validate 0.3.79 native prompt snapshots and curated Data Library round trips."""
import html as html_module
import importlib.util
import json
from pathlib import Path
import re
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1];EXPORTS=ROOT/'docs/validation-exports'


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

grouped=load('prompt_grouped',ROOT/'tools/check-grouped-survival-artifacts.py')
single=load('prompt_single',ROOT/'tools/check-singlearm-artifacts.py')
require=grouped.require;base=grouped.base


def plain(html):return re.sub(r'\s+',' ',html_module.unescape(re.sub(r'<[^>]*>',' ',html))).strip()


def pending_notice(html,mode,counts):
    wording='indicates censoring' if mode=='censor' else 'is the event'
    expected='Choose which level of Status '+wording+': '+counts
    require(expected in plain(html),'Incorrect pending '+mode+' notice')
    if mode=='event':require('indicates censoring' not in plain(html),'Event prompt changed')


def snapshot(path,inspector,mode):
    with ZipFile(path) as z:
        require(z.testzip() is None,'Saved ZIP CRC failure')
        text=z.read('index.html').decode()
        images=inspector(text,mode,z)
        return dict(data={k:z.read(k) for k in ('data.bin','metadata.json','xdata.json')},
            tables=base.module.Tables(text).tables,images=images,html=text)


def check():
    report={};corruptions=0
    for kind,inspector,source,counts in (
        ('grouped',grouped.inspect,ROOT/'data/python_grouped_survival_examples.omv','Censored (5 rows), Event (6 rows).'),
        ('single',single.inspect,EXPORTS/'python-singlearm-0.3.78-compatibility.omv','Censored (5 rows), Event (5 rows).')):
        previous=snapshot(source,inspector,'reopened')
        valid=[];profiles={}
        for mode in ('valid','censor','event','recovered')+ (('reopened',) if kind=='grouped' else ()):
            path=EXPORTS/f'python-survival-prompts-0.3.79-{kind}-{mode}.omv'
            pending=mode in ('censor','event')
            got=snapshot(path,inspector,'incomplete' if pending else 'reopened')
            require(got['data']==previous['data'],kind+' data/metadata changed')
            if pending:
                wording='indicates censoring' if mode=='censor' else 'is the event'
                pending_notice(got['html'],mode,counts)
                changed=got['html'].replace(wording,'has the wrong role')
                require(changed!=got['html'],'No-op role corruption')
                try:pending_notice(changed,mode,counts)
                except ValueError:corruptions+=1
                else:raise ValueError('Corrupt pending role message accepted')
            else:
                require(got['tables']==previous['tables'],kind+' changed valid native tables')
                require(got['images']==previous['images'],kind+' changed cached image')
                valid.append(got)
            profiles[mode]=got['images']
        report[kind]=dict(profiles=profiles,source_unchanged=True,valid_tables_and_cached_pixels_unchanged=True)
    html=(EXPORTS/'python-survival-prompts-0.3.79-grouped-reopened.html').read_text()
    images=grouped.inspect(html,'reopened')
    with ZipFile(EXPORTS/'python-survival-prompts-0.3.79-grouped-reopened.omv') as z:
        cached=z.read('index.html').decode()
    require(grouped.canonical_tables(base.module.Tables(html).tables)==grouped.canonical_tables(base.module.Tables(cached).tables),'HTML/native saved tables differ')
    require([(i['dimensions'],i['pixel_sha256']) for i in images]==[(i['dimensions'],i['pixel_sha256']) for i in report['grouped']['profiles']['reopened']],'HTML and cached image pixels differ')
    direct=base.image_info((EXPORTS/'python-survival-prompts-0.3.79-grouped-plot.png').read_bytes())
    reference=base.image_info(Path('/private/tmp/cpj-grouped-0.3.79-native-reference.png').read_bytes())
    require(direct==reference,'Native PNG and independent reference export differ')
    report.update(profiles=9,prompt_corruptions_rejected=corruptions,native_PNG=direct,
        scope='macOS arm64/jamovi 28.17.0 native prompt/curated example lifecycle/export; full methods and other platforms pending')
    return report


if __name__=='__main__':print(json.dumps(check(),indent=2))
