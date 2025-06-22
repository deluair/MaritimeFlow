"""
Route optimization and shipping lane models for maritime analytics
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class RouteType(str, Enum):
    """Route type classifications"""
    CONTAINER = "container"
    BULK_CARGO = "bulk_cargo"
    TANKER = "tanker"
    PASSENGER = "passenger"
    FERRY = "ferry"
    CRUISE = "cruise"
    FISHING = "fishing"
    RESEARCH = "research"
    MILITARY = "military"
    GENERAL = "general"


class RouteStatus(str, Enum):
    """Route operational status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SEASONAL = "seasonal"
    EMERGENCY_ONLY = "emergency_only"
    UNDER_CONSTRUCTION = "under_construction"
    DECOMMISSIONED = "decommissioned"


class RouteRisk(str, Enum):
    """Route risk levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    PROHIBITED = "prohibited"


class Route(Base):
    """Maritime shipping route master data"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String(50), unique=True, nullable=False, index=True)
    route_name = Column(String(255), nullable=False, index=True)
    
    # Route endpoints
    origin_port = Column(String(20), nullable=False, index=True)
    destination_port = Column(String(20), nullable=False, index=True)
    
    # Route characteristics
    route_type = Column(String(50), nullable=True, index=True)
    route_status = Column(String(50), default="active", index=True)
    distance_nm = Column(Float, nullable=True)           # nautical miles
    estimated_duration = Column(Float, nullable=True)    # hours
    
    # Geographic data
    waypoints = Column(JSONB, default=list)              # List of [lat, lon] coordinates
    chokepoints = Column(JSONB, default=list)            # Critical passage points
    alternative_routes = Column(JSONB, default=list)     # Alternative route IDs
    
    # Operational data
    typical_vessel_types = Column(JSONB, default=list)
    average_vessels_per_day = Column(Float, nullable=True)
    peak_season_months = Column(JSONB, default=list)
    seasonal_restrictions = Column(JSONB, default=dict)
    
    # Risk and restrictions
    risk_level = Column(String(20), nullable=True, index=True)
    geopolitical_risk = Column(Float, nullable=True)     # 0-1 scale
    weather_risk = Column(Float, nullable=True)          # 0-1 scale
    piracy_risk = Column(Float, nullable=True)           # 0-1 scale
    environmental_restrictions = Column(JSONB, default=list)
    
    # Economic data
    average_fuel_cost = Column(Float, nullable=True)     # USD
    average_port_fees = Column(Float, nullable=True)     # USD
    canal_fees = Column(Float, nullable=True)            # USD
    total_cost_estimate = Column(Float, nullable=True)   # USD
    
    # Performance metrics
    schedule_reliability = Column(Float, nullable=True)  # percentage
    average_delay = Column(Float, nullable=True)         # hours
    congestion_probability = Column(Float, nullable=True) # 0-1 scale
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    data_sources = Column(JSONB, default=list)
    tags = Column(JSONB, default=list)


class RouteSegment(Base):
    """Individual segments of shipping routes"""
    __tablename__ = "route_segments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String(50), nullable=False, index=True)
    segment_order = Column(Integer, nullable=False)
    
    # Segment endpoints
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    
    # Segment characteristics
    segment_name = Column(String(255), nullable=True)
    segment_type = Column(String(50), nullable=True)     # open_ocean, coastal, canal, strait, port_approach
    distance_nm = Column(Float, nullable=True)
    typical_speed = Column(Float, nullable=True)         # knots
    estimated_duration = Column(Float, nullable=True)    # hours
    
    # Restrictions and conditions
    max_draft = Column(Float, nullable=True)             # meters
    max_beam = Column(Float, nullable=True)              # meters
    max_length = Column(Float, nullable=True)            # meters
    tide_dependent = Column(Boolean, default=False)
    pilot_required = Column(Boolean, default=False)
    
    # Risk factors
    weather_exposure = Column(Float, nullable=True)      # 0-1 scale
    traffic_density = Column(Float, nullable=True)       # vessels per day
    accident_probability = Column(Float, nullable=True)  # 0-1 scale
    
    # Regulatory
    regulatory_zone = Column(String(100), nullable=True)
    speed_limits = Column(JSONB, default=list)
    environmental_zones = Column(JSONB, default=list)
    
    # Metadata
    segment_data = Column(JSONB, default=dict)


