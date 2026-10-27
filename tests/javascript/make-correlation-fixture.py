import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
s=importlib.util.spec_from_file_location('corr',ROOT/'inst/python/analyses/jjstatsplot/pyjjcorrmat.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=Output(m.SPEC);name='<unsafe>'
m.run({name:np.array([1.,2,3,4]),'b':np.array([1.,2,4,3]),'constant':np.ones(4)},dict(dep=[name,'b','constant'],interactive=True),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
