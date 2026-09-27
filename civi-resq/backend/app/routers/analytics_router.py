import json
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import UrbanZone, RiskAssessment, Intervention

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "trained_models", "metrics.json")


@router.get("/dashboard", response_model=dict)
def dashboard_stats(db: Session = Depends(get_db)):
    """Summary stats for the main analytics dashboard."""
    current_assessments = db.query(RiskAssessment).filter(RiskAssessment.is_current == True).all()
    total_zones = db.query(UrbanZone).count()

    counts = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
    for a in current_assessments:
        counts[a.overall_risk_category] = counts.get(a.overall_risk_category, 0) + 1

    avg_score = (
        round(sum(a.overall_vulnerability_score for a in current_assessments) / len(current_assessments), 2)
        if current_assessments else 0
    )

    highest = max(current_assessments, key=lambda a: a.overall_vulnerability_score, default=None)
    highest_zone_name = None
    if highest:
        zone = db.query(UrbanZone).filter(UrbanZone.id == highest.zone_id).first()
        highest_zone_name = zone.zone_name if zone else None

    total_interventions = db.query(Intervention).count()
    urgent_interventions = db.query(Intervention).filter(Intervention.priority_level == "urgent").count()

    model_metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            model_metrics = json.load(f)

    return {
        "total_zones": total_zones,
        "critical_zones": counts["critical"],
        "high_zones": counts["high"],
        "moderate_zones": counts["moderate"],
        "low_zones": counts["low"],
        "avg_vulnerability_score": avg_score,
        "highest_risk_zone": highest_zone_name,
        "highest_risk_score": highest.overall_vulnerability_score if highest else None,
        "total_interventions_recommended": total_interventions,
        "urgent_interventions": urgent_interventions,
        "model_metrics": model_metrics,
    }


@router.get("/risk-distribution", response_model=dict)
def risk_distribution(db: Session = Depends(get_db)):
    """Distribution data for charts: risk category breakdown per risk type."""
    assessments = db.query(RiskAssessment).filter(RiskAssessment.is_current == True).all()

    def bucket(scores, cat_key):
        counts = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
        for a in assessments:
            counts[getattr(a, cat_key)] += 1
        return counts

    return {
        "flood": bucket(assessments, "flood_risk_category"),
        "heat": bucket(assessments, "heat_risk_category"),
        "accessibility": bucket(assessments, "accessibility_risk_category"),
        "overall": bucket(assessments, "overall_risk_category"),
    }
