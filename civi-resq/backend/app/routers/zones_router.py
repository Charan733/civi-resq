"""
CIVI-RESQ Zones Router
------------------------
Core endpoints: list/filter zones (for map + table), zone detail (profile page),
create zones, trigger/refresh risk assessment (ML + rule engine + interventions),
and CSV upload for real-world datasets.
"""
import csv
import io
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Polygon, mapping

from app.database import get_db
from app.models.db_models import UrbanZone, RiskAssessment, Intervention, UserRole
from app.schemas.schemas import ZoneCreate, ZoneOut, ZoneWithRiskOut, ZoneParams, InterventionOut
from app.auth import require_role, get_current_user
from app.services.risk_engine import get_risk_engine
from app.services.intervention_engine import recommend_interventions

router = APIRouter(prefix="/api/zones", tags=["Urban Zones"])

ZONE_PARAM_FIELDS = [
    "avg_annual_rainfall_mm", "elevation_m", "drainage_capacity_index",
    "impervious_surface_pct", "population_density_per_km2", "road_accessibility_index",
    "green_cover_pct", "avg_land_surface_temp_c", "building_density_pct",
    "dist_to_hospital_km", "dist_to_school_km", "dist_to_emergency_service_km",
    "historical_flood_events_5yr",
]


def zone_to_params_dict(zone: UrbanZone) -> dict:
    return {f: getattr(zone, f) for f in ZONE_PARAM_FIELDS}


def _run_assessment_and_persist(db: Session, zone: UrbanZone) -> RiskAssessment:
    """Runs ML risk prediction + rule-based interventions for a zone, persists both,
    marks previous assessments as not-current."""
    engine = get_risk_engine()
    params = zone_to_params_dict(zone)
    result = engine.assess_zone(params)

    # mark old assessments as not current
    db.query(RiskAssessment).filter(
        RiskAssessment.zone_id == zone.id, RiskAssessment.is_current == True
    ).update({"is_current": False})

    assessment = RiskAssessment(
        zone_id=zone.id,
        flood_risk_score=result["flood_risk_score"],
        heat_risk_score=result["heat_risk_score"],
        accessibility_risk_score=result["accessibility_risk_score"],
        overall_vulnerability_score=result["overall_vulnerability_score"],
        flood_risk_category=result["flood_risk_category"],
        heat_risk_category=result["heat_risk_category"],
        accessibility_risk_category=result["accessibility_risk_category"],
        overall_risk_category=result["overall_risk_category"],
        explanation=result["explanation"],
        model_version=result["model_version"],
        is_current=True,
    )
    db.add(assessment)
    db.flush()  # get assessment.id before commit

    # Clear old interventions for this zone, generate fresh ones
    db.query(Intervention).filter(Intervention.zone_id == zone.id).delete()
    interventions = recommend_interventions(params, result)
    for iv in interventions:
        db.add(Intervention(
            zone_id=zone.id,
            assessment_id=assessment.id,
            intervention_type=iv["intervention_type"],
            priority_level=iv["priority_level"],
            estimated_cost_category=iv["estimated_cost_category"],
            expected_risk_reduction_pct=iv["expected_risk_reduction_pct"],
            affected_population=iv["affected_population"],
            reason=iv["reason"],
            priority_score=iv["priority_score"],
        ))

    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("", response_model=List[ZoneWithRiskOut])
