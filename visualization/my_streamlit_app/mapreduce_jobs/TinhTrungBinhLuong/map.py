# map.py
import sys
import csv

reader = csv.reader(sys.stdin)
header = next(reader)

for line in reader:
    try:
        if len(line) < 7:
            continue

        city = line[6].strip()
        salary = line[4].strip()

        # Bỏ qua nếu chứa nhiều tỉnh/thành phố hoặc mô tả mơ hồ
        if any(x in city.lower() for x in ['&', ',', 'nơi khác']):
            continue

        if not salary:
            continue

        salary = float(salary)
        print(f"{city}\t{salary}")
    except Exception as e:
        print(f"Lỗi dòng: {line}. Lỗi: {e}", file=sys.stderr)
