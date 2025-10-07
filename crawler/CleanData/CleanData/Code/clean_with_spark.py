import json
import re
from datetime import datetime
from pathlib import Path
import spacy
import unicodedata

# Danh sách file đầu vào
INPUT_FILES = [
    Path(r'./crawler/Dataset/topcv.json'),
    Path(r'./crawler/Dataset/vnwork.json')
]

# File output
CLEANED_OUT = Path(r'./spark_jobs/Output/cleaned_data.json')

# Model NER để trích SKILL
NER_MODEL = r"./crawler/CleanData/checkpoint"

EXCHANGE_RATE = 24000

def clean_requirements(text: str) -> str:
    text = re.sub(r'\[(Required|Preferred)\]', '', text)
    text = re.sub(r'\b(Skill Required|Kỹ năng[:&]).*', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_deadline(dl: str):
    m = re.search(r'(\d{2}/\d{2}/\d{4})', dl)
    return datetime.strptime(m.group(1), '%d/%m/%Y').date().isoformat() if m else None

def normalize_salary(salary_str: str) -> int | None:
    s = str(salary_str).lower()
    if 'thoả thuận' in s or 'thỏa thuận' in s:
        return None
    s_clean = s.replace(',', '')
    nums = re.findall(r"\d+(?:\.\d+)?", s_clean)
    if not nums:
        return None
    values = [float(n) for n in nums]
    val = sum(values) / len(values)
    if 'usd' in s_clean or '$' in s_clean:
        multiplier = EXCHANGE_RATE
    elif 'triệu' in s_clean:
        multiplier = 1_000_000
    else:
        multiplier = 1
    result = int(val * multiplier)
    return result if result > 0 else None

def normalize_city_name(city: str) -> str:
    """Bỏ dấu, viết thường, nối liền các ký tự."""
    city = unicodedata.normalize('NFD', city)
    city = city.encode('ascii', 'ignore').decode('utf-8')
    city = city.lower()
    city = re.sub(r'[^a-z0-9]', '', city)
    return city

# Bản đồ tên thành phố phổ biến
CITY_MAP = {
    "hanoi": "Hà Nội",
    "hochiminh": "TP. Hồ Chí Minh",
    "tphcm": "TP. Hồ Chí Minh",
    "hcm": "TP. Hồ Chí Minh",
    "haiphong": "Hải Phòng",
    "danang": "Đà Nẵng",
    "cantho": "Cần Thơ",
    "angiang": "An Giang",
    "bariavungtau": "Bà Rịa - Vũng Tàu",
    "bacgiang": "Bắc Giang",
    "backan": "Bắc Kạn",
    "baclieu": "Bạc Liêu",
    "bacninh": "Bắc Ninh",
    "bentre": "Bến Tre",
    "binhdinh": "Bình Định",
    "binhduong": "Bình Dương",
    "binhphuoc": "Bình Phước",
    "binhthuan": "Bình Thuận",
    "camau": "Cà Mau",
    "caobang": "Cao Bằng",
    "daklak": "Đắk Lắk",
    "daknong": "Đắk Nông",
    "dienbien": "Điện Biên",
    "dongnai": "Đồng Nai",
    "dongthap": "Đồng Tháp",
    "gialai": "Gia Lai",
    "hagiang": "Hà Giang",
    "hatinh": "Hà Tĩnh",
    "haiduong": "Hải Dương",
    "haugiang": "Hậu Giang",
    "hoabinh": "Hòa Bình",
    "hungyen": "Hưng Yên",
    "khanhhoa": "Khánh Hòa",
    "kiengiang": "Kiên Giang",
    "kontum": "Kon Tum",
    "laichau": "Lai Châu",
    "lamdong": "Lâm Đồng",
    "langson": "Lạng Sơn",
    "laocai": "Lào Cai",
    "longan": "Long An",
    "namdinh": "Nam Định",
    "nghean": "Nghệ An",
    "ninhbinh": "Ninh Bình",
    "ninhthuan": "Ninh Thuận",
    "phutho": "Phú Thọ",
    "phuyen": "Phú Yên",
    "quangbinh": "Quảng Bình",
    "quangnam": "Quảng Nam",
    "quangngai": "Quảng Ngãi",
    "quangninh": "Quảng Ninh",
    "quangtri": "Quảng Trị",
    "soctrang": "Sóc Trăng",
    "sonla": "Sơn La",
    "tayninh": "Tây Ninh",
    "thaibinh": "Thái Bình",
    "thainguyen": "Thái Nguyên",
    "thanhhoa": "Thanh Hóa",
    "thuathienhue": "Thừa Thiên - Huế",
    "tiengiang": "Tiền Giang",
    "travinh": "Trà Vinh",
    "tuyenquang": "Tuyên Quang",
    "vinhlong": "Vĩnh Long",
    "vinhphuc": "Vĩnh Phúc",
    "yenbai": "Yên Bái"
}

def normalize_location(loc: str) -> str:
    """Chuẩn hóa location: chỉ lấy tên thành phố hoặc khu vực chính."""
    if not loc:
        return "Không rõ"

    loc = loc.lower().strip()
    loc_new = re.sub(r"[–\-]", ",", loc)
    parts = [p.strip() for p in loc_new.split(",") if p.strip()]
    if not parts:
        return "Không rõ"

    viet_nam_patterns = [r"\bviệt\s*-*\s*nam\b", r"\bvietnam\b", r"\bvn\b"]
    last = parts[-1]
    has_vietnam = any(re.search(pat, last, flags=re.IGNORECASE) for pat in viet_nam_patterns)

    candidate = parts[-2] if has_vietnam and len(parts) >= 2 else last
    candidate = re.sub(r"\b(tp\.?|thanh\s*pho|tinh|city)\b", "", candidate, flags=re.IGNORECASE).strip()

    normalized = normalize_city_name(candidate)

    # So khớp tổng quát – nếu chuỗi chứa một key nào trong CITY_MAP thì lấy tên chuẩn
    for key, val in CITY_MAP.items():
        if key in normalized:
            return val

    return "Không rõ"

def main():
    raw_all = []
    for f in INPUT_FILES:
        if f.exists():
            try:
                raw = json.loads(f.read_text(encoding='utf-8'))
                raw_all.extend(raw)
            except Exception as e:
                print(f"⚠ Lỗi đọc file {f}: {e}")
    nlp = spacy.load(NER_MODEL)
    print("Pipelines:", nlp.pipe_names)
    doc = nlp("Ứng viên có kinh nghiệm với Python và Docker.")
    print([(ent.text, ent.label_) for ent in doc.ents])
    
    
    cleaned = []

    for group_block in raw_all:
        group_name = group_block.get('group')
        cleaned_jobs = []

        for job in group_block.get('jobs', []):
            req_clean = clean_requirements(job.get('requirements', ''))
            deadline = parse_deadline(job.get('deadline', ''))
            location_raw = job.get('location', '')
            location_norm = normalize_location(location_raw)

            doc = nlp(req_clean)
            skills = [ent.text for ent in doc.ents if ent.label_ == 'SKILL']

            wt = job.get('working_time', '').strip() or 'Không rõ'
            salary_raw = job.get('salary', '')
            salary_norm = normalize_salary(salary_raw)

            cleaned_job = {
                'title': job.get('title'),
                'link': job.get('link'),
                'location': location_norm,
                'experience': job.get('experience'),
                'description': job.get('description'),
                'requirements': req_clean,
                'benefits': job.get('benefits'),
                'work_location_detail': job.get('work_location_detail'),
                'working_time': wt,
                'deadline': deadline,
                'salary_raw': salary_raw,
                'salary_normalized': salary_norm,
                'currency_unit': 'VND' if salary_norm is not None else None,
                'skills': skills
            }
            
            cleaned_jobs.append(cleaned_job)

        cleaned.append({
            'group': group_name,
            'jobs': cleaned_jobs
        })
            
    CLEANED_OUT.parent.mkdir(parents=True, exist_ok=True)
    CLEANED_OUT.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✔ Cleaned data written to {CLEANED_OUT} ({len(cleaned)} records)")

if __name__ == '__main__':
    main()
