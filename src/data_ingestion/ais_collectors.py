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

# Optional imports
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from ..core.config import AIS_SOURCES
from ..models.vessel import VesselPositionCreate, NavigationStatus, VesselType, Vessel, VesselPosition
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


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
                    'latmin': -90,  # Default bounds
                    'latmax': 90,
                    'lonmin': -180,
                    'lonmax': 180
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


class AISCollector(BaseCollector):
    """Real AIS data collector using various APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.myshiptracking_api_key = config.get('myshiptracking_api_key')
        self.myshiptracking_secret_key = config.get('myshiptracking_secret_key')
        self.datalastic_api_key = config.get('datalastic_api_key')
        self.rate_limit_delay = config.get('rate_limit_delay', 1.0)  # seconds between requests
        
    async def collect_data(self, region: Optional[str] = None) -> List[Vessel]:
        """Collect real AIS data from available APIs"""
        vessels = []
        
        try:
            # Try MyShipTracking API first (free tier available)
            if self.myshiptracking_api_key:
                mst_vessels = await self._collect_from_myshiptracking(region)
                vessels.extend(mst_vessels)
                logger.info(f"Collected {len(mst_vessels)} vessels from MyShipTracking")
            
            # Try Datalastic API as fallback
            elif self.datalastic_api_key:
                datalastic_vessels = await self._collect_from_datalastic(region)
                vessels.extend(datalastic_vessels)
                logger.info(f"Collected {len(datalastic_vessels)} vessels from Datalastic")
            
            else:
                logger.warning("No API keys configured for real AIS data. Using fallback data.")
                vessels = await self._get_fallback_data(region)
                
        except Exception as e:
            logger.error(f"Error collecting AIS data: {e}")
            # Fallback to sample data if all APIs fail
            vessels = await self._get_fallback_data(region)
            
        return vessels
    
    async def _collect_from_myshiptracking(self, region: Optional[str] = None) -> List[Vessel]:
        """Collect data from MyShipTracking API"""
        vessels = []
        
        if not self.myshiptracking_api_key:
            logger.warning("MyShipTracking API key not configured")
            return vessels
        
        headers = {
            'Authorization': f'Bearer {self.myshiptracking_api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # Get vessels using bulk endpoint
                vessels.extend(await self._get_known_vessels_mst(session))
                await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
                        
            except Exception as e:
                logger.error(f"MyShipTracking API error: {e}")
                
        return vessels
    
    async def _get_known_vessels_mst(self, session: aiohttp.ClientSession) -> List[Vessel]:
        """Get known vessels from MyShipTracking API using bulk endpoint"""
        vessels = []
        
        try:
            # Use some known MMSIs for demonstration
            known_mmsis = [
                "241087000",  # BLUE STAR DELOS
                "239923000",  # BLUE STAR NAXOS  
                "239924000",  # BLUE STAR PAROS
                "219836000",  # Example from docs
                "636091432",  # Common cargo vessel
                "538005936",  # Container ship
                "636015825",  # Oil tanker
                "477995700",  # Bulk carrier
                "636092932",  # Container vessel
                "373785000"   # Ferry
            ]
            
            # Split into chunks of 10 (API allows up to 100)
            chunk_size = 10
            for i in range(0, len(known_mmsis), chunk_size):
                chunk = known_mmsis[i:i + chunk_size]
                mmsi_string = ",".join(chunk)
                
                url = "https://api.myshiptracking.com/api/v2/vessel/bulk"
                params = {
                    'mmsi': mmsi_string,
                    'response': 'extended'  # Get detailed vessel information
                }
                
                async with session.get(url, params=params) as response:
                    logger.info(f"MyShipTracking API request: {url} with MMSIs: {mmsi_string}")
                    logger.info(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            vessel_data_list = data.get('data', [])
                            logger.info(f"Successfully got {len(vessel_data_list)} vessels from MyShipTracking")
                            
                            for vessel_data in vessel_data_list:
                                vessel = self._parse_myshiptracking_vessel(vessel_data)
                                if vessel:
                                    vessels.append(vessel)
                        else:
                            logger.warning(f"MyShipTracking API returned error: {data}")
                                
                    elif response.status == 401:
                        logger.error("MyShipTracking API: Unauthorized - check your API key")
                        break
                    elif response.status == 429:
                        logger.error("MyShipTracking API: Rate limit exceeded")
                        await asyncio.sleep(5)  # Wait before retry
                    else:
                        error_text = await response.text()
                        logger.warning(f"MyShipTracking API returned status {response.status}: {error_text}")
                
                # Rate limiting between chunks
                await asyncio.sleep(self.rate_limit_delay)
                    
        except Exception as e:
            logger.error(f"Error getting vessels from MyShipTracking: {e}")
            
        return vessels
    
    def _parse_myshiptracking_vessel(self, vessel_data: Dict[str, Any]) -> Optional[Vessel]:
        """Parse vessel data from MyShipTracking API"""
        try:
            # MyShipTracking API v2 response format
            vessel_name = vessel_data.get('vessel_name', 'Unknown')
            mmsi = vessel_data.get('mmsi')
            imo = vessel_data.get('imo')
            
            # Create position
            lat = vessel_data.get('lat', 0.0)
            lng = vessel_data.get('lng', 0.0)  # Note: MyShipTracking uses 'lng' not 'lon'
            
            if lat == 0 and lng == 0:
                # Skip vessels with no position data
                return None
                
            position = VesselPosition(
                latitude=lat,
                longitude=lng,
                timestamp=datetime.fromisoformat(vessel_data.get('received', '').replace('Z', '+00:00')),
                speed=vessel_data.get('speed', 0.0),
                course=vessel_data.get('course', 0.0)
            )
            
            # Determine vessel type
            vtype = vessel_data.get('vtype', 0)
            vessel_type_name = vessel_data.get('vessel_type', 'Unknown')
            
            # Map vessel type codes to our categories
            type_mapping = {
                1: 'Fishing',
                2: 'Tug',
                3: 'Passenger',
                4: 'High Speed Craft',
                5: 'Pilot',
                6: 'Passenger',  # Ferry
                7: 'Cargo',
                8: 'Tanker',
                9: 'Other'
            }
            
            vessel_type = type_mapping.get(vtype, 'Unknown')
            
            # Create vessel
            vessel = Vessel(
                mmsi=str(mmsi) if mmsi else '',
                imo=str(imo) if imo else '',
                name=vessel_name,
                vessel_type=vessel_type,
                flag=vessel_data.get('flag', ''),
                length=self._calculate_length(vessel_data),
                width=self._calculate_width(vessel_data),
                current_position=position,
                destination=vessel_data.get('destination', ''),
                eta=self._parse_eta(vessel_data.get('eta')),
                draught=vessel_data.get('draught', 0.0),
                status=self._parse_nav_status(vessel_data.get('nav_status')),
                data_source='myshiptracking'
            )
            
            return vessel
            
        except Exception as e:
            logger.error(f"Error parsing MyShipTracking vessel data: {e}")
            logger.debug(f"Vessel data: {vessel_data}")
            return None
    
    def _calculate_length(self, vessel_data: Dict[str, Any]) -> float:
        """Calculate vessel length from size dimensions"""
        size_a = vessel_data.get('size_a', 0) or 0
        size_b = vessel_data.get('size_b', 0) or 0
        return float(size_a + size_b) if (size_a and size_b) else 0.0
    
    def _calculate_width(self, vessel_data: Dict[str, Any]) -> float:
        """Calculate vessel width from size dimensions"""
        size_c = vessel_data.get('size_c', 0) or 0
        size_d = vessel_data.get('size_d', 0) or 0
        return float(size_c + size_d) if (size_c and size_d) else 0.0
    
    def _parse_eta(self, eta_str: Optional[str]) -> Optional[datetime]:
        """Parse ETA string to datetime"""
        if not eta_str:
            return None
        try:
            return datetime.fromisoformat(eta_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _parse_nav_status(self, nav_status: Optional[int]) -> str:
        """Parse navigation status code to string"""
        status_mapping = {
            0: 'Under way using engine',
            1: 'At anchor',
            2: 'Not under command',
            3: 'Restricted manoeuvrability',
            4: 'Constrained by her draught',
            5: 'Moored',
            6: 'Aground',
            7: 'Engaged in fishing',
            8: 'Under way sailing',
            15: 'Undefined'
        }
        return status_mapping.get(nav_status, 'Unknown')
    
    async def _collect_from_datalastic(self, region: Optional[str] = None) -> List[Vessel]:
        """Collect data from Datalastic API"""
        vessels = []
        
        headers = {
            'Authorization': f'Bearer {self.datalastic_api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # Get live vessel data
                url = "https://api.datalastic.com/api/v0/vessel_inradius"
                
                # Define zones for different regions
                zones = self._get_datalastic_zones(region)
                
                for zone in zones:
                    params = {
                        'api-key': self.datalastic_api_key,
                        'lat': zone['lat'],
                        'lon': zone['lon'],
                        'radius': zone['radius']
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('success') and 'data' in data:
                                for vessel_data in data['data']:
                                    vessel = self._parse_datalastic_vessel(vessel_data)
                                    if vessel:
                                        vessels.append(vessel)
                        
                        await asyncio.sleep(self.rate_limit_delay)
                        
            except Exception as e:
                logger.error(f"Datalastic API error: {e}")
                
        return vessels
    
    def _get_datalastic_zones(self, region: Optional[str] = None) -> List[Dict[str, float]]:
        """Get zones for Datalastic API based on region"""
        all_zones = {
            'strait_of_hormuz': [{'lat': 26.5667, 'lon': 56.2500, 'radius': 50}],
            'suez_canal': [{'lat': 30.5234, 'lon': 32.2502, 'radius': 30}],
            'singapore_strait': [{'lat': 1.290270, 'lon': 103.851959, 'radius': 30}],
            'english_channel': [{'lat': 50.5, 'lon': 1.0, 'radius': 50}],
            'bay_of_bengal': [{'lat': 15.0, 'lon': 90.0, 'radius': 200}],
        }
        
        if region and region in all_zones:
            return all_zones[region]
        
        # Return all major shipping zones if no specific region
        return [zone for zones in all_zones.values() for zone in zones]
    
    def _parse_datalastic_vessel(self, data: Dict[str, Any]) -> Optional[Vessel]:
        """Parse vessel data from Datalastic API response"""
        try:
            return Vessel(
                mmsi=data.get('mmsi'),
                imo=data.get('imo'),
                name=data.get('name', 'Unknown'),
                vessel_type=self._map_vessel_type(data.get('type')),
                country=data.get('country_name'),
                destination=data.get('destination'),
                eta=self._parse_datetime(data.get('eta_UTC')),
                current_position=VesselPosition(
                    latitude=float(data.get('lat', 0)),
                    longitude=float(data.get('lon', 0)),
                    speed=float(data.get('speed', 0)),
                    course=float(data.get('course', 0)),
                    timestamp=datetime.utcnow()
                ),
                length=data.get('length'),
                width=data.get('breadth'),
                draft=data.get('draught_avg'),
                gross_tonnage=data.get('gross_tonnage'),
                cargo_capacity=data.get('deadweight')
            )
        except Exception as e:
            logger.error(f"Error parsing Datalastic vessel data: {e}")
            return None
    
    def _map_vessel_type(self, api_type: str) -> str:
        """Map API vessel types to standard types"""
        if not api_type:
            return "Unknown"
        
        type_mapping = {
            'cargo': 'Cargo',
            'container': 'Container Ship',
            'tanker': 'Tanker',
            'passenger': 'Passenger Ship',
            'fishing': 'Fishing Vessel',
            'tug': 'Tug',
            'yacht': 'Yacht',
            'military': 'Military Vessel',
            'other': 'Other'
        }
        
        api_type_lower = api_type.lower()
        for key, value in type_mapping.items():
            if key in api_type_lower:
                return value
        
        return api_type.title()
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from API"""
        if not dt_str:
            return None
        
        try:
            # Try different datetime formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing datetime {dt_str}: {e}")
        
        return None
    
    async def _get_fallback_data(self, region: Optional[str] = None) -> List[Vessel]:
        """Fallback data when APIs are not available"""
        logger.info("Using fallback vessel data")
        
        # Create some realistic sample vessels based on real ship data
        fallback_vessels = [
            Vessel(
                mmsi=565100000,
                imo=9321483,
                name="EVER GIVEN",
                vessel_type="Container Ship",
                country="Panama",
                destination="ROTTERDAM",
                eta=datetime.utcnow() + timedelta(days=3),
                current_position=VesselPosition(
                    latitude=26.5667,
                    longitude=56.2500,
                    speed=12.5,
                    course=285,
                    timestamp=datetime.utcnow()
                ),
                length=400,
                width=59,
                draft=14.5,
                gross_tonnage=220940,
                cargo_capacity=20388
            ),
            Vessel(
                mmsi=477553000,
                imo=9395044,
                name="MSC GULSUN",
                vessel_type="Container Ship",
                country="Hong Kong",
                destination="SINGAPORE",
                eta=datetime.utcnow() + timedelta(days=1),
                current_position=VesselPosition(
                    latitude=1.290270,
                    longitude=103.851959,
                    speed=15.2,
                    course=45,
                    timestamp=datetime.utcnow()
                ),
                length=400,
                width=61,
                draft=16.0,
                gross_tonnage=232618,
                cargo_capacity=23756
            )
        ]
        
        return fallback_vessels

# Legacy collector for backward compatibility
class MockAISCollector(AISCollector):
    """Mock AIS collector - now redirects to real data collector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.warning("MockAISCollector is deprecated. Use AISCollector for real data.")
    
    async def collect_data(self, region: Optional[str] = None) -> List[Vessel]:
        """Collect data - now uses real AIS data or fallback"""
        return await super().collect_data(region) 