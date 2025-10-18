def clean_skills_main():
    import json, re, unicodedata, logging
    import pandas as pd
    from datetime import datetime
    import sys, os
    sys.path.append('/opt/airflow/ml_jobs')
    # Import helper functions (giữ nguyên như bạn dùng)
    from Code.utils.io_utils import get_data_path, get_hdfs_client, get_hdfs_input_path

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
    logger = logging.getLogger("clean_skills")

    # === Kết nối HDFS ===
    client = get_hdfs_client()
    in_path = get_hdfs_input_path("cleaned_data")
    out_path = get_data_path("processed", suffix="csv")
    logger.info(f"📥 Reading from HDFS: {in_path}")

    # đọc NDJSON an toàn: mỗi dòng là 1 JSON object {"group":..., "jobs":[...]}
    records = []
    with client.read(in_path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                records.append(rec)
            except json.JSONDecodeError as e:
                # Log và tiếp tục (thường không xảy ra với file hợp lệ)
                logger.warning(f"Skipping invalid JSON line {i}: {e}")
                continue

    if not records:
        logger.error("No records read from cleaned_data (file empty or invalid). Exiting.")
        return

    # === Chuẩn hóa dữ liệu ===
    def normalize_text(t):
        if not t:
            return ""
        t = unicodedata.normalize("NFKD", t)
        t = re.sub(r"[^a-zA-Z0-9À-ỹ\s]", " ", t)
        return re.sub(r"\s+", " ", t).strip().lower()

    alias_map = {
        "reactjs": "react", "nodejs": "node", "js": "javascript",
        "machine learning": "ai", "deep learning": "ai",
        "english": "english", "tiếng anh": "english"
    }

    def clean_skill_list(x):
        if not x:
            return []
        # nếu x là list, chuyển thành chuỗi phân tách bởi dấu phẩy để tái sử dụng regex
        if isinstance(x, (list, tuple)):
            s = ", ".join([str(it) for it in x if it is not None])
        else:
            s = str(x)
        skills = re.split(r"[,;/•\n]+", s)
        out = set()
        for s1 in skills:
            s_norm = normalize_text(s1)
            for k, v in alias_map.items():
                if k in s_norm:
                    s_norm = v
            if s_norm:
                out.add(s_norm)
        return list(out)

    def extract_seniority(title):
        if not title:
            return "mid"
        t = str(title).lower()
        if any(w in t for w in ["senior", "lead", "manager"]):
            return "senior"
        if any(w in t for w in ["junior", "fresher", "intern"]):
            return "junior"
        return "mid"

    rows = []
    total_groups = len(records)
    total_jobs_found = 0
    for rec in records:
        # mỗi rec expected: {"group": "...", "jobs": [ {...}, ... ]}
        grp = rec.get("group", "Unknown")
        jobs = rec.get("jobs", []) or []
        if not isinstance(jobs, (list, tuple)):
            # defensive: nếu jobs là dict của 1 job duy nhất
            jobs = [jobs]
        for j in jobs:
            total_jobs_found += 1
            # đảm bảo các key tồn tại
            title = j.get("title", "") if isinstance(j, dict) else ""
            # set group, seniority, skills_clean
            j = dict(j) if isinstance(j, dict) else {"title": title}
            j["group"] = grp
            j["seniority"] = extract_seniority(j.get("title", ""))
            j["skills_clean"] = clean_skill_list(j.get("skills", []))
            rows.append(j)

    logger.info(f"Read {total_groups} groups, expanded to {total_jobs_found} raw jobs.")

    if not rows:
        logger.warning("No job rows extracted after parsing groups. Exiting.")
        return

    # Build dataframe
    df = pd.DataFrame(rows)

    # Normalize salary column: accept salary_normalized (int) or salary (string)
    # Prefer salary_normalized if present; otherwise try to parse salary field numeric
    if "salary_normalized" in df.columns:
        df["salary_normalized"] = pd.to_numeric(df["salary_normalized"], errors="coerce")
    else:
        df["salary_normalized"] = pd.Series([None] * len(df))

    # If salary_normalized missing but raw salary string exists, try to extract a number (best-effort)
    if "salary" in df.columns:
        # attempt to parse first numeric occurrence
        def parse_salary_best(s):
            try:
                if s is None:
                    return None
                s_str = str(s)
                nums = re.findall(r"\d+(?:[.,]\d+)?", s_str)
                if not nums:
                    return None
                # take average if range
                vals = [float(x.replace(",", "").replace(".", ".")) for x in nums]
                return int(sum(vals) / len(vals))
            except Exception:
                return None
        missing_mask = df["salary_normalized"].isna()
        df.loc[missing_mask, "salary_normalized"] = df.loc[missing_mask, "salary"].apply(parse_salary_best)

    # rename to salary for downstream code if they expect "salary" column numeric
    df["salary"] = df["salary_normalized"]

    # filter by salary bounds (keep rows with salary between 3e6 and 200e6)
    df_filtered = df.copy()
    try:
        df_filtered["salary"] = pd.to_numeric(df_filtered["salary"], errors="coerce")
        df_filtered = df_filtered[df_filtered["salary"].between(3e6, 200e6)]
    except Exception as e:
        logger.warning(f"Salary filtering failed: {e} — proceeding without filtering.")
        # fallback: keep df as-is

    # === Lưu output ===
    # ensure output directory exists (get_data_path may return path in HDFS or local; keep your original behavior)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_filtered.to_csv(out_path, index=False, encoding="utf-8")
    logger.info(f"✅ Saved {len(df_filtered)} rows → {out_path}")
