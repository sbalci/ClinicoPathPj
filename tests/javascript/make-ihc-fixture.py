import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
s=importlib.util.spec_from_file_location('ihc',ROOT/'inst/python/analyses/descriptives/pyihcheatmap.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=Output(m.SPEC,['7','9','20'])
m.run({'a':np.array([1.,2,3]),'b':np.array([3.,np.nan,5]),'c':np.array([5.,6,7]),
       'g':['<unsafe>','NA','third'],'id':['same','same','other']},
      dict(markers=['a','b','c'],group='g',subject='id',interactive=True,showScatter=True),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
