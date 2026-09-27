"""
CIVI-RESQ Database Models
Tables:
  - users              : auth + role-based access (admin / civil_engineer / viewer)
  - urban_zones        : spatial zone boundaries + raw input parameters
  - risk_assessments    : model-predicted + rule-based risk scores per zone (versioned by run)
  - interventions        : recommended civil interventions per zone/assessment
  - simulation_runs      : saved what-if simulator scenarios
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, Enum, Boolean, JSON, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    civil_engineer = "civil_engineer"
    viewer = "viewer"


class RiskCategory(str, enum.Enum):
    low = "low"          # green
    moderate = "moderate"  # yellow
    high = "high"          # orange
    critical = "critical"  # red


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UrbanZone(Base):
    """A geographic zone (ward/sector) with raw civil-engineering input parameters."""
    __tablename__ = "urban_zones"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    zone_code = Column(String, unique=True, index=True, nullable=False)
    zone_name = Column(String, nullable=False)
    city = Column(String, nullable=False, default="Guntur")
    state = Column(String, nullable=False, default="Andhra Pradesh")

    # Geometry: polygon boundary of the zone (WGS84 / EPSG:4326)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lng = Column(Float, nullable=False)

    # --- Raw input parameters (from data / uploaded CSV / demo generator) ---
    avg_annual_rainfall_mm = Column(Float, nullable=False)          # rainfall
    elevation_m = Column(Float, nullable=False)                     # elevation above sea level
    drainage_capacity_index = Column(Float, nullable=False)         # 0-100, higher = better drainage
    land_use_type = Column(String, nullable=False)                  # residential/commercial/industrial/mixed/slum
    impervious_surface_pct = Column(Float, nullable=False)          # % paved/built (affects runoff)
    population_density_per_km2 = Column(Float, nullable=False)
    road_accessibility_index = Column(Float, nullable=False)        # 0-100, higher = better connectivity
    green_cover_pct = Column(Float, nullable=False)
    avg_land_surface_temp_c = Column(Float, nullable=False)         # heat indicator
    building_density_pct = Column(Float, nullable=False)
    dist_to_hospital_km = Column(Float, nullable=False)
    dist_to_school_km = Column(Float, nullable=False)
    dist_to_emergency_service_km = Column(Float, nullable=False)
    historical_flood_events_5yr = Column(Integer, default=0)        # count in last 5 years

    data_source = Column(String, default="demo_synthetic")          # demo_synthetic | uploaded_csv | manual
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessments = relationship("RiskAssessment", back_populates="zone", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="zone", cascade="all, delete-orphan")


class RiskAssessment(Base):
    """Model-generated + rule-based risk scores for a zone (one row per assessment run)."""
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    zone_id = Column(UUID(as_uuid=False), ForeignKey("urban_zones.id"), nullable=False)

    flood_risk_score = Column(Float, nullable=False)         # 0-100, ML-predicted
    heat_risk_score = Column(Float, nullable=False)           # 0-100, ML-predicted
    accessibility_risk_score = Column(Float, nullable=False)  # 0-100, rule-based + ML
    overall_vulnerability_score = Column(Float, nullable=False)  # weighted composite

    flood_risk_category = Column(Enum(RiskCategory), nullable=False)
    heat_risk_category = Column(Enum(RiskCategory), nullable=False)
    accessibility_risk_category = Column(Enum(RiskCategory), nullable=False)
    overall_risk_category = Column(Enum(RiskCategory), nullable=False)

    # Explainability: SHAP / feature-importance breakdown stored as JSON
    # { "flood": [{"feature": "drainage_capacity_index", "impact": -0.32, "value": 40}, ...], "heat": [...], ... }
    explanation = Column(JSON, nullable=True)

    model_version = Column(String, default="v1")
    is_current = Column(Boolean, default=True)  # latest assessment for this zone
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("UrbanZone", back_populates="assessments")


class InterventionType(str, enum.Enum):
    drainage_improvement = "drainage_improvement"
    road_improvement = "road_improvement"
    green_infrastructure = "green_infrastructure"
    vegetation_increase = "vegetation_increase"
    water_management = "water_management"
    accessibility_improvement = "accessibility_improvement"
    stormwater_retention = "stormwater_retention"
    cool_roofing_pavement = "cool_roofing_pavement"


class PriorityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class CostCategory(str, enum.Enum):
    low = "low"          # < 10L INR equivalent
    medium = "medium"    # 10L - 1Cr
    high = "high"        # 1Cr - 10Cr
    very_high = "very_high"  # > 10Cr


class Intervention(Base):
    """A recommended civil-engineering intervention for a zone, ranked by priority."""
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    zone_id = Column(UUID(as_uuid=False), ForeignKey("urban_zones.id"), nullable=False)
    assessment_id = Column(UUID(as_uuid=False), ForeignKey("risk_assessments.id"), nullable=False)

    intervention_type = Column(Enum(InterventionType), nullable=False)
    priority_level = Column(Enum(PriorityLevel), nullable=False)
    estimated_cost_category = Column(Enum(CostCategory), nullable=False)
    expected_risk_reduction_pct = Column(Float, nullable=False)   # estimated % reduction in relevant risk
    affected_population = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    priority_score = Column(Float, nullable=False)   # composite ranking score (for sorting)

    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("UrbanZone", back_populates="interventions")


class SimulationRun(Base):
    """Saved what-if simulator scenario: modified params vs predicted before/after risk."""
    __tablename__ = "simulation_runs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    zone_id = Column(UUID(as_uuid=False), ForeignKey("urban_zones.id"), nullable=False)
    created_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)

    modified_params = Column(JSON, nullable=False)   # {"drainage_capacity_index": 75, ...}
    before_scores = Column(JSON, nullable=False)     # {"flood": 78, "heat": 55, "accessibility": 40, "overall": 62}
    after_scores = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
