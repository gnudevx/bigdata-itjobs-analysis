import os
import time
import random
import shutil
import undetected_chromedriver as uc
from selenium_stealth import stealth

def init_topcv_driver(headless=True):
    # 🧹 Dọn cache cũ trước khi init (fix session bị reuse)
    uc_cache = os.path.expanduser("~/.local/share/undetected_chromedriver")
    shutil.rmtree(uc_cache, ignore_errors=True)

    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--remote-debugging-port=9222")
    opts.add_argument("--log-level=3")

    # 🧩 KHÔNG DÙNG --single-process (sẽ crash)
    # 🧩 KHÔNG DÙNG --no-zygote (gây invalid session id trên uc 3.5+)

    if headless:
        opts.add_argument("--headless=new")

    opts.add_argument(f"--user-agent={random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36',
    ])}")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 1,
        "profile.managed_default_content_settings.cookies": 1,
        "profile.managed_default_content_settings.javascript": 1,
    }
    opts.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(options=opts, headless=headless, use_subprocess=True)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.",
            platform="Linux x86_64", webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    time.sleep(random.uniform(2, 4))
    return driver
