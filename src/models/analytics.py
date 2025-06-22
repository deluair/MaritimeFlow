"""
Analytics and metrics models for supply chain and maritime performance tracking
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class MetricType(str, Enum):
    """Metric type classifications"""
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"
    COST = "cost"
    ENVIRONMENTAL = "environmental"
    RELIABILITY = "reliability"
    UTILIZATION = "utilization"
    QUALITY = "quality"


class TimeFrame(str, Enum):
    """Time frame for analytics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SupplyChainMetrics(Base):
    """Supply chain performance metrics"""
    __tablename__ = "supply_chain_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_id = Column(String(50), nullable=False, index=True)
    
    # Time and scope
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, index=True)
    region = Column(String(100), nullable=True, index=True)
    trade_lane = Column(String(100), nullable=True, index=True)
    
    # Overall supply chain health
    supply_chain_health_score = Column(Float, nullable=True)  # 0-100 scale
    disruption_index = Column(Float, nullable=True)           # 0-1 scale
    resilience_score = Column(Float, nullable=True)           # 0-100 scale
    
    # Vessel and cargo metrics
    total_vessels_tracked = Column(Integer, default=0)
    active_vessels = Column(Integer, default=0)
    vessels_delayed = Column(Integer, default=0)
    total_cargo_volume = Column(Float, nullable=True)         # TEU or tons
    delayed_cargo_volume = Column(Float, nullable=True)       # TEU or tons
    
    # Timing metrics
    average_transit_time = Column(Float, nullable=True)       # hours
    schedule_reliability = Column(Float, nullable=True)       # percentage
    average_delay = Column(Float, nullable=True)              # hours
    on_time_performance = Column(Float, nullable=True)        # percentage
    
    # Cost metrics
    average_shipping_cost = Column(Float, nullable=True)      # USD per TEU
    cost_variance = Column(Float, nullable=True)              # percentage
    fuel_cost_index = Column(Float, nullable=True)            # indexed value
    
    # Capacity and utilization
    total_capacity = Column(Float, nullable=True)             # TEU or tons
    utilized_capacity = Column(Float, nullable=True)          # TEU or tons
    capacity_utilization = Column(Float, nullable=True)       # percentage
    empty_container_ratio = Column(Float, nullable=True)      # percentage
    
    # Risk metrics
    geopolitical_risk_score = Column(Float, nullable=True)    # 0-1 scale
    weather_impact_score = Column(Float, nullable=True)       # 0-1 scale
    security_risk_score = Column(Float, nullable=True)        # 0-1 scale
    
    # Environmental metrics
    total_emissions = Column(Float, nullable=True)            # tons CO2
    emissions_per_teu = Column(Float, nullable=True)          # kg CO2 per TEU
    fuel_efficiency = Column(Float, nullable=True)            # L per NM
    
    # Quality metrics
    cargo_damage_rate = Column(Float, nullable=True)          # percentage
    customs_clearance_time = Column(Float, nullable=True)     # hours
    documentation_accuracy = Column(Float, nullable=True)     # percentage
    
    # Metadata
    data_sources = Column(JSONB, default=list)
    calculation_metadata = Column(JSONB, default=dict)


