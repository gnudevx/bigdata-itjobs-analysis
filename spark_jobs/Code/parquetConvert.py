from pyspark.sql import SparkSession
import shutil
from pathlib import Path

# === Khởi tạo SparkSession ===
spark = SparkSession.builder.appName("ConvertCSVtoSingleParquet").master("local[*]").getOrCreate()

# === Đường dẫn trong container ===
input_path = Path('/home/hadoopducdung/Output/cleaned_data.csv')  # file CSV nằm trong container
tmp_output_dir = Path("/home/hadoopducdung/Output/tmp_parquet")  # thư mục tạm
final_output = Path("/home/hadoopducdung/Output/cleaned_data.parquet")  # file output duy nhất

df = spark.read \
    .option("header", True) \
    .option("quote", '"') \
    .option("escape", '"') \
    .option("multiline", True) \
    .option("encoding", "UTF-8") \
    .csv("file://" + str(input_path))

# === Gộp partition và ghi ra Parquet tạm (Spark luôn ghi vào thư mục) ===
tmp_output_dir.mkdir(parents=True, exist_ok=True)
df.coalesce(1).write.mode("overwrite").parquet("file://" + str(tmp_output_dir))

# === Tìm file Parquet duy nhất ===
part_files = list(tmp_output_dir.glob("part-*.parquet"))
if not part_files:
    raise FileNotFoundError(f"Không tìm thấy file part trong {tmp_output_dir}")
part_file = part_files[0]

# === Đổi tên thành cleaned_data.parquet ===
part_file.rename(final_output)

# === Xóa thư mục tạm ===
for f in tmp_output_dir.iterdir():
    if f.is_file():
        f.unlink()
    else:
        shutil.rmtree(f, ignore_errors=True)
tmp_output_dir.rmdir()

spark.stop()
print(f"✅ Xuất thành công: {final_output}")
