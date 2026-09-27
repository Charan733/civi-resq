from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.database import get_db
from app.models.db_models import UrbanZone, RiskAssessment, Intervention
from app.routers.zones_router import zone_to_params_dict
from app.services.report_generator import generate_zone_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/zones/{zone_id}/pdf")
def download_zone_report(zone_id: str, db: Session = Depends(get_db)):
    """Generate and return a downloadable PDF risk assessment report for a zone."""
    zone = db.query(UrbanZone).filter(UrbanZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.zone_id == zone_id, RiskAssessment.is_current == True)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=400, detail="Zone has not been assessed yet")

    interventions = (
        db.query(Intervention)
        .filter(Intervention.zone_id == zone_id)
        .order_by(Intervention.priority_score.desc())
        .all()
    )

    zone_dict = {**zone_to_params_dict(zone), "zone_name": zone.zone_name, "zone_code": zone.zone_code,
                 "city": zone.city, "state": zone.state}
    assessment_dict = {
        "flood_risk_score": assessment.flood_risk_score, "heat_risk_score": assessment.heat_risk_score,
        "accessibility_risk_score": assessment.accessibility_risk_score,
        "overall_vulnerability_score": assessment.overall_vulnerability_score,
        "flood_risk_category": assessment.flood_risk_category, "heat_risk_category": assessment.heat_risk_category,
        "accessibility_risk_category": assessment.accessibility_risk_category,
        "overall_risk_category": assessment.overall_risk_category,
        "explanation": assessment.explanation,
    }
    interventions_list = [
        {
            "intervention_type": iv.intervention_type, "priority_level": iv.priority_level,
            "estimated_cost_category": iv.estimated_cost_category,
            "expected_risk_reduction_pct": iv.expected_risk_reduction_pct,
            "affected_population": iv.affected_population, "reason": iv.reason,
        }
        for iv in interventions
    ]

    pdf_bytes = generate_zone_report(zone_dict, assessment_dict, interventions_list)
    filename = f"CIVI-RESQ_{zone.zone_code}_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
