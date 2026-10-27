"""Bounded maximum and singleton heatmaps for roving keyboard-focus checks."""
import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Output
spec=importlib.util.spec_from_file_location('ihc',ROOT/'inst/python/analyses/descriptives/pyihcheatmap.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
n,markers=(1,3) if '--single' in sys.argv else (200,20)
data={f'm {j}':np.arange(n,dtype=float)+j for j in range(markers)}
out=Output(m.SPEC,[str(2*i+1) for i in range(n)])
m.run(data,dict(markers=list(data),enableSelection=True,showScatter='--scatter' in sys.argv),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
