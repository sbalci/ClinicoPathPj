import sys,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor,Output
spec=importlib.util.spec_from_file_location('sets_module',ROOT/'inst/python/analyses/descriptives/pyvenn.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
out=Output(module.SPEC,['2','5','9','12','15'])
module.run({'<unsafe>':Factor(np.array([0,1,0,1,-1]),['N','Y']),'B':Factor(np.array([0,0,1,1,1]),['N','Y'])},dict(var1='<unsafe>',var2='B',var1true='Y',var2true='Y',showZero=True),out)
Path(sys.argv[1]).write_text(out.htmls['explorer'])

if len(sys.argv)>2 and sys.argv[2]=='frequency':
    out=Output(module.SPEC,['2','5','7','9','10','12','15'])
    module.run({'<unsafe>':Factor(np.array([0,1,1,0,0,1,-1]),['N','Y']),'B':Factor(np.array([0,0,0,1,1,1,1]),['N','Y'])},dict(var1='<unsafe>',var2='B',var1true='Y',var2true='Y',patternOrder='frequency'),out)
    Path(sys.argv[1]).write_text(out.htmls['explorer'])
