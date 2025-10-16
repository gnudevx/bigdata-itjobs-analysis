from pyspark.sql import SparkSession, functions as F
from pyspark.sql.functions import col, lit, explode, udf
from pyspark.sql.types import StringType, ArrayType, StructType, StructField
from hdfs import InsecureClient
from datetime import datetime
import re, unicodedata, spacy, os, sys

sys.path.append('/opt/airflow/spark_jobs/')
from Code.city import CITY_MAP

EXCHANGE_RATE = 24000
NER_MODEL = "/opt/airflow/spark_jobs/Code/checkpoint/"
nlp = spacy.load(NER_MODEL)

# ===================== UTILS =====================
def clean_requirements(text: str) -> str:
    text = re.sub(r'\[(Required|Preferred)\]', '', str(text))
    text = re.sub(r'\b(Skill Required|Kỹ năng[:&]).*', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_deadline(dl: str):
    m = re.search(r'(\d{2}/\d{2}/\d{4})', str(dl))
    return datetime.strptime(m.group(1), '%d/%m/%Y').date().isoformat() if m else None

def normalize_salary(salary_str: str):
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

def normalize_city_name(city: str) -> str:
    city = unicodedata.normalize('NFD', str(city))
    city = city.encode('ascii', 'ignore').decode('utf-8')
    city = city.lower()
    city = re.sub(r'[^a-z0-9]', '', city)
    return city

def normalize_location(loc: str) -> str:
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
    for key, val in CITY_MAP.items():
        if key in normalized:
            return val
    return "Không rõ"

def extract_skills(req):
    doc = nlp(req or '')
    return [ent.text for ent in doc.ents if ent.label_ == 'SKILL']

# ===================== SPARK JOB =====================
def clean_with_spark():
    spark = SparkSession.builder \
        .appName("Clean Job Data with Spark") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-master:9000") \
        .getOrCreate()

    today = "2025-10-15"
    input_path = f"hdfs://hadoop-master:9000/user/hadoopducdung/airflow/dataset/{today}/merged_jobs_{today}.json"
    output_dir = f"hdfs://hadoop-master:9000/user/hadoopducdung/airflow/Output/cleaned_data_{today}"

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

    print(f"📂 Reading from: {input_path}")
    df = spark.read.schema(schema).option("multiline", "true").json(input_path)

    # ===================== EXPLODE JOBS =====================
    dfs = []
    for col_name in ["topcv_jobs", "vnwork_jobs"]:
        dfs.append(
            df.filter(col(col_name).isNotNull()) \
              .select(col(f"{col_name}.group").alias("group"), explode(col(f"{col_name}.jobs")).alias("job"))
        )
    df_jobs = dfs[0].unionByName(dfs[1])

    # ===================== UDFs =====================
    udf_clean_req = udf(clean_requirements, StringType())
    udf_parse_deadline = udf(parse_deadline, StringType())
    udf_normal_salary = udf(normalize_salary, StringType())
    udf_normal_loc = udf(normalize_location, StringType())
    udf_skills = udf(extract_skills, ArrayType(StringType()))

    # ===================== CLEANING =====================
    df_cleaned = df_jobs.withColumn("requirements_clean", udf_clean_req(col("job.requirements"))) \
                        .withColumn("deadline_parsed", udf_parse_deadline(col("job.deadline"))) \
                        .withColumn("salary_normalized", udf_normal_salary(col("job.salary"))) \
                        .withColumn("location_norm", udf_normal_loc(col("job.location"))) \
                        .withColumn("skills", udf_skills(col("requirements_clean"))) \
                        .withColumn("currency_unit", lit("VND"))

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

    # ===================== WRITE SINGLE JSON =====================
    df_grouped.coalesce(1).write.mode("overwrite").json(output_dir)

    # Merge part files into single JSON
    hdfs_client = InsecureClient('http://hadoop-master:9870', user='hadoopducdung')
    files = hdfs_client.list(output_dir, status=True)
    part_files = [f"{output_dir}/{name}" for name, info in files if name.startswith("part-")]

    if not part_files:
        print("❌ No part files found in output directory.")
        spark.stop()
        return

    part_file = part_files[0]
    final_path = f"/user/hadoopducdung/airflow/Output/cleaned_data_{today}.json"

    with hdfs_client.read(part_file) as fsrc:
        data = fsrc.read()
        hdfs_client.write(final_path, data=data, overwrite=True)

    # Xóa folder tạm
    hdfs_client.delete(output_dir, recursive=True)
    print(f"✅ Final single file: {final_path}")

    spark.stop()

# ===================== MAIN =====================
if __name__ == "__main__":
    clean_with_spark()
