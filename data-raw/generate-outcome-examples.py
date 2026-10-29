"""Generate the PII-free outcome coding fixture, including one missing outcome."""
import csv
from pathlib import Path
path = Path(__file__).resolve().parents[1]/'data/python_outcome_examples.csv'
statuses = ['Alive without disease']*6+['Alive with disease']*3+['Dead of disease']*2+['Dead of other causes',None]
with path.open('w',newline='') as handle:
    writer=csv.writer(handle);writer.writerow(['Record','Vital status'])
    writer.writerows((f'Example {i:02}',value) for i,value in enumerate(statuses,1))
