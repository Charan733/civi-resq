"""
CIVI-RESQ Pydantic Schemas
Request/response models for API validation (separate from SQLAlchemy DB models).
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: Literal["admin", "civil_engineer", "viewer"] = "viewer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Zones ----------
class ZoneParams(BaseModel):
    """Raw civil-engineering input parameters for a zone. Used for creation, upload, and simulation."""
    avg_annual_rainfall_mm: float = Field(gt=0, le=5000)
    elevation_m: float = Field(ge=-10, le=3000)
    drainage_capacity_index: float = Field(ge=0, le=100)
    land_use_type: Literal["residential", "commercial", "industrial", "mixed", "slum", "institutional"]
    impervious_surface_pct: float = Field(ge=0, le=100)
    population_density_per_km2: float = Field(ge=0)
    road_accessibility_index: float = Field(ge=0, le=100)
    green_cover_pct: float = Field(ge=0, le=100)
    avg_land_surface_temp_c: float = Field(ge=-10, le=60)
    building_density_pct: float = Field(ge=0, le=100)
    dist_to_hospital_km: float = Field(ge=0)
    dist_to_school_km: float = Field(ge=0)
    dist_to_emergency_service_km: float = Field(ge=0)
    historical_flood_events_5yr: int = Field(ge=0, le=50)


class ZoneCreate(ZoneParams):
    zone_code: str
    zone_name: str
    city: str = "Guntur"
    state: str = "Andhra Pradesh"
    centroid_lat: float
    centroid_lng: float
    geometry: List[List[float]]  # polygon ring [[lng, lat], ...]


class ZoneOut(BaseModel):
    id: str
    zone_code: str
    zone_name: str
    city: str
    state: str
    centroid_lat: float
    centroid_lng: float
    avg_annual_rainfall_mm: float
    elevation_m: float
    drainage_capacity_index: float
    land_use_type: str
    impervious_surface_pct: float
    population_density_per_km2: float
    road_accessibility_index: float
    green_cover_pct: float
    avg_land_surface_temp_c: float
    building_density_pct: float
    dist_to_hospital_km: float
    dist_to_school_km: float
    dist_to_emergency_service_km: float
    historical_flood_events_5yr: int
    data_source: str

    class Config:
        from_attributes = True


class ZoneWithRiskOut(ZoneOut):
    """Zone + its current risk assessment, for map/list display."""
    flood_risk_score: Optional[float] = None
    heat_risk_score: Optional[float] = None
    accessibility_risk_score: Optional[float] = None
    overall_vulnerability_score: Optional[float] = None
    overall_risk_category: Optional[str] = None
    geometry: Optional[List[List[float]]] = None


# ---------- Risk Assessment ----------
class RiskAssessmentOut(BaseModel):
    id: str
    zone_id: str
    flood_risk_score: float
    heat_risk_score: float
    accessibility_risk_score: float
    overall_vulnerability_score: float
    flood_risk_category: str
    heat_risk_category: str
    accessibility_risk_category: str
    overall_risk_category: str
    explanation: dict
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ---------- Interventions ----------
class InterventionOut(BaseModel):
    id: Optional[str] = None
    intervention_type: str
    priority_level: str
    estimated_cost_category: str
    expected_risk_reduction_pct: float
    affected_population: int
    reason: str
    priority_score: float

    class Config:
        from_attributes = True


# ---------- Simulator ----------
class SimulationRequest(BaseModel):
    zone_id: str
    modified_params: dict = Field(
        description="Subset of zone parameters to hypothetically override, e.g. "
                    "{'drainage_capacity_index': 75, 'green_cover_pct': 30}"
    )


class SimulationResult(BaseModel):
    modified_params: dict
    before: dict
    after: dict
    deltas: dict


# ---------- Analytics ----------
class DashboardStats(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    total_zones: int
    critical_zones: int
    high_zones: int
    moderate_zones: int
    low_zones: int
    avg_vulnerability_score: float
    highest_risk_zone: Optional[str] = None
    highest_risk_score: Optional[float] = None
    total_interventions_recommended: int
    urgent_interventions: int
    model_metrics: dict


# ---------- AI Assistant ----------
class AssistantQuery(BaseModel):
    question: str
    zone_id: Optional[str] = None


class AssistantResponse(BaseModel):
    answer: str
    data_used: dict
