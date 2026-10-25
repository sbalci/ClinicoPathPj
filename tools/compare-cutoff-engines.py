"""Warm Python-only comparison; excludes process startup, native rendering and browser work."""
import csv
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'inst/python'))
from cpj_runtime import Factor, Output

records = list(csv.DictReader((ROOT / 'data/python_d3_cutoff_examples.csv').open()))
x = np.array([float(r['Measurement']) for r in records])
g = Factor(np.array([int(r['Reference'] == 'Positive') for r in records]),
           ['Negative', 'Positive'], False)
results = []
for name, direction in [('pydotdecision', 'high'), ('pyd3cutoff', 'ge'), ('pyobservablecutoff', 'ge')]:
    spec = importlib.util.spec_from_file_location(name, ROOT / 'inst/python/analyses/meddecide' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    options = dict(marker='Measurement', reference='Reference', positive='Positive',
                   cutoff='2', direction=direction)
    times = []
    for i in range(8):
        out = Output(module.SPEC)
        start = time.perf_counter()
        module.run(dict(Measurement=x, Reference=g), options, out)
        elapsed = time.perf_counter() - start
        if i:
            times.append(elapsed)
    results.append(dict(analysis=name, rows=len(x),
                        median_python_run_seconds=statistics.median(times),
                        html_bytes=len(out.htmls['explorer'].encode())))
print(json.dumps(results, indent=2))
