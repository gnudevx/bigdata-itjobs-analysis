import streamlit as st
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="070204",
            database="final_bigdata",
            charset="utf8mb4"
        )
        return connection
    except Error as e:
        st.error(f"Không thể kết nối tới MySQL: {e}")
        return None

def page_web():
    st.title("🔍 Danh sách việc làm")

    connection = connect_to_database()
    if not connection:
        return

    cursor = connection.cursor(dictionary=True)

    try:
        # Lấy danh sách nhóm ngành
        cursor.execute("SELECT id, name FROM skill_groups ORDER BY name")
        groups = cursor.fetchall()
        group_options = {g['name']: g['id'] for g in groups}
        group_names = ["Tất cả"] + list(group_options.keys())

        # Lấy danh sách kỹ năng hợp lệ
        cursor.execute("""
            SELECT DISTINCT name FROM skills 
            WHERE name REGEXP '^[A-Za-zÀ-ỹ0-9 ]+$'
            ORDER BY name
        """)
        skill_names = ["Tất cả"] + [row['name'] for row in cursor.fetchall()]

        # Lấy danh sách địa điểm (lọc loại bỏ các vị trí có '&', ',' hoặc chứa "nơi khác")
        cursor.execute("""
            SELECT DISTINCT location FROM jobs
            WHERE location NOT LIKE '%&%'
              AND location NOT LIKE '%,%'
              AND location NOT LIKE '%nơi khác%'
            ORDER BY location
        """)
        locations = ["Tất cả"] + [row['location'] for row in cursor.fetchall()]

        # Lấy danh sách kinh nghiệm
        cursor.execute("SELECT DISTINCT experience FROM jobs ORDER BY experience")
        experiences = ["Tất cả"] + [row['experience'] for row in cursor.fetchall()]

        # Định nghĩa các khoảng lương (ví dụ tính theo triệu hoặc đơn vị bạn dùng)
        salary_ranges = {
            "Tất cả": (None, None),
            "Dưới 5 triệu": (0, 5_000_000),
            "5 - 10 triệu": (5_000_000, 10_000_000),
            "10 - 20 triệu": (10_000_000, 20_000_000),
            "20 - 50 triệu": (20_000_000, 50_000_000),
            "Trên 50 triệu": (50_000_000, None)
        }

        selected_group = st.selectbox("🧩 Lọc theo nhóm ngành", group_names)
        selected_skill = st.selectbox("🛠️ Lọc theo kỹ năng", skill_names)
        selected_location = st.selectbox("📍 Lọc theo địa điểm", locations)
        selected_experience = st.selectbox("⏳ Lọc theo kinh nghiệm", experiences)
        selected_salary = st.selectbox("💰 Lọc theo mức lương", list(salary_ranges.keys()))
        keyword = st.text_input("🔎 Tìm kiếm theo từ khóa (tiêu đề hoặc mô tả)", "")

        # Tạo truy vấn chính
        query = """
            SELECT j.id, j.title, j.location, j.experience, j.working_time, j.deadline,
                   j.salary_raw, j.salary_normalized, sg.name AS group_name, jd.description, jd.requirements, jd.benefits
            FROM jobs j
            JOIN skill_groups sg ON j.group_id = sg.id
            LEFT JOIN job_details jd ON j.id = jd.job_id
            WHERE 1=1
        """
        params = []

        if selected_group != "Tất cả":
            query += " AND j.group_id = %s"
            params.append(group_options[selected_group])

        if selected_location != "Tất cả":
            query += " AND j.location = %s"
            params.append(selected_location)

        if selected_experience != "Tất cả":
            query += " AND j.experience = %s"
            params.append(selected_experience)

        # Lọc theo khoảng lương dựa vào salary_normalized
        if selected_salary != "Tất cả":
            min_salary, max_salary = salary_ranges[selected_salary]
            if min_salary is not None:
                query += " AND j.salary_normalized >= %s"
                params.append(min_salary)
            if max_salary is not None:
                query += " AND j.salary_normalized < %s"
                params.append(max_salary)

        if keyword:
            query += " AND (j.title LIKE %s OR jd.description LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        query += " ORDER BY j.deadline ASC"

        cursor.execute(query, params)
        jobs = cursor.fetchall()

        # Lọc theo kỹ năng nếu chọn skill khác "Tất cả"
        if selected_skill != "Tất cả":
            filtered_jobs = []
            for job in jobs:
                cursor.execute("""
                    SELECT s.name FROM job_skills js
                    JOIN skills s ON js.skill_id = s.id
                    WHERE js.job_id = %s
                """, (job['id'],))
                skills = [row['name'] for row in cursor.fetchall()]
                if selected_skill in skills:
                    job['skills'] = skills
                    filtered_jobs.append(job)
            jobs = filtered_jobs
        else:
            # Gán kỹ năng cho tất cả công việc khi không lọc skill
            for job in jobs:
                cursor.execute("""
                    SELECT s.name FROM job_skills js
                    JOIN skills s ON js.skill_id = s.id
                    WHERE js.job_id = %s
                """, (job['id'],))
                job['skills'] = [row['name'] for row in cursor.fetchall()]

        # Hiển thị kết quả
        if not jobs:
            st.warning("❗Không tìm thấy công việc phù hợp.")
        else:
            for job in jobs:
                with st.container():
                    st.subheader(job['title'])
                    st.markdown(f"**📁 Nhóm ngành:** {job['group_name']}")
                    st.markdown(f"📍 **Địa điểm:** {job['location']}")
                    st.markdown(f"⏳ **Kinh nghiệm:** {job['experience']}")
                    st.markdown(f"🕒 **Thời gian làm việc:** {job['working_time']}")
                    st.markdown(f"💰 **Mức lương:** {job['salary_raw']}")
                    st.markdown(f"🗓️ **Hạn nộp:** {job['deadline']}")

                    if job['skills']:
                        st.markdown(f"🛠️ **Kỹ năng yêu cầu:** {', '.join(job['skills'])}")

                    with st.expander("📄 Mô tả chi tiết"):
                        st.markdown(f"**Mô tả:**\n{job['description'] or 'Không có'}")
                        st.markdown(f"**Yêu cầu:**\n{job['requirements'] or 'Không có'}")
                        st.markdown(f"**Phúc lợi:**\n{job['benefits'] or 'Không có'}")

                    st.markdown("---")

    except Error as e:
        st.error(f"❌ Lỗi khi truy vấn dữ liệu: {e}")
    finally:
        cursor.close()
        connection.close()
