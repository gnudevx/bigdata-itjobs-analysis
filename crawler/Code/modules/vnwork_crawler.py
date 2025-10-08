import os
import time
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium_stealth import stealth

# Import nội bộ
from Code.core.utils import save_json
from Code.core.driver_for_vnwork import init_vnwork_driver
from Code.config.settings import get_output_file, BASE_IT_VNWORK, LOG_DAY_DIR


# ==========================================================
# 🧩 HÀM PHỤ TRỢ
# ==========================================================

def parse_deadline(deadline_text: str, crawl_date=None):
    """
    Chuyển đổi chuỗi thời gian như 'Hết hạn trong 3 ngày' thành ngày cụ thể.
    """
    if crawl_date is None:
        crawl_date = datetime.today()

    text = deadline_text.lower().strip()

    if "hết hạn trong" in text:
        # Ví dụ: "Hết hạn trong 1 tháng", "Hết hạn trong 5 ngày"
        parts = text.replace("hết hạn trong", "").strip().split()
        if len(parts) >= 2:
            num = int(parts[0])
            unit = parts[1]

            if "ngày" in unit:
                expire_date = crawl_date + timedelta(days=num)
            elif "tuần" in unit:
                expire_date = crawl_date + timedelta(weeks=num)
            elif "tháng" in unit:
                expire_date = crawl_date + relativedelta(months=num)
            else:
                return deadline_text  # Không parse được

            return f"Hạn nộp hồ sơ: {expire_date.strftime('%d/%m/%Y')}"

    # Nếu text đã là ngày cụ thể sẵn rồi
    return deadline_text


def get_info(url, driver):
    """
    Lấy thông tin chi tiết cho 1 job cụ thể.
    """
    driver.get(url)
    time.sleep(1)

    # Scroll xuống cuối trang để load đầy đủ nội dung
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # === Thông tin cơ bản ===
    job_title = soup.find("h1", class_="sc-ab270149-0 hAejeW")
    deadline = soup.find("span", class_="sc-ab270149-0 ePOHWr")
    salary = soup.find("span", class_="sc-ab270149-0 cVbwLK")
    location = soup.find("div", class_="sc-a137b890-1 joxJgK")

    job_title = job_title.text.strip() if job_title else "N/A"
    print("Job title: ", job_title)
    deadline = deadline.text.strip() if deadline else "N/A"
    salary = salary.text.strip() if salary else "N/A"
    location = location.text.strip() if location else "N/A"

    # Chuẩn hóa deadline -> ngày cụ thể
    deadline = parse_deadline(deadline, crawl_date=datetime.today())

    # === Mô tả & Yêu cầu ===
    job_description, job_requirement = "", ""
    detail_blocks = soup.find_all("div", class_="sc-1671001a-3 hmvhgA")

    for block in detail_blocks:
        headings = block.find_all("h2", class_="sc-1671001a-5 cjuZti")
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            next_div = heading.find_next_sibling("div")

            if next_div:
                clean_text = next_div.get_text(separator="\n").strip()
                if "Mô tả công việc" in heading_text:
                    job_description = clean_text
                elif "Yêu cầu công việc" in heading_text:
                    job_requirement = clean_text

    # === Phúc lợi ===
    benefits = soup.find_all("div", class_="sc-c683181c-2 fGxLZh")
    benefit = "".join([f"- {b.text.strip()}\n" for b in benefits])

    # === Thông tin thêm ===
    experience_value, work_day_value = "", ""
    info_blocks = soup.find_all("div", class_="sc-7bf5461f-0 dHvFzj")

    for block in info_blocks:
        labels = block.find_all("label")
        for label in labels:
            label_text = label.get_text(strip=True)
            next_p = label.find_next_sibling("p")

            if label_text == "SỐ NĂM KINH NGHIỆM TỐI THIỂU":
                experience_value = next_p.get_text(strip=True) if next_p else ""
            elif label_text == "NGÀY LÀM VIỆC":
                work_day_value = next_p.get_text(strip=True) if next_p else ""

    # Trả kết quả
    return {
        "title": job_title,
        "link": url,
        "salary": salary,
        "location": location,
        "experience": experience_value,
        "description": job_description,
        "requirements": job_requirement,
        "benefits": benefit,
        "work_location_detail": location,
        "working_time": work_day_value,
        "deadline": deadline,
    }


