"""Deterministic synthetic screening measurements; no patient observations."""
import csv
from pathlib import Path
rows=[[10+i,5+(i%7)*.5] for i in range(30)]
rows += [[200,-100],['',20],[20,'']]
with (Path(__file__).resolve().parents[1]/'data/python_outlier_screening_examples.csv').open('w',newline='') as handle:
    writer=csv.writer(handle);writer.writerow(['Marker_A','Marker_B']);writer.writerows(rows)
