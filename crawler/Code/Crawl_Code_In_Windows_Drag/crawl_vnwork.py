import time
import json
from selenium import webdriver
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import os
import shutil
from selenium_stealth import stealth
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from Code.core.driver_for_vnwork import init_vnwork_driver
# Lấy thông tin chi tiết job
def get_info(url, driver):
    driver.get(url)
    time.sleep(1)

    # Scroll xuống cuối để load đầy đủ nội dung
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    job_title = soup.find('h1', class_='sc-ab270149-0 hAejeW')
    deadline = soup.find('span', class_='sc-ab270149-0 ePOHWr')
    salary = soup.find('span', class_='sc-ab270149-0 cVbwLK')
    location = soup.find('div', class_='sc-a137b890-1 joxJgK')

    job_title = job_title.text.strip() if job_title else 'N/A'
    deadline = deadline.text.strip() if deadline else 'N/A'
    salary = salary.text.strip() if salary else 'N/A'
    location = location.text.strip() if location else 'N/A'

    # Chuẩn hóa deadline -> ngày cụ thể
    deadline = parse_deadline(deadline, crawl_date=datetime.today())

    # Mô tả & Yêu cầu
    job_description, job_requirement = "", ""
    job_detail_blocks = soup.find_all('div', class_='sc-1671001a-3 hmvhgA')
    for block in job_detail_blocks:
        headings = block.find_all('h2', class_='sc-1671001a-5 cjuZti')
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            next_div = heading.find_next_sibling('div')
            if next_div:
                clean_text = next_div.get_text(separator="\n").strip()
                if "Mô tả công việc" in heading_text:
                    job_description = clean_text
                elif "Yêu cầu công việc" in heading_text:
                    job_requirement = clean_text

    # Phúc lợi
    benefits = soup.find_all('div', class_='sc-c683181c-2 fGxLZh')
    benefit = ''.join(['- ' + i.text.strip() + '\n' for i in benefits])

    # Thông tin khác
    experience_value, work_day_value = "", ""
    job_informations = soup.find_all('div', class_='sc-7bf5461f-0 dHvFzj')
    for info_block in job_informations:
        labels = info_block.find_all('label')
        for label in labels:
            label_text = label.get_text(strip=True)
            next_p = label.find_next_sibling('p')
            if label_text == "SỐ NĂM KINH NGHIỆM TỐI THIỂU":
                experience_value = next_p.get_text(strip=True) if next_p else ""
            elif label_text == "NGÀY LÀM VIỆC":
                work_day_value = next_p.get_text(strip=True) if next_p else ""

    return {
        'title': job_title,
        'link': url,
        'salary': salary,
        'location': location,
        'experience': experience_value,
        'description': job_description,
        'requirements': job_requirement,
        'benefits': benefit,
        'work_location_detail': location,
        'working_time': work_day_value,
        'deadline': deadline,
    }
def parse_deadline(deadline_text: str, crawl_date=None):
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
                return deadline_text  # không parse được

            return f"Hạn nộp hồ sơ: {expire_date.strftime('%d/%m/%Y')}"
    
    # Nếu text đã là ngày cụ thể sẵn rồi
    return deadline_text

# Lấy jobs theo từng skill
def scrape_jobs_by_skill(driver, skill_name, skill_url, max_pages=50):
    jobs = []
    page = 1
    while True:
        if page > max_pages:  # ✅ Giới hạn số trang
            print(f"Reached max page limit ({max_pages}) for skill={skill_name}")
            break

        print(f"Scraping skill={skill_name}, page={page}")
        driver.get(f"{skill_url}&page={page}")
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_containers = soup.find_all("div", class_="sc-iVDsrp frxvCT")

        if not job_containers:  # hết job
            break

        for container in job_containers:
            a_tag = container.find("a", class_="img_job_card")
            if a_tag:
                url = a_tag.get("href")
                full_url = "https://www.vietnamworks.com" + url
                info = get_info(full_url, driver)
                jobs.append(info)

        page += 1
    return jobs

def scrape_all():
    # ⚙️ Xóa cache cũ (tránh dính driver cũ)
    driver = init_vnwork_driver(headless=True)

    print("[INFO] Opening Vietnamworks...")
    driver.get("https://www.vietnamworks.com/viec-lam?q=it")
    time.sleep(8)

    print("[DEBUG] URL:", driver.current_url)
    print("[DEBUG] Title:", driver.title)
    print("[DEBUG] PAGE LENGTH:", len(driver.page_source))

    with open("/tmp/vnworks_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    skills_div = soup.find("div", class_="skill-tag-details")
    if not skills_div:
        print("[WARN] Không tìm thấy skill-tag-details (có thể web chặn bot).")
        driver.quit()
        return

    skill_elements = skills_div.find_all("div", class_="tag-wrapper")
    print("[INFO] Found", len(skill_elements), "skills.")
    soup = BeautifulSoup(driver.page_source, "html.parser")

    skills_div = soup.find("div", class_="skill-tag-details")
    skill_elements = skills_div.find_all("div", class_="tag-wrapper") if skills_div else []

    skill_groups = []
    for skill_el in skill_elements:
        skill_name = skill_el.get_text(strip=True)
        skill_url = f"https://www.vietnamworks.com/viec-lam?q={skill_name.lower().replace(' ', '-')}"
        print(f"Found skill: {skill_name} ({skill_url})")

        jobs = scrape_jobs_by_skill(driver, skill_name, skill_url)
        skill_groups.append({"group": skill_name, "jobs": jobs})
        
        # ✅ Ghi file ngay sau mỗi skill
        with open("../vnwork2.json", "w", encoding="utf-8") as f:
            json.dump(skill_groups, f, ensure_ascii=False, indent=4)
    driver.quit()
    
if __name__ == "__main__":
    output_file = "../Dataset/vnwork2.json"
    scrape_all()
