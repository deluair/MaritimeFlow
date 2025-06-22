"""
Port data models for maritime analytics and congestion tracking
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class PortSize(str, Enum):
    """Port size classification"""
    MAJOR = "major"           # >10M TEU annually
    LARGE = "large"           # 1-10M TEU annually  
    MEDIUM = "medium"         # 100K-1M TEU annually
    SMALL = "small"           # <100K TEU annually
    TERMINAL = "terminal"     # Specialized terminal


class PortType(str, Enum):
    """Port operational type"""
    CONTAINER = "container"
    BULK = "bulk"
    GENERAL_CARGO = "general_cargo"
    OIL_GAS = "oil_gas"
    PASSENGER = "passenger"
    FISHING = "fishing"
    NAVAL = "naval"
    MARINA = "marina"
    MULTIPURPOSE = "multipurpose"


class CongestionLevel(str, Enum):
    """Port congestion levels"""
    LOW = "low"           # 0-30% capacity
    MODERATE = "moderate" # 30-60% capacity
    HIGH = "high"         # 60-80% capacity
    CRITICAL = "critical" # 80-95% capacity
    BLOCKED = "blocked"   # >95% capacity


class Port(Base):
    """Port master data model"""
    __tablename__ = "ports"
    
    # Primary identification
    port_id = Column(String(20), primary_key=True)  # LOCODE or custom ID
    port_name = Column(String(255), nullable=False, index=True)
    unlocode = Column(String(5), unique=True, nullable=True, index=True)
    
    # Geographic data
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    region = Column(String(100), nullable=True, index=True)
    timezone = Column(String(50), nullable=True)
    
    # Port characteristics
    port_type = Column(String(50), nullable=True, index=True)
    port_size = Column(String(20), nullable=True, index=True)
    max_vessel_length = Column(Float, nullable=True)  # meters
    max_vessel_beam = Column(Float, nullable=True)    # meters
    max_draft = Column(Float, nullable=True)          # meters
    
    # Operational data
    total_berths = Column(Integer, nullable=True)
    container_berths = Column(Integer, nullable=True)
    bulk_berths = Column(Integer, nullable=True)
    annual_throughput = Column(Float, nullable=True)  # TEU or tons
    storage_capacity = Column(Float, nullable=True)   # TEU or tons
    
    # Infrastructure
    has_rail_connection = Column(Boolean, default=False)
    has_road_connection = Column(Boolean, default=True)
    has_pipeline = Column(Boolean, default=False)
    crane_capacity = Column(Float, nullable=True)     # tons
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    data_sources = Column(JSONB, default=list)
    tags = Column(JSONB, default=list)


class PortCongestion(Base):
    """Real-time port congestion and operational metrics"""
    __tablename__ = "port_congestion"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    port_id = Column(String(20), nullable=False, index=True)
    
    # Congestion metrics
    congestion_level = Column(String(20), nullable=True, index=True)
    congestion_score = Column(Float, nullable=True, index=True)  # 0-1 scale
    vessels_waiting = Column(Integer, default=0)
    vessels_at_berth = Column(Integer, default=0)
    vessels_departed_24h = Column(Integer, default=0)
    vessels_arrived_24h = Column(Integer, default=0)
    
    # Wait times
    average_wait_time = Column(Float, nullable=True)    # hours
    median_wait_time = Column(Float, nullable=True)     # hours
    max_wait_time = Column(Float, nullable=True)        # hours
    
    # Operational metrics
    berth_utilization = Column(Float, nullable=True)    # percentage
    throughput_24h = Column(Float, nullable=True)       # TEU or tons
    processing_rate = Column(Float, nullable=True)      # TEU/hour or tons/hour
    
    # Predictions
    predicted_congestion_1h = Column(Float, nullable=True)
    predicted_congestion_6h = Column(Float, nullable=True)
    predicted_congestion_24h = Column(Float, nullable=True)
    predicted_wait_time = Column(Float, nullable=True)  # hours
    
    # Weather and external factors
    weather_impact = Column(Float, nullable=True)       # 0-1 scale
    labor_issues = Column(Boolean, default=False)
    equipment_issues = Column(Boolean, default=False)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    data_collection_time = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    data_source = Column(String(50), nullable=False)
    calculation_metadata = Column(JSONB, default=dict)


class PortSchedule(Base):
    """Port vessel scheduling and berth allocation"""
    __tablename__ = "port_schedules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    port_id = Column(String(20), nullable=False, index=True)
    mmsi = Column(Integer, nullable=False, index=True)
    
    # Schedule data
    scheduled_arrival = Column(DateTime, nullable=True, index=True)
    actual_arrival = Column(DateTime, nullable=True, index=True)
    scheduled_departure = Column(DateTime, nullable=True, index=True)
    actual_departure = Column(DateTime, nullable=True, index=True)
    
    # Berth information
    berth_number = Column(String(20), nullable=True)
    berth_type = Column(String(50), nullable=True)
    priority_level = Column(Integer, default=5)  # 1-10 scale
    
    # Cargo information
    cargo_type = Column(String(100), nullable=True)
    estimated_cargo_volume = Column(Float, nullable=True)
    actual_cargo_volume = Column(Float, nullable=True)
    
    # Service metrics
    service_time = Column(Float, nullable=True)         # hours
    wait_time = Column(Float, nullable=True)            # hours
    
    # Status
    status = Column(String(50), nullable=True, index=True)  # scheduled, arrived, loading, loaded, departed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for API serialization
class PortBase(BaseModel):
    """Base port model"""
    port_id: str
    port_name: str
    unlocode: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country_code: str = Field(..., min_length=2, max_length=2)
    region: Optional[str] = None
    timezone: Optional[str] = None
    port_type: Optional[PortType] = None
    port_size: Optional[PortSize] = None
    max_vessel_length: Optional[float] = None
    max_vessel_beam: Optional[float] = None
    max_draft: Optional[float] = None
    total_berths: Optional[int] = None
    container_berths: Optional[int] = None
    bulk_berths: Optional[int] = None
    annual_throughput: Optional[float] = None
    storage_capacity: Optional[float] = None
    has_rail_connection: bool = False
    has_road_connection: bool = True
    has_pipeline: bool = False
    crane_capacity: Optional[float] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    class Config:
        orm_mode = True


class PortCreate(PortBase):
    """Model for creating ports"""
    pass


class PortUpdate(BaseModel):
    """Model for updating port information"""
    port_name: Optional[str] = None
    unlocode: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    region: Optional[str] = None
    timezone: Optional[str] = None
    port_type: Optional[PortType] = None
    port_size: Optional[PortSize] = None
    max_vessel_length: Optional[float] = None
    max_vessel_beam: Optional[float] = None
    max_draft: Optional[float] = None
    total_berths: Optional[int] = None
    container_berths: Optional[int] = None
    bulk_berths: Optional[int] = None
    annual_throughput: Optional[float] = None
    storage_capacity: Optional[float] = None
    has_rail_connection: Optional[bool] = None
    has_road_connection: Optional[bool] = None
    has_pipeline: Optional[bool] = None
    crane_capacity: Optional[float] = None


class PortResponse(PortBase):
    """Complete port response model"""
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    data_sources: List[str] = []
    tags: List[str] = []


class PortCongestionBase(BaseModel):
    """Base port congestion model"""
    port_id: str
    congestion_level: Optional[CongestionLevel] = None
    congestion_score: Optional[float] = Field(None, ge=0, le=1)
    vessels_waiting: int = 0
    vessels_at_berth: int = 0
    vessels_departed_24h: int = 0
    vessels_arrived_24h: int = 0
    average_wait_time: Optional[float] = None
    median_wait_time: Optional[float] = None
    max_wait_time: Optional[float] = None
    berth_utilization: Optional[float] = Field(None, ge=0, le=100)
    throughput_24h: Optional[float] = None
    processing_rate: Optional[float] = None
    predicted_congestion_1h: Optional[float] = Field(None, ge=0, le=1)
    predicted_congestion_6h: Optional[float] = Field(None, ge=0, le=1)
    predicted_congestion_24h: Optional[float] = Field(None, ge=0, le=1)
    predicted_wait_time: Optional[float] = None
    weather_impact: Optional[float] = Field(None, ge=0, le=1)
    labor_issues: bool = False
    equipment_issues: bool = False
    timestamp: datetime
    data_source: str
    
    class Config:
        orm_mode = True


class PortCongestionCreate(PortCongestionBase):
    """Model for creating congestion records"""
    calculation_metadata: Optional[Dict[str, Any]] = {}


class PortCongestionResponse(PortCongestionBase):
    """Complete congestion response model"""
    id: int
    data_collection_time: datetime
    calculation_metadata: Dict[str, Any] = {}


class PortScheduleBase(BaseModel):
    """Base port schedule model"""
    port_id: str
    mmsi: int
    scheduled_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    berth_number: Optional[str] = None
    berth_type: Optional[str] = None
    priority_level: int = Field(5, ge=1, le=10)
    cargo_type: Optional[str] = None
    estimated_cargo_volume: Optional[float] = None
    actual_cargo_volume: Optional[float] = None
    service_time: Optional[float] = None
    wait_time: Optional[float] = None
    status: Optional[str] = None
    
    class Config:
        orm_mode = True


class PortScheduleCreate(PortScheduleBase):
    """Model for creating schedule entries"""
    pass


class PortScheduleResponse(PortScheduleBase):
    """Complete schedule response model"""
    id: int
    created_at: datetime
    updated_at: datetime


class PortSummary(BaseModel):
    """Port operational summary"""
    port: PortResponse
    current_congestion: Optional[PortCongestionResponse] = None
    vessels_in_port: int = 0
    vessels_waiting: int = 0
    average_wait_time_7d: Optional[float] = None
    throughput_7d: Optional[float] = None
    efficiency_score: Optional[float] = None
    reliability_score: Optional[float] = None
    recent_alerts: List[str] = []


class PortComparison(BaseModel):
    """Comparison between multiple ports"""
    ports: List[PortSummary]
    comparison_metrics: Dict[str, Any]
    ranking_criteria: str
    timestamp: datetime 