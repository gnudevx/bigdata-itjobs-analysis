import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import json

def get_info(url, driver):
    driver.get(url)

    scroll_pause_time = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    wait = WebDriverWait(driver, 3)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sc-b8164b97-1.eifRgc.vnwLayout__container')))
    time.sleep(0.5)

    # Nhấn nút 'Xem đầy đủ mô tả công việc'
    try:
        button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".sc-bd699a4b-0.kBdTlY.btn-info.btn-md.sc-1671001a-2.galMaY.clickable"))
        )
        button.click()
        time.sleep(0.5)
    except:
        pass

    # Nhấn nút 'Xem thêm' đầu tiên
    try:
        button1 = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#vnwLayout__col > div > div.sc-c683181c-0.fRBraR > div > div > div > div > button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", button1)
        time.sleep(0.5)
        button1.click()
        time.sleep(0.5)
    except:
        pass

    # Nhấn nút 'Xem thêm' thứ hai
    try:
        button2 = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#vnwLayout__col > div > div.sc-7bf5461f-0.dHvFzj > div> div > button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", button2)
        time.sleep(0.5)
        button2.click()
        time.sleep(0.5)
    except:
        pass

    # Bắt đầu parse sau khi scroll
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    job_title = soup.find('h1', class_='sc-ab270149-0 hAejeW')
    deadline = soup.find('span', class_='sc-ab270149-0 ePOHWr')
    salary = soup.find('span', class_='sc-ab270149-0 cVbwLK')
    location = soup.find('div', class_='sc-a137b890-1 joxJgK')

    job_title = job_title.text.strip() if job_title else 'N/A'
    deadline = deadline.text.strip() if deadline else 'N/A'
    salary = salary.text.strip() if salary else 'N/A'
    location = location.text.strip() if location else 'N/A'

    job_description = ""
    job_requirement = ""

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

    benefits = soup.find_all('div', class_='sc-c683181c-2 fGxLZh')
    benefit = ''.join(['-' + i.text.strip() for i in benefits])

    job_informations = soup.find_all('div', class_='sc-7bf5461f-0 dHvFzj')

    experience_value = ""
    work_day_value = ""

    for info_block in job_informations:
        labels = info_block.find_all('label', class_=['sc-ab270149-0', 'dfyRSX'])
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



def scrape_jobs(chromepath, output_file, start_page, end_page):
    try:
        service = Service(executable_path=chromepath)
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        driver = webdriver.Chrome(service=service, options=options)

        df_job = []

        for page in range(start_page, end_page + 1):
            driver.get(f'https://www.vietnamworks.com/viec-lam?q=it&page={page}')
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            print(f'Scraping page: {page}')
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            job_containers = soup.find_all('div', class_="sc-iVDsrp frxvCT")

            for container in job_containers:
                a_tag = container.find('a', class_='img_job_card')
                if a_tag:
                    url = a_tag.get('href')
                    full_url = 'https://www.vietnamworks.com' + url

                    info = get_info(full_url, driver)
                    df_job.append(info)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(df_job, f, ensure_ascii=False, indent=4)
            print(f'Data has been saved to {output_file}')

    except Exception as ex:
        print(f'Error: {ex}')


if __name__ == "__main__":
    chromepath = r'C:\Users\User\chromedriver-win64\chromedriver.exe'
    output_file = './crawl/vnwork.json'
    start_page = 1
    end_page = 11
    scrape_jobs(chromepath, output_file, start_page, end_page)