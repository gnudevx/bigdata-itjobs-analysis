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
        if os.path.getsize(f) > 0:  # bỏ file rỗng
            try:
                with open(f, "r", encoding="utf-8") as file:
                    first_char = file.read(1)
                    file.seek(0)
                    if first_char == "[":  # JSON array
                        df_temp = pd.read_json(file, lines=False)
                    else:  # JSON Lines
                        df_temp = pd.read_json(file, lines=True)

                df_temp["source"] = os.path.basename(f)
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

    # phân bố theo thành phố
    if "location" in df.columns:
        st.subheader("Phân bố theo thành phố (Top 10)")
        city_counts = df['location'].value_counts().head(10)
        st.bar_chart(city_counts)

    # phân bố mức lương
    if 'salary' in df.columns:
        st.subheader("Phân bố mức lương")
        fig, ax = plt.subplots()
        df['salary'].value_counts().head(20).plot(kind="barh", ax=ax)
        st.pyplot(fig)
