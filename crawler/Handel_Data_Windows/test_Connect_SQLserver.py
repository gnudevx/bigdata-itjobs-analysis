import pyodbc

# In danh sách driver đang có
print("Installed ODBC drivers:", pyodbc.drivers())

# Kết nối (như ví dụ dùng Windows Authentication)
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Big_Data;"
    "Trusted_Connection=yes;"
)

print("✔ Kết nối thành công!")