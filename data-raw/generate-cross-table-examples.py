"""Synthetic grouped measurements and categories, with explicit missingness."""
import csv
from pathlib import Path

rows = []
for group, offset, positives in [('Control',30,4),('Intervention',35,8)]:
    for i in range(12):
        age = '' if (group == 'Control' and i == 1) or (group == 'Intervention' and i == 2) else offset+i
        marker = '' if group == 'Control' and i == 2 else 'Positive' if i < positives else 'Negative'
        rows.append([group,age,marker,1+i%2])
rows.append(['',99,'Positive',3])
with (Path(__file__).resolve().parents[1]/'data/python_cross_table_examples.csv').open('w',newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(['Group','Age','Marker','Code'])
    writer.writerows(rows)
