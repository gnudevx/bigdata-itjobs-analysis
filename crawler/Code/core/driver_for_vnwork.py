# driver_utils.py
import os, time, random, shutil
import undetected_chromedriver as uc
from pathlib import Path
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
import tempfile
# OPTIONAL: đặt CHROMEDRIVER_PATH nếu bạn cài chromedriver trong Docker và muốn dùng cố định.
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", None)  # ví dụ: /usr/local/bin/chromedriver
HEADLESS = os.environ.get("HEADLESS", "1") == "1"

def init_vnwork_driver():
    # ⚙️ Xóa cache UC cũ (tránh lỗi version mismatch)
    uc_cache_dir = "/home/airflow/.local/share/undetected_chromedriver"
    uc_dir = Path.home() / ".local/share/undetected_chromedriver/undetected"
    if uc_dir.exists():
        shutil.rmtree(uc_dir, ignore_errors=True)
    if os.path.exists(uc_cache_dir):
        shutil.rmtree(uc_cache_dir, ignore_errors=True)

    # ⚙️ Cache riêng cho session này
    unique_cache = f"/tmp/undetected_chromedriver_{int(time.time())}"
    os.makedirs(unique_cache, exist_ok=True)
    os.environ["UDC_DATA_DIR"] = unique_cache

    # ⚙️ Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

    print("[INFO] Starting Chrome UC for Vietnamworks...")

    driver = uc.Chrome(options=options)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver