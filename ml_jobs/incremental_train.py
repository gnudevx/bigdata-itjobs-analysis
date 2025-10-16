def incremental_train(): 
    from xgboost import XGBRegressor
    import joblib
    import pandas as pd

    # Load model cũ
    model = joblib.load("ml_jobs/model_store/xgb_salary_model.pkl")

    # Load data mới (append hoặc chỉ batch mới)
    df_new = pd.read_csv("ml_jobs/data/prepared_dataset_new.csv")
    X_new = df_new.drop(columns=["salary"])
    y_new = np.log1p(df_new["salary"])

    # Train tiếp
    model.fit(X_new, y_new, xgb_model="ml_jobs/model_store/xgb_salary_model.pkl")

    # Lưu lại
    joblib.dump(model, "ml_jobs/model_store/xgb_salary_model.pkl")
