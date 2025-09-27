import json
import time
import random
import re
import os

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

BASE_IT = "https://www.topcv.vn/viec-lam-it"
TARGET_PER_GROUP = 250  # Mục tiêu số job mỗi nhóm
OUTPUT_FILE = "./crawl/topcv.json"

def human_delay(base=1.0, variation=0.5):  # Giảm thời gian delay
    """Sleep một khoảng ngẫu nhiên để mô phỏng người thật."""
    time.sleep(base + random.random() * variation)

def init_driver(headless=False):
    opts = uc.ChromeOptions()
    opts.add_argument(r"--user-data-dir=D:/chrome-profile-topcv")  # Profile đã verify CAPTCHA
    if headless:
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    # opts.add_argument("--blink-settings=imagesEnabled=false")
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

def get_skills_info(driver):
    driver.get(BASE_IT)
    human_delay()
    WebDriverWait(driver, 10).until(  # Giảm timeout
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
            print(f"→ Nhóm '{name}' (skill_id={sid})")
    return skills

def scrape_jobs_on_current_filter(driver, target_count=TARGET_PER_GROUP):
    jobs, seen, page = [], set(), 1

    while len(jobs) < target_count:
        print(f"-- Trang {page} --")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-job"))
            )
        except:
            print("❌ Không load được list-job, dừng.")
            break

        cards = driver.find_elements(By.CSS_SELECTOR, "div.job-item, div.title-block")
        if not cards:
            print("❌ Không tìm thấy job-item, dừng.")
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

                WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#header-job-info"))
                )
                if not driver.find_elements(By.CSS_SELECTOR, ".job-description__item"):
                    print(f"⚠️ Bỏ qua (không chuẩn): {link}")
                    driver.back()
                    human_delay(0.3, 0.2)
                    continue

                root = driver.find_element(By.CSS_SELECTOR, "#header-job-info")
                secs = root.find_elements(By.CSS_SELECTOR, ".job-detail__info--section")
                info = {"salary": "", "location": "", "experience": ""}
                for sec in secs:
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

                desc_root = driver.find_element(By.CSS_SELECTOR, ".job-description")
                items = desc_root.find_elements(By.CSS_SELECTOR, ".job-description__item")
                desc = {"description": "", "requirements": "", "benefits": "", "work_location_detail": "", "working_time": ""}
                for item in items:
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

                dl = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "div.job-detail__information-detail--actions-label"))
                ).text.strip()

                jobs.append({
                    "title": title, "link": link,
                    **info, **desc, "deadline": dl
                })

                driver.back()
                human_delay(0.5, 0.3)

            except Exception as e:
                print("❌ Lỗi job:", e)
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
            print("❌ Hết trang hoặc không tìm thấy nút next.")
            break

    print(f">>> Đã crawl {len(jobs)} jobs cho filter hiện tại.")
    return jobs[:target_count]

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

if __name__ == "__main__":
    driver = init_driver(headless=False)
    skills = get_skills_info(driver)

    for name, sid in skills:
        if name.lower() != "quản lý dự án":
            continue  # Bỏ qua các nhóm khác

        print(f"\n=== Crawl nhóm {name} ===")
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
            print(f"✅ Đã lưu nhóm {name} vào {OUTPUT_FILE}")
        except Exception as e:
            print(f"❌ Lỗi nhóm {name}: {e}")
            continue

