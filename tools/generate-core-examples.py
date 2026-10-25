"""Regenerate the public synthetic examples for ClinicoPathPj's six Python cores."""
import csv
import random
from pathlib import Path
root=Path(__file__).resolve().parent.parent
rng=random.Random(20261025)
rows=[]
for i in range(36):
    reference='Positive' if i%3==0 or i%7==0 else 'Negative'
    p=min(.95,max(.05,(.65 if reference=='Positive' else .30)+rng.uniform(-.25,.25)))
    q=min(.98,max(.02,(.70 if reference=='Positive' else .25)+rng.uniform(-.3,.3)))
    rows.append(dict(Reference=reference,Test='Positive' if p>=.5 else 'Negative',
      RowGroup=['A','B','C'][i%3],ColumnGroup=['X','Y','Z'][(i//3)%3],Frequency=1+i%5,
      Measurement=round(10**(-1+5*i/35),10),RiskA=round(p,4),RiskB=round(q,4)))
(root/'data').mkdir(exist_ok=True)
with (root/'data/python_core_examples.csv').open('w',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
print('Wrote 36 synthetic rows; no patient data.')
