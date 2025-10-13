# Cách chạy: docker -> spark-submit /opt/spark_jobs/csvConvert.py

# Lưu ý: 
# 1. file JSON đầu vào phải là file đã được làm sạch (cleaned_data.json)
# 2. file CSV đầu ra sẽ được ghi vào /home/hadoopducdung/Output/cleaned_data.csv để Hive có thể đọc được

import os, glob, shutil
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col, concat_ws

# Khởi tạo Spark session
spark = SparkSession.builder \
    .appName("Convert JSON to CSV for Hive Table") \
    .master("local[*]") \
    .getOrCreate()

# Đường dẫn file JSON đầu vào
input_path = Path('/opt/Output/cleaned_data.json')
output_path = Path('/opt/Output_csv/cleaned_data.csv')

df = spark.read.option("multiline", True).json("file://" + str(input_path))

# Làm phẳng mảng jobs
df_flat = (
    df.withColumn("job", explode(col("jobs")))
      .select(
          col("group").alias("group"),
          col("job.title").alias("title"),
          col("job.link").alias("link"),
          col("job.location").alias("location"),
          col("job.experience").alias("experience"),  # ép sang string cho Hive
          col("job.description").alias("description"),
          col("job.requirements").alias("requirements"),
          col("job.benefits").alias("benefits"),
          col("job.work_location_detail").alias("work_location_detail"),
          col("job.working_time").alias("working_time"),
          col("job.deadline").alias("deadline"),
          col("job.salary_raw").alias("salary_raw"),
          col("job.salary_normalized").alias("salary_normalized"),
          col("job.currency_unit").alias("currency_unit"),
          concat_ws(", ", col("job.skills")).alias("skills")          
      )
)

# Ghi dữ liệu ra file CSV duy nhất
output_path.parent.mkdir(parents=True, exist_ok=True)
df_flat.coalesce(1).write \
    .option("header", True) \
    .option("quoteAll", True) \
    .option("escape", '"') \
    .option("encoding", "UTF-8") \
    .mode("overwrite") \
    .csv("file://" + str(output_path.parent))

# Đổi tên file part-xxxx.csv thành cleaned_data.csv

part_file = glob.glob(str(output_path.parent / "part-*.csv"))[0]
shutil.move(part_file, output_path)

# Xóa folder tạm
success_file = output_path.parent / "_SUCCESS"
if success_file.exists():
    success_file.unlink()

df_flat.printSchema()
print(f"✅ CSV file has been written to: {output_path}")

spark.stop()
