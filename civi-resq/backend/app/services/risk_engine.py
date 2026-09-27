"""
CIVI-RESQ Risk Engine
-----------------------
Central service that:
  1. Loads the 3 trained XGBoost models once (module-level, cached)
  2. Predicts flood / heat / accessibility risk for a zone's parameters (ML-generated)
  3. Explains each prediction using SHAP (explainable AI requirement)
  4. Computes Overall Urban Vulnerability Score as a transparent RULE-BASED weighted
     composite -- NOT model output -- so engineers can audit/adjust the formula.
  5. Maps numeric scores -> risk categories (low/moderate/high/critical = green/yellow/orange/red)

This module is deliberately the ONLY place that touches the ML models, so the rest
of the app never has to know about XGBoost/SHAP internals.
"""
import json
import os
import joblib
import numpy as np
import shap

# app/services/risk_engine.py -> ../../ml/trained_models (backend/ml/trained_models)
MODEL_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ml", "trained_models")
)

# --- Rule-based composite weights (auditable, adjustable by civil engineers) ---
# Overall Vulnerability = weighted sum of the three risk scores.
# Flood weighted highest because it's the most historically destructive / high-frequency
# risk in this monsoon-delta region; accessibility weighted lowest as it compounds
# other risks rather than causing damage directly.
OVERALL_WEIGHTS = {
    "flood": 0.45,
    "heat": 0.25,
    "accessibility": 0.30,
}

RISK_THRESHOLDS = [
    (25, "low"),        # 0-25   -> green
    (50, "moderate"),   # 25-50  -> yellow
    (75, "high"),        # 50-75  -> orange
    (101, "critical"),   # 75-100 -> red
]


class RiskEngine:
    _instance = None

    def __init__(self):
        self.models = {}
        self.explainers = {}
        self.feature_sets = {}
        self._load()

    def _load(self):
        with open(os.path.join(MODEL_DIR, "feature_names.json")) as f:
            self.feature_sets = json.load(f)
        for risk_name in ["flood", "heat", "accessibility"]:
            model_path = os.path.join(MODEL_DIR, f"{risk_name}_model.joblib")
            model = joblib.load(model_path)
            self.models[risk_name] = model
            # TreeExplainer is fast + exact for XGBoost
            self.explainers[risk_name] = shap.TreeExplainer(model)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def categorize(score: float) -> str:
        for threshold, category in RISK_THRESHOLDS:
            if score < threshold:
                return category
        return "critical"

    def _predict_one(self, risk_name: str, zone_params: dict):
        features = self.feature_sets[risk_name]
        x = np.array([[zone_params[f] for f in features]])
        model = self.models[risk_name]
        score = float(np.clip(model.predict(x)[0], 0, 100))

        # SHAP explanation for this single prediction
        shap_values = self.explainers[risk_name].shap_values(x)[0]
        contributions = sorted(
            [
                {
                    "feature": features[i],
                    "value": float(x[0][i]),
                    "impact": round(float(shap_values[i]), 3),
                }
                for i in range(len(features))
            ],
            key=lambda c: abs(c["impact"]),
            reverse=True,
        )
        return score, contributions

    def assess_zone(self, zone_params: dict) -> dict:
        """
        zone_params: dict with all raw input fields (rainfall, elevation, drainage, etc.)
        Returns full risk assessment: scores, categories, explanations, overall score.
        """
        flood_score, flood_expl = self._predict_one("flood", zone_params)
        heat_score, heat_expl = self._predict_one("heat", zone_params)
        access_score, access_expl = self._predict_one("accessibility", zone_params)

        overall_score = round(
            flood_score * OVERALL_WEIGHTS["flood"]
            + heat_score * OVERALL_WEIGHTS["heat"]
            + access_score * OVERALL_WEIGHTS["accessibility"],
            2,
        )

        return {
            "flood_risk_score": round(flood_score, 2),
            "heat_risk_score": round(heat_score, 2),
            "accessibility_risk_score": round(access_score, 2),
            "overall_vulnerability_score": overall_score,
            "flood_risk_category": self.categorize(flood_score),
            "heat_risk_category": self.categorize(heat_score),
            "accessibility_risk_category": self.categorize(access_score),
            "overall_risk_category": self.categorize(overall_score),
            "explanation": {
                "flood": flood_expl,
                "heat": heat_expl,
                "accessibility": access_expl,
                "overall_formula": (
                    f"Overall = {OVERALL_WEIGHTS['flood']*100:.0f}% x Flood "
                    f"+ {OVERALL_WEIGHTS['heat']*100:.0f}% x Heat "
                    f"+ {OVERALL_WEIGHTS['accessibility']*100:.0f}% x Accessibility "
                    f"(rule-based composite, not model-predicted)"
                ),
            },
            "model_version": "v1",
        }


def get_risk_engine() -> RiskEngine:
    return RiskEngine.instance()
