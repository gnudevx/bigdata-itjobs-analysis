def train_main(execution_date: str = None):
    """
    Huấn luyện mô hình dự đoán lương (RandomForest + XGBoost)
    - Tự động tạo thư mục model_store/YYYY-MM-DD/
    - Lưu bản 'latest' để pipeline kế tiếp dùng
    - Ghi log lịch sử huấn luyện
    """
    import pandas as pd, joblib, json, shutil, os
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestRegressor
    from xgboost import XGBRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from pathlib import Path
    from datetime import datetime
    import numpy as np
    from math import sqrt
    import sys, os
    sys.path.append('/opt/airflow/ml_jobs/')
    from Code.utils.io_utils import get_data_path, get_model_dir
    # === Timestamp & Đường dẫn ===
    today = datetime.now().strftime("%Y-%m-%d")

    if execution_date:
        timestamp = execution_date.strftime("%Y%m%d_%H%M")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    DATA_PATH = get_data_path("prepared")
    VERSION_DIR = get_model_dir(versioned=True)
    LATEST_DIR = get_model_dir(versioned=False)

    VERSION_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    BASE_DIR = VERSION_DIR.parent
    # === Load dữ liệu ===
    df = pd.read_csv(DATA_PATH)
    y = np.log1p(df["salary"])
    X = df.drop(columns=["salary"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # === Train models ===
    rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    xgb = XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.1, n_jobs=-1, random_state=42)
    xgb.fit(X_train, y_train)

    models = {"rf": rf, "xgb": xgb}
    metrics = {}

    # === Evaluate & Save ===
    for name, model in models.items():
        preds = model.predict(X_test)
        mae = mean_absolute_error(np.expm1(y_test), np.expm1(preds))
        rmse = sqrt(mean_squared_error(np.expm1(y_test), np.expm1(preds)))
        r2 = r2_score(y_test, preds)
        metrics[name] = {"mae": mae, "rmse": rmse, "r2": r2}

        # --- Save to versioned folder ---
        model_path = VERSION_DIR / f"{name}_salary_model.pkl"
        joblib.dump(model, model_path)

        # --- Copy to latest ---
        shutil.copy(model_path, LATEST_DIR / f"{name}_salary_model.pkl")

        # --- Save XGB JSON for incremental train ---
        if name == "xgb":
            json_path = VERSION_DIR / "xgb_salary_model.json"
            model.save_model(json_path)
            shutil.copy(json_path, LATEST_DIR / "xgb_salary_model.json")

    # === Save metrics ===
    metrics_path = VERSION_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    shutil.copy(metrics_path, LATEST_DIR / "metrics.json")

    # === Ghi lịch sử train ===
    history_path = BASE_DIR / "training_history.csv"
    rows = [{"timestamp": timestamp, "model": k, **v} for k, v in metrics.items()]
    new_df = pd.DataFrame(rows)

    if history_path.exists():
        old_df = pd.read_csv(history_path)
        new_df = pd.concat([old_df, new_df], ignore_index=True)
    new_df.to_csv(history_path, index=False)

    print(f"✅ Training completed for {today}.")
    print(json.dumps(metrics, indent=2))
