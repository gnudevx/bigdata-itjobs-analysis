# improved_modeltrain_extractor.py
# Script to extract skill spans for NER training from TopCV JSON

import json
import re
from pathlib import Path

# Paths (adjust as needed)
INPUT_FILE = Path(r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/topcv.json")
OUTPUT_FILE = Path(r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/TrainModel/modeltrain_extracted.json")

# List of known skills
# improved_modeltrain_extractor.py
# Script to extract skill spans for NER training from TopCV JSON

# List of known skills
known_skills = [
    "Java", "Spring boot", "Docker", "React", "HTML", "CSS", "JavaScript",
    "Git", "GitFlow", "CI/CD", "Agile", "AWS", "Azure", "Google Cloud",
    "Python", "MySQL", "Node.js", "Vue.js", "FastAPI",
    "MongoDB", "PostgreSQL", "MariaDB", "Jenkins", "Terraform", "Ansible", "Kubernetes",
    "C#", ".NET Core", "ELK Stack", "Kafka", "RabbitMQ", "Tiếng Anh",  "MicroService", "Redis", "Kafka", "Ansible", "Jenkins", "ArgoCD", "Prometheus", "Grafana",
    "Shell", "Go", "Golang", "Linux", "Docker", "CI/CD", "NodeJs", "ReactNative", "TypeScript",
    "Next.js", "Express.js", "NestJS", "GraphQL", "gRPC", "RESTful", "Celery", "Flask", "FastAPI",
    "Django", "Beat", "Batch", "Spark", "HBase", "Big Data", "IoT", "AI", "GenAI", "Openshift",
    "ESB", "Camel", "OpenAI"
]

# Utility to strip HTML tags
TAG_RE = re.compile(r'<[^>]+>')

def clean_text(html_text: str) -> str:
    text = TAG_RE.sub('', html_text)
    return text.replace('\r', ' ').replace('\n', ' ').strip()

# Split text into sentences (simple rule-based)
SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

def split_sentences(text: str) -> list:
    parts = SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def extract_entities(text: str, skills: list) -> list:
    entities = []
    for skill in skills:
        # Use word boundaries, case-insensitive
        for match in re.finditer(rf"\b{re.escape(skill)}\b", text, flags=re.IGNORECASE):
            start, end = match.span()
            # Avoid duplicates
            if not any(s==start and e==end for s,e,_ in entities):
                # Capture original skill casing
                label = 'SKILL'
                entities.append((start, end, label))
    return sorted(entities, key=lambda x: x[0])


def main():
    raw = json.loads(INPUT_FILE.read_text(encoding='utf-8'))
    samples = []

    for group in raw:
        for job in group.get('jobs', []):
            req_html = job.get('requirements', '')
            req_clean = clean_text(req_html)
            for sent in split_sentences(req_clean):
                spans = extract_entities(sent, known_skills)
                if spans:
                    # Only include sentences with at least one skill
                    samples.append({
                        'text': sent,
                        'entities': [[s, e, label] for s, e, label in spans]
                    })
    
    # Remove duplicates: identical text and spans
    unique = []
    seen = set()
    for sample in samples:
        key = (sample['text'], tuple((s,e) for s,e,_ in sample['entities']))
        if key not in seen:
            seen.add(key)
            unique.append(sample)

    OUTPUT_FILE.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Extracted {len(unique)} samples to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()


# Utility to strip HTML tags
TAG_RE = re.compile(r'<[^>]+>')

def clean_text(html_text: str) -> str:
    text = TAG_RE.sub('', html_text)
    return text.replace('\r', ' ').replace('\n', ' ').strip()

# Split text into sentences (simple rule-based)
SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

def split_sentences(text: str) -> list:
    parts = SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def extract_entities(text: str, skills: list) -> list:
    entities = []
    for skill in skills:
        # Use word boundaries, case-insensitive
        for match in re.finditer(rf"\b{re.escape(skill)}\b", text, flags=re.IGNORECASE):
            start, end = match.span()
            # Avoid duplicates
            if not any(s==start and e==end for s,e,_ in entities):
                # Capture original skill casing
                label = 'SKILL'
                entities.append((start, end, label))
    return sorted(entities, key=lambda x: x[0])


def main():
    raw = json.loads(INPUT_FILE.read_text(encoding='utf-8'))
    samples = []

    for group in raw:
        for job in group.get('jobs', []):
            req_html = job.get('requirements', '')
            req_clean = clean_text(req_html)
            for sent in split_sentences(req_clean):
                spans = extract_entities(sent, known_skills)
                if spans:
                    # Only include sentences with at least one skill
                    samples.append({
                        'text': sent,
                        'entities': [[s, e, label] for s, e, label in spans]
                    })
    
    # Remove duplicates: identical text and spans
    unique = []
    seen = set()
    for sample in samples:
        key = (sample['text'], tuple((s,e) for s,e,_ in sample['entities']))
        if key not in seen:
            seen.add(key)
            unique.append(sample)

    OUTPUT_FILE.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Extracted {len(unique)} samples to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
