# reduce.py
import sys

current_city = None
salary_sum = 0.0
count = 0

for line in sys.stdin:
    try:
        city, salary = line.strip().split('\t')
        salary = float(salary)

        if current_city == city:
            salary_sum += salary
            count += 1
        else:
            if current_city:
                avg_salary = salary_sum / count
                print(f"{current_city}\t{avg_salary:.2f}")
            current_city = city
            salary_sum = salary
            count = 1
    except Exception as e:
        print(f"Lỗi dòng: {line}. Lỗi: {e}", file=sys.stderr)

# In ra kết quả cuối cùng
if current_city:
    avg_salary = salary_sum / count
    print(f"{current_city}\t{avg_salary:.2f}")
