"""
CIVI-RESQ Demo Data Generator
------------------------------
Generates a realistic (though synthetic) urban-zone dataset for Guntur & Vijayawada,
Andhra Pradesh -- a genuinely flood-prone Krishna-delta region with real monsoon
rainfall intensity, low elevation, and mixed dense urban land use.

WHY THESE NUMBERS ARE "REAL-WORLD GROUNDED" (not arbitrary random noise):
  - Elevation: Guntur/Vijayawada sit largely between 15-45m MSL (Krishna delta plain);
    a few zones near Guntur's low ridges reach ~60-70m.
  - Rainfall: SE/NE monsoon belt -- IMD long-period average for the district is
    ~900-1050mm/year, concentrated Jun-Oct.
  - Older core-city wards (e.g. near Old Guntur / One Town) have poor legacy drainage
    and high building density -> we model those zones with lower drainage_capacity_index.
  - Newer peripheral layouts (e.g. towards NRI-Guntur, Pothinamallayapalem-type areas)
    have wider roads and more open plots -> higher road_accessibility_index & green_cover.

Each zone is a small rectangular polygon (as a stand-in for a real ward boundary).
Replace `ZONE_SEEDS` + polygon generation with an actual ward shapefile / GeoJSON
import when real municipal boundary data is available -- the rest of the pipeline
(DB schema, ML models, APIs) does not need to change.
"""
import json
import random
from datetime import datetime

random.seed(42)

# Real approximate city centers (WGS84)
CITY_CENTERS = {
    "Guntur": (16.3067, 80.4365),
    "Vijayawada": (16.5062, 80.6480),
}

# Zone archetypes grounded in real urban patterns of these cities
ZONE_SEEDS = [
    # (name, city, land_use, character)
    ("Old Guntur / One Town", "Guntur", "residential", "old_dense_low_drainage"),
    ("Arundelpet", "Guntur", "commercial", "old_dense_low_drainage"),
    ("Lakshmipuram", "Guntur", "residential", "old_dense_low_drainage"),
    ("Kothapet", "Guntur", "mixed", "old_dense_low_drainage"),
    ("Brodipet", "Guntur", "commercial", "old_dense_low_drainage"),
    ("Nagarampalem", "Guntur", "industrial", "industrial_low_green"),
    ("Pattabhipuram", "Guntur", "residential", "mid_density"),
    ("Naaz Center", "Guntur", "commercial", "old_dense_low_drainage"),
    ("Gorantla", "Guntur", "residential", "peripheral_new"),
    ("Etukuru Road", "Guntur", "mixed", "mid_density"),
    ("Chuttugunta", "Guntur", "residential", "mid_density"),
    ("Syamala Nagar", "Guntur", "residential", "mid_density"),
    ("Stambalagaruvu", "Guntur", "slum", "low_income_low_drainage"),
    ("Kaikaluru Colony", "Guntur", "residential", "peripheral_new"),
    ("NRI Layout", "Guntur", "residential", "peripheral_new_green"),
    ("Pothinamallayapalem", "Guntur", "residential", "peripheral_new_green"),
    ("Vidyanagar", "Guntur", "residential", "mid_density"),
    ("Guntur Medical College Area", "Guntur", "institutional", "mid_density"),
    ("Machavaram", "Vijayawada", "residential", "old_dense_low_drainage"),
    ("Governorpet", "Vijayawada", "commercial", "old_dense_low_drainage"),
    ("Bhavanipuram", "Vijayawada", "residential", "mid_density"),
    ("Patamata", "Vijayawada", "mixed", "mid_density"),
    ("Benz Circle", "Vijayawada", "commercial", "mid_density"),
    ("Poranki", "Vijayawada", "residential", "peripheral_new_green"),
    ("Auto Nagar", "Vijayawada", "industrial", "industrial_low_green"),
    ("Ajit Singh Nagar", "Vijayawada", "residential", "low_income_low_drainage"),
]