def list_zones(
    db: Session = Depends(get_db),
    risk_category: Optional[str] = Query(None, description="low|moderate|high|critical"),
    city: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="search zone name/code"),
    min_score: Optional[float] = Query(None),
):
    """List all zones with their current risk assessment, for the map + zone table.
    Supports filtering by risk category, city, and free-text search."""
    query = db.query(UrbanZone)
    if city:
        query = query.filter(UrbanZone.city.ilike(f"%{city}%"))
    if search:
        query = query.filter(
            (UrbanZone.zone_name.ilike(f"%{search}%")) | (UrbanZone.zone_code.ilike(f"%{search}%"))
        )
    zones = query.all()

    out = []
    for z in zones:
        current = next((a for a in z.assessments if a.is_current), None)
        if risk_category and (not current or current.overall_risk_category != risk_category):
            continue
        if min_score and (not current or current.overall_vulnerability_score < min_score):
            continue

        shape = to_shape(z.geom)
        geometry = [[pt[0], pt[1]] for pt in mapping(shape)["coordinates"][0]]

        out.append(ZoneWithRiskOut(
            id=z.id, zone_code=z.zone_code, zone_name=z.zone_name, city=z.city, state=z.state,
            centroid_lat=z.centroid_lat, centroid_lng=z.centroid_lng,
            avg_annual_rainfall_mm=z.avg_annual_rainfall_mm, elevation_m=z.elevation_m,
            drainage_capacity_index=z.drainage_capacity_index, land_use_type=z.land_use_type,
            impervious_surface_pct=z.impervious_surface_pct,
            population_density_per_km2=z.population_density_per_km2,
            road_accessibility_index=z.road_accessibility_index, green_cover_pct=z.green_cover_pct,
            avg_land_surface_temp_c=z.avg_land_surface_temp_c, building_density_pct=z.building_density_pct,
            dist_to_hospital_km=z.dist_to_hospital_km, dist_to_school_km=z.dist_to_school_km,
            dist_to_emergency_service_km=z.dist_to_emergency_service_km,
            historical_flood_events_5yr=z.historical_flood_events_5yr, data_source=z.data_source,
            flood_risk_score=current.flood_risk_score if current else None,
            heat_risk_score=current.heat_risk_score if current else None,
            accessibility_risk_score=current.accessibility_risk_score if current else None,
            overall_vulnerability_score=current.overall_vulnerability_score if current else None,
            overall_risk_category=current.overall_risk_category if current else None,
            geometry=geometry,
        ))
    return out


@router.get("/{zone_id}", response_model=dict)
def get_zone_detail(zone_id: str, db: Session = Depends(get_db)):
    """Full zone profile: parameters, current risk assessment + explanation, interventions."""
    zone = db.query(UrbanZone).filter(UrbanZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    current = next((a for a in zone.assessments if a.is_current), None)
    interventions = sorted(zone.interventions, key=lambda i: i.priority_score, reverse=True)
    shape = to_shape(zone.geom)
    geometry = [[pt[0], pt[1]] for pt in mapping(shape)["coordinates"][0]]

    return {
        "zone": {
            "id": zone.id, "zone_code": zone.zone_code, "zone_name": zone.zone_name,
            "city": zone.city, "state": zone.state,
            "centroid_lat": zone.centroid_lat, "centroid_lng": zone.centroid_lng,
            "geometry": geometry, "data_source": zone.data_source,
            **zone_to_params_dict(zone),
            "land_use_type": zone.land_use_type,
        },
        "risk_assessment": {
            "flood_risk_score": current.flood_risk_score, "heat_risk_score": current.heat_risk_score,
            "accessibility_risk_score": current.accessibility_risk_score,
            "overall_vulnerability_score": current.overall_vulnerability_score,
            "flood_risk_category": current.flood_risk_category, "heat_risk_category": current.heat_risk_category,
            "accessibility_risk_category": current.accessibility_risk_category,
            "overall_risk_category": current.overall_risk_category,
            "explanation": current.explanation, "model_version": current.model_version,
            "assessed_at": current.created_at.isoformat(),
        } if current else None,
        "interventions": [
            {
                "id": iv.id, "intervention_type": iv.intervention_type, "priority_level": iv.priority_level,
                "estimated_cost_category": iv.estimated_cost_category,
                "expected_risk_reduction_pct": iv.expected_risk_reduction_pct,
                "affected_population": iv.affected_population, "reason": iv.reason,
                "priority_score": iv.priority_score,
            }
            for iv in interventions
        ],
    }


@router.post("", response_model=ZoneOut, status_code=201)
def create_zone(
    payload: ZoneCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(UserRole.admin, UserRole.civil_engineer)),
):
    """Create a new zone and immediately run risk assessment + interventions."""
    existing = db.query(UrbanZone).filter(UrbanZone.zone_code == payload.zone_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="zone_code already exists")

    poly = Polygon(payload.geometry)
    zone = UrbanZone(
        zone_code=payload.zone_code, zone_name=payload.zone_name, city=payload.city, state=payload.state,
        geom=from_shape(poly, srid=4326),
        centroid_lat=payload.centroid_lat, centroid_lng=payload.centroid_lng,
        avg_annual_rainfall_mm=payload.avg_annual_rainfall_mm, elevation_m=payload.elevation_m,
        drainage_capacity_index=payload.drainage_capacity_index, land_use_type=payload.land_use_type,
        impervious_surface_pct=payload.impervious_surface_pct,
        population_density_per_km2=payload.population_density_per_km2,
        road_accessibility_index=payload.road_accessibility_index, green_cover_pct=payload.green_cover_pct,
        avg_land_surface_temp_c=payload.avg_land_surface_temp_c, building_density_pct=payload.building_density_pct,
        dist_to_hospital_km=payload.dist_to_hospital_km, dist_to_school_km=payload.dist_to_school_km,
        dist_to_emergency_service_km=payload.dist_to_emergency_service_km,
        historical_flood_events_5yr=payload.historical_flood_events_5yr,
        data_source="manual",
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)

    _run_assessment_and_persist(db, zone)
    return zone