class PortMetrics(Base):
    """Port operational and performance metrics"""
    __tablename__ = "port_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    port_id = Column(String(20), nullable=False, index=True)
    
    # Time and context
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, index=True)
    
    # Operational metrics
    vessels_processed = Column(Integer, default=0)
    total_throughput = Column(Float, nullable=True)           # TEU or tons
    average_turnaround_time = Column(Float, nullable=True)    # hours
    berth_utilization = Column(Float, nullable=True)          # percentage
    crane_utilization = Column(Float, nullable=True)          # percentage
    
    # Efficiency metrics
    moves_per_hour = Column(Float, nullable=True)             # container moves per hour
    productivity_index = Column(Float, nullable=True)         # indexed value
    equipment_availability = Column(Float, nullable=True)     # percentage
    labor_efficiency = Column(Float, nullable=True)           # indexed value
    
    # Congestion metrics
    average_waiting_time = Column(Float, nullable=True)       # hours
    peak_waiting_time = Column(Float, nullable=True)          # hours
    congestion_score = Column(Float, nullable=True)           # 0-1 scale
    queue_length = Column(Integer, default=0)
    
    # Service quality
    schedule_adherence = Column(Float, nullable=True)         # percentage
    service_reliability = Column(Float, nullable=True)        # percentage
    customer_satisfaction = Column(Float, nullable=True)      # 1-5 scale
    
    # Cost metrics
    handling_cost_per_teu = Column(Float, nullable=True)      # USD per TEU
    storage_cost_per_day = Column(Float, nullable=True)       # USD per TEU per day
    total_port_charges = Column(Float, nullable=True)         # USD
    
    # Safety and security
    safety_incidents = Column(Integer, default=0)
    security_breaches = Column(Integer, default=0)
    environmental_violations = Column(Integer, default=0)
    accident_rate = Column(Float, nullable=True)              # incidents per 1000 moves
    
    # Environmental metrics
    emissions_per_move = Column(Float, nullable=True)         # kg CO2 per move
    energy_consumption = Column(Float, nullable=True)         # kWh
    waste_generation = Column(Float, nullable=True)           # tons
    
    # Infrastructure metrics
    quay_length_utilization = Column(Float, nullable=True)    # percentage
    storage_area_utilization = Column(Float, nullable=True)   # percentage
    equipment_downtime = Column(Float, nullable=True)         # hours
    
    # Metadata
    calculation_metadata = Column(JSONB, default=dict)


class VesselMetrics(Base):
    """Individual vessel performance metrics"""
    __tablename__ = "vessel_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(Integer, nullable=False, index=True)
    
    # Time and context
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, index=True)
    
    # Operational metrics
    total_distance = Column(Float, nullable=True)             # nautical miles
    total_voyage_time = Column(Float, nullable=True)          # hours
    port_time = Column(Float, nullable=True)                  # hours
    sea_time = Column(Float, nullable=True)                   # hours
    ports_visited = Column(Integer, default=0)
    
    # Performance metrics
    average_speed = Column(Float, nullable=True)              # knots
    schedule_performance = Column(Float, nullable=True)       # percentage
    fuel_efficiency = Column(Float, nullable=True)            # L per NM
    cargo_utilization = Column(Float, nullable=True)          # percentage
    
    # Cost metrics
    fuel_cost = Column(Float, nullable=True)                  # USD
    port_charges = Column(Float, nullable=True)               # USD
    total_operational_cost = Column(Float, nullable=True)     # USD
    cost_per_teu = Column(Float, nullable=True)               # USD per TEU
    
    # Environmental metrics
    total_emissions = Column(Float, nullable=True)            # tons CO2
    emissions_per_mile = Column(Float, nullable=True)         # kg CO2 per NM
    
    # Safety and compliance
    safety_score = Column(Float, nullable=True)               # 0-100 scale
    compliance_score = Column(Float, nullable=True)           # 0-100 scale
    incidents = Column(Integer, default=0)
    
    # Route efficiency
    route_efficiency = Column(Float, nullable=True)           # percentage
    weather_delays = Column(Float, nullable=True)             # hours
    port_delays = Column(Float, nullable=True)                # hours
    
    # Metadata
    voyage_data = Column(JSONB, default=dict)
    calculation_metadata = Column(JSONB, default=dict)


