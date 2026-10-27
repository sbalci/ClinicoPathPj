"""Synthetic tied/missing, constant and empty-pair views for rectangle inspection."""
import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
spec=importlib.util.spec_from_file_location('ihc',ROOT/'inst/python/analyses/descriptives/pyihcheatmap.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data={'a':np.array([0.,0,1,2]),'b':np.array([0.,0,np.nan,2]),'c':np.array([0.,1,2,3]),
      'id':['same','same','partial','other']}
ids=['2','4','7','9']
if '--empty' in sys.argv:
 data={'a':np.array([0.,np.nan]),'b':np.array([np.nan,0]),'c':np.array([1.,2.]),'id':['left','right']};ids=['2','4']
if '--constant' in sys.argv:data['a']=np.ones(4)
out=Output(m.SPEC,ids)
m.run(data,dict(markers=['a','b','c'],subject='id',showScatter=True,enableSelection=True,
                scaling='zscore' if '--zscore' in sys.argv else 'raw'),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
