
def preprocess_main():
    import pandas as pd, json
    from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer
    import numpy as np
    import shutil
    from pathlib import Path
    import sys, os
    sys.path.append('/opt/airflow/ml_jobs/')
    from Code.utils.io_utils import get_data_path
    
    # --- Lấy đường dẫn ---
    IN_PATH = get_data_path("processed")
    OUT_PATH = get_data_path("prepared")
    FEATURE_PATH = OUT_PATH.parent / "feature_columns.json"
    LATEST_DIR = Path("/opt/airflow/ml_jobs/data/latest")
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    # --- Đọc và xử lý ---
    df = pd.read_csv(IN_PATH)
    df["experience_num"] = pd.to_numeric(df["experience"], errors="coerce").fillna(0).astype(int)
    df["location_norm"] = df["location"].fillna("unknown").str.lower()

    # One-hot + multi-label encode
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    cat_features = ohe.fit_transform(df[["location_norm", "seniority", "group"]])
    cat_cols = ohe.get_feature_names_out(["location_norm", "seniority", "group"])

    mlb = MultiLabelBinarizer()
    skill_features = mlb.fit_transform(df["skills_clean"].apply(eval))
    skill_cols = [f"skill__{s}" for s in mlb.classes_]

    import numpy as np
    X = np.hstack([df[["experience_num"]].values, cat_features, skill_features])
    cols = ["experience_num"] + list(cat_cols) + list(skill_cols)

    prepared = pd.DataFrame(X, columns=cols)
    prepared["salary"] = df["salary"].values

    # --- Lưu ---
    prepared.to_csv(OUT_PATH, index=False)
    with open(FEATURE_PATH, "w", encoding="utf-8") as f:
        json.dump(cols, f, indent=2)
    shutil.copy(OUT_PATH, LATEST_DIR / "prepared_dataset.csv")
    shutil.copy(FEATURE_PATH, LATEST_DIR / "feature_columns.json")

    print(f"✅ Preprocessed data saved to {OUT_PATH}")
