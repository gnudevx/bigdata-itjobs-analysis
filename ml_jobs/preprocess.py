def preprocess_main():
    import pandas as pd, re, json
    from pathlib import Path
    from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer
    import numpy as np
    import json

        
    IN_PATH = "./data/cleaned_extended.csv"
    OUT_PATH = "./data/prepared_dataset.csv"
    Path("./data").mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(IN_PATH)
    df["experience_num"] = pd.to_numeric(df["experience"], errors="coerce").fillna(0).astype(int)
    df["location_norm"] = df["location"].fillna("unknown").str.lower()

    # One-hot encode location + seniority + group
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    cat_features = ohe.fit_transform(df[["location_norm", "seniority", "group"]])

    cat_cols = ohe.get_feature_names_out(["location_norm", "seniority", "group"])
    cat_cols = [c.replace("location_norm_", "loc_")
                .replace("seniority_", "sen_")
                .replace("group_", "grp_")
                for c in cat_cols]

    # Multi-label binarize skills
    mlb = MultiLabelBinarizer()
    skill_features = mlb.fit_transform(df["skills_clean"].apply(eval))
    skill_cols = [f"skill__{s}" for s in mlb.classes_]

    X = np.hstack([df[["experience_num"]].values, cat_features, skill_features])
    cols = ["experience_num"] + list(cat_cols) + list(skill_cols)

    prepared = pd.DataFrame(X, columns=cols)
    prepared["salary"] = df["salary"].values
    prepared.to_csv(OUT_PATH, index=False)
    with open("./data/feature_columns.json", "w", encoding="utf-8") as f:
        json.dump(cols, f, indent=2)
    print(f"✅ Dataset ready for ML: {OUT_PATH}")