class RouteOptimization(Base):
    """Route optimization recommendations and alternatives"""
    __tablename__ = "route_optimizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    optimization_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Request context
    mmsi = Column(Integer, nullable=True, index=True)
    vessel_type = Column(String(50), nullable=True)
    cargo_type = Column(String(100), nullable=True)
    departure_time = Column(DateTime, nullable=False, index=True)
    
    # Route comparison
    original_route = Column(String(50), nullable=True)
    recommended_route = Column(String(50), nullable=False)
    alternative_routes = Column(JSONB, default=list)
    
    # Optimization criteria
    optimization_type = Column(String(50), nullable=False)  # fuel, time, cost, safety, environment
    weather_considered = Column(Boolean, default=True)
    traffic_considered = Column(Boolean, default=True)
    cost_considered = Column(Boolean, default=True)
    
    # Predicted improvements
    fuel_savings_percent = Column(Float, nullable=True)
    time_savings_hours = Column(Float, nullable=True)
    cost_savings_usd = Column(Float, nullable=True)
    emissions_reduction_percent = Column(Float, nullable=True)
    risk_reduction_percent = Column(Float, nullable=True)
    
    # Route details
    optimized_waypoints = Column(JSONB, default=list)
    total_distance_nm = Column(Float, nullable=True)
    estimated_duration_hours = Column(Float, nullable=True)
    estimated_fuel_consumption = Column(Float, nullable=True)
    estimated_total_cost = Column(Float, nullable=True)
    
    # Confidence and validation
    confidence_score = Column(Float, nullable=True)      # 0-1 scale
    model_version = Column(String(50), nullable=True)
    validation_status = Column(String(50), nullable=True)
    
    # Usage tracking
    recommendation_accepted = Column(Boolean, nullable=True)
    actual_performance = Column(JSONB, default=dict)
    feedback_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# Pydantic models for API serialization
class RouteBase(BaseModel):
    """Base route model"""
    route_id: str
    route_name: str
    origin_port: str
    destination_port: str
    route_type: Optional[RouteType] = None
    route_status: RouteStatus = RouteStatus.ACTIVE
    distance_nm: Optional[float] = None
    estimated_duration: Optional[float] = None
    waypoints: List[Tuple[float, float]] = []
    chokepoints: List[str] = []
    alternative_routes: List[str] = []
    typical_vessel_types: List[str] = []
    average_vessels_per_day: Optional[float] = None
    peak_season_months: List[int] = []
    seasonal_restrictions: Dict[str, Any] = {}
    risk_level: Optional[RouteRisk] = None
    geopolitical_risk: Optional[float] = Field(None, ge=0, le=1)
    weather_risk: Optional[float] = Field(None, ge=0, le=1)
    piracy_risk: Optional[float] = Field(None, ge=0, le=1)
    environmental_restrictions: List[str] = []
    average_fuel_cost: Optional[float] = None
    average_port_fees: Optional[float] = None
    canal_fees: Optional[float] = None
    total_cost_estimate: Optional[float] = None
    schedule_reliability: Optional[float] = Field(None, ge=0, le=100)
    average_delay: Optional[float] = None
    congestion_probability: Optional[float] = Field(None, ge=0, le=1)
    tags: List[str] = []
    
    @validator('waypoints')
    def validate_waypoints(cls, v):
        for waypoint in v:
            if len(waypoint) != 2:
                raise ValueError('Waypoint must be [latitude, longitude]')
            lat, lon = waypoint
            if not -90 <= lat <= 90:
                raise ValueError('Latitude must be between -90 and 90')
            if not -180 <= lon <= 180:
                raise ValueError('Longitude must be between -180 and 180')
        return v
    
    class Config:
        orm_mode = True


class RouteCreate(RouteBase):
    """Model for creating routes"""
    pass


class RouteUpdate(BaseModel):
    """Model for updating routes"""
    route_name: Optional[str] = None
    route_type: Optional[RouteType] = None
    route_status: Optional[RouteStatus] = None
    distance_nm: Optional[float] = None
    estimated_duration: Optional[float] = None
    waypoints: Optional[List[Tuple[float, float]]] = None
    chokepoints: Optional[List[str]] = None
    alternative_routes: Optional[List[str]] = None
    typical_vessel_types: Optional[List[str]] = None
    average_vessels_per_day: Optional[float] = None
    peak_season_months: Optional[List[int]] = None
    seasonal_restrictions: Optional[Dict[str, Any]] = None
    risk_level: Optional[RouteRisk] = None
    geopolitical_risk: Optional[float] = Field(None, ge=0, le=1)
    weather_risk: Optional[float] = Field(None, ge=0, le=1)
    piracy_risk: Optional[float] = Field(None, ge=0, le=1)
    environmental_restrictions: Optional[List[str]] = None
    average_fuel_cost: Optional[float] = None
    average_port_fees: Optional[float] = None
    canal_fees: Optional[float] = None
    total_cost_estimate: Optional[float] = None
    schedule_reliability: Optional[float] = Field(None, ge=0, le=100)
    average_delay: Optional[float] = None
    congestion_probability: Optional[float] = Field(None, ge=0, le=1)
    tags: Optional[List[str]] = None