# Pydantic models for API serialization
class SupplyChainMetricsBase(BaseModel):
    """Base supply chain metrics model"""
    metric_id: str
    timestamp: datetime
    timeframe: TimeFrame
    region: Optional[str] = None
    trade_lane: Optional[str] = None
    supply_chain_health_score: Optional[float] = Field(None, ge=0, le=100)
    disruption_index: Optional[float] = Field(None, ge=0, le=1)
    resilience_score: Optional[float] = Field(None, ge=0, le=100)
    total_vessels_tracked: int = 0
    active_vessels: int = 0
    vessels_delayed: int = 0
    total_cargo_volume: Optional[float] = None
    delayed_cargo_volume: Optional[float] = None
    average_transit_time: Optional[float] = None
    schedule_reliability: Optional[float] = Field(None, ge=0, le=100)
    average_delay: Optional[float] = None
    on_time_performance: Optional[float] = Field(None, ge=0, le=100)
    average_shipping_cost: Optional[float] = None
    cost_variance: Optional[float] = None
    fuel_cost_index: Optional[float] = None
    total_capacity: Optional[float] = None
    utilized_capacity: Optional[float] = None
    capacity_utilization: Optional[float] = Field(None, ge=0, le=100)
    empty_container_ratio: Optional[float] = Field(None, ge=0, le=100)
    geopolitical_risk_score: Optional[float] = Field(None, ge=0, le=1)
    weather_impact_score: Optional[float] = Field(None, ge=0, le=1)
    security_risk_score: Optional[float] = Field(None, ge=0, le=1)
    total_emissions: Optional[float] = None
    emissions_per_teu: Optional[float] = None
    fuel_efficiency: Optional[float] = None
    cargo_damage_rate: Optional[float] = Field(None, ge=0, le=100)
    customs_clearance_time: Optional[float] = None
    documentation_accuracy: Optional[float] = Field(None, ge=0, le=100)
    data_sources: List[str] = []
    calculation_metadata: Dict[str, Any] = {}
    
    class Config:
        orm_mode = True


class SupplyChainMetricsCreate(SupplyChainMetricsBase):
    """Model for creating supply chain metrics"""
    pass


class SupplyChainMetricsResponse(SupplyChainMetricsBase):
    """Complete supply chain metrics response model"""
    id: int


class PortMetricsBase(BaseModel):
    """Base port metrics model"""
    port_id: str
    timestamp: datetime
    timeframe: TimeFrame
    vessels_processed: int = 0
    total_throughput: Optional[float] = None
    average_turnaround_time: Optional[float] = None
    berth_utilization: Optional[float] = Field(None, ge=0, le=100)
    crane_utilization: Optional[float] = Field(None, ge=0, le=100)
    moves_per_hour: Optional[float] = None
    productivity_index: Optional[float] = None
    equipment_availability: Optional[float] = Field(None, ge=0, le=100)
    labor_efficiency: Optional[float] = None
    average_waiting_time: Optional[float] = None
    peak_waiting_time: Optional[float] = None
    congestion_score: Optional[float] = Field(None, ge=0, le=1)
    queue_length: int = 0
    schedule_adherence: Optional[float] = Field(None, ge=0, le=100)
    service_reliability: Optional[float] = Field(None, ge=0, le=100)
    customer_satisfaction: Optional[float] = Field(None, ge=1, le=5)
    handling_cost_per_teu: Optional[float] = None
    storage_cost_per_day: Optional[float] = None
    total_port_charges: Optional[float] = None
    safety_incidents: int = 0
    security_breaches: int = 0
    environmental_violations: int = 0
    accident_rate: Optional[float] = None
    emissions_per_move: Optional[float] = None
    energy_consumption: Optional[float] = None
    waste_generation: Optional[float] = None
    quay_length_utilization: Optional[float] = Field(None, ge=0, le=100)
    storage_area_utilization: Optional[float] = Field(None, ge=0, le=100)
    equipment_downtime: Optional[float] = None
    calculation_metadata: Dict[str, Any] = {}
    
    class Config:
        orm_mode = True


class PortMetricsCreate(PortMetricsBase):
    """Model for creating port metrics"""
    pass


class PortMetricsResponse(PortMetricsBase):
    """Complete port metrics response model"""
    id: int


