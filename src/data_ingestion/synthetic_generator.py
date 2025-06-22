"""
Synthetic AIS data generator for testing and simulation scenarios
"""

import random
import math
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from ..core.config import MAJOR_PORTS, SHIPPING_ROUTES
from ..models.vessel import VesselType, NavigationStatus, VesselPositionCreate


class SyntheticDataGenerator:
    """Generate realistic synthetic AIS data for testing and simulation"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        
        self.vessel_database = self._create_vessel_database()
        self.active_voyages = {}
        self.port_locations = MAJOR_PORTS
        self.routes = self._create_shipping_routes()
    
    def _create_vessel_database(self) -> List[Dict[str, Any]]:
        """Create a database of synthetic vessels"""
        vessels = []
        
        # Container ships
        for i in range(100):
            mmsi = 200000000 + i
            vessels.append({
                'mmsi': mmsi,
                'vessel_name': f'CONTAINER_SHIP_{i:03d}',
                'vessel_type': VesselType.CARGO,
                'length': random.uniform(200, 400),
                'max_speed': random.uniform(18, 25),
                'flag_country': random.choice(['US', 'CN', 'SG', 'DE', 'NL'])
            })
        
        # Tankers
        for i in range(50):
            mmsi = 400000000 + i
            vessels.append({
                'mmsi': mmsi,
                'vessel_name': f'TANKER_{i:03d}',
                'vessel_type': VesselType.TANKER,
                'length': random.uniform(180, 350),
                'max_speed': random.uniform(14, 20),
                'flag_country': random.choice(['US', 'NO', 'GR', 'SG'])
            })
        
        return vessels
    
    def _create_shipping_routes(self) -> List[Dict[str, Any]]:
        """Create realistic shipping routes between major ports"""
        routes = []
        
        # Major container routes
        container_routes = [
            ('SHANGHAI', 'LOS_ANGELES', 6200, 280),
            ('SHANGHAI', 'ROTTERDAM', 11800, 480),
            ('SINGAPORE', 'ROTTERDAM', 8300, 350),
            ('NINGBO', 'LONG_BEACH', 6000, 275),
            ('BUSAN', 'LOS_ANGELES', 5500, 250),
            ('HONG_KONG', 'NEW_YORK', 8900, 380),
            ('ROTTERDAM', 'NEW_YORK', 3500, 160),
            ('SINGAPORE', 'DUBAI', 3200, 140)
        ]
        
        for origin, destination, distance, duration in container_routes:
            routes.append({
                'origin': origin,
                'destination': destination,
                'distance_nm': distance,
                'duration_hours': duration,
                'route_type': 'container',
                'waypoints': self._generate_route_waypoints(
                    MAJOR_PORTS[origin], MAJOR_PORTS[destination], distance
                )
            })
        
        return routes
    
    def _generate_route_waypoints(self, origin: Dict, destination: Dict, distance_nm: float) -> List[Tuple[float, float]]:
        """Generate waypoints for a route using great circle interpolation"""
        lat1, lon1 = math.radians(origin['lat']), math.radians(origin['lon'])
        lat2, lon2 = math.radians(destination['lat']), math.radians(destination['lon'])
        
        # Calculate great circle distance
        d = math.acos(math.sin(lat1) * math.sin(lat2) + 
                      math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
        
        # Generate waypoints along the great circle
        waypoints = [(origin['lat'], origin['lon'])]
        num_waypoints = max(5, int(distance_nm / 500))  # Waypoint every ~500nm
        
        for i in range(1, num_waypoints):
            f = i / num_waypoints
            a = math.sin((1 - f) * d) / math.sin(d)
            b = math.sin(f * d) / math.sin(d)
            
            x = a * math.cos(lat1) * math.cos(lon1) + b * math.cos(lat2) * math.cos(lon2)
            y = a * math.cos(lat1) * math.sin(lon1) + b * math.cos(lat2) * math.sin(lon2)
            z = a * math.sin(lat1) + b * math.sin(lat2)
            
            lat = math.atan2(z, math.sqrt(x**2 + y**2))
            lon = math.atan2(y, x)
            
            waypoints.append((math.degrees(lat), math.degrees(lon)))
        
        waypoints.append((destination['lat'], destination['lon']))
        return waypoints
    
    def generate_vessel_position(self, vessel: Dict[str, Any], current_time: datetime) -> VesselPositionCreate:
        """Generate a realistic position for a vessel"""
        
        # Generate random position in shipping lanes
        latitude = random.uniform(-60, 70)
        longitude = random.uniform(-180, 180)
        
        # Generate realistic navigation data
        speed = random.uniform(0, vessel['max_speed'])
        course = random.uniform(0, 360)
        heading = course + random.gauss(0, 2)
        
        # Determine navigation status based on speed
        if speed < 0.5:
            nav_status = NavigationStatus.AT_ANCHOR
        elif speed < 2:
            nav_status = NavigationStatus.RESTRICTED_MANEUVERABILITY
        else:
            nav_status = NavigationStatus.UNDER_WAY_USING_ENGINE
        
        return VesselPositionCreate(
            mmsi=vessel['mmsi'],
            latitude=latitude,
            longitude=longitude,
            course_over_ground=course,
            speed_over_ground=speed,
            true_heading=heading,
            navigation_status=nav_status,
            timestamp=current_time,
            message_timestamp=current_time,
            data_source="synthetic"
        )
    
    def generate_batch_positions(self, vessel_count: int, current_time: datetime) -> List[VesselPositionCreate]:
        """Generate a batch of vessel positions"""
        positions = []
        selected_vessels = random.sample(
            self.vessel_database, 
            min(vessel_count, len(self.vessel_database))
        )
        
        for vessel in selected_vessels:
            position = self.generate_vessel_position(vessel, current_time)
            positions.append(position)
        
        return positions
    
    def generate_port_congestion_scenario(self, port_name: str, congestion_level: float) -> List[VesselPositionCreate]:
        """Generate a port congestion scenario"""
        if port_name not in MAJOR_PORTS:
            raise ValueError(f"Unknown port: {port_name}")
        
        port = MAJOR_PORTS[port_name]
        positions = []
        current_time = datetime.utcnow()
        
        # Number of vessels based on congestion level
        vessel_count = int(20 + congestion_level * 30)
        
        for i in range(vessel_count):
            vessel = random.choice(self.vessel_database)
            
            # Position vessels around the port
            distance = random.uniform(1, 15)  # 1-15 nm from port
            bearing = random.uniform(0, 360)
            
            lat_offset = distance * math.cos(math.radians(bearing)) / 60
            lon_offset = distance * math.sin(math.radians(bearing)) / 60
            
            latitude = port['lat'] + lat_offset
            longitude = port['lon'] + lon_offset
            
            # Vessels closer to port are more likely to be anchored
            if distance < 5:
                nav_status = NavigationStatus.AT_ANCHOR
                speed = random.uniform(0, 0.5)
            else:
                nav_status = NavigationStatus.UNDER_WAY_USING_ENGINE
                speed = random.uniform(2, 8)
            
            position = VesselPositionCreate(
                mmsi=vessel['mmsi'],
                latitude=latitude,
                longitude=longitude,
                course_over_ground=random.uniform(0, 360),
                speed_over_ground=speed,
                navigation_status=nav_status,
                destination=port_name,
                timestamp=current_time,
                message_timestamp=current_time,
                data_source="synthetic_congestion"
            )
            positions.append(position)
        
        return positions
    
    def generate_crisis_scenario(self, scenario_type: str) -> List[VesselPositionCreate]:
        """Generate crisis scenarios (canal blockage, weather, etc.)"""
        positions = []
        current_time = datetime.utcnow()
        
        if scenario_type == "suez_blockage":
            # Simulate vessels queuing at Suez Canal
            suez_north = (31.2653, 32.3424)
            suez_south = (29.9668, 32.5498)
            
            # Create queue of vessels
            for i in range(50):
                vessel = random.choice(self.vessel_database)
                
                # Position in queue
                queue_position = i * 0.5  # 0.5nm spacing
                
                if i % 2 == 0:  # North approach
                    lat = suez_north[0] + queue_position / 60
                    lon = suez_north[1]
                else:  # South approach
                    lat = suez_south[0] - queue_position / 60
                    lon = suez_south[1]
                
                position = VesselPositionCreate(
                    mmsi=vessel['mmsi'],
                    latitude=lat,
                    longitude=lon,
                    course_over_ground=0 if i % 2 == 0 else 180,
                    speed_over_ground=0,
                    navigation_status=NavigationStatus.AT_ANCHOR,
                    timestamp=current_time,
                    message_timestamp=current_time,
                    data_source="synthetic_crisis"
                )
                positions.append(position)
        
        return positions 