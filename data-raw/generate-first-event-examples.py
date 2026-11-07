"""Literal synthetic timelines; expected values are not produced by the implementation."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[
 ('A before B follow-up',2,'Event',8,'Event-free',2,'Event','Component A'),
 ('A after B follow-up',8,'Event',2,'Event-free',2,'Censored','Censored'),
 ('B after A follow-up',2,'Event-free',8,'Event',2,'Censored','Censored'),
 ('B before A follow-up',8,'Event-free',2,'Event',2,'Event','Component B'),
 ('A event/censor tie',5,'Event',5,'Event-free',5,'Event','Component A'),
 ('B event/censor tie',5,'Event-free',5,'Event',5,'Event','Component B'),
 ('Simultaneous events',5,'Event',5,'Event',5,'Event','Both components'),
 ('Time zero event',0,'Event',0,'Event-free',0,'Event','Component A'),
 ('Unknown time',None,'Event',4,'Event-free',None,None,None),
 ('Unknown status',3,None,4,'Event',None,None,None),
 ('Negative duration',-1,'Event',4,'Event-free',None,None,None),
 ('Both event-free',3,'Event-free',4,'Event-free',3,'Censored','Censored')]
with (ROOT/'data/python_first_event_examples.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Record','A time','A status','B time','B status','Expected time','Expected status','Expected source']);w.writerows(rows)
