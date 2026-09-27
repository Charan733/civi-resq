"""
CIVI-RESQ Independent Validation Against Observed Events
------------------------------------------------------------
This is the piece the pitch calls "validate the prediction using independent
observations." Critically, this is NOT the same as the train/test split in
train_models.py -- that split only proves the model learned the synthetic
training formula correctly. THIS script checks whether the model's predictions
line up with REAL, independently reported flood locations that were never
used anywhere in training.

METHOD:
  For each zone with a confirmed real observed flood/waterlogging event,
  check whether the model placed it in the "high" or "critical" flood-risk
  category. Report this as a hit rate, analogous to a recall/sensitivity
  metric: "of the zones we know actually flooded, what fraction did the
  model correctly flag as high-risk?"

  We also report the same check for a random control sample of zones WITHOUT
  a confirmed event, to make sure the model isn't just flagging everything
  as high-risk (which would make the recall number meaningless).

HONEST LIMITATIONS (state these explicitly in your report/defense):
  - Sample size is small (11 observed-event zones) -- this is a face-validity
    check, not a statistically powered validation study.
  - The observed events come from ONE major flood episode (Sept 2024) plus
    one municipal drainage report, not a systematic multi-year incident log.
  - This checks CATEGORY agreement (high/critical vs not), not precise score
    accuracy -- appropriate given the coarse-grained nature of news-report
    ground truth (we know an area flooded, not its exact flood depth/severity).
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.risk_engine import get_risk_engine

random.seed(11)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_zones():
    with open(os.path.join(DATA_DIR, "demo_zones.json")) as f:
        return {z["zone_code"]: z for z in json.load(f)["zones"]}


def load_observed_events():
    with open(os.path.join(DATA_DIR, "observed_waterlogging_events.json")) as f:
        return json.load(f)["events"]


ZONE_PARAM_FIELDS = [
    "avg_annual_rainfall_mm", "elevation_m", "drainage_capacity_index",
    "impervious_surface_pct", "population_density_per_km2", "road_accessibility_index",
    "green_cover_pct", "avg_land_surface_temp_c", "building_density_pct",
    "dist_to_hospital_km", "dist_to_school_km", "dist_to_emergency_service_km",
    "historical_flood_events_5yr",
]


def validate():
    zones = load_zones()
    events = load_observed_events()
    engine = get_risk_engine()

    observed_codes = {e["zone_code"] for e in events}
    all_codes = set(zones.keys())
    control_codes = list(all_codes - observed_codes)
    control_sample = random.sample(control_codes, min(len(observed_codes), len(control_codes)))

    def assess(zone_code):
        z = zones[zone_code]
        params = {f: z[f] for f in ZONE_PARAM_FIELDS}
        result = engine.assess_zone(params)
        return result["flood_risk_score"], result["flood_risk_category"]

    print("=" * 78)
    print("OBSERVED (real-world confirmed flood/waterlogging) ZONES")
    print("=" * 78)
    observed_hits = 0
    observed_results = []
    for code in sorted(observed_codes):
        if code not in zones:
            continue
        score, category = assess(code)
        is_hit = category in ("high", "critical")
        observed_hits += is_hit
        observed_results.append({"zone_code": code, "zone_name": zones[code]["zone_name"],
                                  "flood_score": round(score, 1), "category": category, "flagged_high_risk": is_hit})
        print(f"  {code:10} {zones[code]['zone_name']:28} score={score:5.1f}  category={category:9}  "
              f"{'✓ FLAGGED HIGH-RISK' if is_hit else '✗ missed'}")

    n_observed = len(observed_results)
    print(f"\n  Hit rate: {observed_hits}/{n_observed} observed-flood zones correctly flagged "
          f"high/critical = {100*observed_hits/n_observed:.0f}%")

    print("\n" + "=" * 78)
    print(f"CONTROL SAMPLE ({len(control_sample)} random zones, NO confirmed flood report)")
    print("=" * 78)
    control_hits = 0
    control_results = []
    for code in sorted(control_sample):
        score, category = assess(code)
        is_hit = category in ("high", "critical")
        control_hits += is_hit
        control_results.append({"zone_code": code, "zone_name": zones[code]["zone_name"],
                                 "flood_score": round(score, 1), "category": category, "flagged_high_risk": is_hit})
        print(f"  {code:10} {zones[code]['zone_name']:28} score={score:5.1f}  category={category:9}  "
              f"{'flagged high-risk' if is_hit else 'not flagged'}")

    n_control = len(control_results)
    print(f"\n  Control flag rate: {control_hits}/{n_control} = {100*control_hits/n_control:.0f}%")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"  Observed-flood zones flagged high/critical risk : {100*observed_hits/n_observed:.0f}% "
          f"({observed_hits}/{n_observed})")
    print(f"  Random control zones flagged high/critical risk : {100*control_hits/n_control:.0f}% "
          f"({control_hits}/{n_control})")
    gap = 100*observed_hits/n_observed - 100*control_hits/n_control
    print(f"  Gap (model discriminates real-flood zones)       : +{gap:.0f} percentage points")
    print("\n  NOTE: small sample (n={}), face-validity check against real reported".format(n_observed))
    print("  events -- not a substitute for a large-scale statistical validation study.")

    summary = {
        "observed_hit_rate_pct": round(100*observed_hits/n_observed, 1),
        "control_flag_rate_pct": round(100*control_hits/n_control, 1),
        "gap_percentage_points": round(gap, 1),
        "n_observed": n_observed, "n_control": n_control,
        "observed_results": observed_results, "control_results": control_results,
    }
    with open(os.path.join(DATA_DIR, "validation_results.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved full results -> backend/data/validation_results.json")
    return summary


if __name__ == "__main__":
    validate()
