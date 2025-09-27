import json
import pyodbc
from datetime import datetime

# 0. KẾT NỐI SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Big_Data;"
    "Trusted_Connection=yes;"
)
cur = conn.cursor()

# 1. Load JSON
with open(r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/cleaned_data.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# 2. Chuẩn bị skill_groups
category_ids = {}
for name in {j['group'].strip() for j in jobs}:
    cur.execute("""
        IF NOT EXISTS (SELECT 1 FROM dbo.skill_groups WHERE name = ?)
            INSERT INTO dbo.skill_groups(name) VALUES (?)
    """, (name, name))
# không commit ở đây
cur.execute("SELECT id, name FROM dbo.skill_groups")
for cid, cname in cur.fetchall():
    category_ids[cname] = cid

# 3. Chuẩn bị skills
skill_ids = {}
for skill in {s.strip() for j in jobs for s in j['skills']}:
    cur.execute("""
        IF NOT EXISTS (SELECT 1 FROM dbo.skills WHERE name = ?)
            INSERT INTO dbo.skills(name) VALUES (?)
    """, (skill, skill))
cur.execute("SELECT id, name FROM dbo.skills")
for sid, sname in cur.fetchall():
    skill_ids[sname] = sid

# helper ensure_skill không commit
def ensure_skill(name):
    name = name.strip()
    if name not in skill_ids:
        cur.execute("""
            IF NOT EXISTS (SELECT 1 FROM dbo.skills WHERE name = ?)
                INSERT INTO dbo.skills(name) VALUES (?)
        """, (name, name))
        cur.execute("SELECT id FROM dbo.skills WHERE name = ?", (name,))
        sid = cur.fetchone()[0]
        skill_ids[name] = sid
    return skill_ids[name]

# 4. Chuẩn bị skill_details
for j in jobs:
    gid = category_ids[j['group'].strip()]
    for raw_s in j['skills']:
        sid = ensure_skill(raw_s)
        cur.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM dbo.skill_details 
                WHERE skill_id = ? AND group_id = ?
            )
                INSERT INTO dbo.skill_details(skill_id, group_id) VALUES (?, ?)
        """, (sid, gid, sid, gid))

# 5. Chèn jobs → job_details → job_skills
for j in jobs:
    # parse deadline
    dl = j.get('deadline')
    deadline = datetime.strptime(dl, "%Y-%m-%d").date() if dl else None

    # 5.1 Insert vào jobs và lấy job_id
    sql_insert_job = """
        INSERT INTO dbo.jobs(
            group_id, title, link, location,
            experience, work_location_detail, working_time,
            deadline, salary_raw, salary_normalized, currency_unit
        )
        OUTPUT INSERTED.id
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """
    params = (
        category_ids[j['group'].strip()],
        j['title'], j['link'], j['location'],
        j['experience'], j['work_location_detail'], j['working_time'],
        deadline,
        j['salary_raw'], j['salary_normalized'], j['currency_unit']
    )
    cur.execute(sql_insert_job, params)
    job_id = cur.fetchone()[0]

    # 5.2 Insert vào job_details
    cur.execute("""
        INSERT INTO dbo.job_details(job_id, description, requirements, benefits)
        VALUES (?,?,?,?)
    """, (job_id, j['description'], j['requirements'], j['benefits']))

    # 5.3 Insert vào job_skills
    for raw_s in j['skills']:
        sid = ensure_skill(raw_s)
        cur.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM dbo.job_skills WHERE job_id = ? AND skill_id = ?
            )
                INSERT INTO dbo.job_skills(job_id, skill_id) VALUES (?, ?)
        """, (job_id, sid, job_id, sid))

# Cuối cùng mới commit
conn.commit()
cur.close()
conn.close()
print("✔ Dữ liệu đã lưu vào SQL Server thành công!")
