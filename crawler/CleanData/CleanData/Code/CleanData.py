import json
import re
from datetime import datetime
from pathlib import Path
import spacy

# Danh sách file đầu vào
INPUT_FILES = [
    Path(r'../Dataset/topcv.json'),
    Path(r'../Dataset/vnwork.json')
]

# File output
CLEANED_OUT = Path(r'./CleanData/Code/cleaned_data.json')

# Model NER để trích SKILL
NER_MODEL = r"./checkpoint"

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
        group = group_block.get('group')
        for job in group_block.get('jobs', []):
            req_clean = clean_requirements(job.get('requirements', ''))
            deadline = parse_deadline(job.get('deadline', ''))

            doc = nlp(req_clean)
            skills = [ent.text for ent in doc.ents if ent.label_ == 'SKILL']

            wt = job.get('working_time', '').strip() or 'Không rõ'
            salary_raw = job.get('salary', '')
            salary_norm = normalize_salary(salary_raw)

            cleaned.append({
                'group': group,
                'title': job.get('title'),
                'link': job.get('link'),
                'location': job.get('location'),
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
            })

    CLEANED_OUT.parent.mkdir(parents=True, exist_ok=True)
    CLEANED_OUT.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✔ Cleaned data written to {CLEANED_OUT} ({len(cleaned)} records)")

if __name__ == '__main__':
    main()
