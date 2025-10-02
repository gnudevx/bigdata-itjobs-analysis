import streamlit as st
from dataraw import dataraw
from page_mapreduce import page_mapreduce
from page_web import page_web

st.set_page_config(page_title="My Streamlit App", layout="wide")

st.sidebar.title("Home")
page = st.sidebar.radio("Chọn Tính Năng", ["Dữ liệu ban đầu", "MapReduce", "web"])

if page == "Dữ liệu ban đầu":
    dataraw()
elif page == "MapReduce":
    page_mapreduce()
elif page == "web":
    page_web()
