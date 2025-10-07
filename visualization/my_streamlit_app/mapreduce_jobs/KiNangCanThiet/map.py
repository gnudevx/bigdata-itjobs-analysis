import sys

# Để bỏ qua dòng đầu tiên
first_line = True

# Đọc input từ STDIN (Standard Input)
for line in sys.stdin:
    line = line.strip()
    
    # Bỏ qua dòng đầu tiên (header)
    if first_line:
        first_line = False
        continue
    
    # Chia cột dựa trên dấu phẩy (CSV format), bạn có thể thay đổi nếu dữ liệu có định dạng khác
    fields = line.split(',')
    
    if len(fields) > 1:
        group = fields[0]  # Giả sử nhóm công việc là trường đầu tiên
        # Emit group và giá trị là 1 (để đếm)
        print(f"{group}\t1")
