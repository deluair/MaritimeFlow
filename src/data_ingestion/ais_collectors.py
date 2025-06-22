"""
AIS data collectors for multiple free and commercial data sources
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
import aiohttp
import websockets
from kafka import KafkaProducer
import structlog

from ..core.config import settings, AIS_SOURCES
from ..models.vessel import VesselPositionCreate, NavigationStatus, VesselType

logger = structlog.get_logger(__name__)


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
        self._init_kafka_producer()
        
        # Rate limiting
        self.rate_limit = AIS_SOURCES.get(source_name, {}).get('rate_limit', 60)
        self.min_request_interval = 60.0 / self.rate_limit if self.rate_limit else 0
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer for streaming data"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
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
                    settings.kafka_ais_topic,
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


class AISHubCollector(BaseAISCollector):
    """Collector for AISHub Global Network data"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("aishub", api_key)
        self.base_url = AIS_SOURCES["aishub"]["base_url"]
        self.session = None
    
    async def collect_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Collect data from AISHub API"""
        self.session = aiohttp.ClientSession()
        
        try:
            while self.is_running:
                self._enforce_rate_limit()
                
                # Request parameters for AISHub
                params = {
                    'format': 'json',
                    'encode': 'json',
                    'compress': '0',
                    'output': 'json'
                }
                
                # Add geographic bounds
                params.update({
                    'latmin': settings.ais_bounds_south,
                    'latmax': settings.ais_bounds_north,
                    'lonmin': settings.ais_bounds_west,
                    'lonmax': settings.ais_bounds_east
                })
                
                # Add API key if available
                if self.api_key:
                    params['username'] = self.api_key
                
                try:
                    async with self.session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # AISHub returns array of vessels
                            if isinstance(data, list):
                                for vessel_data in data:
                                    yield vessel_data
                            elif isinstance(data, dict) and 'data' in data:
                                for vessel_data in data['data']:
                                    yield vessel_data
                        else:
                            logger.warning(f"AISHub API returned status {response.status}")
                            await asyncio.sleep(60)  # Wait before retry
                            
                except Exception as e:
                    logger.error(f"Error collecting from AISHub: {e}")
                    await asyncio.sleep(30)  # Wait before retry
                
        finally:
            if self.session:
                await self.session.close()
    
    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[VesselPositionCreate]:
        """Parse AISHub message format"""
        try:
            # AISHub format mapping
            mmsi = raw_message.get('MMSI')
            if not mmsi:
                return None
            
            # Parse position data
            latitude = float(raw_message.get('LATITUDE', 0))
            longitude = float(raw_message.get('LONGITUDE', 0))
            
            # Validate coordinates
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return None
            
            # Parse timestamp
            timestamp_str = raw_message.get('TIMESTAMP')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Parse navigation data
            course = raw_message.get('COG')
            speed = raw_message.get('SOG')
            heading = raw_message.get('HEADING')
            
            # Parse destination and ETA
            destination = raw_message.get('DESTINATION', '').strip()
            eta_str = raw_message.get('ETA')
            eta = None
            if eta_str:
                try:
                    eta = datetime.fromisoformat(eta_str.replace('Z', '+00:00'))
                except:
                    pass
            
            return VesselPositionCreate(
                mmsi=int(mmsi),
                latitude=latitude,
                longitude=longitude,
                course_over_ground=float(course) if course else None,
                speed_over_ground=float(speed) if speed else None,
                true_heading=float(heading) if heading else None,
                destination=destination if destination else None,
                eta=eta,
                timestamp=timestamp,
                message_timestamp=timestamp,
                data_source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing AISHub message: {e}")
            return None


class AISStreamCollector(BaseAISCollector):
    """Collector for AISStream.io WebSocket data"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("aisstream", api_key)
        self.websocket_url = AIS_SOURCES["aisstream"]["websocket_url"]
        self.websocket = None
    
    async def collect_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Collect data from AISStream WebSocket"""
        
        while self.is_running:
            try:
                # Connect to WebSocket
                headers = {}
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'
                
                async with websockets.connect(
                    self.websocket_url,
                    extra_headers=headers
                ) as websocket:
                    self.websocket = websocket
                    logger.info("Connected to AISStream WebSocket")
                    
                    # Send subscription message
                    subscription = {
                        "APIKey": self.api_key or "",
                        "BoundingBoxes": [[
                            settings.ais_bounds_north,
                            settings.ais_bounds_west,
                            settings.ais_bounds_south,
                            settings.ais_bounds_east
                        ]],
                        "FiltersShipAndCargo": [],
                        "FilterMessageTypes": ["PositionReport"]
                    }
                    
                    await websocket.send(json.dumps(subscription))
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self.is_running:
                            break
                            
                        try:
                            data = json.loads(message)
                            yield data
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse WebSocket message: {e}")
                            
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(30)  # Wait before reconnecting
    
    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[VesselPositionCreate]:
        """Parse AISStream message format"""
        try:
            # AISStream format
            message_data = raw_message.get('Message', {})
            if not message_data:
                return None
            
            mmsi = message_data.get('UserID')
            if not mmsi:
                return None
            
            # Parse position data
            latitude = message_data.get('Latitude')
            longitude = message_data.get('Longitude')
            
            if latitude is None or longitude is None:
                return None
            
            # Validate coordinates
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return None
            
            # Parse timestamp
            timestamp_str = raw_message.get('MetaData', {}).get('time_utc')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Parse navigation data
            course = message_data.get('CourseOverGround')
            speed = message_data.get('SpeedOverGround')
            heading = message_data.get('TrueHeading')
            nav_status = message_data.get('NavigationalStatus')
            
            # Map navigation status
            navigation_status = None
            if nav_status is not None:
                status_map = {
                    0: NavigationStatus.UNDER_WAY_USING_ENGINE,
                    1: NavigationStatus.AT_ANCHOR,
                    2: NavigationStatus.NOT_UNDER_COMMAND,
                    3: NavigationStatus.RESTRICTED_MANEUVERABILITY,
                    4: NavigationStatus.CONSTRAINED_BY_DRAFT,
                    5: NavigationStatus.MOORED,
                    6: NavigationStatus.AGROUND,
                    7: NavigationStatus.FISHING,
                    8: NavigationStatus.UNDER_WAY_SAILING,
                    15: NavigationStatus.NOT_DEFINED
                }
                navigation_status = status_map.get(nav_status, NavigationStatus.NOT_DEFINED)
            
            return VesselPositionCreate(
                mmsi=int(mmsi),
                latitude=latitude,
                longitude=longitude,
                course_over_ground=course if course is not None else None,
                speed_over_ground=speed if speed is not None else None,
                true_heading=heading if heading != 511 else None,
                navigation_status=navigation_status,
                timestamp=timestamp,
                message_timestamp=timestamp,
                data_source=self.source_name,
                raw_message=json.dumps(raw_message)
            )
            
        except Exception as e:
            logger.error(f"Error parsing AISStream message: {e}")
            return None


class MarinePlanCollector(BaseAISCollector):
    """Collector for MarinePlan OpenShipData API"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("marineplan", api_key)
        self.base_url = AIS_SOURCES["marineplan"]["base_url"]
        self.session = None
    
    async def collect_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Collect data from MarinePlan API"""
        self.session = aiohttp.ClientSession()
        
        try:
            while self.is_running:
                self._enforce_rate_limit()
                
                # Request parameters for MarinePlan
                params = {
                    'format': 'json',
                    'bbox': f"{settings.ais_bounds_west},{settings.ais_bounds_south},"
                           f"{settings.ais_bounds_east},{settings.ais_bounds_north}"
                }
                
                # Add API key if available
                headers = {}
                if self.api_key:
                    headers['X-API-Key'] = self.api_key
                
                try:
                    async with self.session.get(
                        f"{self.base_url}/vessels/positions",
                        params=params,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # MarinePlan returns vessel array
                            vessels = data.get('vessels', [])
                            for vessel_data in vessels:
                                yield vessel_data
                        else:
                            logger.warning(f"MarinePlan API returned status {response.status}")
                            await asyncio.sleep(60)
                            
                except Exception as e:
                    logger.error(f"Error collecting from MarinePlan: {e}")
                    await asyncio.sleep(30)
                
        finally:
            if self.session:
                await self.session.close()
    
    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[VesselPositionCreate]:
        """Parse MarinePlan message format"""
        try:
            mmsi = raw_message.get('mmsi')
            if not mmsi:
                return None
            
            # Parse position data
            position = raw_message.get('position', {})
            latitude = position.get('latitude')
            longitude = position.get('longitude')
            
            if latitude is None or longitude is None:
                return None
            
            # Validate coordinates
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return None
            
            # Parse timestamp
            timestamp_str = raw_message.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Parse navigation data
            course = raw_message.get('course')
            speed = raw_message.get('speed')
            heading = raw_message.get('heading')
            
            # Parse destination and ETA
            destination = raw_message.get('destination', '').strip()
            eta_str = raw_message.get('eta')
            eta = None
            if eta_str:
                try:
                    eta = datetime.fromisoformat(eta_str.replace('Z', '+00:00'))
                except:
                    pass
            
            return VesselPositionCreate(
                mmsi=int(mmsi),
                latitude=latitude,
                longitude=longitude,
                course_over_ground=course if course is not None else None,
                speed_over_ground=speed if speed is not None else None,
                true_heading=heading if heading is not None else None,
                destination=destination if destination else None,
                eta=eta,
                timestamp=timestamp,
                message_timestamp=timestamp,
                data_source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing MarinePlan message: {e}")
            return None


class DigitalTrafficCollector(BaseAISCollector):
    """Collector for Finnish Digitraffic AIS data"""
    
    def __init__(self):
        super().__init__("digitraffic")
        self.base_url = AIS_SOURCES["digitraffic"]["base_url"]
        self.session = None
    
    async def collect_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Collect data from Digitraffic API"""
        self.session = aiohttp.ClientSession()
        
        try:
            while self.is_running:
                self._enforce_rate_limit()
                
                try:
                    async with self.session.get(f"{self.base_url}/latest") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Digitraffic returns GeoJSON features
                            features = data.get('features', [])
                            for feature in features:
                                yield feature
                        else:
                            logger.warning(f"Digitraffic API returned status {response.status}")
                            await asyncio.sleep(60)
                            
                except Exception as e:
                    logger.error(f"Error collecting from Digitraffic: {e}")
                    await asyncio.sleep(30)
                
        finally:
            if self.session:
                await self.session.close()
    
    def parse_message(self, raw_message: Dict[str, Any]) -> Optional[VesselPositionCreate]:
        """Parse Digitraffic GeoJSON format"""
        try:
            # Extract geometry and properties
            geometry = raw_message.get('geometry', {})
            properties = raw_message.get('properties', {})
            
            mmsi = properties.get('mmsi')
            if not mmsi:
                return None
            
            # Parse coordinates from GeoJSON
            coordinates = geometry.get('coordinates', [])
            if len(coordinates) < 2:
                return None
            
            longitude, latitude = coordinates[0], coordinates[1]
            
            # Validate coordinates
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return None
            
            # Parse timestamp
            timestamp_str = properties.get('timestampExternal')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Parse navigation data
            course = properties.get('cog')
            speed = properties.get('sog')
            heading = properties.get('heading')
            nav_status = properties.get('navStat')
            
            # Map navigation status
            navigation_status = None
            if nav_status is not None:
                status_map = {
                    0: NavigationStatus.UNDER_WAY_USING_ENGINE,
                    1: NavigationStatus.AT_ANCHOR,
                    2: NavigationStatus.NOT_UNDER_COMMAND,
                    3: NavigationStatus.RESTRICTED_MANEUVERABILITY,
                    4: NavigationStatus.CONSTRAINED_BY_DRAFT,
                    5: NavigationStatus.MOORED,
                    6: NavigationStatus.AGROUND,
                    7: NavigationStatus.FISHING,
                    8: NavigationStatus.UNDER_WAY_SAILING,
                    15: NavigationStatus.NOT_DEFINED
                }
                navigation_status = status_map.get(nav_status, NavigationStatus.NOT_DEFINED)
            
            return VesselPositionCreate(
                mmsi=int(mmsi),
                latitude=latitude,
                longitude=longitude,
                course_over_ground=course if course is not None else None,
                speed_over_ground=speed if speed is not None else None,
                true_heading=heading if heading is not None and heading != 511 else None,
                navigation_status=navigation_status,
                timestamp=timestamp,
                message_timestamp=timestamp,
                data_source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing Digitraffic message: {e}")
            return None


class AISCollectorManager:
    """Manager for multiple AIS data collectors"""
    
    def __init__(self):
        self.collectors = {}
        self.tasks = {}
        self.is_running = False
    
    def add_collector(self, collector: BaseAISCollector):
        """Add a collector to the manager"""
        self.collectors[collector.source_name] = collector
    
    async def start_all(self):
        """Start all collectors"""
        self.is_running = True
        logger.info("Starting all AIS collectors")
        
        for name, collector in self.collectors.items():
            task = asyncio.create_task(collector.start_collection())
            self.tasks[name] = task
            logger.info(f"Started collector: {name}")
    
    async def stop_all(self):
        """Stop all collectors"""
        self.is_running = False
        logger.info("Stopping all AIS collectors")
        
        # Stop collectors
        for collector in self.collectors.values():
            collector.stop_collection()
        
        # Wait for tasks to complete
        for name, task in self.tasks.items():
            try:
                await asyncio.wait_for(task, timeout=30)
                logger.info(f"Stopped collector: {name}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout stopping collector: {name}")
                task.cancel()
        
        self.tasks.clear()
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all collectors"""
        status = {}
        for name, collector in self.collectors.items():
            status[name] = {
                'is_running': collector.is_running,
                'request_count': collector.request_count,
                'error_count': collector.error_count,
                'error_rate': collector.error_count / max(collector.request_count, 1)
            }
        return status 