"""Synthetic overall-cohort example; the blank variable is deliberately uncollected."""
import csv
from pathlib import Path

root=Path(__file__).resolve().parents[1]
with (root/'data/python_cross_table_examples.csv').open() as handle:
    records=list(csv.DictReader(handle))
with (root/'data/python_table_one_examples.csv').open('w',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(records[0])+['NeverCollected'])
    writer.writeheader()
    for row in records:writer.writerow(dict(row,NeverCollected=''))
