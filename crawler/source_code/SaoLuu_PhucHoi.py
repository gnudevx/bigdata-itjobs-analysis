import streamlit as st
import os
import subprocess
import mysql.connector

st.title("Sao lưu/phục hồi CSDL bằng MySQL")

backup_dir = "/home/nhom06/backup"

os.makedirs(backup_dir, exist_ok=True)

# Backup Section
st.subheader("SAO LƯU CSDL")
mysql_user = "root"  # Using root user

# Hàm lấy danh sách CSDL
def get_mysql_databases():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=mysql_user,        # Giữ nguyên user root
            password="1",           # Giữ nguyên mật khẩu (nếu đã cấu hình mysql_native_password)
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        # Lọc bỏ schema hệ thống nếu cần
        system = {"information_schema", "mysql", "performance_schema", "sys"}
        return [db for db in dbs if db not in system]
    except Exception as e:
        st.error(f"Lỗi khi kết nối MySQL: {e}")
        return []

# Lấy và hiển thị selectbox
databases = get_mysql_databases()
database_name = st.selectbox("Chọn CSDL cần lưu trữ:", databases)

# Nút Save
if st.button("Save"):
    if database_name:
        backup_file = os.path.join(backup_dir, f"{database_name}_backup.sql")
        
        command = [
            "sudo", "mysqldump",
            "-u", "root", "--password=1",
            database_name
        ]

        try:
            with open(backup_file, "wb") as f:
                proc = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                st.success(f"Sao lưu thành công tại: {backup_file}")
            else:
                st.error(f"Đã xảy ra lỗi khi sao lưu: {proc.stderr}")
        except Exception as e:
            st.error(f"Đã xảy ra lỗi khi sao lưu: {e}")
    else:
        st.warning("Hãy chọn CSDL cần lưu")


# Restore Section
st.subheader("PHỤC HỒI CSDL")
restore_user = "root"  # Using root user
uploaded_file = st.file_uploader("Chọn file SQL để phục hồi", type=["sql"])

if uploaded_file is not None:
    restore_database = st.text_input("Nhập tên CSDL để phục hồi:")

    if st.button("Restore"):
        if restore_database:
            # Save the uploaded file to the backup directory
            restore_path = os.path.join(backup_dir, uploaded_file.name)
            with open(restore_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Delete the existing database and create a new one
            delete_and_create_db_command = f"sudo mysql -u {mysql_user} --password=1 -e 'DROP DATABASE IF EXISTS {restore_database}; CREATE DATABASE {restore_database};'"
            
            # Restore command
            restore_command = [
                "sudo", "mysql",
                "-u", restore_user, "--password=1",
                restore_database
            ]

            try:
                # Delete and create database
                process_delete_create = subprocess.run(delete_and_create_db_command, shell=True, stderr=subprocess.PIPE, text=True)
                if process_delete_create.returncode != 0:
                    st.error(f"Đã xảy ra lỗi khi xóa và tạo lại cơ sở dữ liệu: {process_delete_create.stderr}")

                # Restore the database
                with open(restore_path, "rb") as f:
                    process_restore = subprocess.run(restore_command, stdin=f, stderr=subprocess.PIPE, text=True)
                
                if process_restore.returncode == 0:
                    st.success(f"Phục hồi thành công từ: {uploaded_file.name}")
                else:
                    st.error(f"Đã xảy ra lỗi khi phục hồi: {process_restore.stderr}")
            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi phục hồi: {str(e)}")
        else:
            st.warning("Vui lòng nhập tên CSDL để phục hồi")

