"""
Configuration management for MaritimeFlow platform
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application settings
    app_name: str = "MaritimeFlow"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Database settings
    database_url: str = Field(env="DATABASE_URL", default="postgresql://user:password@localhost/maritimeflow")
    redis_url: str = Field(env="REDIS_URL", default="redis://localhost:6379")
    influxdb_url: str = Field(env="INFLUXDB_URL", default="http://localhost:8086")
    influxdb_token: str = Field(env="INFLUXDB_TOKEN", default="")
    influxdb_org: str = Field(env="INFLUXDB_ORG", default="maritimeflow")
    influxdb_bucket: str = Field(env="INFLUXDB_BUCKET", default="ais_data")
    
    # AIS Data Sources
    aishub_api_key: Optional[str] = Field(env="AISHUB_API_KEY", default=None)
    aisstream_api_key: Optional[str] = Field(env="AISSTREAM_API_KEY", default=None)
    marineplan_api_key: Optional[str] = Field(env="MARINEPLAN_API_KEY", default=None)
    
    # WebSocket settings
    websocket_max_connections: int = Field(default=1000, env="WEBSOCKET_MAX_CONNECTIONS")
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    
    # Kafka settings
    kafka_bootstrap_servers: List[str] = Field(default=["localhost:9092"], env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_ais_topic: str = Field(default="ais_data", env="KAFKA_AIS_TOPIC")
    kafka_alerts_topic: str = Field(default="maritime_alerts", env="KAFKA_ALERTS_TOPIC")
    
    # Machine Learning settings
    ml_model_path: str = Field(default="models/", env="ML_MODEL_PATH")
    ml_update_interval: int = Field(default=3600, env="ML_UPDATE_INTERVAL")  # seconds
    
    # Geographic bounds for AIS data collection
    ais_bounds_north: float = Field(default=85.0, env="AIS_BOUNDS_NORTH")
    ais_bounds_south: float = Field(default=-85.0, env="AIS_BOUNDS_SOUTH")
    ais_bounds_east: float = Field(default=180.0, env="AIS_BOUNDS_EAST")
    ais_bounds_west: float = Field(default=-180.0, env="AIS_BOUNDS_WEST")
    
    # Data processing settings
    batch_size: int = Field(default=1000, env="BATCH_SIZE")
    max_vessel_age_hours: int = Field(default=24, env="MAX_VESSEL_AGE_HOURS")
    data_retention_days: int = Field(default=365, env="DATA_RETENTION_DAYS")
    
    # Alert thresholds
    port_congestion_threshold: float = Field(default=0.8, env="PORT_CONGESTION_THRESHOLD")
    route_deviation_threshold: float = Field(default=50.0, env="ROUTE_DEVIATION_THRESHOLD")  # nautical miles
    
    # External API settings
    weather_api_key: Optional[str] = Field(env="WEATHER_API_KEY", default=None)
    news_api_key: Optional[str] = Field(env="NEWS_API_KEY", default=None)
    
    # Security settings
    secret_key: str = Field(env="SECRET_KEY", default="your-secret-key-here")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Monitoring and logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Global settings instance
settings = get_settings()


# AIS Data Source Configuration
AIS_SOURCES = {
    # Real AIS APIs (recommended)
    "myshiptracking": {
        "name": "MyShipTracking",
        "url": "https://api.myshiptracking.com",
        "api_key_required": True,
        "free_tier": True,
        "description": "Real-time terrestrial AIS data with free trial",
        "coverage": "Global terrestrial AIS",
        "rate_limit": "100 requests/minute",
        "free_credits": 2000
    },
    "datalastic": {
        "name": "Datalastic",
        "url": "https://api.datalastic.com",
        "api_key_required": True,
        "free_tier": False,
        "description": "Professional AIS data with 750,000+ ships",
        "coverage": "Global maritime data",
        "rate_limit": "2000 requests/minute",
        "uptime": "99.8%"
    },
    "aishub": {
        "name": "AISHub",
        "url": "https://www.aishub.net",
        "api_key_required": False,
        "free_tier": True,
        "description": "Community-based AIS data sharing",
        "coverage": "Global community data",
        "requirement": "Contribute your own AIS data"
    },
    "vesselfinder": {
        "name": "VesselFinder",
        "url": "https://www.vesselfinder.com",
        "api_key_required": True,
        "free_tier": False,
        "description": "Professional satellite and terrestrial AIS",
        "coverage": "Global satellite + terrestrial"
    },
    
    # Fallback/Demo sources
    "synthetic": {
        "name": "Synthetic Generator",
        "description": "Generated realistic vessel data for testing",
        "coverage": "All regions",
        "api_key_required": False,
        "free_tier": True
    }
}

# Real AIS API Configuration
REAL_AIS_CONFIG = {
    # MyShipTracking API (Free trial available)
    "myshiptracking_api_key": os.getenv("MYSHIPTRACKING_API_KEY"),
    "myshiptracking_secret_key": os.getenv("MYSHIPTRACKING_SECRET_KEY"),
    "myshiptracking_base_url": "https://api.myshiptracking.com/api/v1",
    
    # Datalastic API (Paid service)
    "datalastic_api_key": os.getenv("DATALASTIC_API_KEY"), 
    "datalastic_base_url": "https://api.datalastic.com/api/v0",
    
    # Rate limiting
    "rate_limit_delay": float(os.getenv("AIS_API_RATE_LIMIT", "1.0")),
    "max_vessels_per_request": int(os.getenv("MAX_VESSELS_PER_REQUEST", "100")),
    
    # Fallback settings
    "use_fallback_on_error": os.getenv("USE_FALLBACK_ON_ERROR", "true").lower() == "true",
    "preferred_api": os.getenv("PREFERRED_AIS_API", "myshiptracking")  # myshiptracking, datalastic
}

# Major world ports with coordinates
MAJOR_PORTS = {
    "SHANGHAI": {"lat": 31.2304, "lon": 121.4737, "country": "CN"},
    "NINGBO": {"lat": 29.8683, "lon": 121.5440, "country": "CN"},
    "SINGAPORE": {"lat": 1.2966, "lon": 103.7764, "country": "SG"},
    "SHENZHEN": {"lat": 22.5431, "lon": 114.0579, "country": "CN"},
    "GUANGZHOU": {"lat": 23.1291, "lon": 113.2644, "country": "CN"},
    "BUSAN": {"lat": 35.1796, "lon": 129.0756, "country": "KR"},
    "HONG_KONG": {"lat": 22.3193, "lon": 114.1694, "country": "HK"},
    "QINGDAO": {"lat": 36.0986, "lon": 120.3719, "country": "CN"},
    "TIANJIN": {"lat": 39.1612, "lon": 117.4413, "country": "CN"},
    "ROTTERDAM": {"lat": 51.9244, "lon": 4.4777, "country": "NL"},
    "ANTWERP": {"lat": 51.2194, "lon": 4.4025, "country": "BE"},
    "LOS_ANGELES": {"lat": 33.7405, "lon": -118.2668, "country": "US"},
    "LONG_BEACH": {"lat": 33.7701, "lon": -118.2437, "country": "US"},
    "HAMBURG": {"lat": 53.5511, "lon": 9.9937, "country": "DE"},
    "DUBAI": {"lat": 25.2769, "lon": 55.2962, "country": "AE"},
    "NEW_YORK": {"lat": 40.6892, "lon": -74.0445, "country": "US"},
    "SAVANNAH": {"lat": 32.1313, "lon": -81.1426, "country": "US"},
    "PIRAEUS": {"lat": 37.9364, "lon": 23.6503, "country": "GR"},
    "FELIXSTOWE": {"lat": 51.9543, "lon": 1.3511, "country": "GB"},
    "VALENCIA": {"lat": 39.4699, "lon": -0.3763, "country": "ES"}
}

# Critical shipping routes and chokepoints
SHIPPING_ROUTES = {
    "SUEZ_CANAL": {
        "name": "Suez Canal",
        "start": {"lat": 31.2653, "lon": 32.3424},
        "end": {"lat": 29.9668, "lon": 32.5498},
        "importance": "critical",
        "daily_traffic": 50
    },
    "PANAMA_CANAL": {
        "name": "Panama Canal",
        "start": {"lat": 9.3793, "lon": -79.9199},
        "end": {"lat": 8.9824, "lon": -79.5199},
        "importance": "critical",
        "daily_traffic": 40
    },
    "STRAIT_OF_HORMUZ": {
        "name": "Strait of Hormuz",
        "start": {"lat": 26.5667, "lon": 56.2500},
        "end": {"lat": 26.6167, "lon": 56.3833},
        "importance": "critical",
        "daily_traffic": 30
    },
    "STRAIT_OF_MALACCA": {
        "name": "Strait of Malacca",
        "start": {"lat": 5.5833, "lon": 95.3167},
        "end": {"lat": 1.2966, "lon": 103.7764},
        "importance": "critical",
        "daily_traffic": 25
    },
    "DANISH_STRAITS": {
        "name": "Danish Straits",
        "start": {"lat": 56.0000, "lon": 12.6000},
        "end": {"lat": 55.7000, "lon": 12.5833},
        "importance": "major",
        "daily_traffic": 15
    }
} 