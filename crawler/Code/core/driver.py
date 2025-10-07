# driver_utils.py
import os, time, random, shutil
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
import tempfile
# OPTIONAL: đặt CHROMEDRIVER_PATH nếu bạn cài chromedriver trong Docker và muốn dùng cố định.
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", None)  # ví dụ: /usr/local/bin/chromedriver
HEADLESS = os.environ.get("HEADLESS", "1") == "1"

def init_driver(profile_dir=None, proxy=None, headless=True, fixed_driver_path=None):
    # xóa cache uc global để tránh xung đột driver cũ (nếu cần)
    # shutil.rmtree("/home/airflow/.local/share/undetected_chromedriver", ignore_errors=True)
    unique_cache = tempfile.mkdtemp(prefix="uc_cache_")
    os.environ["UDC_DATA_DIR"] = unique_cache
    opts = uc.ChromeOptions()
    if profile_dir:
        opts.add_argument(f"--user-data-dir={profile_dir}")
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")

    # required args for container
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--window-size=1920,1080")

    # headless handling: try flexible
    if headless:
        # prefer legacy headless for compatibility
        opts.add_argument("--headless")
        opts.add_argument("--disable-blink-features=AutomationControlled")
    else:
        # headfull (for local debug)
        pass

    # opts.add_argument("--remote-debugging-port=9222")
    debug_port = random.randint(9000, 9999)
    opts.add_argument(f"--remote-debugging-port={debug_port}")
    # Randomize UA
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    ]
    opts.add_argument(f"--user-agent={random.choice(user_agents)}")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.cookies": 2,
        # javascript off may break SPA - be careful (set to 1 if site needs js)
        "profile.managed_default_content_settings.javascript": 1,
    }
    opts.add_experimental_option("prefs", prefs)

    service = None
    if fixed_driver_path:
        service = Service(fixed_driver_path)

    # use_subprocess=True can help avoid "Text file busy" issues in some envs
    driver = uc.Chrome(options=opts, service=service, use_subprocess=True, headless=headless)

    # Inject safe navigator overwrites early
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Linux x86_64' });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        """
    })

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Linux x86_64",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # small random delay before using
    time.sleep(random.uniform(1.5, 3.5))
    return driver
