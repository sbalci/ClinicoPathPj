"""Synthetic unequal marker memberships for plotting; no patient data."""
import csv
from pathlib import Path

COUNTS = [12, 8, 6, 10, 4, 5, 3, 2, 3, 1, 2, 1, 1, 0, 1, 1]
ROOT = Path(__file__).resolve().parents[1]
rows = []
for code, count in enumerate(COUNTS):
    row = ['Positive' if (code >> j) & 1 else 'Negative' for j in range(4)]
    rows.extend([row] * count)
rows.extend([['', 'Positive', 'Negative', 'Negative'],
             ['Negative', 'Negative', '', 'Negative']])
with (ROOT / 'data/python_set_intersection_unequal_examples.csv').open('w', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(['Marker_A', 'Marker_B', 'Marker_C', 'Marker_D'])
    writer.writerows(rows)
print(f'{sum(COUNTS)} complete rows + 2 missing-value examples')
