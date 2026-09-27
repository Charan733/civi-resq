"""
CIVI-RESQ DB Seed Script
---------------------------
Creates all tables (via SQLAlchemy metadata) and loads the demo Guntur/Vijayawada
zone dataset, running full risk assessment + intervention generation for each zone
so the app works immediately on first run.

Usage: python3 scripts/seed_db.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shapely.geometry import Polygon
from geoalchemy2.shape import from_shape

from app.database import Base, engine, SessionLocal
from app.models.db_models import UrbanZone, User, UserRole
from app.auth import hash_password
from app.routers.zones_router import _run_assessment_and_persist


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


def seed_admin_user(db):
    existing = db.query(User).filter(User.email == "admin@civiresq.gov.in").first()
    if existing:
        print("Admin user already exists, skipping.")
        return
    admin = User(
        email="admin@civiresq.gov.in",
        full_name="CIVI-RESQ Admin",
        hashed_password=hash_password("Admin@12345"),
        role=UserRole.admin,
    )
    engineer = User(
        email="engineer@civiresq.gov.in",
        full_name="Demo Civil Engineer",
        hashed_password=hash_password("Engineer@12345"),
        role=UserRole.civil_engineer,
    )
    db.add_all([admin, engineer])
    db.commit()
    print("Seeded admin + civil_engineer demo users.")
    print("  admin@civiresq.gov.in / Admin@12345")
    print("  engineer@civiresq.gov.in / Engineer@12345")


def seed_zones(db):
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "demo_zones.json")
    with open(data_path) as f:
        payload = json.load(f)

    count = 0
    for z in payload["zones"]:
        existing = db.query(UrbanZone).filter(UrbanZone.zone_code == z["zone_code"]).first()
        if existing:
            continue
        poly = Polygon(z["geometry"])
        zone = UrbanZone(
            zone_code=z["zone_code"], zone_name=z["zone_name"], city=z["city"], state=z["state"],
            geom=from_shape(poly, srid=4326),
            centroid_lat=z["centroid_lat"], centroid_lng=z["centroid_lng"],
            avg_annual_rainfall_mm=z["avg_annual_rainfall_mm"], elevation_m=z["elevation_m"],
            drainage_capacity_index=z["drainage_capacity_index"], land_use_type=z["land_use_type"],
            impervious_surface_pct=z["impervious_surface_pct"],
            population_density_per_km2=z["population_density_per_km2"],
            road_accessibility_index=z["road_accessibility_index"], green_cover_pct=z["green_cover_pct"],
            avg_land_surface_temp_c=z["avg_land_surface_temp_c"], building_density_pct=z["building_density_pct"],
            dist_to_hospital_km=z["dist_to_hospital_km"], dist_to_school_km=z["dist_to_school_km"],
            dist_to_emergency_service_km=z["dist_to_emergency_service_km"],
            historical_flood_events_5yr=z["historical_flood_events_5yr"],
            data_source=z["data_source"],
        )
        db.add(zone)
        db.flush()
        _run_assessment_and_persist(db, zone)
        count += 1
    print(f"Seeded {count} zones with full risk assessments + interventions.")


if __name__ == "__main__":
    create_tables()
    db = SessionLocal()
    try:
        seed_admin_user(db)
        seed_zones(db)
    finally:
        db.close()
    print("Seed complete.")
