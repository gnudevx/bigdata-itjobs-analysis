import os
import time
import json
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium_stealth import stealth
import sys

sys.path.append('/opt/airflow/crawler')
from Code.core.utils import save_json
from Code.core.driver_for_vnwork import init_vnwork_driver
from Code.config.settings import get_output_file, BASE_IT_VNWORK


# ==========================================================
# 🧩 HÀM PHỤ TRỢ
# ==========================================================

def human_delay(base=1.0, variance=0.5):
    """Random sleep tránh bị anti-bot."""
    time.sleep(base + random.random() * variance)


def parse_deadline(deadline_text: str, crawl_date=None):
    """Chuyển đổi 'Hết hạn trong 3 ngày' -> ngày cụ thể"""
    if crawl_date is None:
        crawl_date = datetime.today()

    if not deadline_text:
        return "N/A"

    text = deadline_text.lower().strip()

    if "hết hạn trong" in text:
        parts = text.replace("hết hạn trong", "").strip().split()
        if len(parts) >= 2:
            try:
                num = int(parts[0])
            except ValueError:
                return deadline_text
            unit = parts[1]

            if "ngày" in unit:
                expire_date = crawl_date + timedelta(days=num)
            elif "tuần" in unit:
                expire_date = crawl_date + timedelta(weeks=num)
            elif "tháng" in unit:
                expire_date = crawl_date + relativedelta(months=num)
            else:
                return deadline_text

            return f"Hạn nộp hồ sơ: {expire_date.strftime('%d/%m/%Y')}"

    return deadline_text


# ==========================================================
# 🧠 HÀM CRAWL 1 JOB
# ==========================================================

def get_info(url, driver):
    """Lấy chi tiết job cụ thể"""
    driver.get(url)
    human_delay(1, 0.5)

    # Scroll hết trang
    last_height = 0
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_delay(0.6, 0.3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")

    def safe_text(selector, cls):
        el = soup.find(selector, class_=cls)
        return el.text.strip() if el else "N/A"

    job_title = safe_text("h1", "sc-ab270149-0 hAejeW")
    deadline = safe_text("span", "sc-ab270149-0 ePOHWr")
    salary = safe_text("span", "sc-ab270149-0 cVbwLK")
    location = safe_text("div", "sc-a137b890-1 joxJgK")

    print(f"🔹 Job: {job_title}")

    deadline = parse_deadline(deadline)

    job_description, job_requirement = "", ""
    for block in soup.find_all("div", class_="sc-1671001a-3 hmvhgA"):
        heading = block.find("h2", class_="sc-1671001a-5 cjuZti")
        if not heading:
            continue
        title = heading.text.strip().lower()
        next_div = heading.find_next_sibling("div")
        if next_div:
            content = next_div.get_text(separator="\n").strip()
            if "mô tả" in title:
                job_description = content
            elif "yêu cầu" in title:
                job_requirement = content

    # Phúc lợi
    benefits = soup.find_all("div", class_="sc-c683181c-2 fGxLZh")
    benefit = "\n".join([f"- {b.text.strip()}" for b in benefits])

    # Info phụ
    exp, workday = "", ""
    for block in soup.find_all("div", class_="sc-7bf5461f-0 dHvFzj"):
        label = block.find("label")
        value = block.find("p")
        if not label or not value:
            continue
        label_text = label.text.strip().upper()
        if "KINH NGHIỆM" in label_text:
            exp = value.text.strip()
        elif "NGÀY LÀM VIỆC" in label_text:
            workday = value.text.strip()

    return {
        "title": job_title,
        "link": url,
        "salary": salary,
        "location": location,
        "experience": exp,
        "description": job_description,
        "requirements": job_requirement,
        "benefits": benefit,
        "work_location_detail": location,
        "working_time": workday,
        "deadline": deadline,
    }


# ==========================================================
# 🌐 HÀM CRAWL THEO SKILL
# ==========================================================

def scrape_jobs_by_skill(driver, skill_name, skill_url, max_pages=1, limit_jobs_per_page=None):
    jobs = []
    for page in range(1, max_pages + 1):
        url_page = f"{skill_url}&page={page}"
        print(f"[PAGE] {skill_name} → {url_page}")
        try:
            driver.get(url_page)
            human_delay(2, 1)
        except Exception as e:
            print(f"[WARN] Không mở được trang {url_page}: {e}")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_containers = soup.find_all("div", class_="sc-iVDsrp frxvCT")

        if not job_containers:
            print(f"[INFO] Hết dữ liệu ở trang {page}.")
            break

        if limit_jobs_per_page:
            job_containers = job_containers[:limit_jobs_per_page]

        for container in job_containers:
            a_tag = container.find("a", class_="img_job_card")
            if not a_tag:
                continue
            job_link = a_tag.get("href")
            if not job_link:
                continue

            full_url = "https://www.vietnamworks.com" + job_link
            try:
                job_data = get_info(full_url, driver)
                jobs.append(job_data)
            except Exception as e:
                print(f"[ERROR] Lỗi crawl job {full_url}: {e}")
                continue

        human_delay(1.2, 0.5)

    return jobs


# ==========================================================
# 🚀 HÀM CHÍNH
# ==========================================================

def run_vnwork_crawler():
    driver = init_vnwork_driver()
    print("[INFO] Truy cập Vietnamworks...")
    driver.get(BASE_IT_VNWORK)
    human_delay(10, 2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    skills_div = soup.find("div", class_="skill-tag-details")
    if not skills_div:
        print("[ERROR] ❌ Không tìm thấy danh sách kỹ năng. Có thể bị chặn.")
        driver.quit()
        return

    skill_elements = skills_div.find_all("div", class_="tag-wrapper")
    print(f"[INFO] Found {len(skill_elements)} kỹ năng")

    output_path = get_output_file(prefix="vnwork")
    print(f"[SAVE PATH] {output_path}")

    for idx, skill_el in enumerate(skill_elements, 1):
        skill_name = skill_el.get_text(strip=True)
        skill_url = f"https://www.vietnamworks.com/viec-lam?q={skill_name.lower().replace(' ', '-')}"
        print(f"\n=== [{idx}/{len(skill_elements)}] Crawling: {skill_name} ===")

        try:
            jobs = scrape_jobs_by_skill(driver, skill_name, skill_url, max_pages=1, limit_jobs_per_page=2)
            if jobs:
                save_json([{"group": skill_name, "jobs": jobs}], output_path)
                print(f"✅ Đã lưu {len(jobs)} job cho {skill_name}")
            else:
                print(f"[WARN] Không có job cho {skill_name}")
        except Exception as e:
            print(f"[ERROR] Skill {skill_name} bị lỗi: {e}")

        human_delay(2, 1)

    driver.quit()
    print(f"[DONE] ✅ Dữ liệu lưu tại: {output_path}")


# ==========================================================
# 🏁 ENTRYPOINT
# ==========================================================
if __name__ == "__main__":
    run_vnwork_crawler()
