import json
import mysql.connector
from pathlib import Path
from datetime import datetime
import re

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456789",
    "database": "final_bigdata",
    "charset": "utf8mb4"
}

# Load file cleaned_data.json sau khi đã làm sạch dữ liệu
with open(r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/cleaned_data.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

# 1. Thêm bảng group (skill_groups)
groups = set(j['group'] for j in jobs)
category_ids = {}
for g in groups:
    cur.execute("INSERT IGNORE INTO skill_groups(name) VALUES (%s)", (g,))
conn.commit()
cur.execute("SELECT id, name FROM skill_groups")
for cid, cname in cur.fetchall():
    category_ids[cname] = cid

# 2. Insert skills
skill_set = {skill for job in jobs for skill in job['skills']}
skill_ids = {}
for s in skill_set:
    cur.execute("INSERT IGNORE INTO skills(name) VALUES (%s)", (s,))
conn.commit()
cur.execute("SELECT id, name FROM skills")
for sid, sname in cur.fetchall():
    skill_ids[sname] = sid

# 3. Thêm 2 trường dữ liệu group_id và skill_id vào bảng skill_details
for job in jobs:
    gid = category_ids[job['group']]
    for s in job['skills']:
        sid = skill_ids.get(s)
        if sid:
            cur.execute(
                "INSERT IGNORE INTO skill_details(skill_id, group_id) VALUES (%s, %s)",
                (sid, gid)
            )
conn.commit()

# 4. thêm các bảng jobs, job_details, job_skills
for job in jobs:
    # parse deadline
    dl = job.get('deadline')
    deadline = datetime.strptime(dl, "%Y-%m-%d").date() if dl else None

    # insert into jobs with group_id
    group_id = category_ids[job['group']]
    cur.execute(
        """
        INSERT INTO jobs(
            group_id, title, link, location,
            experience, work_location_detail, working_time,
            deadline, salary_raw, salary_normalized, currency_unit
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            group_id,
            job['title'], job['link'], job['location'],
            job['experience'], job['work_location_detail'], job['working_time'],
            deadline,
            job['salary_raw'], job['salary_normalized'], job['currency_unit']
        )
    )
    job_id = cur.lastrowid

    # thêm dữ liệu cho Job_detals
    cur.execute(
        "INSERT INTO job_details(job_id, description, requirements, benefits) VALUES (%s,%s,%s,%s)",
        (job_id, job['description'], job['requirements'], job['benefits'])
    )

    # Thêm dữ liệu cho bảng job_skills
    for s in job['skills']:
        sid = skill_ids.get(s)
        if sid:
            cur.execute(
                "INSERT IGNORE INTO job_skills(job_id, skill_id) VALUES (%s, %s)",
                (job_id, sid)
            )

conn.commit()
cur.close()
conn.close()
print("✔ Đã lưu vào MySQL thành công!")