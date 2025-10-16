def clean_skills_main():
    import json, re, unicodedata
    import pandas as pd
    from pathlib import Path
    import numpy as np
    from hdfs import InsecureClient
    from datetime import datetime

    client = InsecureClient('http://hadoop-master:9870', user='hadoopducdung')
    today = datetime.now().strftime("%Y-%m-%d")
    IN_PATH = f"/user/hadoopducdung/Output/cleaned_data_{today}.json"
    OUT_PATH = Path("./data/cleaned_extended.csv")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"📥 Reading cleaned Spark data from HDFS: {IN_PATH}")

    with client.read(IN_PATH, encoding="utf-8") as f:
        data = json.load(f)

    def normalize_text(t):
        if not t: return ""
        t = unicodedata.normalize("NFKD", t)
        t = re.sub(r"[^a-zA-Z0-9À-ỹ\s]", " ", t)
        return re.sub(r"\s+", " ", t).strip().lower()

    def extract_seniority(title):
        title = title.lower()
        if "senior" in title or "lead" in title:
            return "senior"
        if "junior" in title or "fresher" in title:
            return "junior"
        return "mid"

    def clean_skill_list(x):
        if not x: return []
        parts = re.split(r"[,;/•\n]+", str(x))
        skills = [normalize_text(p) for p in parts if p.strip()]
        mapped = []
        for s in skills:
            if "js" in s: s = "javascript"
            if "reactjs" in s: s = "react"
            if "nodejs" in s: s = "node"
            if "english" in s or "tiếng anh" in s: s = "english"
            mapped.append(s)
        seen = set(); out=[]
        for s in mapped:
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        return out

    rows = []
    for group in data:
        grp = group["group"]
        for j in group["jobs"]:
            r = j.copy()
            r["group"] = grp
            r["skills_str"] = ", ".join(j.get("skills", []))
            r["seniority"] = extract_seniority(j.get("title", ""))
            rows.append(r)

    df = pd.DataFrame(rows)
    df["salary"] = pd.to_numeric(df["salary_normalized"], errors="coerce")
    df = df[df["salary"].notna()]
    df = df[df["salary"].between(3e6, 200e6)]
    df["skills_clean"] = df["skills_str"].apply(clean_skill_list)

    df.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"✅ Saved cleaned dataset to {OUT_PATH} ({len(df)} rows)")
