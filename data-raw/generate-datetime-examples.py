"""PII-free independent calendar/Excel/Unix columns for explicit conversion checks."""
import csv
from pathlib import Path
calendar=['2024-02-29','2023-02-29','2021-01-01','2020-12-31','2024-04-31',None,'Unknown','01/02/2024','2024-07-01','2024-12-31','2024-01-01','2024-03-01']
excel=[45000+5/1440,45000.5,61,60,None,0,45291,45292,45474,45657,1462,.5]
unix=[0,1.125,-.25,1709164800,None,-86400,1609459200,1609462800,1e20,253402300799,946684800,951782400]
p=Path(__file__).resolve().parents[1]/'data/python_datetime_examples.csv'
with p.open('w',newline='') as handle:
    w=csv.writer(handle);w.writerow(['Record','Calendar text','Excel serial','Unix seconds'])
    w.writerows((f'Example {i:02}',c,e,u) for i,(c,e,u) in enumerate(zip(calendar,excel,unix),1))
