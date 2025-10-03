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

BASE_IT = "https://www.topcv.vn/viec-lam-it"
TARGET_PER_GROUP = 500  # Mục tiêu số job mỗi nhóm
OUTPUT_FILE = "../Dataset/topcv.json"
LOG_FILE = "../Dataset/crawl.log"

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

# -----------------------------
# Tiện ích delay mô phỏng người
# -----------------------------
def human_delay(base=1.0, variation=0.5):
    time.sleep(base + random.random() * variation)

# -----------------------------
# Khởi tạo driver Chrome stealth
# -----------------------------
def init_driver(headless=False):
    opts = uc.ChromeOptions()
    opts.add_argument(r"--user-data-dir=D:/chrome-profile-topcv")  # Profile đã verify CAPTCHA
    if headless:
        opts.add_argument("--headless=new")  # headless mới
        opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=opts)
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*topcvconnect.com/*"]})

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

# -----------------------------
# Lấy danh sách kỹ năng filter
# -----------------------------
def get_skills_info(driver):
    driver.get(BASE_IT)
    human_delay()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-top-skill"))
    )
    btns = driver.find_elements(
        By.CSS_SELECTOR,
        "div.list-top-skill button.change-skill, div.list-top-skill button.change-skill-other"
    )
    skills = []
    for btn in btns:
        raw = btn.text.strip()
        name = re.sub(r"\s*\d+$", "", raw).strip()
        sid = btn.get_attribute("data-skill-id") or btn.get_attribute("data-skill-id-other")
        if sid:
            skills.append((name, sid))
            log(f"→ Nhóm '{name}' (skill_id={sid})")
    return skills

# -----------------------------
# Giúp việc tránh captcha
# -----------------------------
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

# -----------------------------
# Crawl job theo filter hiện tại
# -----------------------------
def scrape_jobs_on_current_filter(driver, target_count=TARGET_PER_GROUP):
    jobs, seen, page = [], set(), 1

    while len(jobs) < target_count:
        log(f"-- Trang {page} --")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-job"))
            )
        except:
            log(f"⚠️ Trang {page} không load được list-job, bỏ qua.")
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "ul.pagination a[rel='next']")
                driver.execute_script("arguments[0].click();", next_btn)
                human_delay(1.0, 0.5)
                page += 1
                continue
            except:
                log("❌ Hết trang hoặc không tìm thấy nút next.")
                break

        cards = driver.find_elements(By.CSS_SELECTOR, "div.job-item, div.title-block")
        if not cards:
            log(f"⚠️ Trang {page} không tìm thấy job-item, bỏ qua.")
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "ul.pagination a[rel='next']")
                driver.execute_script("arguments[0].click();", next_btn)
                human_delay(1.0, 0.5)
                page += 1
                continue
            except:
                log("❌ Hết trang hoặc không tìm thấy nút next.")
                break

        for c in cards:
            if len(jobs) >= target_count:
                break
            try:
                a = c.find_element(By.CSS_SELECTOR, "h3.title a")
                title = a.text.strip()
                link = a.get_attribute("href")
                if link in seen or "/brand/" in link:
                    continue
                seen.add(link)

                driver.get(link)
                human_delay(0.5, 0.3)
                human_scroll(driver)

                WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#header-job-info"))
                )
                if not driver.find_elements(By.CSS_SELECTOR, ".job-description__item"):
                    log(f"⚠️ Bỏ qua (không chuẩn): {link}")
                    driver.back()
                    human_delay(0.3, 0.2)
                    continue

                root = driver.find_element(By.CSS_SELECTOR, "#header-job-info")
                secs = root.find_elements(By.CSS_SELECTOR, ".job-detail__info--section")
                info = {"salary": "", "location": "", "experience": ""}
                for sec in secs:
                    try:
                        key = sec.find_element(
                            By.CSS_SELECTOR, ".job-detail__info--section-content-title"
                        ).text.lower()
                        val = sec.find_element(
                            By.CSS_SELECTOR, ".job-detail__info--section-content-value"
                        ).text.strip()
                        if "lương" in key:
                            info["salary"] = val
                        elif "địa điểm" in key:
                            info["location"] = val
                        elif "kinh nghiệm" in key:
                            info["experience"] = val
                    except:
                        continue

                desc_root = driver.find_element(By.CSS_SELECTOR, ".job-description")
                items = desc_root.find_elements(By.CSS_SELECTOR, ".job-description__item")
                desc = {
                    "description": "",
                    "requirements": "",
                    "benefits": "",
                    "work_location_detail": "",
                    "working_time": ""
                }
                for item in items:
                    try:
                        h = item.find_element(By.TAG_NAME, "h3").text.lower()
                        content = item.find_element(By.CSS_SELECTOR, ".job-description__item--content")
                        if "thời gian làm việc" in h:
                            desc["working_time"] = content.text.strip()
                        elif "mô tả công việc" in h:
                            desc["description"] = content.text.strip()
                        elif "yêu cầu ứng viên" in h:
                            desc["requirements"] = content.text.strip()
                        elif "quyền lợi" in h:
                            desc["benefits"] = content.text.strip()
                        elif "địa điểm làm việc" in h:
                            desc["work_location_detail"] = content.text.strip()
                    except:
                        continue

                dl = ""
                try:
                    dl = WebDriverWait(driver, 7).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                            "div.job-detail__information-detail--actions-label"))
                    ).text.strip()
                except:
                    pass

                jobs.append({
                    "title": title, "link": link,
                    **info, **desc, "deadline": dl
                })

                driver.back()
                human_delay(0.5, 0.3)

            except Exception as e:
                log(f"❌ Lỗi job: {e}")
                try: driver.back()
                except: pass
                human_delay(0.5, 0.3)
                continue

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "ul.pagination a[rel='next']")
            driver.execute_script("arguments[0].click();", next_btn)
            human_delay(1.0, 0.5)
            page += 1
        except:
            log("❌ Hết trang hoặc không tìm thấy nút next.")
            break

    log(f">>> Đã crawl {len(jobs)} jobs cho filter hiện tại.")
    return jobs[:target_count]

# -----------------------------
# Đọc checkpoint đã crawl
# -----------------------------
def load_checkpoint(filepath):
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {entry["group"] for entry in data if "group" in entry}
    except:
        return set()

# -----------------------------
# Ghi file JSON
# -----------------------------
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

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    driver = init_driver(headless=False)
    skills = get_skills_info(driver)

    done_groups = load_checkpoint(OUTPUT_FILE)
    log(f"Đã có {len(done_groups)} nhóm trong checkpoint: {done_groups}")

    for name, sid in skills:
        if name in done_groups:
            log(f"⏩ Bỏ qua nhóm {name} (đã crawl)")
            continue

        log(f"\n=== Crawl nhóm {name} ===")
        driver.get(BASE_IT)
        human_delay()
        sel = (
            f"div.list-top-skill button[data-skill-id='{sid}']," +
            f"div.list-top-skill button[data-skill-id-other='{sid}']"
        )
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            driver.execute_script("arguments[0].scrollIntoView();", btn)
            human_delay(0.3, 0.2)
            driver.execute_script("arguments[0].click();", btn)
            human_delay(1.0, 0.5)
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, "div.list-top-skill + div"), "Tìm thấy"
                )
            )
            human_delay(0.5, 0.3)

            jobs = scrape_jobs_on_current_filter(driver, TARGET_PER_GROUP)
            append_to_json_file({"group": name, "jobs": jobs}, OUTPUT_FILE)
            log(f"✅ Đã lưu nhóm {name} vào {OUTPUT_FILE}")
        except Exception as e:
            log(f"❌ Lỗi nhóm {name}: {e}")
            continue
