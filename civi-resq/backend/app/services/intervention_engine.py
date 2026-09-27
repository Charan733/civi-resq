"""
CIVI-RESQ Intervention Recommendation Engine
-----------------------------------------------
Rule-based (explicitly NOT a black-box model) system that maps a zone's risk profile
to concrete civil-engineering interventions, then ranks them by a transparent
priority formula. Civil engineers need to be able to see and challenge exactly why
an intervention was recommended -- so every rule here is an explicit, documented
if/then condition grounded in standard urban-planning/civil-engineering practice.

INTERVENTION -> TRIGGER CONDITION mapping:
  drainage_improvement        : flood_risk high/critical AND drainage_capacity_index low
  stormwater_retention        : flood_risk high/critical AND impervious_surface_pct very high
  water_management            : flood_risk moderate+ AND historical_flood_events present
  green_infrastructure        : heat_risk high/critical AND green_cover_pct low
  vegetation_increase         : heat_risk moderate+ AND green_cover_pct low-moderate
  cool_roofing_pavement       : heat_risk high/critical AND building_density high
  road_improvement            : accessibility_risk high/critical AND road_accessibility_index low
  accessibility_improvement   : accessibility_risk moderate+ (general connectivity gaps)

PRIORITY SCORE formula (0-100, used purely for ranking/sorting):
  priority_score = 0.4 * risk_severity_weight
                  + 0.3 * expected_risk_reduction_pct
                  + 0.2 * population_impact_weight
                  - 0.1 * cost_penalty_weight

  This keeps the formula auditable and adjustable -- an engineer can retune the
  weights without touching any model.
"""
import math

RISK_SEVERITY_WEIGHT = {"low": 10, "moderate": 35, "high": 65, "critical": 95}
COST_PENALTY = {"low": 5, "medium": 15, "high": 30, "very_high": 45}


def _cost_category_for(intervention_type: str, zone_params: dict) -> str:
    """Rough cost bucket by intervention type + scale (population/area proxy)."""
    base_cost = {
        "drainage_improvement": "high",
        "stormwater_retention": "very_high",
        "water_management": "medium",
        "green_infrastructure": "medium",
        "vegetation_increase": "low",
        "cool_roofing_pavement": "medium",
        "road_improvement": "high",
        "accessibility_improvement": "medium",
    }[intervention_type]

    # Scale up cost bucket one level if population density is very high (larger works needed)
    order = ["low", "medium", "high", "very_high"]
    idx = order.index(base_cost)
    if zone_params.get("population_density_per_km2", 0) > 25000 and idx < 3:
        idx += 1
    return order[idx]


def _population_impact_weight(zone_params: dict) -> float:
    """Normalize population density into a 0-100 impact weight."""
    density = zone_params.get("population_density_per_km2", 0)
    return min(100, (density / 40000) * 100)


def _reason_text(intervention_type: str, zone_params: dict, risk_scores: dict) -> str:
    reasons = {
        "drainage_improvement": (
            f"Flood risk is {risk_scores['flood_risk_category']} "
            f"({risk_scores['flood_risk_score']:.0f}/100) with low drainage capacity "
            f"({zone_params['drainage_capacity_index']:.0f}/100). Upgrading stormwater "
            f"drains directly targets the strongest contributing factor."
        ),
        "stormwater_retention": (
            f"High impervious surface coverage ({zone_params['impervious_surface_pct']:.0f}%) "
            f"is driving excess runoff; retention basins/permeable pavement reduce peak "
            f"flood loading without full drainage rebuild."
        ),
        "water_management": (
            f"{int(zone_params.get('historical_flood_events_5yr', 0))} recorded flood "
            f"event(s) in the last 5 years indicate recurring waterlogging that needs "
            f"active water-management measures (retention, channeling, pumping stations)."
        ),
        "green_infrastructure": (
            f"Heat risk is {risk_scores['heat_risk_category']} "
            f"({risk_scores['heat_risk_score']:.0f}/100) with only "
            f"{zone_params['green_cover_pct']:.0f}% green cover. Parks/urban forestry "
            f"reduce the urban heat island effect and improve stormwater absorption."
        ),
        "vegetation_increase": (
            f"Green cover ({zone_params['green_cover_pct']:.0f}%) is below healthy "
            f"levels for this heat profile; street trees and roadside planting are a "
            f"low-cost first step to reduce surface temperatures."
        ),
        "cool_roofing_pavement": (
            f"High building density ({zone_params['building_density_pct']:.0f}%) with "
            f"elevated land surface temperature ({zone_params['avg_land_surface_temp_c']:.1f}°C) "
            f"means reflective roofing/pavement can meaningfully cut absorbed heat "
            f"where new green space isn't feasible."
        ),
        "road_improvement": (
            f"Accessibility risk is {risk_scores['accessibility_risk_category']} "
            f"({risk_scores['accessibility_risk_score']:.0f}/100) with a low road "
            f"accessibility index ({zone_params['road_accessibility_index']:.0f}/100), "
            f"limiting emergency-vehicle and general connectivity."
        ),
        "accessibility_improvement": (
            f"Distance to critical facilities (hospital "
            f"{zone_params['dist_to_hospital_km']:.1f}km, school "
            f"{zone_params['dist_to_school_km']:.1f}km, emergency "
            f"{zone_params['dist_to_emergency_service_km']:.1f}km) suggests the zone "
            f"would benefit from improved transit links or a new local facility."
        ),
    }
    return reasons[intervention_type]


