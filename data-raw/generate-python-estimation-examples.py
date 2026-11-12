"""Build a small synthetic data-library example from independent frozen fixtures."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fixtures = json.loads((ROOT/'tests/fixtures/estimation-core.json').read_text())['fixtures']
independent = next(f for f in fixtures if f['id'] == 'hand_unequal_variance')
paired = next(f for f in fixtures if f['id'] == 'paired_missing_alignment')
path = ROOT/'data/python_estimation_examples.csv'
with path.open('w', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(['Subject', 'IndependentGroup', 'Outcome', 'FirstMeasurement', 'SecondMeasurement'])
    for i, (value, code) in enumerate(zip(independent['values'], independent['codes'])):
        writer.writerow([['001','01','1'][i] if i < 3 else f'S{i+1:02d}',
            independent['levels'][code], value,
            paired['a'][i] if i < len(paired['a']) else None,
            paired['b'][i] if i < len(paired['b']) else None])
print(path.relative_to(ROOT))
