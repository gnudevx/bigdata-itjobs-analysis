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
from Code.core.utils import save_temp_json, merge_temp_files, cleanup_temp, get_output_file, get_base_dir
from Code.core.driver_for_vnwork import init_vnwork_driver
from Code.config.settings import BASE_IT_VNWORK


def human_delay(base=1.0, variance=0.5):
    time.sleep(base + random.random() * variance)


def parse_deadline(deadline_text: str, crawl_date=None):
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


def get_info(url, driver):
    """Lấy chi tiết job cụ thể, bỏ qua nếu lỗi."""
    try:
        driver.set_page_load_timeout(60)
        driver.get(url)
        human_delay(1, 0.5)
    except Exception as e:
        print(f"[WARN] Không mở được job: {url} ({e})")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")

    def safe_text(selector, cls):
        el = soup.find(selector, class_=cls)
        return el.text.strip() if el else "N/A"

    try:
        job_title = safe_text("h1", "sc-ab270149-0 hAejeW")
        if job_title == "N/A":
            raise Exception("Không lấy được tiêu đề job")
        print(f"🔹 Job: {job_title}")

        deadline = parse_deadline(safe_text("span", "sc-ab270149-0 ePOHWr"))
        salary = safe_text("span", "sc-ab270149-0 cVbwLK")
        location = safe_text("div", "sc-a137b890-1 joxJgK")

        job_description, job_requirement = "", ""
        for block in soup.find_all("div", class_="sc-1671001a-3 hmvhgA"):
            for section in block.find_all("div", class_="sc-1671001a-4 gDSEwb"):
                heading = section.find("h2", class_="sc-1671001a-5 cjuZti")
                content_div = section.find("div", class_="sc-1671001a-6 dVvinc")

                if not heading or not content_div:
                    continue

                title = heading.get_text(strip=True).lower()
                content = content_div.get_text(separator="\n").strip()

                if "mô tả" in title:
                    job_description = content
                elif "yêu cầu" in title:
                    job_requirement = content

        benefits = soup.find_all("div", class_="sc-c683181c-2 fGxLZh")
        benefit = "\n".join([f"- {b.text.strip()}" for b in benefits])

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
    except Exception as e:
        print(f"[WARN] Bỏ qua job lỗi {url}: {e}")
        return None


def scrape_jobs_by_skill(skill_name, skill_url, max_pages=10):
    """Crawl 1 skill – luôn tạo driver mới, không crash toàn bộ."""
    driver = None
    jobs = []
    fail_pages = 0

    try:
        driver = init_vnwork_driver()
        for page in range(1, max_pages + 1):
            url_page = f"{skill_url}&page={page}"
            print(f"[PAGE] {skill_name} → {url_page}")

            try:
                driver.set_page_load_timeout(60)
                driver.get(url_page)
                human_delay(2, 1)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                job_containers = soup.find_all("div", class_="sc-iVDsrp frxvCT")

                if not job_containers:
                    fail_pages += 1
                    print(f"[INFO] Trang {page} rỗng ({fail_pages}/2).")
                    if fail_pages >= 2:
                        print(f"[SKIP] Bỏ qua skill {skill_name} (2 trang liên tiếp rỗng).")
                        break
                    continue
                else:
                    fail_pages = 0

                fail_jobs = 0
                for container in job_containers:
                    a_tag = container.find("a", class_="img_job_card")
                    if not a_tag:
                        continue
                    job_link = a_tag.get("href")
                    if not job_link:
                        continue

                    full_url = "https://www.vietnamworks.com" + job_link
                    job_data = get_info(full_url, driver)
                    if job_data:
                        jobs.append(job_data)
                    else:
                        fail_jobs += 1

                if fail_jobs >= 4:
                    print(f"[WARN] Trang {page} có {fail_jobs} job lỗi → bỏ skill {skill_name}.")
                    break

                human_delay(1.2, 0.5)

            except Exception as e:
                print(f"[ERROR] Lỗi khi crawl trang {page} ({url_page}): {e}")
                fail_pages += 1
                if fail_pages >= 2:
                    print(f"[SKIP] Liên tiếp 2 lỗi trang → bỏ skill {skill_name}")
                    break
                continue
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
                
    return jobs


def run_vnwork_crawler():
    print("[INFO] Truy cập trang chủ Vietnamworks...")
    driver = init_vnwork_driver()
    driver.get(BASE_IT_VNWORK)
    human_delay(10, 2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    skills_div = soup.find("div", class_="skill-tag-details")
    if not skills_div:
        print("[ERROR] ❌ Không tìm thấy danh sách kỹ năng.")
        return

    skill_elements = skills_div.find_all("div", class_="tag-wrapper")
    print(f"[INFO] Found {len(skill_elements)} kỹ năng")

    base_dir = get_base_dir()
    output_path = get_output_file("vnwork")
    print(f"[SAVE PATH] {output_path}")

    for idx, skill_el in enumerate(skill_elements, 1):
        skill_name = skill_el.get_text(strip=True)
        skill_url = f"https://www.vietnamworks.com/viec-lam?q={skill_name.lower().replace(' ', '-')}"
        print(f"\n=== [{idx}/{len(skill_elements)}] Crawling: {skill_name} ===")

        jobs = []
        try:
            jobs = scrape_jobs_by_skill(skill_name, skill_url, max_pages=5)
        except Exception as e:
            print(f"[ERROR] Skill {skill_name} bị lỗi nặng: {e}")

        # Lưu file tạm (kể cả rỗng, để dễ tracking)
        save_temp_json([{"group": skill_name, "jobs": jobs}], base_dir, idx)
        print(f"✅ Đã lưu {len(jobs)} job cho {skill_name}")

        human_delay(2, 1)

    # Gộp tất cả part lại
    merge_temp_files(base_dir, output_path)
    cleanup_temp(base_dir)

    print(f"[DONE] ✅ Dữ liệu lưu tại: {output_path}")


if __name__ == "__main__":
    run_vnwork_crawler()
