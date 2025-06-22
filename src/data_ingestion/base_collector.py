"""
Base AIS data collector with common functionality
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator

# Optional imports
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
    logger = structlog.get_logger(__name__)
except ImportError:
    STRUCTLOG_AVAILABLE = False
    logger = logging.getLogger(__name__)

from ..core.config import AIS_SOURCES
from ..models.vessel import VesselPositionCreate


class BaseAISCollector(ABC):
    """Base class for AIS data collectors"""
    
    def __init__(self, source_name: str, api_key: Optional[str] = None):
        self.source_name = source_name
        self.api_key = api_key
        self.is_running = False
        self.last_request_time = 0
        self.request_count = 0
        self.error_count = 0
        self.kafka_producer = None
        
        # Initialize Kafka producer
        if KAFKA_AVAILABLE:
            self._init_kafka_producer()
        
        # Rate limiting
        self.rate_limit = AIS_SOURCES.get(source_name, {}).get('rate_limit', 60)
        self.min_request_interval = 60.0 / self.rate_limit if self.rate_limit else 0
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer for streaming data"""
        if not KAFKA_AVAILABLE:
            return
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],  # Default kafka servers
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        if self.min_request_interval > 0:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _publish_to_kafka(self, ais_data: Dict[str, Any]):
        """Publish AIS data to Kafka topic"""
        if self.kafka_producer:
            try:
                self.kafka_producer.send(
                    'ais_data',  # Default topic name
                    key=str(ais_data.get('mmsi')),
                    value=ais_data
                )
                self.kafka_producer.flush()
            except Exception as e:
                logger.error(f"Failed to publish to Kafka: {e}")
    
    @abstractmethod
    async def collect_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Collect AIS data from the source"""
        pass
    
    @abstractmethod
    def parse_message(self, raw_message: Any) -> Optional[VesselPositionCreate]:
        """Parse raw message to standardized format"""
        pass
    
    async def start_collection(self):
        """Start the data collection process"""
        self.is_running = True
        logger.info(f"Starting AIS data collection from {self.source_name}")
        
        try:
            async for data in self.collect_data():
                if not self.is_running:
                    break
                    
                # Parse and validate data
                parsed_data = self.parse_message(data)
                if parsed_data:
                    # Convert to dict and publish
                    data_dict = parsed_data.dict()
                    data_dict['source'] = self.source_name
                    data_dict['collection_timestamp'] = datetime.utcnow().isoformat()
                    
                    self._publish_to_kafka(data_dict)
                    self.request_count += 1
                else:
                    self.error_count += 1
                    
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            self.error_count += 1
        finally:
            self.is_running = False
    
    def stop_collection(self):
        """Stop the data collection process"""
        self.is_running = False
        logger.info(f"Stopping AIS data collection from {self.source_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            'source_name': self.source_name,
            'is_running': self.is_running,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'last_request_time': self.last_request_time
        }


class BaseCollector(ABC):
    """Simple base collector for real AIS data integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    async def collect_data(self, region: Optional[str] = None) -> List[Any]:
        """Collect data from the source"""
        pass 