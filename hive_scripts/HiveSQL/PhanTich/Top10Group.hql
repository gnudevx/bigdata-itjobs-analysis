CREATE TABLE IF NOT EXISTS job_analysis.top10_jobs_Group
STORED AS PARQUET
AS
SELECT 
    `group`, 
    COUNT(*) AS job_count
FROM 
    git_jobs_raw
GROUP BY 
    `group`
ORDER BY 
    job_count DESC
LIMIT 10;

