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
from selenium.common.exceptions import WebDriverException
import shutil
# Import dùng chung\
import sys, os
sys.path.append('/opt/airflow/crawler')
from Code.core.driver_for_topcv import init_topcv_driver
from Code.core.utils import setup_logger, log_and_print, human_delay, get_base_dir, get_output_file, save_temp_json, merge_temp_files, cleanup_temp
from Code.config.settings import  BASE_IT_TOPCV, TARGET_PER_GROUP, LOG_DIR

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
def ensure_driver_alive(driver):
    """
    Kiểm tra driver còn hoạt động, nếu không thì khởi tạo mới.
    """
    try:
        driver.execute_script("return 1")  # ping nhẹ
        return driver
    except Exception:
        print("[WARN] 🚨 Driver mất kết nối, khởi động lại UC mới...")
        try:
            driver.quit()
        except:
            pass
        time.sleep(2)
        return init_topcv_driver(headless=True)
def scrape_jobs_on_current_filter_single_tab(driver, sid, target_count=50):
    jobs, seen = [], set()
    all_links = []
    empty_pages = 0

    for page in [""] + list(range(2, 20)):
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
            try:
                driver.get(url)
            except WebDriverException as e:
                if "invalid session id" in str(e).lower():
                    log_and_print("🚨 Mất session Chrome, tạo driver mới...", logger)
                    driver = init_topcv_driver(headless=True)
                    driver.get(url)
                else:
                    raise
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
            driver = ensure_driver_alive(driver)
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
    driver = None
    try:
        # --- Init ---
        driver = init_topcv_driver(headless=True)
        skills = get_skills_info(driver)

        base_dir = get_base_dir()
        output_file = get_output_file("topcv")
        log_file = os.path.join(LOG_DIR, f"topcv_{datetime.now().strftime('%Y-%m-%d')}.log")
        logger = setup_logger("topcv_logger", log_file)

        log_and_print(f"[INFO] 🕷️ Tổng số kỹ năng: {len(skills)}", logger)
        print(f"[SAVE PATH] {output_file}")

        # --- Crawl từng nhóm ---
        for idx, (name, sid) in enumerate(skills, 1):
            log_and_print(f"\n=== [{idx}/{len(skills)}] Crawl nhóm {name} ===", logger)
            jobs = []

            try:
                jobs = scrape_jobs_on_current_filter_single_tab(driver, sid, TARGET_PER_GROUP)
            except Exception as e:
                log_and_print(f"[ERROR] Lỗi khi crawl nhóm {name}: {e}", logger)

            # ✅ Lưu tạm từng nhóm (kể cả rỗng để tracking)
            save_temp_json([{"group": name, "jobs": jobs}], base_dir, idx)

            if jobs:
                log_and_print(f"[SAVE] ✅ {len(jobs)} jobs saved for {name}", logger)
            else:
                log_and_print(f"[WARN] ⚠️ No jobs found for {name}", logger)

            human_delay(2, 1)

        # --- Merge & Cleanup ---
        merge_temp_files(base_dir, output_file)
        cleanup_temp(base_dir)
        log_and_print(f"[DONE] ✅ Dữ liệu TopCV lưu tại: {output_file}", logger)

    except Exception as e:
        log_and_print(f"❌ Lỗi tổng trong crawler: {e}", logger)

    finally:
        # ✅ Đảm bảo driver đóng gọn gàng
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        # ✅ Cleanup cache của undetected-chromedriver
        shutil.rmtree(os.path.expanduser("~/.local/share/undetected_chromedriver"), ignore_errors=True)

if __name__ == "__main__":
    run_topcv_crawler()
