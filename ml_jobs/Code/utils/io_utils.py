from pathlib import Path
import yaml
from datetime import datetime
import sys, os
sys.path.append('/opt/airflow/ml_jobs/')

# Load config YAML khi khởi tạo
CONFIG_PATH = Path("/opt/airflow/ml_jobs/configs/paths.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

def get_today():
    """Trả về ngày hiện tại định dạng YYYY-MM-DD"""
    return datetime.now().strftime(cfg["defaults"]["date_format"])

def get_data_path(stage: str, suffix="csv"):
    """
    Trả về đường dẫn file dữ liệu theo giai đoạn.
    stage: raw | processed | prepared
    """
    today = get_today()
    base = Path(cfg["data_root"])
    sub = cfg["folders"].get(stage)
    if not sub:
        raise ValueError(f"Stage '{stage}' không tồn tại trong config")
    dir_path = base / sub
    dir_path.mkdir(parents=True, exist_ok=True)  # ✅ tự tạo thư mục
    return dir_path / f"{stage}_dataset_{today}.{suffix}"

def get_model_dir(versioned: bool = False):
    """Trả về thư mục model (latest hoặc theo ngày)"""
    base = Path(cfg["model_root"])
    if versioned:
        today = get_today()
        path = base / today
    else:
        path = base / cfg["folders"]["latest_model"]
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_log_path(name: str):
    """Tạo đường dẫn file log theo tên"""
    base = Path(cfg["log_root"])
    base.mkdir(parents=True, exist_ok=True)
    today = get_today()
    return base / f"{name}_{today}.log"

def get_hdfs_client():
    """Tạo client HDFS từ config"""
    from hdfs import InsecureClient
    hdfs_cfg = cfg["hdfs"]
    return InsecureClient(hdfs_cfg["url"], user=hdfs_cfg["user"])

def get_hdfs_input_path(prefix="cleaned_data"):
    """Trả về đường dẫn file JSON trên HDFS theo ngày"""
    hdfs_cfg = cfg["hdfs"]
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{hdfs_cfg['input_root']}/{prefix}_{today}.json"
