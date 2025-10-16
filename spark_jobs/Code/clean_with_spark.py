# clean_job_data.py
import os
import sys
import re
import unicodedata
import logging
import traceback
from datetime import datetime

from hdfs import InsecureClient
import spacy  # vẫn import, nhưng load model để lazy-load trong worker
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, explode, udf
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, ArrayType, StructType, StructField, IntegerType

# đảm bảo path chứa module của bạn
sys.path.append('/opt/airflow/spark_jobs/')
sys.path.append('/opt/hadoop-conf/')
from Code.city import CITY_MAP  # dict mapping chuẩn của bạn

# ===== CONSTANTS =====
EXCHANGE_RATE = 24000
NER_MODEL = "/opt/airflow/spark_jobs/Code/checkpoint/"  # nếu model tồn tại trên executor
# không load model tại import time: sẽ lazy-load trong UDF (tránh pickle/overhead)

# ====== LOGGING SETUP FUNCTION ======
def setup_logger():
    log_dir = "/opt/airflow/logs/spark_cleaning"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"cleaning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("spark_cleaning")
    logger.info(f"Logger created. Log file: {log_path}")
    return logger

# ===================== UTILS =====================
def clean_requirements(text: str) -> str:
    text = re.sub(r'\[(Required|Preferred)\]', '', str(text))
    text = re.sub(r'\b(Skill Required|Kỹ năng[:&]).*', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_deadline(dl: str):
    try:
        m = re.search(r'(\d{2}/\d{2}/\d{4})', str(dl))
        return datetime.strptime(m.group(1), '%d/%m/%Y').date().isoformat() if m else None
    except Exception:
        return None

def normalize_salary(salary_str):
    try:
        s = str(salary_str).lower()
        if 'thoả thuận' in s or 'thỏa thuận' in s:
            return None
        s_clean = s.replace(',', '')
        nums = re.findall(r"\d+(?:\.\d+)?", s_clean)
        if not nums:
            return None
        values = [float(n) for n in nums]
        val = sum(values) / len(values)
        if 'usd' in s_clean or '$' in s_clean:
            multiplier = EXCHANGE_RATE
        elif 'triệu' in s_clean:
            multiplier = 1_000_000
        else:
            multiplier = 1
        result = int(val * multiplier)
        return result if result > 0 else 0
    except Exception:
        return None

def normalize_city_name(city: str) -> str:
    city = unicodedata.normalize('NFD', str(city))
    city = city.encode('ascii', 'ignore').decode('utf-8')
    city = city.lower()
    city = re.sub(r'[^a-z0-9]', '', city)
    return city

def normalize_location(loc: str, city_map_broadcast):
    if not loc:
        return "Không rõ"
    loc = loc.lower().strip()
    loc_new = re.sub(r"[–\-]", ",", loc)
    parts = [p.strip() for p in loc_new.split(",") if p.strip()]
    if not parts:
        return "Không rõ"
    viet_nam_patterns = [r"\bviệt\s*-*\s*nam\b", r"\bvietnam\b", r"\bvn\b"]
    last = parts[-1]
    has_vietnam = any(re.search(pat, last, flags=re.IGNORECASE) for pat in viet_nam_patterns)
    candidate = parts[-2] if has_vietnam and len(parts) >= 2 else last
    candidate = re.sub(r"\b(tp\.?|thanh\s*pho|tinh|city)\b", "", candidate, flags=re.IGNORECASE).strip()
    normalized = normalize_city_name(candidate)
    city_map = city_map_broadcast.value if city_map_broadcast is not None else CITY_MAP
    for key, val in city_map.items():
        if key in normalized:
            return val
    return "Không rõ"

# ===== SPA Cy lazy-loading for executors =====
# mỗi executor sẽ có _nlp riêng; global biến để lazy load
_nlp = None
def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            # nếu model nặng không có sẵn, có thể fallback sang blank model
            _nlp = spacy.load(NER_MODEL)
        except Exception:
            try:
                _nlp = spacy.blank("vi")
            except Exception:
                _nlp = None
    return _nlp

def extract_skills(req: str):
    try:
        nlp_local = get_nlp()
        if nlp_local is None:
            return []
        doc = nlp_local(req or '')
        return [ent.text for ent in doc.ents if getattr(ent, "label_", None) == 'SKILL' or ent.label_ == 'SKILL']
    except Exception:
        return []

# ===================== SPARK JOB =====================
def clean_with_spark():
    logger = setup_logger()
    try:
        logger.info("Starting Spark job...")

        # === Spark session: chú ý dùng đúng scheme hdfs://
        spark = SparkSession.builder \
            .appName("Clean Job Data with Spark") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://ducdung-master:9000") \
            .getOrCreate()
        sc = spark.sparkContext
        logger.info("Spark session created.")

        # broadcast CITY_MAP để dùng trong UDF
        city_map_b = sc.broadcast(CITY_MAP)
        logger.info("CITY_MAP broadcasted to executors.")

        # ======== Paths ========
        today = "2025-10-15"
        input_path = f"hdfs:///user/hadoopducdung/airflow/dataset/{today}/merged_jobs_{today}.json"
        output_dir = f"hdfs:///user/hadoopducdung/airflow/Output/cleaned_data_{today}"

        logger.info(f"Input path: {input_path}")
        logger.info(f"Output dir: {output_dir}")

        # ===================== DEFINE SCHEMA =====================
        job_struct = StructType([
            StructField("benefits", StringType(), True),
            StructField("deadline", StringType(), True),
            StructField("description", StringType(), True),
            StructField("experience", StringType(), True),
            StructField("link", StringType(), True),
            StructField("location", StringType(), True),
            StructField("requirements", StringType(), True),
            StructField("salary", StringType(), True),
            StructField("title", StringType(), True),
            StructField("work_location_detail", StringType(), True),
            StructField("working_time", StringType(), True)
        ])

        topcv_struct = StructType([
            StructField("group", StringType(), True),
            StructField("jobs", ArrayType(job_struct), True)
        ])

        schema = StructType([
            StructField("date", StringType(), True),
            StructField("topcv_jobs", topcv_struct, True),
            StructField("vnwork_jobs", topcv_struct, True),
            StructField("total_jobs", StringType(), True)
        ])

        logger.info("Reading JSON with specified schema...")
        df = spark.read.schema(schema).option("multiline", "true").json(input_path)
        logger.info(f"Read complete. Rows: {df.count()}")

        # ===================== EXPLODE JOBS =====================
        dfs = []
        for col_name in ["topcv_jobs", "vnwork_jobs"]:
            subset = df.filter(col(col_name).isNotNull()) \
                       .select(col(f"{col_name}.group").alias("group"),
                               explode(col(f"{col_name}.jobs")).alias("job"))
            dfs.append(subset)
            logger.info(f"Prepared exploded dataframe for {col_name}, rows: {subset.count()}")
        if len(dfs) == 0:
            logger.warning("No job columns found (topcv_jobs or vnwork_jobs). Exiting.")
            spark.stop()
            return
        df_jobs = dfs[0]
        if len(dfs) > 1:
            df_jobs = df_jobs.unionByName(dfs[1])
        logger.info(f"Unioned jobs dataframe rows: {df_jobs.count()}")

        # ===================== UDFs (with correct return types) =====================
        udf_clean_req = udf(clean_requirements, StringType())
        udf_parse_deadline = udf(parse_deadline, StringType())
        udf_normal_salary = udf(normalize_salary, IntegerType())
        # location udf uses broadcast value
        udf_normal_loc = udf(lambda l: normalize_location(l, city_map_b), StringType())
        udf_skills = udf(extract_skills, ArrayType(StringType()))

        # ===================== CLEANING =====================
        df_cleaned = df_jobs.withColumn("requirements_clean", udf_clean_req(col("job.requirements"))) \
                            .withColumn("deadline_parsed", udf_parse_deadline(col("job.deadline"))) \
                            .withColumn("salary_normalized", udf_normal_salary(col("job.salary"))) \
                            .withColumn("location_norm", udf_normal_loc(col("job.location"))) \
                            .withColumn("skills", udf_skills(col("requirements_clean"))) \
                            .withColumn("currency_unit", lit("VND"))

        logger.info("Applied cleaning UDFs.")

        # ===================== GROUP & WRITE =====================
        df_grouped = df_cleaned.groupBy("group").agg(
            F.collect_list(
                F.struct(
                    col("job.title").alias("title"),
                    col("job.link").alias("link"),
                    col("location_norm").alias("location"),
                    col("job.experience").alias("experience"),
                    col("job.description").alias("description"),
                    col("requirements_clean").alias("requirements"),
                    col("job.benefits").alias("benefits"),
                    col("job.work_location_detail").alias("work_location_detail"),
                    col("job.working_time").alias("working_time"),
                    col("deadline_parsed").alias("deadline"),
                    col("job.salary").alias("salary"),
                    col("salary_normalized").alias("salary_normalized"),
                    col("currency_unit").alias("currency_unit"),
                    col("skills").alias("skills")
                )
            ).alias("jobs")
        )

        logger.info("Grouping completed. Writing coalesced single-part JSON to HDFS...")
        # coalesce(1) để tạo 1 part- file; lưu tạm vào thư mục output_dir
        df_grouped.coalesce(1).write.mode("overwrite").json(output_dir)
        logger.info("Write finished.")

        # ===================== Merge part files into single JSON using WebHDFS =====================
        hdfs_client = InsecureClient('http://ducdung-master:9870', user='hadoopducdung')
        logger.info("Listing files in output_dir via WebHDFS...")
        files = hdfs_client.list(output_dir, status=True)
        part_files = [name for name, info in files if name.startswith("part-")]
        if not part_files:
            logger.error("No part-* files found in HDFS output directory.")
            spark.stop()
            return

        part_file = f"{output_dir}/{part_files[0]}"
        final_path = f"/user/hadoopducdung/airflow/Output/cleaned_data_{today}.json"

        logger.info(f"Reading part file {part_file} and writing to final path {final_path} ...")
        with hdfs_client.read(part_file) as fsrc:
            data = fsrc.read()
            hdfs_client.write(final_path, data=data, overwrite=True)
        logger.info(f"Final single file written to HDFS: {final_path}")

        # Xóa folder tạm output_dir (nếu muốn)
        try:
            hdfs_client.delete(output_dir, recursive=True)
            logger.info(f"Deleted temporary HDFS folder: {output_dir}")
        except Exception as e:
            logger.warning(f"Could not delete temporary output dir: {e}")

        spark.stop()
        logger.info("Spark job finished successfully.")
    except Exception as e:
        # đảm bảo logger tồn tại
        try:
            logger.exception(f"Spark job failed: {e}")
        except Exception:
            print("Spark job failed (logger unavailable):", e)
            traceback.print_exc()
        # stop spark nếu có
        try:
            if 'spark' in locals():
                spark.stop()
        except Exception:
            pass
        raise

if __name__ == "__main__":
    clean_with_spark()
