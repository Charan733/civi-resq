"""
CIVI-RESQ What-If Simulator
------------------------------
Lets a user hypothetically modify one or more zone input parameters (e.g. "increase
drainage_capacity_index to 75", "increase green_cover_pct by 15") and see the
predicted BEFORE vs AFTER risk scores, using the exact same ML models + rule engine
as the live assessment -- so simulated results stay consistent with real predictions.
"""
from app.services.risk_engine import get_risk_engine


def simulate(zone_params: dict, modified_params: dict) -> dict:
    """
    zone_params: the zone's current full parameter set
    modified_params: dict of {field: new_value} overrides to apply hypothetically
    Returns: { before: {...scores}, after: {...scores}, deltas: {...}, modified_params }
    """
    engine = get_risk_engine()

    before = engine.assess_zone(zone_params)

    hypothetical_params = {**zone_params, **modified_params}
    after = engine.assess_zone(hypothetical_params)

    def pct_change(old, new):
        if old == 0:
            return 0.0
        return round(((new - old) / old) * 100, 1)

    deltas = {
        "flood_risk_score": {
            "before": before["flood_risk_score"],
            "after": after["flood_risk_score"],
            "change_pct": pct_change(before["flood_risk_score"], after["flood_risk_score"]),
        },
        "heat_risk_score": {
            "before": before["heat_risk_score"],
            "after": after["heat_risk_score"],
            "change_pct": pct_change(before["heat_risk_score"], after["heat_risk_score"]),
        },
        "accessibility_risk_score": {
            "before": before["accessibility_risk_score"],
            "after": after["accessibility_risk_score"],
            "change_pct": pct_change(before["accessibility_risk_score"], after["accessibility_risk_score"]),
        },
        "overall_vulnerability_score": {
            "before": before["overall_vulnerability_score"],
            "after": after["overall_vulnerability_score"],
            "change_pct": pct_change(
                before["overall_vulnerability_score"], after["overall_vulnerability_score"]
            ),
        },
    }

    return {
        "modified_params": modified_params,
        "before": before,
        "after": after,
        "deltas": deltas,
    }
