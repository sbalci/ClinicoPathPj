"""Synthetic numeric interval2 endpoints; no survival model or patient records."""
import csv
from pathlib import Path
left=[1,None,1,1,None,5,-3,0,4,None]
right=[1,3,None,4,None,2,-1,0,4,0]
with (Path(__file__).resolve().parents[1]/'data/python_interval_censoring_examples.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Record','Left endpoint','Right endpoint'])
    for i,(a,b) in enumerate(zip(left,right),1):w.writerow([f'Synthetic interval {i}',a,b])
