def visualize_main():
    """
    Log và visualize feature importance (RF và XGB).
    - Hoạt động cả sau incremental training.
    - Theo dõi biến động feature importance theo thời gian.
    """
    import joblib, json, pandas as pd, numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime
    from xgboost import XGBRegressor
    import sys, os
    sys.path.append('/opt/airflow/ml_jobs/')
    from Code.utils.io_utils import get_model_dir, get_data_path

    # === Đường dẫn động ===
    OUT_DIR = get_model_dir(versioned=False)  # /opt/airflow/ml_jobs/model_store/latest
    DATA_ROOT = get_data_path("prepared").parent.parent  # → /opt/airflow/ml_jobs/data
    feature_path = DATA_ROOT / "feature_columns.json"
    # === Timestamp & load feature names ===
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(feature_path, "r", encoding="utf-8") as f:
        features = json.load(f)

    # === Load model bản mới nhất ===
    rf_path = OUT_DIR / "rf_salary_model.pkl"
    xgb_path = OUT_DIR / "xgb_salary_model.pkl"
    xgb_json_path = OUT_DIR / "xgb_salary_model.json"

    # Fallback linh hoạt
    if rf_path.exists():
        rf = joblib.load(rf_path)
    else:
        raise FileNotFoundError("❌ Không tìm thấy rf_salary_model.pkl")

    if xgb_path.exists():
        xgb = joblib.load(xgb_path)
    elif xgb_json_path.exists():
        xgb = XGBRegressor()
        xgb.load_model(str(xgb_json_path))
    else:
        raise FileNotFoundError("❌ Không tìm thấy XGBoost model (pkl/json)")

    # === Lấy feature importance ===
    rf_imp = rf.feature_importances_
    xgb_imp = getattr(xgb, "feature_importances_", np.zeros_like(rf_imp))

    min_len = min(len(features), len(rf_imp), len(xgb_imp))
    features = features[:min_len]
    rf_imp = rf_imp[:min_len]
    xgb_imp = xgb_imp[:min_len]

    fi_df = pd.DataFrame({
        "timestamp": [timestamp]*min_len*2,
        "feature": features*2,
        "importance": np.concatenate([rf_imp, xgb_imp]),
        "model": ["rf"]*min_len + ["xgb"]*min_len
    })
    # === Append log lịch sử ===
    csv_path = OUT_DIR / "feature_importance_history.csv"
    old = pd.read_csv(csv_path) if csv_path.exists() else pd.DataFrame()
    fi_df = pd.concat([old, fi_df], ignore_index=True)
    fi_df.to_csv(csv_path, index=False)

    # === Tính trung bình importance ===
    avg_imp = fi_df.groupby("feature")["importance"].mean().sort_values(ascending=False).head(20)

    plt.figure(figsize=(10,6))
    plt.barh(avg_imp.index, avg_imp.values)
    plt.title(f"🔥 Top 20 Important Features (avg over time) - {timestamp}")
    plt.xlabel("Average importance")
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"feature_importance_avg_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
    plt.close()

    print(f"✅ Feature importance logged ({len(features)} features, at {timestamp})")
