"""
CIVI-RESQ Baseline Model
---------------------------
Implements the CLASSIC weighted-overlay susceptibility scoring method -- the
standard approach that most "waterlogging susceptibility map" studies stop at
(exactly what the pitch says this project goes beyond). This gives us a real
baseline to compare the XGBoost model against, rather than just asserting our
model is better.

WEIGHTED OVERLAY METHOD (standard in flood-susceptibility GIS literature):
  1. Normalize each contributing factor to 0-1
  2. Assign expert-judgment weights to each factor (commonly done via AHP --
     Analytic Hierarchy Process -- in published studies; here we use
     literature-typical weights for simplicity/transparency)
  3. Susceptibility = weighted sum of normalized factors
  4. NO machine learning, NO training, NO feature interactions -- every
     factor contributes independently and linearly. This is precisely the
     limitation that ML-based approaches (like our XGBoost models) improve on.

We evaluate this baseline on the EXACT SAME train/test split and metrics as
the XGBoost model, so the comparison is apples-to-apples.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import spearmanr

# Literature-typical weighted-overlay weights for flood susceptibility mapping
# (rainfall, imperviousness, and drainage are consistently the top-weighted
# factors across published weighted-overlay flood studies; elevation and
# density are secondary contributors)
FLOOD_WEIGHTS = {
    "avg_annual_rainfall_mm": 0.25,
    "impervious_surface_pct": 0.25,
    "drainage_capacity_index": 0.25,  # inverted: higher drainage = lower risk
    "elevation_m": 0.15,              # inverted: higher elevation = lower risk
    "population_density_per_km2": 0.10,
}

HEAT_WEIGHTS = {
    "avg_land_surface_temp_c": 0.40,
    "impervious_surface_pct": 0.30,
    "building_density_pct": 0.20,
    "green_cover_pct": 0.10,  # inverted
}

ACCESS_WEIGHTS = {
    "dist_to_hospital_km": 0.35,
    "dist_to_school_km": 0.30,
    "dist_to_emergency_service_km": 0.25,
    "road_accessibility_index": 0.10,  # inverted
}

INVERTED_FEATURES = {"drainage_capacity_index", "elevation_m", "green_cover_pct", "road_accessibility_index"}


def _normalize(series: pd.Series, invert: bool) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    norm = (series - lo) / (hi - lo)
    return 1 - norm if invert else norm


def weighted_overlay_score(df: pd.DataFrame, weights: dict) -> np.ndarray:
    score = np.zeros(len(df))
    for feature, weight in weights.items():
        invert = feature in INVERTED_FEATURES
        score += weight * _normalize(df[feature], invert).values
    return score * 100  # scale to 0-100 like the ML models


def evaluate_baseline():
    """
    Weighted-overlay scores are RELATIVE susceptibility rankings by construction
    (that's how they're used and validated in the flood-susceptibility literature
    -- via rank correlation / AUC against observed events, not raw regression
    error). Comparing a raw 0-100 overlay score directly against a differently-
    scaled numeric target with MAE is not a fair or standard comparison -- it
    penalizes a systematic offset that a real analyst would calibrate away.

    So we report BOTH:
      1. Spearman rank correlation (the standard weighted-overlay validation
         metric) -- does the overlay rank zones in the same order as ground truth?
      2. A linearly-calibrated version (fit a 1-feature linear regression of
         true score ~ overlay score on the TRAIN split, apply to test) -- this
         gives the overlay method a fair shot at matching scale/offset while
         still being a dramatically simpler model than XGBoost (1 coefficient
         vs. a full nonlinear multi-feature tree ensemble).
    """
    df = pd.read_csv("backend/ml/training_data.csv")

    results = {}
    configs = [
        ("flood", FLOOD_WEIGHTS, "flood_risk_score"),
        ("heat", HEAT_WEIGHTS, "heat_risk_score"),
        ("accessibility", ACCESS_WEIGHTS, "accessibility_risk_score"),
    ]

    for risk_name, weights, target_col in configs:
        features = list(weights.keys())
        X = df[features]
        y = df[target_col]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        overlay_train = np.clip(weighted_overlay_score(X_train, weights), 0, 100)
        overlay_test = np.clip(weighted_overlay_score(X_test, weights), 0, 100)

        # Rank correlation (standard weighted-overlay validation metric)
        rank_corr, _ = spearmanr(overlay_test, y_test)

        # Linear calibration: fit true ~ a*overlay + b on train, apply to test
        lr = LinearRegression()
        lr.fit(overlay_train.reshape(-1, 1), y_train)
        preds = np.clip(lr.predict(overlay_test.reshape(-1, 1)), 0, 100)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        results[risk_name] = {
            "mae": round(mae, 3), "rmse": round(rmse, 3), "r2_score": round(r2, 4),
            "spearman_rank_correlation": round(float(rank_corr), 4),
        }
        print(f"[BASELINE-{risk_name}] MAE={mae:.2f}  RMSE={rmse:.2f}  R2={r2:.4f}  "
              f"Spearman={rank_corr:.3f}")

    return results


if __name__ == "__main__":
    evaluate_baseline()
