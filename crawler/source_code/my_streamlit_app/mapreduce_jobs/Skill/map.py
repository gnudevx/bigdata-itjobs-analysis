import sys
import csv

reader = csv.reader(sys.stdin)
header = next(reader)  # Bỏ qua dòng tiêu đề

for line in reader:
    try:
        if len(line) < 15:
            continue  # Bỏ qua nếu dòng không đủ cột

        title = line[1].strip()  # Tên công việc
        skills_raw = line[14].strip().lower()  # Cột kỹ năng

        # Nếu cột kỹ năng rỗng thì bỏ qua
        if not skills_raw:
            continue

        # Tách kỹ năng và loại bỏ khoảng trắng dư
        skills = [skill.strip() for skill in skills_raw.split(",")]

        # Kiểm tra xem có chứa 'python' hay không
        if any("python" in skill for skill in skills):
            print(f"{title}\t{', '.join(skills)}")

    except Exception as e:
        print(f"Lỗi khi xử lý dòng: {line}. Lỗi: {e}", file=sys.stderr)
