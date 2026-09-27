"""
CIVI-RESQ ML Training Data Generator
--------------------------------------
We only have 26 real demo zones -- not enough to train a model on. Real risk-prediction
projects in this situation do one of two things: (1) use historical disaster-event
records if available, or (2) generate a larger domain-grounded synthetic training set
using established civil-engineering risk relationships, and train on that.

We do (2) here, transparently. The formulas below encode real, well-established
engineering relationships (not arbitrary):

FLOOD/WATERLOGGING RISK increases with:
  + rainfall intensity            (more water input)
  + impervious surface %          (less infiltration -> more runoff, standard urban hydrology)
  + population/building density   (more impact per unit area)
  + historical flood frequency    (strong real-world predictor)
  - elevation                     (higher ground drains better -- basic topography)
  - drainage capacity index       (engineered mitigation)

URBAN HEAT RISK increases with:
  + impervious/building density   (urban heat island effect -- well documented)
  + land surface temperature
  - green cover %                 (vegetation cooling effect -- well documented)

ACCESSIBILITY/INFRASTRUCTURE RISK increases with:
  + distance to hospital/school/emergency services
  - road accessibility index

We add realistic Gaussian noise to each formula to simulate real-world measurement
variance and avoid the model simply memorizing a deterministic function.
"""
import numpy as np
import pandas as pd

np.random.seed(7)
N = 6000


def clip01_100(x):
    return np.clip(x, 0, 100)


def generate_training_set(n=N):
    rainfall = np.random.normal(1000, 220, n).clip(400, 2200)
    elevation = np.random.normal(28, 18, n).clip(2, 120)
    drainage = np.random.normal(50, 22, n).clip(2, 100)
    impervious = np.random.normal(60, 22, n).clip(5, 98)
    pop_density = np.random.normal(14000, 9000, n).clip(300, 45000)
    road_access = np.random.normal(58, 22, n).clip(5, 100)
    green_cover = np.random.normal(18, 12, n).clip(0, 60)
    lst = np.random.normal(34, 4, n).clip(24, 46)
    building_density = np.random.normal(50, 22, n).clip(5, 95)
    dist_hospital = np.random.exponential(2.2, n).clip(0.1, 15)
    dist_school = np.random.exponential(1.3, n).clip(0.05, 8)
    dist_emergency = np.random.exponential(2.0, n).clip(0.1, 12)
    flood_events_5yr = np.random.poisson(1.4, n).clip(0, 8)

    # --- FLOOD RISK (0-100) ---
    flood_raw = (
        0.028 * rainfall
        + 0.55 * impervious
        + 0.00035 * pop_density
        - 0.42 * elevation
        - 0.55 * drainage
        + 6.5 * flood_events_5yr
    )
    flood_risk = clip01_100(
        20 + (flood_raw - flood_raw.mean()) / flood_raw.std() * 22 + np.random.normal(0, 5, n)
    )

    # --- HEAT RISK (0-100) ---
    heat_raw = (
        1.9 * lst
        + 0.32 * impervious
        + 0.28 * building_density
        - 0.85 * green_cover
    )
    heat_risk = clip01_100(
        20 + (heat_raw - heat_raw.mean()) / heat_raw.std() * 22 + np.random.normal(0, 5, n)
    )

    # --- ACCESSIBILITY RISK (0-100), higher = worse access ---
    access_raw = (
        6.5 * dist_hospital + 8.0 * dist_school + 5.5 * dist_emergency - 0.55 * road_access
    )
    accessibility_risk = clip01_100(
        20 + (access_raw - access_raw.mean()) / access_raw.std() * 22 + np.random.normal(0, 5, n)
    )

    df = pd.DataFrame({
        "avg_annual_rainfall_mm": rainfall,
        "elevation_m": elevation,
        "drainage_capacity_index": drainage,
        "impervious_surface_pct": impervious,
        "population_density_per_km2": pop_density,
        "road_accessibility_index": road_access,
        "green_cover_pct": green_cover,
        "avg_land_surface_temp_c": lst,
        "building_density_pct": building_density,
        "dist_to_hospital_km": dist_hospital,
        "dist_to_school_km": dist_school,
        "dist_to_emergency_service_km": dist_emergency,
        "historical_flood_events_5yr": flood_events_5yr,
        "flood_risk_score": flood_risk,
        "heat_risk_score": heat_risk,
        "accessibility_risk_score": accessibility_risk,
    })
    return df


if __name__ == "__main__":
    df = generate_training_set()
    df.to_csv("backend/ml/training_data.csv", index=False)
    print(f"Generated {len(df)} training rows -> backend/ml/training_data.csv")
    print(df.describe().T[["mean", "std", "min", "max"]])
