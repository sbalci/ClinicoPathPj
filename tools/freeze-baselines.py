"""Explicitly freeze the 61 migration targets. Developer tool; requires PyYAML.

Run only when intentionally establishing a new baseline: python3 tools/freeze-baselines.py.
Normal builds never refresh baselines from mutable sibling repositories.
"""
import ast
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
 'ClinicoPathDescriptives': ('descriptives', 'Descriptives', 'agepyramid alluvial benford categorize checkdata chisqposttest crosstable dataquality outlierdetection reportcat summarydata tableone vartree venn'),
 'jjstatsplot': ('jjstatsplot', 'Statistical Plots', 'advancedraincloud hullplot jjarcdiagram jjbarstats jjbetweenstats jjcorrmat jjdotchart jjdotplotstats jjhistostats jjpiestats jjridges jjscatterstats jjsegmentedtotalbar jwaffle jjwithinstats linechart lollipop raincloud statsplot2'),
 'meddecide': ('meddecide', 'Medical Decisions', 'agreement cotest decision decisioncalculator decisioncombine decisioncompare decisioncurve enhancedROC kappaSizeCI kappaSizeFixedN kappaSizePower lassologistic nogoldstandard psychopdaROC sequentialtests'),
 'jsurvival': ('jsurvival', 'Survival', 'datetimeconverter lassocox multisurvival oddsratio outcomeorganizer singlearm survival survivalcont timeinterval'),
 'OncoPath': ('oncopath', 'Oncology', 'diagnosticmeta ihcheterogeneity swimmerplot waterfall'),
}
PORTS = {'benford':'pybenford', 'chisqposttest':'pychisqposttest', 'cotest':'pycotest',
 'decision':'pydecision', 'decisioncalculator':'pydecisioncalculator',
 'decisioncurve':'pydecisioncurve', 'sequentialtests':'pysequentialtests',
 'kappaSizeCI':'pykappaci', 'kappaSizeFixedN':'pykappafixedn', 'kappaSizePower':'pykappapower'}

def sha(data): return hashlib.sha256(data).hexdigest()
def spec(path):
 tree=ast.parse(path.read_text())
 return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets)))

def main():
 target=ROOT/'inst/python/registry.json'
 if target.exists(): raise SystemExit('Baseline already exists; archive and review it before replacing it.')
 roadmap=json.loads((ROOT/'docs/python-roadmap.json').read_text())['analyses']
 records=[]; snapshots={}; packed={}
 for module,(folder,menu,names) in FAMILIES.items():
  for name in names.split():
   source=ROOT.parent/(module if name!='timeinterval' else 'ClinicoPathJamoviModule')
   manifest=yaml.safe_load((source/'jamovi/0000.yaml').read_text())
   files={}; defs={}
   for relative in [f'jamovi/{name}.{k}.yaml' for k in ('a','r','u')]+[f'R/{name}.b.R']:
    data=(source/relative).read_bytes(); files[relative]=sha(data); packed[f'{source.name}/{relative}']=data
    if relative.endswith('.yaml'): defs[relative.split('.')[-2]]=yaml.safe_load(data)
   baseline={'module':source.name,'version':str(manifest['version']),
    'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
    'provenance':'production-routing candidate' if name=='timeinterval' else 'sibling manifest',
    'files':files}
   old=PORTS.get(name); legacy=spec(ROOT/f'inst/python/analyses/{old}.py') if old else None
   row={'id':old or 'py'+name.lower(),'source_name':name,'family':folder,'menu':menu,'title':defs['a']['title'],
    'aliases':[],'source':f'analyses/{folder}/{old}.py' if old else None,
    'baseline':baseline,'wave':1 if module=='ClinicoPathDescriptives' or name in ('datetimeconverter','outcomeorganizer','timeinterval') else 2 if module=='meddecide' and name not in ('agreement','lassologistic','nogoldstandard') else 3 if module=='jjstatsplot' else 5 if module=='OncoPath' else 4,
    'status':'partial' if old else 'planned','coverage':{'full_parity':False,'numerical':'existing core tests' if old else 'pending','gui':'pending','compatibility':'pending','platforms':[]},
    'methods':roadmap[name]['core_method'],'oracle':roadmap[name]['oracle'],
    'dependencies':{'bundled':['numpy','scipy'] if old else [],'candidates':roadmap[name].get('needs',[])},
    'legacy_title':legacy['title'] if old else None}
   records.append(row); snapshots[name]={'baseline':baseline,'definitions':defs}
 # Utilities are retained and participate in registry-based loading and UI generation.
 for p in sorted((ROOT/'inst/python/analyses').glob('*.py')):
  s=spec(p)
  if p.stem in PORTS.values(): continue
  folder='jjstatsplot' if p.stem=='pywelch' else 'descriptives' if p.stem=='pydescriptives' else 'meddecide' if p.stem in ('pyexacttests','pydotdecision') else 'utilities'
  menu=next((v[1] for v in FAMILIES.values() if v[0]==folder),'Utilities')
  records.append({'id':p.stem,'family':folder,'menu':menu,'title':s['title'],'aliases':[],
    'source':f'analyses/{folder}/{p.name}','status':'utility','coverage':{'full_parity':False}})
 target.write_text(json.dumps({'schema_version':1,'module':'ClinicoPathPj','baseline_date':'2026-10-25','analyses':records},indent=2)+'\n')
 (ROOT/'docs/baselines/released-2026-10-25.json').write_text(json.dumps(snapshots,indent=2,default=str)+'\n')
 with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz','w:gz') as archive:
  for name,data in sorted(packed.items()):
   info=tarfile.TarInfo(name); info.size=len(data); info.mtime=0; archive.addfile(info,io.BytesIO(data))
 print(f'Frozen {len(snapshots)} targets and {len(records)-len(snapshots)} retained utilities.')

if __name__=='__main__': main()
