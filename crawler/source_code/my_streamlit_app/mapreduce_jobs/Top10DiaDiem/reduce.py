#!/usr/bin/env python3
import sys
from collections import defaultdict

city_counts = defaultdict(int)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    city, count = line.split("\t")
    city_counts[city] += int(count)

top_10 = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:10]

for city, total_count in top_10:
    print(f"{city}\t{total_count}")
