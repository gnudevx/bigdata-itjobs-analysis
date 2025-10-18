def incremental_train(execution_date: str = None):
    """
    Incremental training cho XGBoost:
    - Dùng model .json bản latest làm checkpoint
    - Tiếp tục huấn luyện trên dữ liệu mới (prepared dataset)
    - Tự động lưu version mới (model_store/YYYY-MM-DD)
    - Cập nhật bản latest
    """
    import pandas as pd, numpy as np, joblib, shutil
    from xgboost import XGBRegressor
    from datetime import datetime
    from pathlib import Path
    import sys, os
    sys.path.append('/opt/airflow/ml_jobs/')
    # === Import utils ===
    from Code.utils.io_utils import get_data_path, get_model_dir, get_today

    # === Thời gian & đường dẫn tự động ===
    today = get_today()
    timestamp = (
        execution_date.replace("-", "") if execution_date
        else datetime.now().strftime("%Y%m%d_%H%M")
    )

    DATA_PATH = get_data_path("prepared")  # Tự sinh từ YAML
    MODEL_LATEST_JSON = get_model_dir(versioned=False) / "xgb_salary_model.json"
    MODEL_VERSION_DIR = get_model_dir(versioned=True)

    MODEL_VERSION_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📥 Loading latest model and data for incremental training ({today})...")

    # === Load dữ liệu mới ===
    df_new = pd.read_csv(DATA_PATH)
    X_new = df_new.drop(columns=["salary"])
    y_new = np.log1p(df_new["salary"])

    # === Load model JSON (checkpoint) ===
    model = XGBRegressor()
    model.load_model(str(MODEL_LATEST_JSON))

    # === Incremental training ===
    print("🚀 Continuing XGBoost training...")
    model.fit(
        X_new, y_new,
        xgb_model=str(MODEL_LATEST_JSON),
        verbose=False
    )

    # === Lưu model version mới ===
    model_json_new = MODEL_VERSION_DIR / f"xgb_salary_model_{timestamp}.json"
    model_pkl_new = MODEL_VERSION_DIR / f"xgb_salary_model_{timestamp}.pkl"

    model.save_model(model_json_new)
    joblib.dump(model, model_pkl_new)

    # === Cập nhật bản latest ===
    latest_dir = get_model_dir(versioned=False)
    shutil.copy(model_json_new, latest_dir / "xgb_salary_model.json")
    shutil.copy(model_pkl_new, latest_dir / "xgb_salary_model.pkl")

    print(f"✅ Incremental training done! Saved to {model_json_new}")
