# driver.py
import time
import random
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from crawler.Code.config.settings import CHROMEDRIVER_PATH, HEADLESS

def init_driver(profile_dir=None, proxy=None, headless=True, version_main=None):
    opts = uc.ChromeOptions()
    if profile_dir:
        opts.add_argument(f"--user-data-dir={profile_dir}")
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")

    # ⚙️ Bắt buộc có
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--window-size=1920,1080")

    # ⚠️ Bỏ dấu hiệu headless Chrome mặc định
    if HEADLESS:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")

    # 👤 Random user-agent mỗi lần
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    ]
    opts.add_argument(f"--user-agent={random.choice(user_agents)}")

    service = Service(CHROMEDRIVER_PATH)

    driver = uc.Chrome(
        options=opts,
        service=service,
        use_subprocess=True,
        headless=headless,
        version_main=version_main,
    )

    # 🔒 Fake fingerprint (giúp qua Cloudflare)
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
    # 💤 Delay khởi động để Cloudflare không nghi
    time.sleep(random.uniform(3, 6))
    return driver