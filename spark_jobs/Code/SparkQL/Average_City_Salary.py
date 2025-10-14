from pyspark.sql import SparkSession
from pathlib import Path
import shutil

# === Khởi tạo SparkSession ===
spark = SparkSession.builder \
    .appName("ITJobs_Average_City_Salary") \
    .master("local[*]") \
    .getOrCreate()

# === Đường dẫn input/output ===
input_path = Path('/home/hadoopducdung/Output/cleaned_data.parquet')
tmp_output_dir = Path('/opt/Output_sparkQL/tmp_average_city_salary')
final_output = Path('/opt/Output_sparkQL/average_city_salary.csv')

# === Đọc dữ liệu Parquet ===
df = spark.read.parquet("file://" + str(input_path))

# === Tạo view & chạy SparkQL ===
df.createOrReplaceTempView("jobs")

query = """
SELECT 
    location,
    CAST(ROUND(AVG(salary_normalized), 0) AS BIGINT) AS avg_salary
FROM jobs
WHERE salary_normalized IS NOT NULL
GROUP BY location
ORDER BY avg_salary DESC
"""

result_df = spark.sql(query)

# === In kết quả ra console ===
print("== Mức lương trung bình theo thành phố ==")
result_df.show(truncate=False)

# === Ghi tạm ra thư mục (Spark bắt buộc tạo folder) ===
tmp_output_dir.mkdir(parents=True, exist_ok=True)
result_df.coalesce(1).write.mode("overwrite").option("header", True).csv("file://" + str(tmp_output_dir))

# === Tìm file part-xxxxx.csv trong thư mục tạm ===
part_file = next(tmp_output_dir.glob("part-*.csv"))

# === Đổi tên file part thành file CSV cuối cùng ===
final_output.parent.mkdir(parents=True, exist_ok=True)
shutil.move(str(part_file),str(final_output))

# === Xóa thư mục tạm còn lại (_SUCCESS, metadata, v.v.) ===
for f in tmp_output_dir.iterdir():
    if f.exists():
        if f.is_file():
            f.unlink()
        else:
            shutil.rmtree(f, ignore_errors=True)
tmp_output_dir.rmdir()

print(f"✅ Xuất thành công: {final_output}")

spark.stop()
