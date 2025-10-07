import json
import os
from datetime import datetime

BASE_DIR = "/opt/airflow/crawler/Dataset"

def merge_crawl_results():
    today_str = datetime.now().strftime("%Y-%m-%d")
    day_dir = os.path.join(BASE_DIR, today_str)  # ✅ thư mục của ngày hôm nay
    merged_file = os.path.join(day_dir, f"merged_jobs_{today_str}.json")

    if not os.path.exists(day_dir):
        print(f"⚠️ Không có thư mục {day_dir}")
        return

    topcv_file = None
    vnwork_file = None

    for f in os.listdir(day_dir):
        if f.startswith("topcv_") and today_str in f:
            topcv_file = os.path.join(day_dir, f)
        elif f.startswith("vnwork_") and today_str in f:
            vnwork_file = os.path.join(day_dir, f)

    if not topcv_file or not vnwork_file:
        print("⚠️ Không tìm thấy đủ file nguồn để merge.")
        return

    with open(topcv_file, "r", encoding="utf-8") as f1, open(vnwork_file, "r", encoding="utf-8") as f2:
        topcv_data = json.load(f1)
        vnwork_data = json.load(f2)

    # Gộp danh sách job
    merged_data = {
        "date": today_str,
        "topcv_jobs": topcv_data,
        "vnwork_jobs": vnwork_data,
        "total_jobs": len(topcv_data) + len(vnwork_data),
    }

    with open(merged_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã gộp file: {merged_file}")
