import streamlit as st
from dataraw import dataraw
from page_hive import page_hive

st.set_page_config(page_title="My Streamlit App", layout="wide")

st.sidebar.title("Home")
page = st.sidebar.radio("Chọn Tính Năng", ["Dữ liệu ban đầu", "Hive Analysis", "web"])

if page == "Dữ liệu ban đầu":
    dataraw()
elif page == "Hive Analysis":
    page_hive()
elif page == "web":
    page_web()
