import streamlit as st
from page_mysql import page_mysql 
from page_mapreduce import page_mapreduce 
from page_web import page_web
st.set_page_config(page_title="My Streamlit App", layout="wide")
st.sidebar.title("Home")
page = st.sidebar.radio("Chọn Tính Năng", ["MapReduce", "Truy vấn MySQL","web"])
if page == "MapReduce":
    page_mapreduce()  # Gọi hàm MapReduce
elif page == "Truy vấn MySQL":
    page_mysql()  # Gọi hàm MySQL
elif page  == "web":
    page_web()