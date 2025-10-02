#!/usr/bin/env python
import sys
import csv

# Đọc dữ liệu đầu vào
reader = csv.reader(sys.stdin)

# Bỏ qua dòng header
header = next(reader)

for line in reader:
    try:
        company_name = line[0].strip()  # Tên công ty ở vị trí index 0
        title = line[1].strip()  # Tiêu đề công việc ở vị trí index 1
        salary_raw = line[3].strip()  # Lương raw ở vị trí index 3
        salary_normalized = line[4].strip()  # Lương đã chuẩn hóa ở vị trí index 4
        salary_unit = line[5].strip()  # Đơn vị tiền tệ ở vị trí index 5

        # Kiểm tra nếu lương có giá trị và là dạng số
        if salary_normalized.isdigit():
            salary = int(salary_normalized)
            if 10000000 <= salary :
                # Chỉ xuất tên công ty, tiêu đề công việc, và lương 
                print(f"{title}\t{salary_normalized}")

    except Exception as e:
        # Nếu có lỗi thì in thông báo lỗi
        print(f"Lỗi khi xử lý dòng: {line}. Lỗi: {e}")
