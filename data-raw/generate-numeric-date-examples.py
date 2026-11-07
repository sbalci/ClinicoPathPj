"""Synthetic equivalent packed, Excel and Unix pairs with one malformed packed variant."""
import csv
from datetime import datetime,timezone
from pathlib import Path
pairs=[('2024-01-31','2024-02-29'),('2024-01-31','2024-03-01'),
       ('2024-02-29','2024-03-01'),('2024-03-01','2024-04-01'),
       ('2024-01-01','2024-12-31'),(None,'2024-01-01')]
def encode(value,fmt):
    if value is None:return ''
    d=datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    if fmt=='packed':return int(d.strftime('%Y%m%d'))
    origin=datetime(1970,1,1,tzinfo=timezone.utc) if fmt=='Unix' else datetime(1899,12,30,tzinfo=timezone.utc) if fmt=='Excel1900' else datetime(1904,1,1,tzinfo=timezone.utc)
    return int((d-origin).total_seconds()/(1 if fmt=='Unix' else 86400))
with (Path(__file__).resolve().parents[1]/'data/python_numeric_date_examples.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Record']+[f'{side} {fmt}' for fmt in ['packed','Excel1900','Excel1904','Unix'] for side in ['Start','End']]+['Malformed packed end'])
    for i,(a,b) in enumerate(pairs,1):
        w.writerow([f'Synthetic {i}']+[encode(d,fmt) for fmt in ['packed','Excel1900','Excel1904','Unix'] for d in [a,b]]+[20240230 if i==5 else encode(b,'packed')])
