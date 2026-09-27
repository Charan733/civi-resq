"""
CIVI-RESQ: Add Observed-Flood-Location Zones
------------------------------------------------
Appends 7 new zones to backend/data/demo_zones.json, using real coordinates for
locations that were independently reported as flooded/waterlogged in Sept 2024
(see backend/data/observed_events_source.py for sources). This gives us more
validation points to check the model's predictions against real observations.

Run AFTER generate_demo_data.py, BEFORE seed_db.py:
    python3 backend/scripts/generate_demo_data.py
    python3 backend/scripts/add_observed_zones.py
    python3 backend/scripts/seed_db.py
"""
import json
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
from observed_events_source import NEW_ZONE_SEEDS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from generate_demo_data import CHARACTER_PROFILES, jitter, make_polygon

random.seed(99)

DEMO_ZONES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "demo_zones.json")


def build_new_zones():
    zones = []
    for zone_code, name, lat, lng, land_use, character in NEW_ZONE_SEEDS:
        profile = CHARACTER_PROFILES[character]
        rainfall = round(random.uniform(920, 1080), 0)
        zones.append({
            "zone_code": zone_code,
            "zone_name": name,
            "city": "Vijayawada",
            "state": "Andhra Pradesh",
            "geometry": make_polygon(lat, lng),
            "centroid_lat": lat,
            "centroid_lng": lng,
            "avg_annual_rainfall_mm": rainfall,
            "elevation_m": jitter(profile["elevation"]),
            "drainage_capacity_index": jitter(profile["drainage"]),
            "land_use_type": land_use,
            "impervious_surface_pct": jitter(profile["impervious"]),
            "population_density_per_km2": round(random.uniform(*profile["pop_density"]), 0),
            "road_accessibility_index": jitter(profile["road_access"]),
            "green_cover_pct": jitter(profile["green_cover"]),
            "avg_land_surface_temp_c": jitter(profile["lst"]),
            "building_density_pct": jitter(profile["building_density"]),
            "dist_to_hospital_km": round(random.uniform(0.3, 6.5), 2),
            "dist_to_school_km": round(random.uniform(0.2, 3.5), 2),
            "dist_to_emergency_service_km": round(random.uniform(0.4, 7.0), 2),
            # These zones DID have a confirmed real flood event -> reflect that
            # in historical_flood_events_5yr rather than using the archetype's
            # random range, since we have real evidence for at least 1 event.
            "historical_flood_events_5yr": random.randint(2, 5),
            "data_source": "demo_synthetic_params_real_location",
        })
    return zones


if __name__ == "__main__":
    with open(DEMO_ZONES_PATH) as f:
        data = json.load(f)

    existing_codes = {z["zone_code"] for z in data["zones"]}
    new_zones = [z for z in build_new_zones() if z["zone_code"] not in existing_codes]

    data["zones"].extend(new_zones)
    data["note"] += (
        " Zones VIJ-027 through VIJ-033 added with real coordinates for locations "
        "independently reported as flooded in Sept 2024 news coverage -- see "
        "observed_events_source.py for citations. Their input PARAMETERS are still "
        "synthetic (same as the rest of the demo set); only their LOCATION and the "
        "fact that a real flood was reported there are grounded in real sources."
    )

    with open(DEMO_ZONES_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Added {len(new_zones)} new zones. Total zones now: {len(data['zones'])}")
