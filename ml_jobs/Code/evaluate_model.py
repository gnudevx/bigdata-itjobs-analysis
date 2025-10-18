def evaluate_main():
    """Đánh giá mô hình bản latest"""
    import pandas as pd, joblib, json, numpy as np
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import matplotlib.pyplot as plt
    from pathlib import Path
    import sys, os
    sys.path.append('/opt/airflow/ml_jobs')
    from Code.utils.io_utils import get_data_path, get_model_dir
    
    # === Lấy đường dẫn ===
    DATA_PATH = get_data_path("prepared")
    MODEL_DIR = get_model_dir(versioned=False)
    
    # === Load data & model ===
    df = pd.read_csv(DATA_PATH)
    rf = joblib.load(MODEL_DIR / "rf_salary_model.pkl")

    y = np.log1p(df["salary"])
    X = df.drop(columns=["salary"])

    # === Evaluate ===
    preds = rf.predict(X)
    mae = mean_absolute_error(np.expm1(y), np.expm1(preds))
    rmse = mean_squared_error(np.expm1(y), np.expm1(preds), squared=False)
    r2 = r2_score(y, preds)

    # === Save metrics ===
    metrics = {"mae": mae, "rmse": rmse, "r2": r2}
    with open(MODEL_DIR / "evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Evaluation done for {DATA_PATH.name}")
    print(metrics)
