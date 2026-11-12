"""Synthetic paired binary calls, with audited missing and outside-pair rows."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reference = json.loads((ROOT/'tests/fixtures/paired-decision.json').read_text())
fixture = next(x for x in reference['fixtures'] if x['id'] == 'hand_correctness_not_positivity')
labels = ['Negative', 'Positive']
rows = [[f'S{i+1:02d}', labels[code]]+
        [labels[fixture['tests'][test][i]] for test in ('A', 'B', 'C')]
        for i, code in enumerate(fixture['reference'])]
rows += [['S17', 'Positive', '', 'Positive', 'Positive'],
         ['S18', '', 'Positive', 'Positive', 'Positive'],
         ['S19', 'Negative', 'Negative', '', 'Negative'],
         ['S20', 'Positive', 'Positive', 'Negative', 'Indeterminate']]
with (ROOT/'data/python_paired_test_examples.csv').open('w', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['Case', 'Reference', 'Test_A', 'Test_B', 'Test_C'])
    writer.writerows(rows)