CHARACTER_PROFILES = {
    "old_dense_low_drainage": dict(
        elevation=(14, 24), drainage=(15, 40), impervious=(75, 92), pop_density=(18000, 32000),
        road_access=(30, 55), green_cover=(3, 12), building_density=(70, 90), lst=(34, 39),
        flood_events=(2, 5),
    ),
    "industrial_low_green": dict(
        elevation=(16, 26), drainage=(30, 50), impervious=(70, 88), pop_density=(3000, 9000),
        road_access=(45, 65), green_cover=(2, 8), building_density=(55, 75), lst=(36, 41),
        flood_events=(1, 3),
    ),
    "mid_density": dict(
        elevation=(18, 32), drainage=(40, 65), impervious=(55, 75), pop_density=(9000, 18000),
        road_access=(50, 75), green_cover=(10, 22), building_density=(45, 65), lst=(32, 37),
        flood_events=(0, 3),
    ),
    "low_income_low_drainage": dict(
        elevation=(12, 20), drainage=(10, 30), impervious=(70, 85), pop_density=(20000, 38000),
        road_access=(20, 40), green_cover=(2, 8), building_density=(65, 85), lst=(34, 39),
        flood_events=(3, 6),
    ),
    "peripheral_new": dict(
        elevation=(25, 45), drainage=(55, 78), impervious=(35, 55), pop_density=(2500, 7000),
        road_access=(60, 85), green_cover=(15, 28), building_density=(25, 45), lst=(30, 35),
        flood_events=(0, 1),
    ),
    "peripheral_new_green": dict(
        elevation=(28, 50), drainage=(65, 88), impervious=(25, 45), pop_density=(1800, 5000),
        road_access=(65, 90), green_cover=(28, 45), building_density=(18, 35), lst=(28, 33),
        flood_events=(0, 1),
    ),
}


def jitter(rng_tuple, decimals=1):
    lo, hi = rng_tuple
    return round(random.uniform(lo, hi), decimals)


def make_polygon(lat, lng, size_deg=0.006):
    """Small rectangular polygon around a centroid, standing in for a real ward boundary."""
    half = size_deg / 2
    return [
        [lng - half, lat - half],
        [lng + half, lat - half],
        [lng + half, lat + half],
        [lng - half, lat + half],
        [lng - half, lat - half],
    ]


def generate_zones():
    zones = []
    for i, (name, city, land_use, character) in enumerate(ZONE_SEEDS):
        base_lat, base_lng = CITY_CENTERS[city]
        # Spread zones around the city center in a rough grid + randomness
        row, col = divmod(i, 6)
        lat = base_lat + (row - 2) * 0.012 + random.uniform(-0.004, 0.004)
        lng = base_lng + (col - 2.5) * 0.012 + random.uniform(-0.004, 0.004)

        profile = CHARACTER_PROFILES[character]
        rainfall = round(random.uniform(920, 1080), 0)  # IMD district-scale monsoon average band

        zone = {
            "zone_code": f"{city[:3].upper()}-{i+1:03d}",
            "zone_name": name,
            "city": city,
            "state": "Andhra Pradesh",
            "geometry": make_polygon(lat, lng),
            "centroid_lat": round(lat, 6),
            "centroid_lng": round(lng, 6),
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
            "historical_flood_events_5yr": random.randint(*profile["flood_events"]),
            "data_source": "demo_synthetic",
        }
        zones.append(zone)
    return zones


if __name__ == "__main__":
    zones = generate_zones()
    out = {
        "generated_at": datetime.utcnow().isoformat(),
        "note": "Synthetic demo dataset grounded in real Guntur/Vijayawada geography & IMD monsoon averages. Replace with real ward shapefiles + municipal sensor/survey data for production use.",
        "zones": zones,
    }
    with open("backend/data/demo_zones.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Generated {len(zones)} zones -> backend/data/demo_zones.json")