@router.post("/{zone_id}/assess", response_model=dict)
def reassess_zone(
    zone_id: str, db: Session = Depends(get_db),
    user=Depends(require_role(UserRole.admin, UserRole.civil_engineer)),
):
    """Re-run risk assessment + interventions for an existing zone (e.g. after editing params)."""
    zone = db.query(UrbanZone).filter(UrbanZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    assessment = _run_assessment_and_persist(db, zone)
    return {"status": "assessed", "overall_vulnerability_score": assessment.overall_vulnerability_score}


@router.post("/upload-csv", response_model=dict)
async def upload_zones_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(UserRole.admin, UserRole.civil_engineer)),
):
    """
    Upload real-world zone data via CSV. Expected columns match ZoneCreate fields
    (zone_code, zone_name, city, centroid_lat, centroid_lng, avg_annual_rainfall_mm, ...).
    Zones without an explicit polygon get a small auto-generated square around the centroid.
    """
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    created, errors = 0, []

    for i, row in enumerate(reader):
        try:
            lat, lng = float(row["centroid_lat"]), float(row["centroid_lng"])
            half = 0.003
            poly_coords = [
                [lng - half, lat - half], [lng + half, lat - half],
                [lng + half, lat + half], [lng - half, lat + half], [lng - half, lat - half],
            ]
            existing = db.query(UrbanZone).filter(UrbanZone.zone_code == row["zone_code"]).first()
            if existing:
                errors.append(f"Row {i+1}: zone_code {row['zone_code']} already exists, skipped")
                continue

            zone = UrbanZone(
                zone_code=row["zone_code"], zone_name=row["zone_name"],
                city=row.get("city", "Guntur"), state=row.get("state", "Andhra Pradesh"),
                geom=from_shape(Polygon(poly_coords), srid=4326),
                centroid_lat=lat, centroid_lng=lng,
                avg_annual_rainfall_mm=float(row["avg_annual_rainfall_mm"]),
                elevation_m=float(row["elevation_m"]),
                drainage_capacity_index=float(row["drainage_capacity_index"]),
                land_use_type=row.get("land_use_type", "residential"),
                impervious_surface_pct=float(row["impervious_surface_pct"]),
                population_density_per_km2=float(row["population_density_per_km2"]),
                road_accessibility_index=float(row["road_accessibility_index"]),
                green_cover_pct=float(row["green_cover_pct"]),
                avg_land_surface_temp_c=float(row["avg_land_surface_temp_c"]),
                building_density_pct=float(row["building_density_pct"]),
                dist_to_hospital_km=float(row["dist_to_hospital_km"]),
                dist_to_school_km=float(row["dist_to_school_km"]),
                dist_to_emergency_service_km=float(row["dist_to_emergency_service_km"]),
                historical_flood_events_5yr=int(row.get("historical_flood_events_5yr", 0)),
                data_source="uploaded_csv",
            )
            db.add(zone)
            db.flush()
            _run_assessment_and_persist(db, zone)
            created += 1
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")

    return {"created": created, "errors": errors}
