"""All nine binary/unknown component pairs, without patient data or event times."""
import csv
from itertools import product
from pathlib import Path
with (Path(__file__).resolve().parents[1]/'data/python_composite_outcome_examples.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Record','Outcome','Progression','Binary outcome'])
    for i,(a,b) in enumerate(product([0,1,None],repeat=2),1):
        w.writerow([f'Synthetic pair {i}','' if a is None else 'Death' if a else 'Alive',
                    '' if b is None else 'Yes' if b else 'No','' if a is None else a])
