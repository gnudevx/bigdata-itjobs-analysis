# topcv_crawler.py
import re
import os
import json
import time
from datetime import datetime
# from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# Import dùng chung
from crawler.Code.core.driver import init_driver
from crawler.Code.core.utils import setup_logger, log_and_print, human_delay, save_json
from crawler.Code.config.settings import BASE_IT, TARGET_PER_GROUP, DATASET_DIR

logger = setup_logger("topcv")

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
        log_and_print(logger, f"⚠️ Scroll lỗi: {e}")

# ---------------------------
# Crawl danh sách kỹ năng
# ---------------------------
def get_skills_info(driver):
    driver.get(BASE_IT)
    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-top-skill"))
    )
    btns = driver.find_elements(By.CSS_SELECTOR, "div.list-top-skill button")
    skills = []
    for btn in btns:
        raw = btn.text.strip()
        name = re.sub(r"\s*\d+$", "", raw).strip()
        sid = btn.get_attribute("data-skill-id") or btn.get_attribute("data-skill-id-other")
        if sid:
            skills.append((name, sid))
            log_and_print(logger, f"→ Nhóm '{name}' (skill_id={sid})")
    return skills

# ---------------------------
# Crawl jobs 
# ---------------------------
def scrape_jobs_on_current_filter(driver, sid, target_count=50):
    jobs, seen = [], set()
    all_links = []
    for page in [""] + list(range(2, 11)):
        if page == "":
            url = f"{BASE_IT}?skill_id={sid}"
        else:
            url = f"{BASE_IT}?skill_id={sid}&page={page}"
        log_and_print(logger, f"-- Trang {page or 1}: {url}")
        driver.get(url)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.job-item-2 h3.title a[target='_blank']"))
            )
        except:
            continue
        cards = driver.find_elements(By.CSS_SELECTOR, "div.job-item-2 h3.title a[target='_blank']")
        page_links = [a.get_attribute("href") for a in cards if a.get_attribute("href")]
        new_links = [l for l in page_links if l not in seen]
        if not new_links:
            break
        all_links.extend(new_links)
        seen.update(new_links)
        if len(all_links) >= target_count:
            break
    # Crawl từng job
    for i, link in enumerate(all_links[:target_count]):
        try:
            driver.execute_script(f"window.open('{link}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
            title = driver.title.strip()
            jobs.append({"title": title, "link": link})
            log_and_print(logger, f"✅ Job {i+1}: {title}")
        except Exception as e:
            log_and_print(logger, f"❌ Lỗi job: {e}")
        finally:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            human_delay(1.5, 0.7)
    return jobs

# ---------------------------
# Main function for airflow DAG
# ---------------------------
def run_topcv_crawler():
    driver = init_driver()
    skills = get_skills_info(driver)
    output_file = os.path.join(DATASET_DIR, f"topcv_{datetime.now().strftime('%Y-%m-%d')}.json")
    for name, sid in skills:
        log_and_print(logger, f"\n=== Crawl nhóm {name} ===")
        jobs = scrape_jobs_on_current_filter(driver, sid, TARGET_PER_GROUP)
        save_json({"group": name, "jobs": jobs}, output_file)
        log_and_print(logger, f"✅ Lưu nhóm {name}")
    driver.quit()

if __name__ == "__main__":
    run_topcv_crawler()
