"""
CIVI-RESQ Model Training
--------------------------
Trains three separate XGBoost regressors (Flood Risk, Heat Risk, Accessibility Risk),
each 0-100. We deliberately keep them SEPARATE (not one multi-output model) because:
  - each risk type is driven by different, largely non-overlapping features
  - separate models -> separate, cleaner SHAP explanations per risk type
  - matches the spec: "clearly separate model-generated predictions from
    rule-based civil-engineering calculations"

Overall Vulnerability Score is NOT ML-predicted -- it's a transparent, auditable
RULE-BASED weighted composite (see app/services/risk_engine.py), because civil
engineers need to be able to justify/adjust that formula directly rather than
trust a black box for the top-line number.

Outputs:
  - backend/ml/trained_models/{flood,heat,accessibility}_model.joblib
  - backend/ml/trained_models/metrics.json   (MAE, RMSE, R2 for each model)
  - backend/ml/trained_models/feature_names.json
"""
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

MODEL_DIR = "backend/ml/trained_models"
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_SETS = {
    "flood": [
        "avg_annual_rainfall_mm", "elevation_m", "drainage_capacity_index",
        "impervious_surface_pct", "population_density_per_km2",
        "historical_flood_events_5yr",
    ],
    "heat": [
        "avg_land_surface_temp_c", "impervious_surface_pct",
        "building_density_pct", "green_cover_pct",
    ],
    "accessibility": [
        "dist_to_hospital_km", "dist_to_school_km", "dist_to_emergency_service_km",
        "road_accessibility_index",
    ],
}

TARGET_COLS = {
    "flood": "flood_risk_score",
    "heat": "heat_risk_score",
    "accessibility": "accessibility_risk_score",
}


def train_all():
    df = pd.read_csv("backend/ml/training_data.csv")
    all_metrics = {}

    for risk_name, features in FEATURE_SETS.items():
        X = df[features]
        y = df[TARGET_COLS[risk_name]]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.06,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            random_state=42,
            objective="reg:squarederror",
        )
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        preds = np.clip(preds, 0, 100)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        all_metrics[risk_name] = {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2_score": round(r2, 4),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "features": features,
        }

        joblib.dump(model, f"{MODEL_DIR}/{risk_name}_model.joblib")
        print(f"[{risk_name}] MAE={mae:.2f}  RMSE={rmse:.2f}  R2={r2:.4f}")

    with open(f"{MODEL_DIR}/metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)
    with open(f"{MODEL_DIR}/feature_names.json", "w") as f:
        json.dump(FEATURE_SETS, f, indent=2)

    print(f"\nSaved models + metrics.json -> {MODEL_DIR}")
    return all_metrics


if __name__ == "__main__":
    train_all()
