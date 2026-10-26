import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
s=importlib.util.spec_from_file_location('ihc',ROOT/'inst/python/analyses/descriptives/pyihcheatmap.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=Output(m.SPEC,['7','9'])
m.run({'a':np.array([1.,2]),'b':np.array([3.,np.nan]),'g':['<unsafe>','NA']},dict(markers=['a','b'],group='g',interactive=True),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
