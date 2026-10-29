"""Deterministic synthetic categorical tree example; contains no patient data."""
import csv
from pathlib import Path
rows=[(tumor,grade,stage) for tumor,grade,stage,n in [('Type A','I','Early',12),('Type A','II','Early',6),('Type A','II','Advanced',4),('Type B','II','Early',5),('Type B','III','Advanced',7),('Type C','III','Advanced',2)] for _ in range(n)]
rows += [('', 'II','Early'),('Type A','','Advanced')]
with (Path(__file__).resolve().parents[1]/'data/python_variable_tree_examples.csv').open('w',newline='') as h:
    w=csv.writer(h);w.writerow(['Tumor','Grade','Stage']);w.writerows(rows)
