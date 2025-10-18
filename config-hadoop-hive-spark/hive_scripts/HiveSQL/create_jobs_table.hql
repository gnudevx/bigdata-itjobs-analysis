
CREATE DATABASE IF NOT EXISTS job_analysis;
USE job_analysis;

CREATE EXTERNAL TABLE IF NOT EXISTS git_jobs_raw (
    `group` STRING,
    jobs ARRAY<STRUCT<
        title:STRING,
        link:STRING,
        salary:STRING,
        location:STRING,
        experience:STRING,
        description:STRING,
        requirements:STRING,
        benefits:STRING,
        work_location_detail:STRING,
        working_time:STRING,
        deadline:STRING
    >>
)
STORED AS PARQUET;
