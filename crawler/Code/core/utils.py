# utils.py
import os
import json
import time
import random
import logging
from datetime import datetime
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

def save_json(data, filepath):
    """Ghi thêm dữ liệu vào JSON (append) mà không ghi đè."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    existing = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    
    # Gộp dữ liệu mới vào
    if isinstance(existing, list):
        existing.extend(data if isinstance(data, list) else [data])
    else:
        existing = [existing] + ([data] if not isinstance(data, list) else data)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)