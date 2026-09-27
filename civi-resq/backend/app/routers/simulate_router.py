from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import UrbanZone, SimulationRun
from app.schemas.schemas import SimulationRequest, SimulationResult
from app.auth import get_current_user
from app.services.simulator import simulate
from app.routers.zones_router import zone_to_params_dict

router = APIRouter(prefix="/api/simulate", tags=["What-If Simulator"])


@router.post("", response_model=SimulationResult)
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Run a what-if scenario: apply hypothetical parameter changes to a zone and
    compare before/after risk scores. Doesn't modify the actual zone record --
    purely a prediction, optionally saved to simulation_runs for history.
    """
    zone = db.query(UrbanZone).filter(UrbanZone.id == payload.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    current_params = zone_to_params_dict(zone)
    result = simulate(current_params, payload.modified_params)

    run = SimulationRun(
        zone_id=zone.id,
        created_by=user.id if user else None,
        modified_params=payload.modified_params,
        before_scores={
            "flood": result["before"]["flood_risk_score"],
            "heat": result["before"]["heat_risk_score"],
            "accessibility": result["before"]["accessibility_risk_score"],
            "overall": result["before"]["overall_vulnerability_score"],
        },
        after_scores={
            "flood": result["after"]["flood_risk_score"],
            "heat": result["after"]["heat_risk_score"],
            "accessibility": result["after"]["accessibility_risk_score"],
            "overall": result["after"]["overall_vulnerability_score"],
        },
    )
    db.add(run)
    db.commit()

    return result
