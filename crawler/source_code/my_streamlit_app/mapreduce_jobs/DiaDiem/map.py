#!/usr/bin/env python3
import sys
import csv

reader = csv.reader(sys.stdin)
next(reader)  # bỏ dòng header

for line in reader:
    try:
        company_name = line[1].strip()
        location = line[6].strip().lower()  # chuyển về lower để so sánh dễ

        if "hà nội" in location or "ho chi minh" in location or "hồ chí minh" in location:
            print(f"{company_name}\t{location}")

    except Exception as e:
        continue
