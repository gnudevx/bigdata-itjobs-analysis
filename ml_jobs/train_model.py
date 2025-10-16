def train_main():
    """
    Hàm chính để huấn luyện mô hình dự đoán lương.
    """
    import pandas as pd, joblib, json
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestRegressor
    from xgboost import XGBRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from pathlib import Path
    import numpy as np
    from math import sqrt

    DATA_PATH = "./data/prepared_dataset.csv"
    OUT_DIR = Path("./model_store")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    y = np.log1p(df["salary"])
    X = df.drop(columns=["salary"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # RandomForest
    rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=2)
    rf.fit(X_train, y_train)

    # XGBoost
    xgb = XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.1, n_jobs=2, random_state=42)
    xgb.fit(X_train, y_train)

    models = {"rf": rf, "xgb": xgb}
    metrics = {}

    for name, model in models.items():
        preds = model.predict(X_test)
        mae = mean_absolute_error(np.expm1(y_test), np.expm1(preds))
        rmse = sqrt(mean_squared_error(np.expm1(y_test), np.expm1(preds)))
        r2 = r2_score(y_test, preds)
        metrics[name] = {"mae": mae, "rmse": rmse, "r2": r2}

        joblib.dump(model, OUT_DIR / f"{name}_salary_model.pkl")

    with open(OUT_DIR / "metrics_v2.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("✅ Training complete. Metrics:", json.dumps(metrics, indent=2))
