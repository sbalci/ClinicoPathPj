"""Synthetic node-summary example with node-local numeric missingness; no patient data."""
import csv
from pathlib import Path
rows=[('Type A','I',10),('Type A','I',14),('Type A','II',20),('Type A','II',''),('Type B','III',30),('Type B','III',''),('Type C','III',''),('','III',999)]
with (Path(__file__).resolve().parents[1]/'data/python_tree_node_summary_examples.csv').open('w',newline='') as handle:
    writer=csv.writer(handle);writer.writerow(['Tumor','Grade','MarkerScore']);writer.writerows(rows)