# ==========================================================
# 🧭 HÀM CHÍNH CRAWL
# ==========================================================

def scrape_jobs_by_skill(driver, skill_name, skill_url, max_pages=10):
    """Crawl tất cả job thuộc một skill, tự skip nếu trang lỗi liên tiếp."""
    jobs = []
    page = 1
    fail_streak = 0

    while page <= max_pages:
        print(f"[INFO] Scraping skill={skill_name}, page={page}")
        try:
            driver.get(f"{skill_url}&page={page}")
            time.sleep(1.5)
            fail_streak = 0  # reset khi thành công
        except Exception as e:
            print(f"[WARN] Page {page} failed for {skill_name}: {e}")
            fail_streak += 1
            if fail_streak >= 3:
                print(f"[WARN] ❌ Quá nhiều lỗi liên tiếp, dừng kỹ năng {skill_name}.")
                break
            page += 1
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_containers = soup.find_all("div", class_="sc-iVDsrp frxvCT")
        if not job_containers:
            print(f"[INFO] No more jobs found at page {page}")
            break

        for container in job_containers:
            a_tag = container.find("a", class_="img_job_card")
            if not a_tag:
                continue
            url = a_tag.get("href")
            if not url:
                continue

            full_url = "https://www.vietnamworks.com" + url
            try:
                info = get_info(full_url, driver)
                jobs.append(info)
            except Exception as e:
                print(f"[ERROR] Failed to crawl job at {full_url}: {e}")
                continue

        page += 1
        time.sleep(1.0 + (page % 3) * 0.5)

    return jobs

def run_vnwork_crawler():
    driver = init_vnwork_driver()

    print("[INFO] Opening Vietnamworks...")
    driver.get(BASE_IT_VNWORK)
    time.sleep(10)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    skills_div = soup.find("div", class_="skill-tag-details")
    if not skills_div:
        print("[ERROR] Không tìm thấy danh sách kỹ năng. Có thể bị chặn.")
        driver.quit()
        return

    skill_elements = skills_div.find_all("div", class_="tag-wrapper")
    output_path = get_output_file(prefix="vnwork")
    print(f"[INFO] Found {len(skill_elements)} skills, saving to {output_path}")

    for idx, skill_el in enumerate(skill_elements, 1):
        skill_name = skill_el.get_text(strip=True)
        skill_url = f"https://www.vietnamworks.com/viec-lam?q={skill_name.lower().replace(' ', '-')}"

        print(f"\n=== [{idx}/{len(skill_elements)}] Crawling {skill_name} ===")

        # 👉 Khởi tạo driver riêng cho từng kỹ năng
        driver = init_vnwork_driver()
        time.sleep(3)

        try:
            jobs = scrape_jobs_by_skill(driver, skill_name, skill_url)
            if jobs:
                save_json([{"group": skill_name, "jobs": jobs}], output_path)
                print(f"[SAVE] {len(jobs)} jobs saved for {skill_name}")
            else:
                print(f"[WARN] No jobs found for {skill_name}")
        except Exception as e:
            print(f"[ERROR] Skill {skill_name} failed: {e}")
        finally:
            driver.quit()
            os.system("pkill -f chrome || true")  # 🧹 đảm bảo kill Chrome zombie
            time.sleep(2)
    print(f"[DONE] ✅ Tất cả dữ liệu đã lưu vào {output_path}")

# ==========================================================
# 🏁 ENTRYPOINT
# ==========================================================
if __name__ == "__main__":
    run_vnwork_crawler()
