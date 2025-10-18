-- Nếu bảng đã tồn tại, drop trước
DROP TABLE IF EXISTS job_analysis.git_jobs_top10;

-- Tạo bảng mới lưu kết quả top 10 tỉnh/thành
CREATE TABLE job_analysis.git_jobs_top10
STORED AS PARQUET
AS
SELECT standardized_location AS location, COUNT(*) AS total_jobs
FROM (
    SELECT
        CASE
            WHEN LOWER(TRIM(loc)) IN ('hà nội','ha noi','hanoi') THEN 'Hà Nội'
            WHEN LOWER(TRIM(loc)) IN ('hồ chí minh','hcm','ho chi minh') THEN 'Hồ Chí Minh'
            WHEN LOWER(TRIM(loc)) IN ('đà nẵng','da nang') THEN 'Đà Nẵng'
            WHEN LOWER(TRIM(loc)) IN ('bình định','binh dinh') THEN 'Bình Định'
            WHEN LOWER(TRIM(loc)) IN ('hải phòng','hai phong') THEN 'Hải Phòng'
            WHEN LOWER(TRIM(loc)) IN ('cần thơ','can tho') THEN 'Cần Thơ'
            WHEN LOWER(TRIM(loc)) IN ('đồng nai','dong nai') THEN 'Đồng Nai'
            WHEN LOWER(TRIM(loc)) IN ('bình dương','binh duong') THEN 'Bình Dương'
            WHEN LOWER(TRIM(loc)) IN ('khánh hòa','khanh hoa') THEN 'Khánh Hòa'
            WHEN LOWER(TRIM(loc)) IN ('thừa thiên huế','thua thien hue') THEN 'Thừa Thiên Huế'
            WHEN LOWER(TRIM(loc)) IN ('nha trang') THEN 'Nha Trang'
            ELSE NULL
        END AS standardized_location
    FROM git_jobs_raw
         LATERAL VIEW explode(
             split(location, ',')
         ) loc_table AS loc
    WHERE location IS NOT NULL
      AND TRIM(location) != ''
      AND loc IS NOT NULL
      AND TRIM(loc) != ''
      AND LENGTH(TRIM(loc)) > 1
      AND loc NOT RLIKE '([0-9]+ nơi|khác)'
) t
WHERE standardized_location IS NOT NULL
GROUP BY standardized_location
ORDER BY total_jobs DESC
LIMIT 10;
