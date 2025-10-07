import os
from datetime import datetime

# Base URL
BASE_IT_TOPCV = "https://www.topcv.vn/viec-lam-it"
BASE_IT_VNWORK = "https://www.vietnamworks.com/viec-lam?q=it"

TARGET_PER_GROUP = 500

# Base folder
BASE_DIR = "/opt/airflow/crawler"
DATASET_DIR = f"{BASE_DIR}/Dataset"
LOG_DIR = f"{BASE_DIR}/Logs"

# Tạo thư mục ngày
TODAY = datetime.now().strftime("%Y-%m-%d")
DATASET_DAY_DIR = os.path.join(DATASET_DIR, TODAY)
LOG_DAY_DIR = os.path.join(LOG_DIR, TODAY)
os.makedirs(DATASET_DAY_DIR, exist_ok=True)
os.makedirs(LOG_DAY_DIR, exist_ok=True)

def get_output_file(prefix="vnwork"):
    """
    Trả về đường dẫn file JSON trong thư mục ngày, ví dụ:
    /opt/airflow/crawler/Dataset/2025-10-06/vnwork_2025-10-06.json
    """
    return os.path.join(DATASET_DAY_DIR, f"{prefix}_{TODAY}.json")


# Chrome config
HEADLESS = True
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
