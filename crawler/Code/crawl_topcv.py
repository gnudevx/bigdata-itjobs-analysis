# topcv_crawler.py
import json
import time
import random
import re
import os
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from bs4 import BeautifulSoup
# ---------------------------
# Config
# ---------------------------
BASE_IT = "https://www.topcv.vn/viec-lam-it"
TARGET_PER_GROUP = 500
DATA_DIR = "/opt/airflow/crawler/Dataset"
LOG_DIR = "/opt/airflow/crawler/Logs"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT_FILE = os.path.join(DATA_DIR, f"topcv_{TODAY}.json")
LOG_FILE = os.path.join(LOG_DIR, f"topcv_{TODAY}.log")

logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

def human_delay(base=1.0, variation=0.5):
    time.sleep(base + random.random() * variation)

# ---------------------------
# Init driver Linux + Docker
# ---------------------------
def init_driver(profile_dir=None, proxy=None, headless=True, version_main=None):
    import random

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
    if headless:
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

    service = Service("/usr/local/bin/chromedriver")

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


# ---------------------------
# Scroll page
# ---------------------------
def human_scroll(driver):
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
        human_delay(0.5, 0.3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        human_delay(0.5, 0.3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_delay(0.5, 0.3)
    except Exception as e:
        log(f"⚠️ Scroll lỗi: {e}")

# ---------------------------
# Crawl danh sách kỹ năng
# ---------------------------
def get_skills_info(driver, retries=3):
    for attempt in range(retries):
        driver.get(BASE_IT)
        log(f"🔗 Mở trang {BASE_IT}")
        time.sleep(6)

        html = driver.page_source.lower()
        if "just a moment" in html or "challenge" in driver.current_url:
            log(f"⚠️ Cloudflare chặn lần {attempt+1}/{retries} — thử lại...")
            time.sleep(8)
            continue

        try:
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-top-skill"))
            )
            break
        except TimeoutException:
            log("⏳ Hết thời gian chờ load kỹ năng.")
            if attempt < retries - 1:
                continue
            raise

    btns = driver.find_elements(By.CSS_SELECTOR, "div.list-top-skill button")
    skills = []
    for btn in btns:
        raw = btn.text.strip()
        name = re.sub(r"\s*\d+$", "", raw).strip()
        sid = btn.get_attribute("data-skill-id") or btn.get_attribute("data-skill-id-other")
        if sid:
            skills.append((name, sid))
            log(f"→ Nhóm '{name}' (skill_id={sid})")
    return skills

# ---------------------------
# Next page
# ---------------------------
def next_page(driver):
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pagination = soup.select_one("ul.pagination")
        if not pagination:
            log("⚠️ Không tìm thấy phần phân trang (pagination).")
            return False

        # Tìm trang hiện tại
        active = pagination.select_one("li.active span")
        if not active:
            log("⚠️ Không tìm thấy trang hiện tại trong phân trang.")
            return False

        current_page = active.text.strip()
        next_li = active.find_parent("li").find_next_sibling("li")

        # Nếu không còn li kế tiếp hoặc li kế tiếp không có link
        if not next_li or not next_li.find("a"):
            log("⛔ Không còn nút Next (đã đến trang cuối).")
            return False

        next_url = next_li.find("a")["href"]
        if not next_url.startswith("http"):
            next_url = "https://www.topcv.vn" + next_url

        log(f"➡️ Chuyển sang trang kế tiếp: {next_url}")
        driver.get(next_url)
        human_delay(2.0, 0.5)
        return True

    except Exception as e:
        log(f"⚠️ Lỗi khi chuyển trang: {e}")
        return False

# ---------------------------
# Crawl jobs
# ---------------------------
def scrape_jobs_on_current_filter(driver, sid, target_count=50):
    jobs, seen = [], set()
    max_pages = 10  # Giới hạn tối đa (40 trang để dư)
    all_links = []

    empty_pages = 0  # 🧩 Đếm số trang liên tiếp không có job

    # Duyệt trang 1 (rỗng) + các trang tiếp theo
    for page in [""] + list(range(2, max_pages + 1)):
        if page == "":
            url = f"https://www.topcv.vn/viec-lam-it?sort=&skill_id={sid}&skill_id_other=&keyword=&position=&salary="
        else:
            url = f"https://www.topcv.vn/viec-lam-it?sort=&skill_id={sid}&skill_id_other=&keyword=&position=&salary=&page={page}"

        log(f"-- Trang {page or 'rỗng'}: {url}")
        driver.get(url)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.job-item-2 h3.title a[target='_blank']"))
            )
        except:
            log("⚠️ Trang không có job (chờ timeout).")

        time.sleep(1)
        cards = driver.find_elements(By.CSS_SELECTOR, "div.job-item-2 h3.title a[target='_blank']")
        page_links = [a.get_attribute("href") for a in cards if a.get_attribute("href")]

        # 🧩 Kiểm tra nếu không có job nào
        if not page_links:
            empty_pages += 1
            log(f"⚠️ Trang không có job ({empty_pages}/2) — thử trang kế tiếp...")
            if empty_pages >= 2:
                log("🚫 Dừng: 2 trang liên tiếp không có job.")
                break
            continue
        else:
            empty_pages = 0  # reset lại vì trang này có job

        new_links = [l for l in page_links if l not in seen]
        if not new_links:
            log("⚠️ Không có link mới — dừng lại.")
            break

        log(f"🔗 Tìm thấy {len(new_links)} link job mới trên trang {page or 1}")
        all_links.extend(new_links)
        seen.update(new_links)

        # Dừng nếu đã đủ số lượng job mục tiêu
        if len(all_links) >= target_count:
            break
    # 🧩 In tổng kết
    log(f"🧩 Tổng {len(all_links)} link job thu được cho skill {sid}")
    # 2️⃣ Crawl chi tiết từng job trong tab mới
    for i, link in enumerate(all_links[:target_count]):
        try:
            driver.execute_script(f"window.open('{link}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            log(f"👉 Crawl job ({i+1}/{len(all_links)}): {link}")

            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
            )
            human_scroll(driver)
            retry_count = 0
            while "just a moment" in driver.title.lower() and retry_count < 3:
                log(f"⏳ Cloudflare chặn, chờ 2s và reload lần {retry_count+1}")
                time.sleep(2)
                driver.refresh()
                retry_count += 1

            # Nếu sau 3 lần vẫn bị chặn, bỏ qua job
            if "just a moment" in driver.title.lower():
                log("⚠️ Trang bị chặn bởi Cloudflare — bỏ qua job này.")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                human_delay(1.5, 0.7)
                continue

            # — phần crawl job chi tiết chạy ở đây —
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, "h1.job-detail__info--title a")
                title = title_elem.text.strip()
                title = re.sub(r"\s*\(.*?\)", "", title).strip()
            except Exception:
                title = driver.title.strip()
                if "topcv.vn" in title.lower():
                    title = "(no title)"
            info = {"salary": "", "location": "", "experience": ""}
            for sec in driver.find_elements(By.CSS_SELECTOR, ".job-detail__info--section"):
                try:
                    key = sec.find_element(By.CSS_SELECTOR, ".job-detail__info--section-content-title").text.lower()
                    val = sec.find_element(By.CSS_SELECTOR, ".job-detail__info--section-content-value").text.strip()
                    if "lương" in key:
                        info["salary"] = val
                    elif "địa điểm" in key:
                        info["location"] = val
                    elif "kinh nghiệm" in key:
                        info["experience"] = val
                except:
                    continue

            desc = {"description": "", "requirements": "", "benefits": "", "work_location_detail": "", "working_time": ""}
            for item in driver.find_elements(By.CSS_SELECTOR, ".job-description__item"):
                try:
                    h = item.find_element(By.TAG_NAME, "h3").text.lower()
                    content = item.find_element(By.CSS_SELECTOR, ".job-description__item--content").text.strip()
                    if "thời gian làm việc" in h:
                        desc["working_time"] = content
                    elif "mô tả công việc" in h:
                        desc["description"] = content
                    elif "yêu cầu ứng viên" in h:
                        desc["requirements"] = content
                    elif "quyền lợi" in h:
                        desc["benefits"] = content
                    elif "địa điểm làm việc" in h:
                        desc["work_location_detail"] = content
                except:
                    continue

            try:
                deadline = driver.find_element(By.CSS_SELECTOR, "div.job-detail__information-detail--actions-label").text.strip()
            except:
                deadline = ""

            jobs.append({"title": title, "link": link, **info, **desc, "deadline": deadline})
            log(f"✅ Đã lấy job: {title}")

        except Exception as e:
            log(f"❌ Lỗi khi crawl job {link}: {e}")

        finally:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            human_delay(1.5, 0.7)

    log(f"🎯 Đã crawl {len(jobs)} jobs cho filter {sid}")
    return jobs[:target_count]

# ---------------------------
# Ghi JSON
# ---------------------------
def append_to_json_file(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except:
                pass
    existing.append(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

# ---------------------------
# Main
# ---------------------------
def run_topcv_crawler():
    driver = init_driver(headless=True)
    skills = get_skills_info(driver)
    for name, sid in skills:
        log(f"\n=== Crawl nhóm {name} ===")
        driver.get(BASE_IT)
        human_delay()
        try:
            jobs = scrape_jobs_on_current_filter(driver, sid, TARGET_PER_GROUP)
            append_to_json_file({"group": name, "jobs": jobs}, OUTPUT_FILE)
            log(f"✅ Đã lưu nhóm {name} vào {OUTPUT_FILE}")
        except Exception as e:
            log(f"❌ Lỗi nhóm {name}: {e}")
            continue
    driver.quit()

if __name__ == "__main__":
    run_topcv_crawler()
