import os
import json
import pandas as pd
import glob
import streamlit as st
import matplotlib.pyplot as plt

def dataraw():
    st.title("📊 Phân tích dữ liệu tuyển dụng IT - Dữ liệu ban đầu")

    files = glob.glob("../../spark_jobs/Output/*.json")
    dfs = []

    for f in files:
        if os.path.getsize(f) > 0:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    rows = []
                    for group_block in data:
                        group = group_block.get("group", "")
                        jobs = group_block.get("jobs", [])
                        for job in jobs:
                            job["group"] = group
                            job["source"] = os.path.basename(f)
                            rows.append(job)
                    df_temp = pd.DataFrame(rows)
                    dfs.append(df_temp)
            except Exception as e:
                st.warning(f"Lỗi khi đọc {f}: {e}")

    if not dfs:
        st.error("Không load được dữ liệu JSON nào. Kiểm tra lại Dataset/")
        return

    df = pd.concat(dfs, ignore_index=True)

    st.subheader("Tổng quan")
    st.write(f"Số job: {len(df)}")
    st.write("Các cột:", list(df.columns))
    st.write("Nguồn dữ liệu:", df['source'].unique())

    # --- Phân bố theo thành phố ---
    if "location" in df.columns:
        st.subheader("Phân bố theo thành phố (Top 10)")
        df["location"] = df["location"].fillna("Không rõ").replace("", "Không rõ")
        city_counts = df["location"].value_counts().head(10)
        st.bar_chart(city_counts)

    # --- Phân bố mức lương ---
    if 'salary_raw' in df.columns:
        st.subheader("Phân bố mức lương")
        fig, ax = plt.subplots()
        df['salary_raw'].value_counts().head(20).plot(kind="barh", ax=ax)
        st.pyplot(fig)
