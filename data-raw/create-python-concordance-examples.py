"""Deterministic synthetic same-unit measurements; no patient data."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
first = [10,12,14,16,18,20,22,24,26,28,30,32,None,36,None]
second = [11,11,16,15,20,19,24,23,29,27,33,31,35,None,None]
with (ROOT/'data/python_concordance_examples.csv').open('w', newline='') as stream:
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['Case', 'Method_A', 'Method_B'])
    for i, (x, y) in enumerate(zip(first, second)):
        writer.writerow([f'S{i+1:02d}', x, y])