def _expected_risk_reduction(intervention_type: str, risk_scores: dict) -> float:
    """Estimated % reduction in the RELEVANT risk score if intervention is implemented,
    based on typical documented ranges for these intervention classes (engineering
    literature ballpark, not a precise guarantee -- flagged as an ESTIMATE)."""
    ranges = {
        "drainage_improvement": (25, 40),
        "stormwater_retention": (15, 28),
        "water_management": (12, 22),
        "green_infrastructure": (15, 25),
        "vegetation_increase": (8, 15),
        "cool_roofing_pavement": (10, 18),
        "road_improvement": (20, 35),
        "accessibility_improvement": (10, 20),
    }
    lo, hi = ranges[intervention_type]
    # scale toward high end of range if underlying risk is more severe (more room to improve)
    relevant_risk_map = {
        "drainage_improvement": risk_scores["flood_risk_score"],
        "stormwater_retention": risk_scores["flood_risk_score"],
        "water_management": risk_scores["flood_risk_score"],
        "green_infrastructure": risk_scores["heat_risk_score"],
        "vegetation_increase": risk_scores["heat_risk_score"],
        "cool_roofing_pavement": risk_scores["heat_risk_score"],
        "road_improvement": risk_scores["accessibility_risk_score"],
        "accessibility_improvement": risk_scores["accessibility_risk_score"],
    }
    severity_frac = min(1.0, relevant_risk_map[intervention_type] / 100)
    return round(lo + (hi - lo) * severity_frac, 1)


def _priority_level(priority_score: float) -> str:
    if priority_score >= 75:
        return "urgent"
    if priority_score >= 55:
        return "high"
    if priority_score >= 35:
        return "medium"
    return "low"


def recommend_interventions(zone_params: dict, risk_scores: dict) -> list[dict]:
    """
    zone_params: raw zone input fields
    risk_scores: output of RiskEngine.assess_zone() (scores + categories)
    Returns list of intervention dicts, sorted by priority_score descending.
    """
    candidates = []

    flood_cat = risk_scores["flood_risk_category"]
    heat_cat = risk_scores["heat_risk_category"]
    access_cat = risk_scores["accessibility_risk_category"]

    triggered = []

    # --- Flood-related ---
    if flood_cat in ("high", "critical") and zone_params["drainage_capacity_index"] < 55:
        triggered.append("drainage_improvement")
    if flood_cat in ("high", "critical") and zone_params["impervious_surface_pct"] > 65:
        triggered.append("stormwater_retention")
    if flood_cat in ("moderate", "high", "critical") and zone_params.get("historical_flood_events_5yr", 0) >= 1:
        triggered.append("water_management")

    # --- Heat-related ---
    if heat_cat in ("high", "critical") and zone_params["green_cover_pct"] < 15:
        triggered.append("green_infrastructure")
    if heat_cat in ("moderate", "high", "critical") and zone_params["green_cover_pct"] < 25:
        triggered.append("vegetation_increase")
    if heat_cat in ("high", "critical") and zone_params["building_density_pct"] > 55:
        triggered.append("cool_roofing_pavement")

    # --- Accessibility-related ---
    if access_cat in ("high", "critical") and zone_params["road_accessibility_index"] < 55:
        triggered.append("road_improvement")
    if access_cat in ("moderate", "high", "critical"):
        triggered.append("accessibility_improvement")

    # Deduplicate while preserving order
    seen = set()
    triggered = [t for t in triggered if not (t in seen or seen.add(t))]

    for intervention_type in triggered:
        cost_cat = _cost_category_for(intervention_type, zone_params)
        risk_reduction = _expected_risk_reduction(intervention_type, risk_scores)
        pop_weight = _population_impact_weight(zone_params)

        relevant_severity = {
            "drainage_improvement": flood_cat, "stormwater_retention": flood_cat,
            "water_management": flood_cat,
            "green_infrastructure": heat_cat, "vegetation_increase": heat_cat,
            "cool_roofing_pavement": heat_cat,
            "road_improvement": access_cat, "accessibility_improvement": access_cat,
        }[intervention_type]
        severity_weight = RISK_SEVERITY_WEIGHT[relevant_severity]
        cost_penalty = COST_PENALTY[cost_cat]

        priority_score = round(
            0.4 * severity_weight + 0.3 * risk_reduction * 2.5 + 0.2 * pop_weight - 0.1 * cost_penalty,
            1,
        )
        priority_score = max(0, min(100, priority_score))

        candidates.append({
            "intervention_type": intervention_type,
            "priority_level": _priority_level(priority_score),
            "estimated_cost_category": cost_cat,
            "expected_risk_reduction_pct": risk_reduction,
            "affected_population": int(
                zone_params.get("population_density_per_km2", 0) * 0.36  # approx per zone area (~0.36 km2 zone)
            ),
            "reason": _reason_text(intervention_type, zone_params, risk_scores),
            "priority_score": priority_score,
        })

    candidates.sort(key=lambda c: c["priority_score"], reverse=True)
    return candidates
