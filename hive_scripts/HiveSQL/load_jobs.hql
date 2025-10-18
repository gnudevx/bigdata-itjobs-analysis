-- Load dữ liệu JSON từ HDFS vào bảng external Hive
-- Được tạo và chạy bằng:
--   docker cp "D:\bigdata-itjobs-analysis\hive_scripts\HiveSQL\load_jobs.hql" hive-server:/tmp/load_jobs.hql
--   hive -f /tmp/load_jobs.hql

CREATE DATABASE IF NOT EXISTS job_analysis;

USE job_analysis;

CREATE EXTERNAL TABLE IF NOT EXISTS git_jobs_raw (
    `group` STRING,
    title STRING,
    link STRING,
    location STRING,
    experience STRING,
    description STRING,
    requirements STRING,
    benefits STRING,
    work_location_detail STRING,
    working_time STRING,
    deadline STRING,
    salary_raw STRING,
    salary_normalized DOUBLE,
    currency_unit STRING,
    skills ARRAY<STRING>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/user/DatasetRaw/';


