"""
Vessel data models for AIS tracking and maritime analytics
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class VesselType(str, Enum):
    """Standard vessel type classifications based on AIS codes"""
    CARGO = "cargo"
    TANKER = "tanker"
    PASSENGER = "passenger"
    FISHING = "fishing"
    TUG = "tug"
    PLEASURE_CRAFT = "pleasure_craft"
    HIGH_SPEED_CRAFT = "high_speed_craft"
    PILOT_VESSEL = "pilot_vessel"
    SEARCH_RESCUE = "search_rescue"
    PORT_TENDER = "port_tender"
    ANTI_POLLUTION = "anti_pollution"
    LAW_ENFORCEMENT = "law_enforcement"
    MEDICAL_TRANSPORT = "medical_transport"
    SPECIAL_CRAFT = "special_craft"
    MILITARY = "military"
    SAILING_VESSEL = "sailing_vessel"
    WIG = "wig"  # Wing in ground craft
    UNKNOWN = "unknown"


class NavigationStatus(str, Enum):
    """Vessel navigation status codes"""
    UNDER_WAY_USING_ENGINE = "under_way_using_engine"
    AT_ANCHOR = "at_anchor"
    NOT_UNDER_COMMAND = "not_under_command"
    RESTRICTED_MANEUVERABILITY = "restricted_maneuverability"
    CONSTRAINED_BY_DRAFT = "constrained_by_draft"
    MOORED = "moored"
    AGROUND = "aground"
    FISHING = "fishing"
    UNDER_WAY_SAILING = "under_way_sailing"
    RESERVED_HSC = "reserved_hsc"
    RESERVED_WIG = "reserved_wig"
    RESERVED_1 = "reserved_1"
    RESERVED_2 = "reserved_2"
    RESERVED_3 = "reserved_3"
    AIS_SART = "ais_sart"
    NOT_DEFINED = "not_defined"


class Vessel(Base):
    """Vessel master data model"""
    __tablename__ = "vessels"
    
    # Primary identification
    mmsi = Column(Integer, primary_key=True, index=True)
    imo = Column(String(10), unique=True, nullable=True, index=True)
    call_sign = Column(String(20), nullable=True, index=True)
    vessel_name = Column(String(255), nullable=True, index=True)
    
    # Classification
    vessel_type = Column(String(50), nullable=True, index=True)
    vessel_type_code = Column(Integer, nullable=True)
    cargo_type = Column(String(100), nullable=True)
    
    # Physical characteristics
    length = Column(Float, nullable=True)  # meters
    width = Column(Float, nullable=True)   # meters
    draft = Column(Float, nullable=True)   # meters
    gross_tonnage = Column(Float, nullable=True)
    deadweight = Column(Float, nullable=True)
    max_speed = Column(Float, nullable=True)  # knots
    
    # Registration and ownership
    flag_country = Column(String(2), nullable=True, index=True)  # ISO country code
    built_year = Column(Integer, nullable=True)
    owner = Column(String(255), nullable=True)
    operator = Column(String(255), nullable=True)
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    data_sources = Column(JSONB, default=list)
    tags = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True, index=True)


class VesselPosition(Base):
    """Real-time vessel position data from AIS"""
    __tablename__ = "vessel_positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(Integer, ForeignKey("vessels.mmsi"), nullable=False, index=True)
    
    # Position data
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    course_over_ground = Column(Float, nullable=True)  # degrees
    speed_over_ground = Column(Float, nullable=True)   # knots
    true_heading = Column(Float, nullable=True)        # degrees
    
    # Navigation data
    navigation_status = Column(String(50), nullable=True, index=True)
    rate_of_turn = Column(Float, nullable=True)        # degrees per minute
    position_accuracy = Column(Boolean, default=True)
    
    # Destination and ETA
    destination = Column(String(255), nullable=True, index=True)
    eta = Column(DateTime, nullable=True, index=True)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    message_timestamp = Column(DateTime, nullable=False)
    received_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Data quality and source
    data_source = Column(String(50), nullable=False, index=True)
    signal_strength = Column(Float, nullable=True)
    message_type = Column(Integer, nullable=True)
    
    # Calculated fields
    distance_from_shore = Column(Float, nullable=True)  # nautical miles
    nearest_port = Column(String(100), nullable=True)
    port_distance = Column(Float, nullable=True)        # nautical miles
    in_port_area = Column(Boolean, default=False, index=True)
    
    # Additional metadata
    raw_message = Column(Text, nullable=True)
    processing_metadata = Column(JSONB, default=dict)


# Pydantic models for API serialization
class VesselBase(BaseModel):
    """Base vessel model for API responses"""
    mmsi: int
    imo: Optional[str] = None
    call_sign: Optional[str] = None
    vessel_name: Optional[str] = None
    vessel_type: Optional[VesselType] = None
    vessel_type_code: Optional[int] = None
    cargo_type: Optional[str] = None
    length: Optional[float] = None
    width: Optional[float] = None
    draft: Optional[float] = None
    gross_tonnage: Optional[float] = None
    deadweight: Optional[float] = None
    max_speed: Optional[float] = None
    flag_country: Optional[str] = None
    built_year: Optional[int] = None
    owner: Optional[str] = None
    operator: Optional[str] = None
    
    @validator('mmsi')
    def validate_mmsi(cls, v):
        if not (100000000 <= v <= 999999999):
            raise ValueError('MMSI must be a 9-digit number')
        return v
    
    @validator('imo')
    def validate_imo(cls, v):
        if v and len(v) != 7:
            raise ValueError('IMO number must be 7 digits')
        return v
    
    class Config:
        orm_mode = True


class VesselCreate(VesselBase):
    """Model for creating new vessels"""
    pass


class VesselUpdate(BaseModel):
    """Model for updating vessel information"""
    vessel_name: Optional[str] = None
    vessel_type: Optional[VesselType] = None
    cargo_type: Optional[str] = None
    length: Optional[float] = None
    width: Optional[float] = None
    draft: Optional[float] = None
    gross_tonnage: Optional[float] = None
    deadweight: Optional[float] = None
    max_speed: Optional[float] = None
    flag_country: Optional[str] = None
    built_year: Optional[int] = None
    owner: Optional[str] = None
    operator: Optional[str] = None


class VesselResponse(VesselBase):
    """Complete vessel response model"""
    first_seen: datetime
    last_updated: datetime
    data_sources: List[str] = []
    tags: List[str] = []
    is_active: bool = True


class VesselPositionBase(BaseModel):
    """Base vessel position model"""
    mmsi: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    course_over_ground: Optional[float] = Field(None, ge=0, lt=360)
    speed_over_ground: Optional[float] = Field(None, ge=0)
    true_heading: Optional[float] = Field(None, ge=0, lt=360)
    navigation_status: Optional[NavigationStatus] = None
    rate_of_turn: Optional[float] = None
    position_accuracy: bool = True
    destination: Optional[str] = None
    eta: Optional[datetime] = None
    timestamp: datetime
    data_source: str
    
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


class VesselPositionCreate(VesselPositionBase):
    """Model for creating vessel positions"""
    message_timestamp: datetime
    signal_strength: Optional[float] = None
    message_type: Optional[int] = None
    raw_message: Optional[str] = None


class VesselPositionResponse(VesselPositionBase):
    """Complete vessel position response"""
    id: int
    message_timestamp: datetime
    received_timestamp: datetime
    signal_strength: Optional[float] = None
    message_type: Optional[int] = None
    distance_from_shore: Optional[float] = None
    nearest_port: Optional[str] = None
    port_distance: Optional[float] = None
    in_port_area: bool = False
    processing_metadata: Dict[str, Any] = {}


class VesselTrack(BaseModel):
    """Vessel track containing multiple positions"""
    vessel: VesselResponse
    positions: List[VesselPositionResponse]
    start_time: datetime
    end_time: datetime
    total_distance: Optional[float] = None  # nautical miles
    average_speed: Optional[float] = None   # knots
    ports_visited: List[str] = []
    route_efficiency: Optional[float] = None  # percentage


class VesselSummary(BaseModel):
    """Summary statistics for vessel operations"""
    mmsi: int
    vessel_name: Optional[str] = None
    total_positions: int
    first_position: datetime
    last_position: datetime
    total_distance: float = 0.0  # nautical miles
    average_speed: float = 0.0   # knots
    max_speed: float = 0.0       # knots
    ports_visited: int = 0
    time_at_sea: float = 0.0     # hours
    time_in_port: float = 0.0    # hours
    fuel_efficiency_score: Optional[float] = None
    route_optimization_score: Optional[float] = None
    safety_score: Optional[float] = None 