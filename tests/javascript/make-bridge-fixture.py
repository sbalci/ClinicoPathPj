"""Write the six-row bridge DOM fixture using the same Python workflow as jamovi."""
import importlib.util
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor,Output

spec=importlib.util.spec_from_file_location('bridge',ROOT/'inst/python/analyses/meddecide/pybridgecompare.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
out=Output(module.SPEC)
module.run({'x':np.array([1,2,2,4,5,6.]),'g':Factor(np.array([0,0,1,0,1,1]),['N','P'],False)},
           dict(marker='x',reference='g',positive='P',cutoff='2'),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])
