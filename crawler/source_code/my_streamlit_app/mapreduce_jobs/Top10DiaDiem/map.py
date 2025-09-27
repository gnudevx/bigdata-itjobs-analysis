#!/usr/bin/env python3
import sys
import csv
import re

invalid_keywords = ['khác', 'nơi khác']

reader = csv.reader(sys.stdin)
for fields in reader:
    if len(fields) < 6:
        continue

    dia_diem = fields[6]  # Thay bằng cột chứa "thành phố" trong dữ liệu của bạn
    parts = re.split(r'[,&]| và ', dia_diem)

    for part in parts:
        part = part.strip()
        if any(invalid in part.lower() for invalid in invalid_keywords):
            continue
        if part:
            print(f"{part}\t1")
