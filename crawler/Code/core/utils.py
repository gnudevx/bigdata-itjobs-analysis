# utils.py
import os
import json
import time
import random
import logging
from datetime import datetime
from hdfs import InsecureClient
# --- Logging setup ---
import logging
import os

def setup_logger(name="crawler_logger", log_file=None):
    """
    Tạo logger ghi ra cả console và file.
    Nếu không truyền log_file thì chỉ log ra console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Tránh trùng handler khi gọi nhiều lần
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Ghi ra console
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

        # Nếu có file log thì ghi ra file
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

# --- Helpers ---
def log_and_print(msg, logger=None):
    """In ra console và ghi log nếu logger có."""
    print(msg)
    if logger is not None:
        logger.info(msg)

def human_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

# def save_json(data, filepath):
#     """Ghi thêm dữ liệu vào JSON (append) mà không ghi đè."""
#     os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
#     existing = []
#     if os.path.exists(filepath):
#         try:
#             with open(filepath, "r", encoding="utf-8") as f:
#                 existing = json.load(f)
#         except Exception:
#             existing = []
    
#     # Gộp dữ liệu mới vào
#     if isinstance(existing, list):
#         existing.extend(data if isinstance(data, list) else [data])
#     else:
#         existing = [existing] + ([data] if not isinstance(data, list) else data)
    
#     with open(filepath, "w", encoding="utf-8") as f:
#         json.dump(existing, f, ensure_ascii=False, indent=2)
        
        # Kết nối tới HDFS qua WebHDFS
client = InsecureClient('http://hadoop-master:9870', user='hadoopducdung')


def get_base_dir():
    """Thư mục gốc trên HDFS theo ngày crawl"""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"/user/hadoopducdung/airflow/dataset/{today}/vnwork"

def get_output_file(prefix="vnwork"):
    today = datetime.now().strftime("%Y-%m-%d")
    return f"/user/hadoopducdung/airflow/dataset/{today}/{prefix}_{today}.json"

# --- 1️⃣ Hàm ghi file tạm ---
def save_temp_json(data, base_dir, index):
    """Lưu từng batch nhỏ, ví dụ: .../tmp/part_1.json"""
    temp_dir = os.path.join(base_dir, "tmp")
    if not client.status(temp_dir, strict=False):
        client.makedirs(temp_dir)

    file_path = os.path.join(temp_dir, f"part_{index}.json")
    with client.write(file_path, encoding="utf-8", overwrite=True) as writer:
        json.dump(data, writer, ensure_ascii=False, indent=2)
    print(f"✅ Ghi file tạm: {file_path}")
    return file_path


# --- 2️⃣ Hàm merge các file nhỏ lại thành 1 file tổng ---
def merge_temp_files(base_dir, output_path):
    temp_dir = os.path.join(base_dir, "tmp")
    if not client.status(temp_dir, strict=False):
        print("[WARN] Không có thư mục tạm để merge.")
        return

    files = sorted(client.list(temp_dir))
    all_data = []

    for f in files:
        file_path = os.path.join(temp_dir, f)
        with client.read(file_path, encoding="utf-8") as reader:
            data = json.load(reader)
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)

    with client.write(output_path, encoding="utf-8", overwrite=True) as writer:
        json.dump(all_data, writer, ensure_ascii=False, indent=2)

    print(f"✅ Merge {len(files)} file → {output_path}")
    return output_path


# --- 3️⃣ Xóa thư mục tạm sau khi merge ---
def cleanup_temp(base_dir):
    temp_dir = os.path.join(base_dir, "tmp")
    if client.status(temp_dir, strict=False):
        client.delete(temp_dir, recursive=True)
        print(f"🧹 Đã xóa thư mục tạm: {temp_dir}")