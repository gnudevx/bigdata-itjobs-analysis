def evaluate_main():
    """Hàm chính để đánh giá mô hình"""
    import joblib, json, pandas as pd, numpy as np
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import matplotlib.pyplot as plt
    from pathlib import Path

    OUT_DIR = Path("ml_jobs/output_v2")
    df = pd.read_csv("ml_jobs/data/prepared_dataset.csv")

    y = np.log1p(df["salary"])
    X = df.drop(columns=["salary"])
    rf = joblib.load(OUT_DIR / "rf_salary_model.pkl")

    # Evaluate
    preds = rf.predict(X)
    mae = mean_absolute_error(np.expm1(y), np.expm1(preds))
    rmse = mean_squared_error(np.expm1(y), np.expm1(preds), squared=False)
    r2 = r2_score(y, preds)

    metrics = {"mae": mae, "rmse": rmse, "r2": r2}
    with open(OUT_DIR / "evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    plt.figure(figsize=(6,6))
    plt.scatter(np.expm1(y), np.expm1(preds), alpha=0.5, s=8)
    plt.plot([0, 2e8],[0,2e8],'r--')
    plt.title("Predicted vs Actual Salary (VND)")
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "pred_vs_actual_v2.png")
    plt.close()

    print("✅ Evaluation done:", metrics)
