import json
from datetime import datetime
from hdfs import InsecureClient

# Kết nối WebHDFS
client = InsecureClient('http://hadoop-master:9870', user='hadoopducdung')

BASE_HDFS_DIR = "/user/hadoopducdung/airflow/dataset"

def merge_crawl_results():
    today_str = datetime.now().strftime("%Y-%m-%d")
    day_dir = f"{BASE_HDFS_DIR}/{today_str}"
    merged_file = f"{day_dir}/merged_jobs_{today_str}.json"

    # Liệt kê file trong HDFS
    try:
        files = client.list(day_dir)
    except Exception as e:
        print(f"⚠️ Không có thư mục {day_dir} trên HDFS: {e}")
        return

    # Tìm file crawl
    topcv_file = next((f"{day_dir}/{f}" for f in files if f.startswith("topcv_")), None)
    vnwork_file = next((f"{day_dir}/{f}" for f in files if f.startswith("vnwork_")), None)

    if not topcv_file or not vnwork_file:
        print("⚠️ Không tìm thấy đủ file nguồn để merge trên HDFS.")
        return

    # Đọc file từ HDFS
    with client.read(topcv_file, encoding='utf-8') as f1:
        topcv_data = json.load(f1)
    with client.read(vnwork_file, encoding='utf-8') as f2:
        vnwork_data = json.load(f2)

    # Gộp dữ liệu
    merged_data = {
        "date": today_str,
        "topcv_jobs": topcv_data,
        "vnwork_jobs": vnwork_data,
        "total_jobs": len(topcv_data) + len(vnwork_data),
    }

    # Ghi lên HDFS
    with client.write(merged_file, encoding='utf-8', overwrite=True) as writer:
        json.dump(merged_data, writer, ensure_ascii=False, indent=2)

    print(f"✅ Đã gộp và lưu lên HDFS: {merged_file}")

# Chạy merge
if __name__ == "__main__":
    merge_crawl_results()
