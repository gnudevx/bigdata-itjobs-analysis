import os
import json
import pandas as pd
import glob
import streamlit as st
import matplotlib.pyplot as plt

def dataraw():
    st.title("📊 Phân tích dữ liệu tuyển dụng IT - Dữ liệu ban đầu")

    files = glob.glob("../../crawler/Dataset/*.json")
    dfs = []

    for f in files:
        if os.path.getsize(f) > 0:
            try:
                with open(f, "r", encoding="utf-8") as f_in:
                    data = json.load(f_in)

                if isinstance(data, list):  # xử lý JSON array
                    for group_obj in data:
                        group_name = group_obj.get("group", os.path.basename(f))
                        jobs = group_obj.get("jobs", [])
                        df_temp = pd.DataFrame(jobs)
                        df_temp["source"] = group_name
                        dfs.append(df_temp)
                else:
                    st.warning(f"File {f} không đúng định dạng JSON array")

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

    if "location" in df.columns:
        st.subheader("Phân bố theo thành phố (Top 10)")
        city_counts = df['location'].value_counts().head(10)
        st.bar_chart(city_counts)

    if 'salary' in df.columns:
        st.subheader("Phân bố mức lương")
        fig, ax = plt.subplots()
        df['salary'].value_counts().head(20).plot(kind="barh", ax=ax)
        st.pyplot(fig)
