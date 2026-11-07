"""Create synthetic local fixtures for the inspector's DOM interaction tests."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'inst/python'),str(ROOT/'tests/python')]
from test_diagnostic_studies import data,OPTIONS
from cpj_runtime import _decode
from cpj_diagnostic_studies import calculate
from cpj_study_inspector import render
target=Path(sys.argv[1]);target.mkdir(parents=True,exist_ok=True)
studies=calculate(_decode(data()),OPTIONS,[str(2*i+3) for i in range(12)])['studies']
variants=dict(main=studies,single=studies[:1],maximum=[dict(studies[i%8],sourceID=str(i+1),study='Bounded study '+str(i+1)) for i in range(200)],hostile=[dict(studies[0],study='</script><img src=x onerror="window.pwned=1"> & label')])
for name,rows in variants.items():(target/(name+'.html')).write_text(render(rows,95))
print('Created four bounded synthetic inspector fixtures')

for name,included,valid in [('included',['3','7'],True),('empty',[],True),('stale',[],False)]:
    (target/(name+'.html')).write_text(render(studies,95,dict(snapshot='a'*64,valid=valid,included=included)))
