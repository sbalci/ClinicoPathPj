"""Generate the bounded 200-study desktop fixture; synthetic counts repeat eight examples."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = [(80,10,20,90),(45,20,5,80),(0,5,10,15),(12,0,3,20),
          (1,1,0,0),(18,4,2,16),(16,2,4,18),(9,1,1,9)]


def rows():
    return [(f'Bounded study {i+1:03d}', *COUNTS[i % len(COUNTS)]) for i in range(200)]


if __name__ == '__main__':
    target = ROOT / 'docs/validation-exports/python-study-inspector-0.3.56-maximum.csv'
    with target.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Study','TP','FP','FN','TN'])
        writer.writerows(rows())
    print(target)
