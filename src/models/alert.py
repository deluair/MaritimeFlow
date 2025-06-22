"""
Alert system models for maritime intelligence and risk management
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class AlertType(str, Enum):
    """Alert type classifications"""
    PORT_CONGESTION = "port_congestion"
    ROUTE_DEVIATION = "route_deviation"
    WEATHER_WARNING = "weather_warning"
    SECURITY_THREAT = "security_threat"
    GEOPOLITICAL_RISK = "geopolitical_risk"
    SANCTIONS_VIOLATION = "sanctions_violation"
    EQUIPMENT_FAILURE = "equipment_failure"
    SUPPLY_CHAIN_DISRUPTION = "supply_chain_disruption"
    VESSEL_BREAKDOWN = "vessel_breakdown"
    ENVIRONMENTAL_VIOLATION = "environmental_violation"
    EMERGENCY = "emergency"
    MAINTENANCE_REQUIRED = "maintenance_required"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    DELAY_PREDICTION = "delay_prediction"
    PRICE_ANOMALY = "price_anomaly"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"           # Information only
    MEDIUM = "medium"     # Attention required
    HIGH = "high"         # Action required
    CRITICAL = "critical" # Immediate action required
    EMERGENCY = "emergency" # Emergency response required


class AlertStatus(str, Enum):
    """Alert processing status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class Alert(Base):
    """Maritime alert and notification system"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Alert classification
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default="active", index=True)
    
    # Alert content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    
    # Geographic and entity context
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    affected_ports = Column(JSONB, default=list)
    affected_vessels = Column(JSONB, default=list)
    affected_routes = Column(JSONB, default=list)
    
    # Metrics and thresholds
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 scale
    
    # Impact assessment
    estimated_impact = Column(String(50), nullable=True)  # low, medium, high, critical
    economic_impact = Column(Float, nullable=True)        # USD
    vessels_affected = Column(Integer, default=0)
    cargo_affected = Column(Float, nullable=True)         # TEU or tons
    
    # Timing
    detection_time = Column(DateTime, nullable=False, index=True)
    event_start_time = Column(DateTime, nullable=True, index=True)
    estimated_end_time = Column(DateTime, nullable=True, index=True)
    actual_end_time = Column(DateTime, nullable=True, index=True)
    
    # Data source and processing
    data_source = Column(String(100), nullable=False)
    detection_method = Column(String(100), nullable=True)  # manual, automated, ml_prediction
    source_system = Column(String(100), nullable=True)
    
    # Resolution tracking
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(JSONB, default=list)
    alert_data = Column(JSONB, default=dict)
    escalation_count = Column(Integer, default=0)
    is_recurring = Column(Boolean, default=False)
    parent_alert_id = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertSubscription(Base):
    """User alert subscription preferences"""
    __tablename__ = "alert_subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Subscription criteria
    alert_types = Column(JSONB, default=list)
    severity_levels = Column(JSONB, default=list)
    regions = Column(JSONB, default=list)
    ports = Column(JSONB, default=list)
    vessels = Column(JSONB, default=list)
    routes = Column(JSONB, default=list)
    
    # Delivery preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(String(500), nullable=True)
    
    # Timing preferences
    immediate_notification = Column(Boolean, default=True)
    daily_digest = Column(Boolean, default=False)
    weekly_digest = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for API serialization
class AlertBase(BaseModel):
    """Base alert model"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., max_length=500)
    description: str
    recommendation: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    region: Optional[str] = None
    affected_ports: List[str] = []
    affected_vessels: List[int] = []
    affected_routes: List[str] = []
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    estimated_impact: Optional[str] = None
    economic_impact: Optional[float] = None
    vessels_affected: int = 0
    cargo_affected: Optional[float] = None
    detection_time: datetime
    event_start_time: Optional[datetime] = None
    estimated_end_time: Optional[datetime] = None
    data_source: str
    detection_method: Optional[str] = None
    source_system: Optional[str] = None
    tags: List[str] = []
    alert_data: Dict[str, Any] = {}
    is_recurring: bool = False
    parent_alert_id: Optional[str] = None
    
    class Config:
        orm_mode = True


class AlertCreate(AlertBase):
    """Model for creating alerts"""
    pass


class AlertUpdate(BaseModel):
    """Model for updating alerts"""
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    recommendation: Optional[str] = None
    estimated_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    tags: Optional[List[str]] = None
    alert_data: Optional[Dict[str, Any]] = None


class AlertResponse(AlertBase):
    """Complete alert response model"""
    id: int
    alert_id: str
    status: AlertStatus
    actual_end_time: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    escalation_count: int = 0
    created_at: datetime
    updated_at: datetime


class AlertSubscriptionBase(BaseModel):
    """Base alert subscription model"""
    user_id: str
    alert_types: List[AlertType] = []
    severity_levels: List[AlertSeverity] = []
    regions: List[str] = []
    ports: List[str] = []
    vessels: List[int] = []
    routes: List[str] = []
    email_enabled: bool = True
    sms_enabled: bool = False
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    immediate_notification: bool = True
    daily_digest: bool = False
    weekly_digest: bool = False
    is_active: bool = True
    
    class Config:
        orm_mode = True


class AlertSubscriptionCreate(AlertSubscriptionBase):
    """Model for creating alert subscriptions"""
    pass


class AlertSubscriptionUpdate(BaseModel):
    """Model for updating alert subscriptions"""
    alert_types: Optional[List[AlertType]] = None
    severity_levels: Optional[List[AlertSeverity]] = None
    regions: Optional[List[str]] = None
    ports: Optional[List[str]] = None
    vessels: Optional[List[int]] = None
    routes: Optional[List[str]] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    immediate_notification: Optional[bool] = None
    daily_digest: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    is_active: Optional[bool] = None


class AlertSubscriptionResponse(AlertSubscriptionBase):
    """Complete alert subscription response model"""
    id: int
    created_at: datetime
    updated_at: datetime


class AlertSummary(BaseModel):
    """Alert summary statistics"""
    total_alerts: int = 0
    active_alerts: int = 0
    critical_alerts: int = 0
    resolved_today: int = 0
    average_resolution_time: Optional[float] = None  # hours
    alerts_by_type: Dict[str, int] = {}
    alerts_by_severity: Dict[str, int] = {}
    recent_alerts: List[AlertResponse] = []
    top_affected_ports: List[str] = []
    top_affected_routes: List[str] = []


class AlertMetrics(BaseModel):
    """Alert system performance metrics"""
    detection_accuracy: Optional[float] = None     # percentage
    false_positive_rate: Optional[float] = None    # percentage
    average_detection_time: Optional[float] = None # minutes
    average_response_time: Optional[float] = None  # minutes
    escalation_rate: Optional[float] = None        # percentage
    resolution_rate: Optional[float] = None        # percentage
    user_satisfaction: Optional[float] = None      # 1-5 scale
    system_uptime: Optional[float] = None          # percentage


class AlertNotification(BaseModel):
    """Alert notification message"""
    alert_id: str
    user_id: str
    notification_type: str  # email, sms, webhook, push
    delivered_at: datetime
    delivery_status: str    # sent, delivered, failed, bounced
    failure_reason: Optional[str] = None
    retry_count: int = 0 