from pyspark.sql import SparkSession, functions as F
from pyspark.sql.functions import col, lit, explode, udf, when, regexp_extract, expr
from pyspark.sql.types import StringType, ArrayType, IntegerType
from pathlib import Path
import re, json, unicodedata, os, glob, shutil
from datetime import datetime
import spacy
from city import CITY_MAP

EXCHANGE_RATE = 24000
NER_MODEL = r"/opt/spark_jobs/checkpoint"
nlp = spacy.load(NER_MODEL)

# Các hàm xử lý như cũ
def clean_requirements(text: str) -> str:
    text = re.sub(r'\[(Required|Preferred)\]', '', str(text))
    text = re.sub(r'\b(Skill Required|Kỹ năng[:&]).*', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_deadline(dl: str):
    m = re.search(r'(\d{2}/\d{2}/\d{4})', str(dl))
    return datetime.strptime(m.group(1), '%d/%m/%Y').date().isoformat() if m else None

def normalize_salary(salary_str: str):
    s = str(salary_str).lower()
    if 'Thoả thuận' in s or 'thỏa thuận' in s:
        return None
    s_clean = s.replace(',', '')
    nums = re.findall(r"\d+(?:\.\d+)?", s_clean)
    if not nums:
        return None
    values = [float(n) for n in nums]
    val = sum(values) / len(values)
    if 'usd' in s_clean or '$' in s_clean:
        multiplier = EXCHANGE_RATE
    elif 'triệu' or 'tr' in s_clean:
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

def main():
    spark = SparkSession.builder \
        .appName("Clean Job Data with Spark") \
        .master("local[*]") \
        .getOrCreate()

    input_path = Path('/opt/Dataset/2025-10-08/merged_jobs_2025-10-08.json')
    output_path = Path('/opt/Output/cleaned_data.json')
    
    # Kiểm tra file tồn tại
    if not input_path.exists():
        print(f"⚠ File không tồn tại: {input_path}")
        return

    # Đọc JSON
    df = spark.read.option("multiline", "true").json("file://" + str(input_path))

    # Gộp dữ liệu từ topcv_jobs và vnwork_jobs
    df_topcv = df.select(explode(col("topcv_jobs")).alias("grp"))
    df_vnwork = df.select(explode(col("vnwork_jobs")).alias("grp"))
    df_all = df_topcv.unionByName(df_vnwork)

    # Bóc tách từng job
    df_jobs = df_all.select(
        col("grp.group").alias("group"),
        explode(col("grp.jobs")).alias("job")
    ).select(
        col("group"),
        col("job.title"),
        col("job.link"),
        col("job.location"),
        col("job.experience"),
        col("job.description"),
        col("job.requirements"),
        col("job.benefits"),
        col("job.work_location_detail"),
        col("job.working_time"),
        col("job.deadline"),
        col("job.salary")
    )
    # Định nghĩa UDFs
    udf_clean_requirements = udf(lambda r: clean_requirements(r or ''), StringType())
    udf_parse_deadline = udf(lambda d: parse_deadline(d or ''), StringType())
    udf_normalize_salary = udf(lambda s: normalize_salary(s or ''), StringType())
    udf_normalize_location = udf(lambda l: normalize_location(l or ''), StringType())
    
    # SpaCy model nạp ngoài UDF để tránh load nhiều lần
    nlp = spacy.load(NER_MODEL)
    def extract_skills(req):
        doc = nlp(req or '')
        return [ent.text for ent in doc.ents if ent.label_ == 'SKILL']
    udf_skills = udf(extract_skills, ArrayType(StringType()))

    # Xử lý DataFrame
    df_cleaned = df_jobs \
        .withColumn("requirements_clean", udf_clean_requirements(col("requirements"))) \
        .withColumn("deadline_parsed", udf_parse_deadline(col("deadline"))) \
        .withColumn("salary_normalized", udf_normalize_salary(col("salary"))) \
        .withColumn("location_norm", udf_normalize_location(col("location"))) \
        .withColumn("skills", udf_skills(col("requirements_clean"))) \
        .withColumn("currency_unit", lit("VND")) \
        .withColumn("working_time_norm", 
                    when(col("working_time").isNull() | (col("working_time") == ""), "Không rõ")
                    .otherwise(col("working_time"))) \
        .withColumn("experience_num",
                    when(col("experience").rlike(r"\d+"), regexp_extract(col("experience"), r"(\d+)", 1).cast("int"))
                    .otherwise(0)
                    )

    df_grouped = df_cleaned.groupBy("group").agg(
        F.collect_list(
            F.struct(
                "title",
                "link",
                F.col("location_norm").alias("location"),
                F.col("experience_num").alias("experience"),
                "description",
                F.col("requirements_clean").alias("requirements"),
                "benefits",
                "work_location_detail",
                F.col("working_time_norm").alias("working_time"),
                F.col("deadline_parsed").alias("deadline"),
                F.col("salary").alias("salary_raw"),
                ("salary_normalized"),
                "currency_unit",
                "skills"
            )
        ).alias("jobs")
    )

    # Coalesce 1 partition và collect ra Python
    json_list = df_grouped.coalesce(1).toJSON().collect()
    cleaned_json = '[\n' + ',\n'.join(json_list) + '\n]'

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned_json, encoding='utf-8')

    print(f"✔ Cleaned data written to {output_path}")
    spark.stop()

if __name__ == "__main__":
    main()
