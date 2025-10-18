USE job_analysis;
CREATE TABLE IF NOT EXISTS job_analysis.top10_jobs_experience
STORED AS PARQUET
AS
SELECT 
    CASE
        WHEN LOWER(TRIM(experience)) = 'không yêu cầu' THEN 'Không yêu cầu kinh nghiệm'
        WHEN LOWER(TRIM(experience)) = 'dưới 1 năm' THEN 'Dưới 1 năm'
        WHEN LOWER(TRIM(experience)) = '1 năm' THEN '1 năm'
        WHEN LOWER(TRIM(experience)) = '2 năm' THEN '2 năm'
        WHEN LOWER(TRIM(experience)) = '3 năm' THEN '3 năm'
        WHEN LOWER(TRIM(experience)) = '4 năm' THEN '4 năm'
        WHEN LOWER(TRIM(experience)) = 'trên 5 năm' THEN 'Trên 5 năm'
        ELSE 'Khác'
    END AS experience_group,
    COUNT(*) AS total_jobs
FROM git_jobs_raw
WHERE experience IS NOT NULL 
      AND TRIM(experience) != ''
GROUP BY 
    CASE
        WHEN LOWER(TRIM(experience)) = 'không yêu cầu' THEN 'Không yêu cầu kinh nghiệm'
        WHEN LOWER(TRIM(experience)) = 'dưới 1 năm' THEN 'Dưới 1 năm'
        WHEN LOWER(TRIM(experience)) = '1 năm' THEN '1 năm'
        WHEN LOWER(TRIM(experience)) = '2 năm' THEN '2 năm'
        WHEN LOWER(TRIM(experience)) = '3 năm' THEN '3 năm'
        WHEN LOWER(TRIM(experience)) = '4 năm' THEN '4 năm'
        WHEN LOWER(TRIM(experience)) = 'trên 5 năm' THEN 'Trên 5 năm'
        ELSE 'Khác'
    END
ORDER BY total_jobs DESC;
