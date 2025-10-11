# Cách chạy: docker -> spark-submit /opt/spark_jobs/csvConvert.py

from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col

# 1. Khởi tạo Spark session
spark = SparkSession.builder \
    .appName("Convert JSON to CSV for Hive Table") \
    .getOrCreate()

# 2. Đường dẫn file JSON đầu vào
input_path = "hdfs:///user/hive/data/git_jobs_raw/cleaned_data.json"
output_path = "hdfs:///user/hive/data/git_jobs_csv/cleaned_data_csv"

df = spark.read.option("multiline", True).json(input_path)

# 4. Làm phẳng mảng jobs
df_flat = (
    df.withColumn("job", explode(col("jobs")))
      .select(
          col("group").alias("group"),
          col("job.title").alias("title"),
          col("job.link").alias("link"),
          # dùng salary_raw thay vì salary
          col("job.salary_normalized").alias("salary"),
          col("job.location").alias("location"),
          col("job.experience").cast("string").alias("experience"),  # ép sang string cho Hive
          col("job.description").alias("description"),
          col("job.requirements").alias("requirements"),
          col("job.benefits").alias("benefits"),
          col("job.work_location_detail").alias("work_location_detail"),
          col("job.working_time").alias("working_time"),
          col("job.deadline").alias("deadline")
      )
)

# 5. Ghi dữ liệu ra file CSV có header, để Hive LOAD dễ
df_flat.write \
    .option("header", True) \
    .option("encoding", "UTF-8") \
    .option("bom", True) \
    .mode("overwrite") \
    .csv(output_path)

# 6. Kiểm tra schema
df_flat.printSchema()
print(f"✅ CSV file has been written to: {output_path}")

spark.stop()
