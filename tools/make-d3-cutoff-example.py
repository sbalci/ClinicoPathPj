"""Reproduce the synthetic teaching fixture from Maurizio Agosti's shared D3 demo."""
import csv
import random
from pathlib import Path

rng = random.Random(20261025)
path = Path(__file__).resolve().parents[1] / 'data/python_d3_cutoff_examples.csv'
with path.open('w', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['Row', 'Measurement', 'Reference'])
    for index in range(180):
        positive = index >= 125
        value = rng.gauss(3.0 if positive else .65, 1.1 if positive else 1.0)
        writer.writerow([index + 1, value, 'Positive' if positive else 'Negative'])
print(path)
