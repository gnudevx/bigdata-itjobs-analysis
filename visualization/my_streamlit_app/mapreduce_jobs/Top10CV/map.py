# map.py
import sys
import csv

reader = csv.reader(sys.stdin)
header = next(reader)

for line in reader:
    try:
        if len(line) < 5:
            continue

        title = line[1].strip()
        salary = line[4].strip()

        if not salary:
            continue

        salary = float(salary)
        print(f"{title}\t{salary}")
    except Exception as e:
        print(f"Lỗi dòng: {line}. Lỗi: {e}", file=sys.stderr)
