import os
import json
import pandas as pd
import glob
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def dataraw():
    st.title("📊 Phân tích dữ liệu tuyển dụng IT - Sau khi clean đầu")

    files = glob.glob("../../spark_jobs/Output/2025-10-18/cleaned_data.json")
    dfs = []

    for f in files:
        if os.path.getsize(f) > 0:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    # FIX: đọc JSON theo dòng (Spark output kiểu line-delimited)
                    data = []
                    for line in file:
                        if line.strip():
                            try:
                                obj = json.loads(line)
                                data.append(obj)
                            except Exception as e:
                                st.warning(f"Lỗi parse dòng trong {f}: {e}")

                    # Mỗi phần tử là {group:..., jobs:[...]}
                    rows = []
                    for group_block in data:
                        if not isinstance(group_block, dict):
                            continue
                        group = group_block.get("group", "")
                        jobs = group_block.get("jobs", [])
                        for job in jobs:
                            job["group"] = group
                            job["source"] = os.path.basename(f)
                            rows.append(job)
                    if rows:
                        df_temp = pd.DataFrame(rows)
                        dfs.append(df_temp)
            except Exception as e:
                st.warning(f"Lỗi khi đọc {f}: {e}")

    if not dfs:
        st.error("❌ Không load được dữ liệu JSON nào. Kiểm tra lại Output/")
        return

    df = pd.concat(dfs, ignore_index=True)
    st.success(f"✅ Đã load {len(df)} job từ {len(files)} file JSON.")
    st.write("Các cột:", list(df.columns))

    # === Trực quan hóa ===
    st.header("📈 Phân tích các yếu tố ảnh hưởng đến mức lương")

    if "location" in df.columns:
        st.subheader("Lương trung bình theo thành phố (Top 10)")
        city_salary = df.groupby("location")["salary_normalized"].mean().sort_values(ascending=False).head(10)
        st.bar_chart(city_salary)
    if "skills" in df.columns:
        st.subheader("Skills (Top 10)")
        # Giả sử df['skills'] là list, ví dụ: ['Python', 'SQL', 'Spark']
        all_skills = df['skills'].explode()  # 'explode' biến list thành từng row
        skill_counts = all_skills.value_counts().head(10)  # top 10 skills
        st.bar_chart(skill_counts)
    
    if "group" in df.columns:
        st.subheader("Lương trung bình theo nhóm nghề")
        group_salary = df.groupby("group")["salary_normalized"].mean().sort_values(ascending=False).head(10)
        fig2, ax2 = plt.subplots()
        group_salary.plot(kind="barh", ax=ax2, color="teal")
        st.pyplot(fig2)

    st.caption("Nguồn: cleaned_data_2025-10-18.json (Spark output)")
