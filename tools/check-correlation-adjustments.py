"""Compare Python to fixtures produced by correlation-adjustment-reference.R."""
import json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'inst/python'))
from cpj_correlation import adjust
reference=json.loads(Path(sys.argv[1]).read_text())
for index,case in enumerate(reference['fixtures']):
    actual=adjust(case['p'],case['method'])
    assert [v is None for v in actual]==[v is None for v in case['expected']],index
    np.testing.assert_allclose([v for v in actual if v is not None],
                               [v for v in case['expected'] if v is not None],
                               rtol=2e-13,atol=1e-15,err_msg=f"fixture {index}: {case['method']}")
print(json.dumps(dict(oracle=reference['oracle'],R=reference['R'],
                     fixtures=len(reference['fixtures']),status='passed',
                     methods=sorted({v['method'] for v in reference['fixtures']})),indent=2))
