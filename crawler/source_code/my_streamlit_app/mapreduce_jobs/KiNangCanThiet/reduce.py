import sys

current_group = None
current_count = 0

# Đọc input từ STDIN (Standard Input)
for line in sys.stdin:
    line = line.strip()
    
    # Tách group và count từ các cặp key-value (group, count)
    group, count = line.split('\t')
    
    # Chuyển count thành số
    try:
        count = int(count)
    except ValueError:
        continue
    
    # Nếu group thay đổi, in kết quả
    if current_group == group:
        current_count += count
    else:
        if current_group:
            print(f"{current_group}\t{current_count}")
        current_group = group
        current_count = count

# In kết quả cho nhóm cuối cùng
if current_group == group:
    print(f"{current_group}\t{current_count}")
