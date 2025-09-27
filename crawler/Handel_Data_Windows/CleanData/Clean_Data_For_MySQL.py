import json
import re
from datetime import datetime
from pathlib import Path
import spacy

# Đường dẫn đầu vào/ra
JSON_INPUT   = Path(r'D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/topcv.json')
CLEANED_OUT  = Path(r'D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/cleaned_data.json')

# Model NER để trích SKILL (bạn phải fine-tune/training trước)
NER_MODEL    = r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/checkpoint"

# Tỉ giá USD -> VND
EXCHANGE_RATE = 24000

# Hàm làm sạch phần mô tả requirements
def clean_requirements(text: str) -> str:
    text = re.sub(r'\[(Required|Preferred)\]', '', text)
    text = re.sub(r'\b(Skill Required|Kỹ năng[:&]).*', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()  

# Hàm parse deadline thành ISO format
def parse_deadline(dl: str):
    m = re.search(r'(\d{2}/\d{2}/\d{4})', dl)
    return datetime.strptime(m.group(1), '%d/%m/%Y').date().isoformat() if m else None

# Hàm chuẩn hóa salary: lấy midpoint nếu range hoặc giá trị nếu đơn lẻ
def normalize_salary(salary_str: str) -> int | None:
    s = salary_str.lower()
    # Loại bỏ trường hợp thoả thuận
    if 'thoả thuận' in s or 'thỏa thuận' in s:
        return None
    # Xoá tất cả dấu phẩy (là dấu phân cách ngàn)
    s_clean = s.replace(',', '')
    # Tìm tất cả các số
    nums = re.findall(r"\d+(?:\.\d+)?", s_clean)
    if not nums:
        return None
    # Chuyển thành float
    values = [float(n) for n in nums]
    # Tính midpoint nếu nhiều số, hoặc giữ số đơn lẻ
    val = sum(values) / len(values)
    # Xác định đơn vị
    if 'usd' in s_clean or '$' in s_clean:
        multiplier = EXCHANGE_RATE
    elif 'triệu' in s_clean:
        multiplier = 1_000_000
    else:
        # mặc định VND
        multiplier = 1
    result = int(val * multiplier)
    return result if result > 0 else None


def main():
    raw = json.loads(JSON_INPUT.read_text(encoding='utf-8'))
    cleaned = []

    nlp = spacy.load(NER_MODEL)

    for group_block in raw:
        group = group_block.get('group')
        for job in group_block.get('jobs', []):
            req_clean = clean_requirements(job.get('requirements', ''))
            deadline  = parse_deadline(job.get('deadline', ''))

            # Extract skills
            doc = nlp(req_clean)
            skills = [ent.text for ent in doc.ents if ent.label_ == 'SKILL']

            # Normalize working_time
            wt = job.get('working_time', '').strip()
            working_time = wt if wt else 'Không rõ'

            # Normalize salary
            salary_raw = job.get('salary', '')
            salary_norm = normalize_salary(salary_raw)

            cleaned.append({
                'group':               group,
                'title':               job.get('title'),
                'link':                job.get('link'),
                'location':            job.get('location'),
                'experience':          job.get('experience'),
                'description':         job.get('description'),
                'requirements':        req_clean,
                'benefits':            job.get('benefits'),
                'work_location_detail':job.get('work_location_detail'),
                'working_time':        working_time,
                'deadline':            deadline,
                'salary_raw':          salary_raw,
                'salary_normalized':   salary_norm,
                'currency_unit':       'VND' if salary_norm is not None else None,
                'skills':              skills
            })

    CLEANED_OUT.parent.mkdir(parents=True, exist_ok=True)
    CLEANED_OUT.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✔ Cleaned data written to {CLEANED_OUT}")


if __name__ == '__main__':
    main()
