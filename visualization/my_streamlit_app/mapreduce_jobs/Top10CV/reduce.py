# reduce.py
import sys
import heapq

top_jobs = []

for line in sys.stdin:
    try:
        title, salary = line.strip().rsplit('\t', 1)
        salary = float(salary)

        # Thêm vào heap
        heapq.heappush(top_jobs, (salary, title))

        # Nếu > 10 phần tử thì bỏ phần tử lương nhỏ nhất
        if len(top_jobs) > 10:
            heapq.heappop(top_jobs)
    except Exception as e:
        continue  # Bỏ qua lỗi để không dừng chương trình

# Sắp xếp top 10 theo lương giảm dần
for salary, title in sorted(top_jobs, reverse=True):
    print(f"{title}\t{int(salary)}")
