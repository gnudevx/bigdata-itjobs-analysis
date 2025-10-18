# clean_job_data_debug.py
import os
import sys
import re
import unicodedata
import logging
import traceback
from datetime import datetime

from hdfs import InsecureClient
import spacy
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, explode, udf
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, ArrayType, StructType, StructField, IntegerType

sys.path.append('/opt/airflow/spark_jobs/')
sys.path.append('/opt/hadoop-conf/')
from Code.city import CITY_MAP

EXCHANGE_RATE = 24000
NER_MODEL = "/opt/airflow/spark_jobs/Code/checkpoint/"


# ---------------- LOGGING ----------------
def setup_logger():
    log_dir = "/opt/airflow/logs/spark_cleaning"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"cleaning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger("spark_cleaning")
    logger.info(f"Logger created. Log file: {log_path}")
    return logger


# ---------------- UTILS ----------------
def clean_requirements(text):
    if not text:
        return ""
    text = re.sub(r'\[(Required|Preferred)\]', '', text)
    text = re.sub(r'\b(Skill Required|Kỹ năng[:&]).*', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()


def parse_deadline(dl):
    if not dl:
        return None
    try:
        m = re.search(r'(\d{2}/\d{2}/\d{4})', str(dl))
        return datetime.strptime(m.group(1), '%d/%m/%Y').date().isoformat() if m else None
    except Exception:
        return None


def normalize_salary(salary_str):
    if not salary_str:
        return None
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
        return int(val * multiplier)
    except Exception:
        return None


def normalize_city_name(city):
    city = unicodedata.normalize('NFD', str(city))
    city = city.encode('ascii', 'ignore').decode('utf-8')
    city = city.lower()
    city = re.sub(r'[^a-z0-9]', '', city)
    return city


def normalize_location(loc, city_map_broadcast):
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
    city_map = city_map_broadcast.value
    for key, val in city_map.items():
        if key in normalized:
            return val
    return "Không rõ"


_nlp = None
def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load(NER_MODEL)
        except Exception:
            _nlp = spacy.blank("vi")
    return _nlp


def extract_skills(req):
    try:
        nlp_local = get_nlp()
        doc = nlp_local(req or '')
        return [ent.text for ent in doc.ents if ent.label_ == 'SKILL']
    except Exception:
        return []


# ---------------- MAIN ----------------
def clean_with_spark():
    logger = setup_logger()
    try:
        logger.info("=== Starting Spark job ===")
        spark = SparkSession.builder \
            .appName("Clean Job Data Debug") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://ducdung-master:9000") \
            .getOrCreate()
        sc = spark.sparkContext

        today = datetime.now().strftime("%Y-%m-%d")
        input_path = f"hdfs:///user/hadoopducdung/airflow/dataset/{today}/merged_jobs_{today}.json"
        output_dir = f"/user/hadoopducdung/airflow/Output/cleaned_data_{today}"
        logger.info(f"Input: {input_path}")
        logger.info(f"Output dir: {output_dir}")

        # schema sửa: ARRAY
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
            StructField("topcv_jobs", ArrayType(topcv_struct), True),
            StructField("vnwork_jobs", ArrayType(topcv_struct), True)
        ])

        df = spark.read.schema(schema).option("multiline", "true").json(input_path)
        logger.info(f"Rows read: {df.count()}")
        df.printSchema()

        city_map_b = sc.broadcast(CITY_MAP)

        # explode từng nguồn
        dfs = []
        for col_name in ["topcv_jobs", "vnwork_jobs"]:
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing.")
                continue
            subset = df.select(explode(col(col_name)).alias("entry")) \
                       .select(col("entry.group").alias("group"),
                               explode(col("entry.jobs")).alias("job"))
            c = subset.count()
            logger.info(f"Exploded {col_name}: {c} rows")
            if c > 0:
                dfs.append(subset)

        if not dfs:
            logger.error("No job data found in any source.")
            spark.stop()
            return

        df_jobs = dfs[0]
        if len(dfs) > 1:
            df_jobs = df_jobs.unionByName(dfs[1])
        logger.info(f"Total exploded jobs: {df_jobs.count()}")

        # UDFs
        udf_clean_req = udf(clean_requirements, StringType())
        udf_parse_deadline = udf(parse_deadline, StringType())
        udf_normal_salary = udf(normalize_salary, IntegerType())
        udf_normal_loc = udf(lambda l: normalize_location(l, city_map_b), StringType())
        udf_skills = udf(extract_skills, ArrayType(StringType()))

        df_cleaned = df_jobs \
            .withColumn("requirements_clean", udf_clean_req(col("job.requirements"))) \
            .withColumn("deadline_parsed", udf_parse_deadline(col("job.deadline"))) \
            .withColumn("salary_normalized", udf_normal_salary(col("job.salary"))) \
            .withColumn("location_norm", udf_normal_loc(col("job.location"))) \
            .withColumn("skills", udf_skills(col("requirements_clean"))) \
            .withColumn("currency_unit", lit("VND"))

        logger.info(f"Cleaned jobs count: {df_cleaned.count()}")

        # group & write
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

        logger.info(f"Grouped jobs count: {df_grouped.count()}")

        df_grouped.coalesce(1).write.mode("overwrite").json(output_dir)
        logger.info("Write finished successfully.")

        hdfs_client = InsecureClient('http://ducdung-master:9870', user='hadoopducdung')
        files = hdfs_client.list(output_dir, status=True)
        part_files = [name for name, info in files if name.startswith("part-")]
        if not part_files:
            logger.error("No part-* files found.")
            spark.stop()
            return

        part_file = f"{output_dir}/{part_files[0]}"
        final_path = f"/user/hadoopducdung/airflow/Output/cleaned_data_{today}.json"
        with hdfs_client.read(part_file) as fsrc:
            data = fsrc.read()
            hdfs_client.write(final_path, data=data, overwrite=True)
        logger.info(f"✅ Final single file written: {final_path}")

        try:
            hdfs_client.delete(output_dir, recursive=True)
            logger.info("Temporary folder deleted.")
        except Exception as e:
            logger.warning(f"Delete temp failed: {e}")

        spark.stop()
        logger.info("=== Spark job completed ===")
    except Exception as e:
        logger.exception(f"Job failed: {e}")
        if 'spark' in locals():
            try:
                spark.stop()
            except:
                pass
        raise


if __name__ == "__main__":
    clean_with_spark()
