"""Synthetic unequal categorical paths, with two incomplete profiles; no patient data."""
import csv
from pathlib import Path

rows = [('Type A','Negative','Low')]*12 + [('Type A','Positive','Low')]*5
rows += [('Type B','Negative','High')]*2 + [('Type B','Positive','High')]
rows += [('Type A','','Low'), ('','Positive','High')]
path = Path(__file__).resolve().parents[1] / 'data/python_alluvial_examples.csv'
with path.open('w', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(['Diagnosis','Marker','Response'])
    writer.writerows(rows)
