
import json
import re
from pathlib import Path

# Paths
INPUT_FILES = [
    Path(r'../Dataset/topcv.json'),
    Path(r'../Dataset/vnwork.json')
]

OUTPUT_FILE = Path(r"./CleanData/TrainModel/modeltrain_extracted_label.json")
# HTML tag remover
TAG_RE = re.compile(r'<[^>]+>')

def clean_text(html_text: str) -> str:
    # Loại bỏ tag HTML
    text = TAG_RE.sub('', html_text)
    # 🔹 Thay thế ký hiệu bullet và các ký tự đặc biệt dễ gây lệch offset
    text = re.sub(r'[•●▪️■□○★☆‣⁃∙–—-]', ' ', text)
    # 🔹 Chuẩn hóa xuống dòng, tab, v.v.
    text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    # 🔹 Rút gọn khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Known skills (merged + standardized)
known_skills = [
    # Languages
    "Python", "Java", "C#", "C++", "Go", "Golang", "PHP", "Ruby", "Swift", "Kotlin", "TypeScript", "JavaScript",
    # Backend
    ".NET", ".NET Core", "Spring Boot", "FastAPI", "Flask", "Django", "Express.js", "NestJS", "Laravel", "Node.js",
    # Frontend
    "React", "React Native", "Vue.js", "Next.js", "Angular", "HTML", "CSS", "SASS", "Bootstrap",
    # Cloud & DevOps
    "AWS", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "GitLab CI", "GitFlow", "ArgoCD", "Prometheus", "Grafana", "Linux", "Shell",
    # Data & Big Data
    "SQL", "MySQL", "PostgreSQL", "MariaDB", "MongoDB", "Redis", "Elasticsearch", "Kafka", "RabbitMQ",
    "Hadoop", "Spark", "HBase", "Hive", "Big Data", "Airflow", "ETL",
    # AI & Data Science
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "AI", "GenAI",
    # Architecture
    "Microservice", "SOA", "ESB", "Camel", "OpenShift", "Openshift", "RESTful", "GraphQL", "gRPC",
    # Soft skills
    "Agile", "Scrum", "Git", "CI/CD", "Tiếng Anh", "Communication", "Problem Solving", "Teamwork"
]



# Sentence splitter
SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

def split_sentences(text: str) -> list:
    parts = SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]

# Entity extractor
def extract_entities(text: str, skills: list) -> list:
    entities = []
    for skill in skills:
        for match in re.finditer(rf"\b{re.escape(skill)}\b", text, flags=re.IGNORECASE):
            start, end = match.span()
            if not any(s == start and e == end for s, e, _ in entities):
                entities.append((start, end, "SKILL"))
    return sorted(entities, key=lambda x: x[0])

# Main
def main():
    samples = []

    for path in INPUT_FILES:
        if not path.exists():
            print(f"⚠️ File not found: {path}")
            continue

        print(f"🔹 Reading {path.name} ...")
        raw = json.loads(path.read_text(encoding='utf-8'))
        for group in raw:
            for job in group.get('jobs', []):
                req_html = job.get('requirements', '')
                req_clean = clean_text(req_html)
                for sent in split_sentences(req_clean):
                    spans = extract_entities(sent, known_skills)
                    if spans:
                        samples.append({
                            'text': sent,
                            'entities': [[s, e, label] for s, e, label in spans]
                        })

    # Remove duplicates
    unique, seen = [], set()
    for s in samples:
        key = (s['text'], tuple((x[0], x[1]) for x in s['entities']))
        if key not in seen:
            seen.add(key)
            unique.append(s)

    OUTPUT_FILE.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✅ Extracted {len(unique)} labeled samples to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
