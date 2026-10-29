"""Synthetic reference proportions with node-local missingness; contains no patient data."""
import csv
from pathlib import Path
rows=[('Type A','I',10,'Positive'),('Type A','I',14,''),('Type A','II',20,'Negative'),('Type A','II','','Positive'),('Type B','III',30,'Negative'),('Type B','III','',''),('Type C','III','',''),('','III',999,'Positive')]
with (Path(__file__).resolve().parents[1]/'data/python_tree_reference_examples.csv').open('w',newline='') as handle:
    writer=csv.writer(handle);writer.writerow(['Tumor','Grade','MarkerScore','MarkerStatus']);writer.writerows(rows)
