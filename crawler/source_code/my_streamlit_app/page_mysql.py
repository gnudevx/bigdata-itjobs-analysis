import streamlit as st
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    """Kết nối tới cơ sở dữ liệu MySQL."""
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

def get_table_names(cursor):
    """Lấy danh sách tên bảng từ cơ sở dữ liệu."""
    cursor.execute("SHOW TABLES")
    return [table[0] for table in cursor.fetchall()]

def get_column_names(cursor, table_name):
    """Lấy danh sách cột của một bảng cụ thể."""
    cursor.execute(f"DESCRIBE {table_name}")
    return [column[0] for column in cursor.fetchall()]

def page_mysql():
    st.title("Quản Lý Dữ Liệu với MySQL (CRUD)")
    
    # Lựa chọn hành động
    action = st.sidebar.selectbox("Chọn hành động", ["Tạo (Create)", "Đọc (Read)", "Cập nhật (Update)", "Xóa (Delete)"])

    # Kết nối tới MySQL
    connection = connect_to_database()
    if not connection:
        return
    
    cursor = connection.cursor()

    # Lấy danh sách bảng
    table_names = get_table_names(cursor)
    
    # Tạo (Create)
    if action == "Tạo (Create)":
        st.subheader("Thêm dữ liệu mới")
        table_name = st.selectbox("Chọn bảng:", table_names)  # Combobox chọn bảng
        
        # Lấy danh sách cột của bảng đã chọn
        columns = get_column_names(cursor, table_name)
        selected_columns = st.multiselect("Chọn cột để thêm dữ liệu:", columns)
        values = {}
        
        # Hiển thị các ô nhập dữ liệu cho các cột đã chọn
        for column in selected_columns:
            values[column] = st.text_input(f"Nhập giá trị cho {column}:")
        
        if st.button("Thêm dữ liệu"):
            columns_str = ", ".join(selected_columns)
            values_str = ", ".join([f"'{values[column]}'" for column in selected_columns])
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"
            try:
                cursor.execute(query)
                connection.commit()
                st.success("Thêm dữ liệu thành công!")
            except Error as e:
                st.error(f"Lỗi khi thêm dữ liệu: {e}")

    # Cập nhật (Update)
    elif action == "Cập nhật (Update)":
        st.subheader("Cập nhật dữ liệu")
        table_name = st.selectbox("Chọn bảng:", table_names)  # Combobox chọn bảng
        
        # Lấy danh sách cột của bảng đã chọn
        columns = get_column_names(cursor, table_name)
        set_column = st.selectbox("Chọn cột cần cập nhật:", columns)
        new_value = st.text_input(f"Nhập giá trị mới cho {set_column}:")
        condition_column = st.selectbox("Chọn cột điều kiện WHERE:", columns)
        condition_value = st.text_input(f"Nhập giá trị cho điều kiện WHERE {condition_column}:")

        if st.button("Cập nhật dữ liệu"):
            query = f"UPDATE {table_name} SET {set_column} = '{new_value}' WHERE {condition_column} = '{condition_value}'"
            try:
                cursor.execute(query)
                connection.commit()
                st.success("Cập nhật dữ liệu thành công!")
            except Error as e:
                st.error(f"Lỗi khi cập nhật dữ liệu: {e}")

    # Đọc (Read)
    elif action == "Đọc (Read)":
        st.subheader("Truy vấn dữ liệu")
        query = st.text_area("Nhập câu truy vấn SQL:", "SELECT * FROM jobs LIMIT 10;")
        
        if st.button("Thực hiện truy vấn"):
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                if result:
                    st.write("Kết quả truy vấn:")
                    for row in result:
                        st.write(row)
                else:
                    st.warning("Không có kết quả.")
            except Error as e:
                st.error(f"Lỗi khi truy vấn: {e}")

    # Xóa (Delete)
    elif action == "Xóa (Delete)":
        st.subheader("Xóa dữ liệu")
        table_name = st.selectbox("Chọn bảng:", table_names)  # Combobox chọn bảng
        condition_column = st.selectbox("Chọn cột điều kiện WHERE:", get_column_names(cursor, table_name))
        condition_value = st.text_input(f"Nhập giá trị cho điều kiện WHERE {condition_column}:")

        if st.button("Xóa dữ liệu"):
            query = f"DELETE FROM {table_name} WHERE {condition_column} = '{condition_value}'"
            try:
                cursor.execute(query)
                connection.commit()
                st.success("Xóa dữ liệu thành công!")
            except Error as e:
                st.error(f"Lỗi khi xóa dữ liệu: {e}")
    
    # Đóng kết nối
    cursor.close()
    connection.close()
