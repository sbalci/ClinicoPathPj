import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
spec=importlib.util.spec_from_file_location('ihc',ROOT/'inst/python/analyses/descriptives/pyihcheatmap.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=Output(m.SPEC,['2','4','7','9'])
m.run({'a':np.array([0.,10,1,11]),'b':np.array([0.,20,2,22]),'c':np.array([0.,5,.5,5.5]),
       'id':['same','same','other','other'],'g':['<unsafe>']*4},
      dict(markers=['a','b','c'],subject='id',group='g',showScatter=True,
           clusterRows=True,clusterColumns=True,showDendrograms=True),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
