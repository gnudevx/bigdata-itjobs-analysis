def visualize_main():
    """
    Visualize and log feature importance of the trained Random Forest model.
    Saves a CSV log of feature importances over time and a plot of the top 25 features.
    """
    import joblib, json, pandas as pd, numpy as np
    import matplotlib.pyplot as plt
    from pathlib import Path
    from datetime import datetime

    OUT_DIR = Path("./model_store/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # === Load model & feature names ===
    rf = joblib.load(OUT_DIR / "rf_salary_model.pkl")
    features = json.load(open("./data/feature_columns.json", "r", encoding="utf-8"))

    # === Tính feature importance ===
    importances = rf.feature_importances_
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # === Ghi log feature importance vào CSV (tích lũy theo thời gian) ===
    fi_df = pd.DataFrame({
        "timestamp": timestamp,
        "feature": features,
        "importance": importances
    })
    csv_path = OUT_DIR / "feature_importance_history.csv"
    if csv_path.exists():
        old = pd.read_csv(csv_path)
        fi_df = pd.concat([old, fi_df], ignore_index=True)
    fi_df.to_csv(csv_path, index=False)

    # === Vẽ Top 25 của lần này ===
    idx = np.argsort(importances)[-25:]
    plt.figure(figsize=(8,6))
    plt.barh(np.array(features)[idx], importances[idx])
    plt.title(f"Top 25 Feature Importances (RF) - {timestamp}")
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"feature_importance_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
    plt.close()

    print(f"✅ Feature importance logged and plotted for {timestamp}")
