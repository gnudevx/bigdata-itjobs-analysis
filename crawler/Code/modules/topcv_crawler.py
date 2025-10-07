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
from selenium.common.exceptions import InvalidSessionIdException
import shutil
# Import dùng chung
from Code.core.driver_for_topcv import init_topcv_driver
from Code.core.utils import setup_logger, log_and_print, human_delay, save_json
from Code.config.settings import get_output_file, BASE_IT_TOPCV, TARGET_PER_GROUP, LOG_DIR

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
        log_and_print(f"⚠️ Scroll lỗi: {e}", logger)

# ---------------------------
# Crawl danh sách kỹ năng
# ---------------------------
def get_skills_info(driver):
    retries = 0
    while retries < 3:
        try:
            log_and_print(f"🌐 Đang mở trang kỹ năng (lần {retries+1})...", logger)
            driver.get(BASE_IT_TOPCV)
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-top-skill"))
            )
            break
        except Exception as e:
            log_and_print(f"⚠️ Lỗi khi load trang kỹ năng: {e}", logger)
            retries += 1
            time.sleep(3)
    else:
        raise Exception("Không thể tải trang kỹ năng sau 3 lần thử")

    btns = driver.find_elements(By.CSS_SELECTOR, "div.list-top-skill button")
    skills = []
    for btn in btns:
        raw = btn.text.strip()
        name = re.sub(r"\s*\d+$", "", raw).strip()
        sid = btn.get_attribute("data-skill-id") or btn.get_attribute("data-skill-id-other")
        if sid:
            skills.append((name, sid))
            log_and_print(f"→ Nhóm '{name}' (skill_id={sid})", logger)
    return skills

# ---------------------------
# Crawl jobs 
# ---------------------------
def scrape_jobs_on_current_filter_single_tab(driver, sid, target_count=50):
    jobs, seen = [], set()
    all_links = []
    empty_pages = 0

    for page in [""] + list(range(2, 11)):
        if sid == "other":
            url = f"{BASE_IT_TOPCV}?skill_id=&skill_id_other=other"
            if page != "":
                url += f"&page={page}"
        else:
            url = f"{BASE_IT_TOPCV}?skill_id={sid}"
            if page != "":
                url += f"&page={page}"
        log_and_print(f"-- Trang {page or 1}: {url}", logger)

        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.job-item-2 h3.title a[target='_blank']"))
            )
        except TimeoutException:
            log_and_print(f"⚠️ Timeout khi tải trang {page or 1}", logger)

        cards = driver.find_elements(By.CSS_SELECTOR, "div.job-item-2 h3.title a[target='_blank']")
        page_links = [a.get_attribute("href") for a in cards if a.get_attribute("href")]

        if not page_links:
            empty_pages += 1
            log_and_print(f"⚠️ Trang {page or 1} không có job ({empty_pages}/2) — thử trang kế tiếp...", logger)
            if empty_pages >= 2:
                log_and_print("🚫 Dừng: Gặp 2 trang liên tiếp không có job → kết thúc vòng lặp.", logger)
                break
            continue
        else:
            empty_pages = 0

        new_links = [l for l in page_links if l not in seen]
        if not new_links:
            log_and_print("⚠️ Không có job mới (toàn link trùng lặp). Dừng crawl trang kế tiếp.", logger)
            break
        all_links.extend(new_links)
        seen.update(new_links)
        if len(all_links) >= target_count:
            log_and_print(f"🎯 Đủ {target_count} job → dừng tìm thêm trang.", logger)
            break

    # Crawl từng job trên cùng 1 tab
    for i, link in enumerate(all_links[:target_count]):
        try:
            driver.get(link)
            log_and_print(f"👉 Crawl job ({i+1}/{len(all_links)}): {link}")

            try:
                WebDriverWait(driver, 25).until(
                    lambda d: "just a moment" not in d.title.lower()
                )
            except:
                log_and_print("⚠️ Trang load quá lâu hoặc bị chặn Cloudflare", logger)

            human_scroll(driver)

            # Nếu vẫn còn bị Cloudflare — thử reload 3 lần
            retry_count = 0
            while "just a moment" in driver.title.lower() and retry_count < 3:
                log_and_print(f"⏳ Cloudflare chặn, chờ 2s và reload lần {retry_count+1}", logger)
                time.sleep(2)
                driver.refresh()
                retry_count += 1

            if "just a moment" in driver.title.lower():
                log_and_print("⚠️ Trang bị chặn bởi Cloudflare — bỏ qua job này.", logger)
                continue

            # Crawl job chi tiết
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
            log_and_print(f"✅ Đã lấy job: {title}", logger)

        except Exception as e:
            log_and_print(f"❌ Lỗi khi crawl job {link}: {e}", logger)

        human_delay(1.5, 0.7)

    log_and_print(f"🎯 Đã crawl {len(jobs)} jobs cho filter {sid}", logger)
    return jobs[:target_count]
# ---------------------------
# Main function for airflow DAG
# ---------------------------
def run_topcv_crawler():
    try:
        driver = init_topcv_driver(headless=True)
        skills = get_skills_info(driver)
        output_file = get_output_file("topcv")
        log_file = os.path.join(LOG_DIR, f"topcv_{datetime.now().strftime('%Y-%m-%d')}.log")
        logger = setup_logger("topcv_logger", log_file)
        for name, sid in skills:
            log_and_print(f"\n=== Crawl nhóm {name} ===", logger)
            jobs = scrape_jobs_on_current_filter_single_tab(driver, sid, TARGET_PER_GROUP)
            save_json({"group": name, "jobs": jobs}, output_file)
            log_and_print(f"✅ Lưu nhóm {name}", logger)
    finally:
        driver.quit()
        # cleanup temp UC cache
        shutil.rmtree(os.environ.get("UDC_DATA_DIR", ""), ignore_errors=True)
if __name__ == "__main__":
    run_topcv_crawler()
