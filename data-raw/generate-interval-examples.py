"""Synthetic UTC elapsed intervals; no patient data."""
import csv
from datetime import date,timedelta
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with (root/'data/python_interval_examples.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['Record','Start date','End date','End with reversal'])
    for i,d in enumerate([0,1,2,6,10,30,31,60,365,366,None,None],1):
        start='' if i==12 else '2024-01-01'
        end=str(date(2024,1,1)+timedelta(days=d)) if d is not None else ''
        if i==12:end='2024-01-11'
        writer.writerow([f'Synthetic {i}',start,end,'2023-12-31' if i==5 else end])