class VesselMetricsBase(BaseModel):
    """Base vessel metrics model"""
    mmsi: int
    timestamp: datetime
    timeframe: TimeFrame
    total_distance: Optional[float] = None
    total_voyage_time: Optional[float] = None
    port_time: Optional[float] = None
    sea_time: Optional[float] = None
    ports_visited: int = 0
    average_speed: Optional[float] = None
    schedule_performance: Optional[float] = Field(None, ge=0, le=100)
    fuel_efficiency: Optional[float] = None
    cargo_utilization: Optional[float] = Field(None, ge=0, le=100)
    fuel_cost: Optional[float] = None
    port_charges: Optional[float] = None
    total_operational_cost: Optional[float] = None
    cost_per_teu: Optional[float] = None
    total_emissions: Optional[float] = None
    emissions_per_mile: Optional[float] = None
    safety_score: Optional[float] = Field(None, ge=0, le=100)
    compliance_score: Optional[float] = Field(None, ge=0, le=100)
    incidents: int = 0
    route_efficiency: Optional[float] = Field(None, ge=0, le=100)
    weather_delays: Optional[float] = None
    port_delays: Optional[float] = None
    voyage_data: Dict[str, Any] = {}
    calculation_metadata: Dict[str, Any] = {}
    
    class Config:
        orm_mode = True


class VesselMetricsCreate(VesselMetricsBase):
    """Model for creating vessel metrics"""
    pass


class VesselMetricsResponse(VesselMetricsBase):
    """Complete vessel metrics response model"""
    id: int


class AnalyticsDashboard(BaseModel):
    """Comprehensive analytics dashboard data"""
    timestamp: datetime
    timeframe: TimeFrame
    
    # Overall KPIs
    global_supply_chain_health: Optional[float] = Field(None, ge=0, le=100)
    total_vessels_tracked: int = 0
    total_cargo_volume: Optional[float] = None
    average_delay_hours: Optional[float] = None
    schedule_reliability: Optional[float] = Field(None, ge=0, le=100)
    
    # Regional breakdown
    regional_metrics: Dict[str, Dict[str, Any]] = {}
    
    # Top performers and issues
    top_performing_ports: List[str] = []
    most_congested_ports: List[str] = []
    most_efficient_routes: List[str] = []
    highest_risk_routes: List[str] = []
    
    # Trends and predictions
    trend_indicators: Dict[str, Any] = {}
    predictions: Dict[str, Any] = {}
    
    # Alerts and recommendations
    active_alerts: int = 0
    recommendations: List[str] = []


class PerformanceBenchmark(BaseModel):
    """Performance benchmarking data"""
    entity_id: str
    entity_type: str  # port, vessel, route, region
    metric_type: MetricType
    current_value: float
    benchmark_value: float
    percentile_ranking: Optional[float] = Field(None, ge=0, le=100)
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    comparison_group: str
    improvement_potential: Optional[float] = None
    recommendations: List[str] = []
    timestamp: datetime


class TrendAnalysis(BaseModel):
    """Trend analysis for metrics over time"""
    metric_name: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    data_points: List[Dict[str, Any]] = []
    trend_direction: str  # increasing, decreasing, stable, volatile
    trend_strength: Optional[float] = Field(None, ge=0, le=1)
    seasonal_pattern: Optional[bool] = None
    anomalies_detected: List[Dict[str, Any]] = []
    forecast: Optional[List[Dict[str, Any]]] = None


class MarketIntelligence(BaseModel):
    """Market intelligence and economic indicators"""
    timestamp: datetime
    
    # Freight rates
    container_rates: Dict[str, float] = {}  # route -> USD per TEU
    bulk_rates: Dict[str, float] = {}       # route -> USD per ton
    tanker_rates: Dict[str, float] = {}     # route -> USD per ton
    
    # Market indicators
    baltic_dry_index: Optional[float] = None
    container_throughput_index: Optional[float] = None
    fuel_price_index: Optional[float] = None
    
    # Economic factors
    trade_volume_growth: Optional[float] = None
    gdp_impact_factor: Optional[float] = None
    currency_exchange_impact: Optional[float] = None
    
    # Supply and demand
    vessel_supply_utilization: Optional[float] = Field(None, ge=0, le=100)
    cargo_demand_index: Optional[float] = None
    capacity_shortage_index: Optional[float] = None
    
    # Predictions
    rate_forecast_30d: Dict[str, float] = {}
    demand_forecast_90d: Dict[str, float] = {}
    risk_outlook: Dict[str, str] = {} 