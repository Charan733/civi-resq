"""
CIVI-RESQ AI Assistant
-------------------------
Answers natural-language questions about a zone using ONLY real computed system
data (risk scores, SHAP explanations, intervention recommendations, simulator
results) -- never fabricated facts. This is a deterministic, template-based
NLG system, not a general LLM call, specifically so every answer is traceable
back to an actual number the system computed.

Supported question patterns (matched by keyword, not exact phrasing):
  - "why is this zone high/critical/flood risk"      -> explains top SHAP factors
  - "main cause of flooding" / "why flooding"          -> flood-specific SHAP factors
  - "which intervention should be prioritized"          -> top-ranked intervention + reason
  - "what happens if X improved/increased by N%"        -> runs the actual simulator
"""
import re
from sqlalchemy.orm import Session

from app.models.db_models import UrbanZone, RiskAssessment, Intervention
from app.services.simulator import simulate
from app.routers.zones_router import zone_to_params_dict

PARAM_KEYWORDS = {
    "drainage": "drainage_capacity_index",
    "green cover": "green_cover_pct",
    "green": "green_cover_pct",
    "vegetation": "green_cover_pct",
    "road": "road_accessibility_index",
    "accessibility": "road_accessibility_index",
    "impervious": "impervious_surface_pct",
    "building density": "building_density_pct",
}


def _get_zone_and_assessment(db: Session, zone_id: str):
    zone = db.query(UrbanZone).filter(UrbanZone.id == zone_id).first()
    if not zone:
        return None, None
    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.zone_id == zone_id, RiskAssessment.is_current == True)
        .first()
    )
    return zone, assessment


def _extract_pct_change(question: str) -> float:
    match = re.search(r"(\d+)\s*%", question)
    return float(match.group(1)) if match else 25.0  # default hypothetical improvement


def _extract_param_key(question: str) -> str:
    q = question.lower()
    for kw, field in PARAM_KEYWORDS.items():
        if kw in q:
            return field
    return "drainage_capacity_index"  # most common default


def answer_question(db: Session, question: str, zone_id: str | None) -> dict:
    q_lower = question.lower()

    if not zone_id:
        return {
            "answer": "Please select a specific zone on the map or zone list so I can answer using that zone's actual data.",
            "data_used": {},
        }

    zone, assessment = _get_zone_and_assessment(db, zone_id)
    if not zone:
        return {"answer": "I couldn't find that zone in the system.", "data_used": {}}
    if not assessment:
        return {
            "answer": f"{zone.zone_name} hasn't been assessed yet. Trigger an assessment first.",
            "data_used": {},
        }

    # --- Pattern: "what happens if ... improved/changed ..." -> run real simulator ---
    if any(w in q_lower for w in ["what happens if", "what if", "simulate"]):
        param_field = _extract_param_key(question)
        pct = _extract_pct_change(question)
        current_val = getattr(zone, param_field)
        direction = -1 if any(w in q_lower for w in ["reduce", "decrease", "worse", "lower"]) else 1
        new_val = max(0, min(100, current_val + direction * (current_val * pct / 100)))

        params = zone_to_params_dict(zone)
        sim = simulate(params, {param_field: round(new_val, 1)})
        overall_delta = sim["deltas"]["overall_vulnerability_score"]

        answer = (
            f"If {param_field.replace('_', ' ')} in {zone.zone_name} changes from "
            f"{current_val:.1f} to {new_val:.1f} ({'+' if direction>0 else '-'}{pct:.0f}%), "
            f"the model predicts Overall Vulnerability would go from "
            f"{overall_delta['before']:.1f} to {overall_delta['after']:.1f} "
            f"({overall_delta['change_pct']:+.1f}%). "
            f"Flood risk: {sim['deltas']['flood_risk_score']['before']:.1f} -> "
            f"{sim['deltas']['flood_risk_score']['after']:.1f}. "
            f"Heat risk: {sim['deltas']['heat_risk_score']['before']:.1f} -> "
            f"{sim['deltas']['heat_risk_score']['after']:.1f}."
        )
        return {"answer": answer, "data_used": sim}

    # --- Pattern: "which intervention should be prioritized" ---
    if "intervention" in q_lower and ("prioritiz" in q_lower or "recommend" in q_lower or "which" in q_lower):
        interventions = (
            db.query(Intervention)
            .filter(Intervention.zone_id == zone_id)
            .order_by(Intervention.priority_score.desc())
            .all()
        )
        if not interventions:
            return {
                "answer": f"No interventions are currently recommended for {zone.zone_name} -- its risk levels don't trigger any of the defined intervention rules.",
                "data_used": {},
            }
        top = interventions[0]
        answer = (
            f"For {zone.zone_name}, the top-priority intervention is "
            f"'{top.intervention_type.replace('_', ' ')}' ({top.priority_level.upper()} priority, "
            f"priority score {top.priority_score:.0f}/100). Expected risk reduction: "
            f"{top.expected_risk_reduction_pct:.0f}%. Estimated cost category: "
            f"{top.estimated_cost_category.replace('_', ' ')}. Reason: {top.reason}"
        )
        return {
            "answer": answer,
            "data_used": {"top_intervention": top.intervention_type, "priority_score": top.priority_score},
        }

    # --- Pattern: "why is this zone high/critical risk" or "main cause of flooding" ---
    risk_key = "flood"
    if "heat" in q_lower or "temperature" in q_lower:
        risk_key = "heat"
    elif "access" in q_lower or "road" in q_lower or "connectivity" in q_lower:
        risk_key = "accessibility"
    elif "flood" in q_lower or "waterlog" in q_lower or "rain" in q_lower:
        risk_key = "flood"

    score_map = {
        "flood": assessment.flood_risk_score,
        "heat": assessment.heat_risk_score,
        "accessibility": assessment.accessibility_risk_score,
    }
    def _val(x):
        return x.value if hasattr(x, "value") else x

    cat_map = {
        "flood": _val(assessment.flood_risk_category),
        "heat": _val(assessment.heat_risk_category),
        "accessibility": _val(assessment.accessibility_risk_category),
    }
    factors = assessment.explanation.get(risk_key, [])[:3]
    factor_text = "; ".join(
        f"{f['feature'].replace('_', ' ')} (value {f['value']:.1f}, "
        f"{'increases' if f['impact']>0 else 'decreases'} risk by {abs(f['impact']):.1f} pts)"
        for f in factors
    )

    answer = (
        f"{zone.zone_name} has a {cat_map[risk_key]} {risk_key} risk score of "
        f"{score_map[risk_key]:.1f}/100. The main contributing factors (from the model's "
        f"SHAP explanation) are: {factor_text}."
    )
    return {"answer": answer, "data_used": {"risk_type": risk_key, "score": score_map[risk_key], "factors": factors}}
