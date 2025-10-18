USE job_analysis;

CREATE TABLE job_analysis.git_jobs_parquet
STORED AS PARQUET
AS SELECT * FROM job_analysis.git_jobs_raw;
