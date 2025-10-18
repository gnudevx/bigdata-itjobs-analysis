# driver_utils.py
import os, time, random, shutil
import undetected_chromedriver as uc
from pathlib import Path
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
import tempfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.fonts": 2,
    })
    user_agent = random.choice([
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'
    ])
    options.add_argument(f"--user-agent={user_agent}")
    print("[INFO] Starting Chrome UC for Vietnamworks...")
    # Đảm bảo logging và capabilities
    
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"
    driver = uc.Chrome(options=options, headless=True, use_subprocess=True, desired_capabilities=caps,
                       driver_executable_path=CHROMEDRIVER_PATH if CHROMEDRIVER_PATH else None)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )
    driver.set_page_load_timeout(180)   # ⏳ tăng timeout từ 60 → 180s
    driver.set_script_timeout(180)
    return driver