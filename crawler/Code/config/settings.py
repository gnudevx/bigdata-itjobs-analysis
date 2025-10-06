import os
from datetime import datetime

# Base URL
BASE_IT = "https://www.topcv.vn/viec-lam-it"
TARGET_PER_GROUP = 500

# Folder lưu dữ liệu & log
BASE_DIR = "/opt/airflow/crawler"
DATASET_DIR = f"{BASE_DIR}/Dataset"
LOG_DIR = f"{BASE_DIR}/Logs"

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Ngày hiện tại
TODAY = datetime.now().strftime("%Y-%m-%d")

# Chrome config
HEADLESS = True
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
