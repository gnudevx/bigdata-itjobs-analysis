import sys
import csv
import re

reader = csv.reader(sys.stdin)
header = next(reader)

for line in reader:
    try:
        title = line[1].strip()
        experience = line[7].strip().lower()

        # Nếu không yêu cầu kinh nghiệm
        if "không yêu cầu" in experience:
            print(f"{title}\t{experience}")  # In với tab
            continue

        # Dùng regex tìm số trong chuỗi
        match = re.search(r"\d+", experience)
        if match:
            year_str = match.group(0)
            if year_str in ["0"]:
                print(f"{title}\t{experience}")  # In với tab

    except Exception as e:
        print(f"Lỗi khi xử lý dòng: {line}. Lỗi: {e}")
