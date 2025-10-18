CREATE TABLE IF NOT EXISTS job_analysis.top10_jobs_Skill
STORED AS PARQUET
AS
SELECT 
    LOWER(TRIM(regexp_replace(skill, '\\\\.', ''))) AS clean_skill,
    COUNT(*) AS total_demand
FROM git_jobs_raw
LATERAL VIEW explode(skills) s AS skill
WHERE 
    skill IS NOT NULL 
    AND TRIM(skill) != ''
    AND skill NOT RLIKE '^[0-9]+$'     -- bỏ giá trị toàn số
    AND TRIM(skill) != '•'             -- bỏ ký tự chấm đầu dòng
GROUP BY LOWER(TRIM(regexp_replace(skill, '\\\\.', '')))
ORDER BY total_demand DESC
LIMIT 10;
