import json
import csv

# Đọc file JSON
with open('cleaned_data1.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Tạo file CSV để lưu kết quả
with open('converted_data.csv', 'w', newline='', encoding='utf-8') as csv_file:
    fieldnames = [
        'group', 'title', 'link', 'salary_raw', 'salary_normalized', 'currency_unit',
        'location', 'experience', 'description', 'requirements', 'benefits',
        'work_location_detail', 'working_time', 'deadline', 'skills'
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for item in data:
        row = {
            'group': item.get('group', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'title': item.get('title', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'link': item.get('link', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'salary_raw': item.get('salary_raw', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'salary_normalized': item.get('salary_normalized', ''),  # Có thể là số hoặc None
            'currency_unit': item.get('currency_unit', ''),
            'location': item.get('location', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'experience': item.get('experience', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'description': item.get('description', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'requirements': item.get('requirements', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'benefits': item.get('benefits', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'work_location_detail': item.get('work_location_detail', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'working_time': item.get('working_time', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'deadline': item.get('deadline', '').replace('\n', ' ').replace('\r', ' ').strip(),
            'skills': ', '.join([skill.strip() for skill in item.get('skills', [])]) if item.get('skills') else ''
        }
        writer.writerow(row)

print("Đã chuyển đổi thành công từ JSON sang CSV.")
