CREATE TABLE IF NOT EXISTS job_analysis.top10_jobs_salary
STORED AS PARQUET
AS
SELECT
    title AS job_title,
    location,
    salary_normalized AS salary
FROM job_analysis.git_jobs_raw
WHERE salary_normalized IS NOT NULL
      AND salary_normalized > 0
ORDER BY salary_normalized DESC
LIMIT 10;
