import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
s=importlib.util.spec_from_file_location('corr',ROOT/'inst/python/analyses/jjstatsplot/pyjjcorrmat.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=Output(m.SPEC);name='<unsafe>'
if len(sys.argv)>2:
 n=int(sys.argv[2]); names=['marker'+str(i) for i in range(n)]
 m.run({v:np.array([1.,2,4,3])+i for i,v in enumerate(names)},dict(dep=names,interactive=True),out)
 Path(sys.argv[1]).write_text(out.htmls['explorer']);sys.exit(0)
m.run({name:np.array([1.,2,3,4]),'b':np.array([1.,2,4,3]),'constant':np.ones(4)},dict(dep=[name,'b','constant'],interactive=True),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