class RouteResponse(RouteBase):
    """Complete route response model"""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    data_sources: List[str] = []


class RouteSegmentBase(BaseModel):
    """Base route segment model"""
    route_id: str
    segment_order: int
    start_latitude: float = Field(..., ge=-90, le=90)
    start_longitude: float = Field(..., ge=-180, le=180)
    end_latitude: float = Field(..., ge=-90, le=90)
    end_longitude: float = Field(..., ge=-180, le=180)
    segment_name: Optional[str] = None
    segment_type: Optional[str] = None
    distance_nm: Optional[float] = None
    typical_speed: Optional[float] = None
    estimated_duration: Optional[float] = None
    max_draft: Optional[float] = None
    max_beam: Optional[float] = None
    max_length: Optional[float] = None
    tide_dependent: bool = False
    pilot_required: bool = False
    weather_exposure: Optional[float] = Field(None, ge=0, le=1)
    traffic_density: Optional[float] = None
    accident_probability: Optional[float] = Field(None, ge=0, le=1)
    regulatory_zone: Optional[str] = None
    speed_limits: List[Dict[str, Any]] = []
    environmental_zones: List[str] = []
    segment_data: Dict[str, Any] = {}
    
    class Config:
        orm_mode = True


class RouteSegmentCreate(RouteSegmentBase):
    """Model for creating route segments"""
    pass


class RouteSegmentResponse(RouteSegmentBase):
    """Complete route segment response model"""
    id: int


class RouteOptimizationRequest(BaseModel):
    """Route optimization request model"""
    mmsi: Optional[int] = None
    vessel_type: Optional[str] = None
    cargo_type: Optional[str] = None
    origin_port: str
    destination_port: str
    departure_time: datetime
    optimization_type: str = "fuel"  # fuel, time, cost, safety, environment
    weather_consideration: bool = True
    traffic_consideration: bool = True
    cost_consideration: bool = True
    constraints: Dict[str, Any] = {}


class RouteOptimizationResponse(BaseModel):
    """Route optimization response model"""
    optimization_id: str
    original_route: Optional[str] = None
    recommended_route: str
    alternative_routes: List[str] = []
    fuel_savings_percent: Optional[float] = None
    time_savings_hours: Optional[float] = None
    cost_savings_usd: Optional[float] = None
    emissions_reduction_percent: Optional[float] = None
    risk_reduction_percent: Optional[float] = None
    optimized_waypoints: List[Tuple[float, float]] = []
    total_distance_nm: Optional[float] = None
    estimated_duration_hours: Optional[float] = None
    estimated_fuel_consumption: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    model_version: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class RouteAnalytics(BaseModel):
    """Route performance analytics"""
    route_id: str
    route_name: str
    total_vessels_30d: int = 0
    average_transit_time: Optional[float] = None  # hours
    schedule_reliability: Optional[float] = None  # percentage
    fuel_efficiency: Optional[float] = None       # L/NM
    cost_efficiency: Optional[float] = None       # USD/NM
    safety_score: Optional[float] = None          # 0-100
    environmental_score: Optional[float] = None   # 0-100
    congestion_frequency: Optional[float] = None  # percentage of time
    weather_delays: Optional[float] = None        # hours per month
    recent_incidents: int = 0
    user_satisfaction: Optional[float] = None     # 1-5 scale


class RouteComparison(BaseModel):
    """Comparison between multiple routes"""
    routes: List[RouteResponse]
    comparison_criteria: List[str]
    best_for_fuel: Optional[str] = None
    best_for_time: Optional[str] = None
    best_for_cost: Optional[str] = None
    best_for_safety: Optional[str] = None
    comparison_matrix: Dict[str, Dict[str, Any]] = {}
    recommendations: List[str] = [] 