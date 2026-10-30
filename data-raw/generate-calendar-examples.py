"""Six synthetic date pairs illustrating explicit calendar versus fixed units."""
import csv
from pathlib import Path
rows=[['Record','Start date','End date'],
      ['Leap month end','2024-01-31','2024-02-29'],
      ['Ordinary month end','2023-01-31','2023-02-28'],
      ['Beyond anniversary','2024-01-31','2024-03-01'],
      ['Leap year anniversary','2024-02-29','2025-02-28'],
      ['Short follow-up','2024-01-31','2024-02-28'],
      ['Missing end','2024-01-31','']]
with (Path(__file__).resolve().parents[1]/'data/python_calendar_interval_examples.csv').open('w',newline='') as f:
    csv.writer(f).writerows(rows)
