# utils.py
import os
import json
import time
import random
import logging
from datetime import datetime
from crawler.Code.config.settings import LOG_DIR

# --- Logging setup ---
def setup_logger(name="topcv"):
    log_file = os.path.join(LOG_DIR, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger(name)

# --- Helpers ---
def log_and_print(logger, msg):
    print(msg)
    logger.info(msg)

def human_delay(base=1.0, variation=0.5):
    time.sleep(base + random.random() * variation)

def save_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except:
            existing = []
    else:
        existing = []
    existing.append(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
