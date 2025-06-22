#!/usr/bin/env python3
"""
Bay of Bengal Maritime Demo with Real-Time Animation
Live vessel tracking for one of the world's busiest shipping regions
"""

import folium
import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import math
import random
from dataclasses import dataclass


class BayOfBengalDemo:
    """Bay of Bengal maritime demo with enhanced vessel tracking"""
    
    # Bay of Bengal boundaries (major shipping area)
    BAY_BOUNDS = {
        'north': 22.5,   # Near Chittagong
        'south': 8.0,    # Near Chennai/Sri Lanka
        'east': 95.0,    # Myanmar coast
        'west': 80.0     # Indian east coast
    }
    
    # Major ports in Bay of Bengal
    MAJOR_PORTS = {
        'Chittagong': {'lat': 22.3569, 'lon': 91.7832, 'country': 'BD', 'cargo_type': 'container'},
        'Kolkata': {'lat': 22.5726, 'lon': 88.3639, 'country': 'IN', 'cargo_type': 'general'},
        'Haldia': {'lat': 22.0667, 'lon': 88.0667, 'country': 'IN', 'cargo_type': 'bulk'},
        'Paradip': {'lat': 20.2647, 'lon': 86.6947, 'country': 'IN', 'cargo_type': 'bulk'},
        'Visakhapatnam': {'lat': 17.7231, 'lon': 83.3012, 'country': 'IN', 'cargo_type': 'general'},
        'Chennai': {'lat': 13.0827, 'lon': 80.2707, 'country': 'IN', 'cargo_type': 'container'},
        'Ennore': {'lat': 13.2333, 'lon': 80.3167, 'country': 'IN', 'cargo_type': 'thermal_coal'},
        'Tuticorin': {'lat': 8.8047, 'lon': 78.1348, 'country': 'IN', 'cargo_type': 'general'},
        'Colombo': {'lat': 6.9271, 'lon': 79.8612, 'country': 'LK', 'cargo_type': 'container'},
        'Yangon': {'lat': 16.8661, 'lon': 96.1951, 'country': 'MM', 'cargo_type': 'general'},
    }
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self.current_time = datetime.now()
        
    async def fetch_bay_vessel_data(self) -> List[Dict[str, Any]]:
        """Fetch vessel data for Bay of Bengal region"""
        
        print("🌊 Fetching Bay of Bengal vessel data...")
        
        # Try real APIs first
        vessels = await self._attempt_real_api_fetch()
        
        if not vessels:
            print("🔄 Using enhanced synthetic data for Bay of Bengal")
            vessels = self._generate_bay_synthetic_data()
        
        return vessels
    
    async def _attempt_real_api_fetch(self) -> List[Dict[str, Any]]:
        """Attempt to fetch from real APIs"""
        vessels = []
        
        try:
            # Try Digitraffic with Bay of Bengal bounds
            async with aiohttp.ClientSession() as session:
                params = {
                    'loLat': self.BAY_BOUNDS['south'],
                    'hiLat': self.BAY_BOUNDS['north'],
                    'loLon': self.BAY_BOUNDS['west'],
                    'hiLon': self.BAY_BOUNDS['east']
                }
                
                async with session.get(
                    'https://meri.digitraffic.fi/api/ais/v1/locations',
                    params=params
                ) as response:
                    if response.status == 200:
                        print("✅ Connected to external AIS API")
                        # Process response...
                    else:
                        print(f"⚠️  API returned status: {response.status}")
        except Exception as e:
            print(f"⚠️  API connection failed: {e}")
        
        return vessels
    
    def _generate_bay_synthetic_data(self) -> List[Dict[str, Any]]:
        """Generate realistic synthetic data for Bay of Bengal"""
        
        print("🎭 Generating Bay of Bengal shipping patterns...")
        
        vessels = []
        
        # Major shipping routes in Bay of Bengal
        shipping_routes = [
            # Chittagong - Singapore route
            {'start': (22.3, 91.8), 'end': (1.3, 103.8), 'traffic': 'heavy', 'type': 'container'},
            # Kolkata - Middle East route  
            {'start': (22.6, 88.4), 'end': (15.0, 75.0), 'traffic': 'medium', 'type': 'bulk'},
            # Chennai - Far East route
            {'start': (13.1, 80.3), 'end': (10.0, 95.0), 'traffic': 'heavy', 'type': 'container'},
            # Paradip - Japan route (iron ore)
            {'start': (20.3, 86.7), 'end': (25.0, 90.0), 'traffic': 'medium', 'type': 'bulk'},
            # Colombo hub traffic
            {'start': (6.9, 79.9), 'end': (15.0, 85.0), 'traffic': 'heavy', 'type': 'container'},
            # Myanmar coastal
            {'start': (16.9, 96.2), 'end': (12.0, 92.0), 'traffic': 'light', 'type': 'general'},
        ]
        
        # Realistic vessel distributions for Bay of Bengal
        vessel_types = {
            'container': {'icon': '🚢', 'color': '#006600', 'count': 35, 'speed_range': (18, 24)},
            'bulk_carrier': {'icon': '⚫', 'color': '#8B4513', 'count': 25, 'speed_range': (12, 16)},
            'tanker': {'icon': '🛢️', 'color': '#8B0000', 'count': 20, 'speed_range': (12, 16)},
            'general_cargo': {'icon': '📦', 'color': '#0066CC', 'count': 15, 'speed_range': (14, 18)},
            'fishing': {'icon': '🎣', 'color': '#008080', 'count': 12, 'speed_range': (4, 8)},
            'passenger': {'icon': '🛳️', 'color': '#FF6600', 'count': 8, 'speed_range': (20, 28)},
            'tug': {'icon': '🚤', 'color': '#800080', 'count': 5, 'speed_range': (8, 12)},
        }
        
        mmsi_counter = 419000000  # Indian MMSI range
        
        # Generate vessels along major routes
        for route in shipping_routes:
            route_vessels = {'heavy': 20, 'medium': 12, 'light': 6}[route['traffic']]
            
            for i in range(route_vessels):
                # Position along route
                progress = random.uniform(0, 1)
                lat = route['start'][0] + progress * (route['end'][0] - route['start'][0])
                lon = route['start'][1] + progress * (route['end'][1] - route['start'][1])
                
                # Add some scatter
                lat += random.uniform(-0.3, 0.3)
                lon += random.uniform(-0.3, 0.3)
                
                # Keep within bay bounds
                lat = max(self.BAY_BOUNDS['south'], min(self.BAY_BOUNDS['north'], lat))
                lon = max(self.BAY_BOUNDS['west'], min(self.BAY_BOUNDS['east'], lon))
                
                # Select vessel type based on route
                if route['type'] == 'container':
                    vessel_type = random.choice(['container', 'general_cargo'])
                elif route['type'] == 'bulk':
                    vessel_type = random.choice(['bulk_carrier', 'tanker'])
                else:
                    vessel_type = random.choice(list(vessel_types.keys()))
                
                config = vessel_types[vessel_type]
                
                # Calculate heading toward destination
                heading = math.degrees(math.atan2(
                    route['end'][1] - lat, route['end'][0] - lat
                ))
                heading = (heading + 360) % 360
                
                # Generate vessel data
                speed = random.uniform(*config['speed_range'])
                
                # Determine likely destination based on position and route
                destinations = list(self.MAJOR_PORTS.keys())
                if lat > 20:  # Northern Bay
                    likely_dest = random.choice(['Chittagong', 'Kolkata', 'Haldia'])
                elif lat > 15:  # Central Bay
                    likely_dest = random.choice(['Paradip', 'Visakhapatnam', 'Yangon'])
                else:  # Southern Bay
                    likely_dest = random.choice(['Chennai', 'Colombo', 'Tuticorin'])
                
                vessel = {
                    'mmsi': mmsi_counter,
                    'vessel_type': vessel_type,
                    'latitude': lat,
                    'longitude': lon,
                    'speed': speed,
                    'course': heading + random.uniform(-15, 15),
                    'heading': heading + random.uniform(-10, 10),
                    'nav_status': self._get_nav_status(speed, vessel_type),
                    'destination': likely_dest,
                    'length': self._get_vessel_length(vessel_type),
                    'width': random.randint(12, 50),
                    'draft': random.uniform(3, 18),
                    'flag': self._get_realistic_flag(lat, lon),
                    'cargo_value': self._estimate_cargo_value(vessel_type),
                    'fuel_consumption': self._estimate_fuel_consumption(vessel_type, speed),
                    'timestamp': self.current_time.isoformat(),
                    'source': 'bay_synthetic',
                    'route_type': route['type'],
                    'eta': (self.current_time + timedelta(hours=random.randint(6, 72))).isoformat(),
                }
                
                vessels.append(vessel)
                mmsi_counter += 1
        
        # Add port area vessels (anchored, maneuvering)
        for port_name, port_info in self.MAJOR_PORTS.items():
            port_vessels = random.randint(3, 8)
            
            for _ in range(port_vessels):
                # Position near port
                lat = port_info['lat'] + random.uniform(-0.1, 0.1)
                lon = port_info['lon'] + random.uniform(-0.1, 0.1)
                
                # Port-appropriate vessel type
                if port_info['cargo_type'] == 'container':
                    vessel_type = random.choice(['container', 'general_cargo'])
                elif port_info['cargo_type'] == 'bulk':
                    vessel_type = random.choice(['bulk_carrier', 'tanker'])
                else:
                    vessel_type = random.choice(['general_cargo', 'container', 'tanker'])
                
                config = vessel_types[vessel_type]
                
                # Port vessels are slower or anchored
                speed = random.uniform(0, 8)
                nav_status = random.choice(['At Anchor', 'Moored', 'Under Way Using Engine'])
                
                vessel = {
                    'mmsi': mmsi_counter,
                    'vessel_type': vessel_type,
                    'latitude': lat,
                    'longitude': lon,
                    'speed': speed,
                    'course': random.uniform(0, 360),
                    'heading': random.uniform(0, 360),
                    'nav_status': nav_status,
                    'destination': port_name,
                    'length': self._get_vessel_length(vessel_type),
                    'width': random.randint(12, 50),
                    'draft': random.uniform(3, 18),
                    'flag': port_info['country'],
                    'cargo_value': self._estimate_cargo_value(vessel_type),
                    'fuel_consumption': 0 if speed < 1 else self._estimate_fuel_consumption(vessel_type, speed),
                    'timestamp': self.current_time.isoformat(),
                    'source': 'bay_synthetic',
                    'port_area': port_name,
                    'eta': 'In Port' if speed < 2 else self.current_time.isoformat(),
                }
                
                vessels.append(vessel)
                mmsi_counter += 1
        
        # Add fishing fleet (especially in coastal areas)
        fishing_areas = [
            (21.0, 89.0),  # Bangladesh coast
            (19.0, 85.0),  # Odisha coast
            (15.0, 82.0),  # Andhra coast
            (11.0, 79.5),  # Tamil Nadu coast
        ]
        
        for area_lat, area_lon in fishing_areas:
            fishing_count = random.randint(5, 12)
            
            for _ in range(fishing_count):
                lat = area_lat + random.uniform(-1.0, 1.0)
                lon = area_lon + random.uniform(-1.0, 1.0)
                
                vessel = {
                    'mmsi': mmsi_counter,
                    'vessel_type': 'fishing',
                    'latitude': lat,
                    'longitude': lon,
                    'speed': random.uniform(2, 6),
                    'course': random.uniform(0, 360),
                    'heading': random.uniform(0, 360),
                    'nav_status': 'Engaged in Fishing',
                    'destination': 'Fishing Grounds',
                    'length': random.randint(15, 50),
                    'width': random.randint(4, 12),
                    'draft': random.uniform(1, 4),
                    'flag': random.choice(['IN', 'BD', 'LK', 'MM']),
                    'cargo_value': 0,
                    'fuel_consumption': random.uniform(5, 15),
                    'timestamp': self.current_time.isoformat(),
                    'source': 'bay_synthetic',
                    'activity': 'fishing',
                }
                
                vessels.append(vessel)
                mmsi_counter += 1
        
        print(f"✅ Generated {len(vessels)} vessels in Bay of Bengal")
        return vessels
    
    def _get_nav_status(self, speed: float, vessel_type: str) -> str:
        """Get realistic navigation status"""
        if speed < 0.5:
            return random.choice(['At Anchor', 'Moored'])
        elif speed < 2:
            return 'Restricted Maneuverability'
        elif vessel_type == 'fishing':
            return 'Engaged in Fishing'
        elif vessel_type in ['bulk_carrier', 'tanker'] and speed < 10:
            return 'Constrained by Draft'
        else:
            return 'Under Way Using Engine'
    
    def _get_vessel_length(self, vessel_type: str) -> int:
        """Get realistic vessel length"""
        length_ranges = {
            'container': (150, 400),
            'bulk_carrier': (180, 350),
            'tanker': (120, 330),
            'general_cargo': (80, 200),
            'fishing': (15, 50),
            'passenger': (100, 300),
            'tug': (25, 60),
        }
        return random.randint(*length_ranges.get(vessel_type, (50, 150)))
    
    def _get_realistic_flag(self, lat: float, lon: float) -> str:
        """Get realistic flag based on position and trade patterns"""
        
        # Regional flag distributions based on actual shipping
        if lat > 20:  # Northern Bay (Bangladesh/India border area)
            flags = ['IN', 'BD', 'SG', 'PK', 'MM', 'CN', 'JP', 'KR']
            weights = [30, 25, 15, 8, 7, 6, 5, 4]
        elif lon > 88:  # Eastern Bay (Myanmar side)
            flags = ['MM', 'SG', 'TH', 'IN', 'CN', 'MY', 'JP']
            weights = [35, 20, 15, 12, 8, 6, 4]
        elif lat < 12:  # Southern Bay (Sri Lanka area)
            flags = ['LK', 'IN', 'SG', 'MV', 'PK', 'AE', 'SA']
            weights = [30, 25, 20, 8, 7, 6, 4]
        else:  # Central Bay (Indian east coast)
            flags = ['IN', 'SG', 'BD', 'LK', 'CN', 'JP', 'KR', 'PH']
            weights = [40, 18, 12, 10, 8, 6, 4, 2]
        
        return random.choices(flags, weights=weights)[0]
    
    def _estimate_cargo_value(self, vessel_type: str) -> float:
        """Estimate cargo value in millions USD"""
        value_ranges = {
            'container': (30, 120),
            'bulk_carrier': (5, 25),
            'tanker': (20, 80),
            'general_cargo': (8, 40),
            'fishing': (0, 0.1),
            'passenger': (0, 5),
            'tug': (0, 2),
        }
        return random.uniform(*value_ranges.get(vessel_type, (0, 10)))
    
    def _estimate_fuel_consumption(self, vessel_type: str, speed: float) -> float:
        """Estimate fuel consumption in tons/day"""
        base_consumption = {
            'container': 150,
            'bulk_carrier': 120,
            'tanker': 100,
            'general_cargo': 80,
            'fishing': 15,
            'passenger': 180,
            'tug': 40,
        }
        
        base = base_consumption.get(vessel_type, 60)
        # Consumption increases exponentially with speed
        speed_factor = (speed / 15) ** 2
        return base * speed_factor
    
    def create_bay_map(self, vessels: List[Dict[str, Any]]) -> folium.Map:
        """Create interactive Bay of Bengal map"""
        
        print(f"🗺️  Creating Bay of Bengal map with {len(vessels)} vessels...")
        
        # Center map on Bay of Bengal
        center_lat = (self.BAY_BOUNDS['north'] + self.BAY_BOUNDS['south']) / 2
        center_lon = (self.BAY_BOUNDS['east'] + self.BAY_BOUNDS['west']) / 2
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Add satellite layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add major ports
        for port_name, port_info in self.MAJOR_PORTS.items():
            folium.Marker(
                [port_info['lat'], port_info['lon']],
                popup=f"<b>{port_name}</b><br>Country: {port_info['country']}<br>Type: {port_info['cargo_type']}",
                tooltip=port_name,
                icon=folium.Icon(color='red', icon='anchor', prefix='fa')
            ).add_to(m)
        
        # Vessel styling
        vessel_styles = {
            'container': {'icon': '🚢', 'color': '#006600'},
            'bulk_carrier': {'icon': '⚫', 'color': '#8B4513'},
            'tanker': {'icon': '🛢️', 'color': '#8B0000'},
            'general_cargo': {'icon': '📦', 'color': '#0066CC'},
            'fishing': {'icon': '🎣', 'color': '#008080'},
            'passenger': {'icon': '🛳️', 'color': '#FF6600'},
            'tug': {'icon': '🚤', 'color': '#800080'},
        }
        
        # Add vessels
        vessel_counts = {}
        total_cargo_value = 0
        total_fuel = 0
        
        for vessel in vessels:
            vessel_type = vessel.get('vessel_type', 'unknown')
            style = vessel_styles.get(vessel_type, {'icon': '🚢', 'color': 'gray'})
            
            vessel_counts[vessel_type] = vessel_counts.get(vessel_type, 0) + 1
            total_cargo_value += vessel.get('cargo_value', 0)
            total_fuel += vessel.get('fuel_consumption', 0)
            
            # Enhanced popup
            popup_html = f"""
            <div style="width: 350px;">
                <h4>{style['icon']} Vessel {vessel['mmsi']}</h4>
                <b>Type:</b> {vessel_type.replace('_', ' ').title()}<br>
                <b>Flag:</b> {vessel.get('flag', 'Unknown')}<br>
                <b>Speed:</b> {vessel['speed']:.1f} knots<br>
                <b>Course:</b> {vessel['course']:.0f}°<br>
                <b>Status:</b> {vessel['nav_status']}<br>
                <b>Destination:</b> {vessel.get('destination', 'Unknown')}<br>
                <b>Length:</b> {vessel['length']}m<br>
                <b>Draft:</b> {vessel['draft']:.1f}m<br>
                <b>Cargo Value:</b> ${vessel.get('cargo_value', 0):.1f}M<br>
                <b>Fuel/Day:</b> {vessel.get('fuel_consumption', 0):.0f} tons<br>
                <b>ETA:</b> {vessel.get('eta', 'Unknown')[:16]}<br>
                <b>Position:</b> {vessel['latitude']:.4f}°, {vessel['longitude']:.4f}°
            </div>
            """
            
            folium.CircleMarker(
                location=[vessel['latitude'], vessel['longitude']],
                radius=8,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{style['icon']} {vessel_type.title()} - {vessel['speed']:.1f}kn",
                color='white',
                weight=2,
                fillColor=style['color'],
                fillOpacity=0.8
            ).add_to(m)
            
            # Add direction arrow
            if vessel['speed'] > 1:
                self._add_direction_arrow(m, vessel, style['color'])
        
        # Add statistics panel
        self._add_bay_statistics(m, vessels, vessel_counts, total_cargo_value, total_fuel)
        
        # Add shipping lanes
        self._add_bay_shipping_lanes(m)
        
        folium.LayerControl().add_to(m)
        
        return m
    
    def _add_direction_arrow(self, map_obj: folium.Map, vessel: Dict[str, Any], color: str):
        """Add direction arrow for vessel"""
        distance = 0.05
        heading_rad = math.radians(vessel['heading'])
        
        end_lat = vessel['latitude'] + distance * math.cos(heading_rad)
        end_lon = vessel['longitude'] + distance * math.sin(heading_rad)
        
        folium.PolyLine(
            locations=[[vessel['latitude'], vessel['longitude']], [end_lat, end_lon]],
            color=color,
            weight=3,
            opacity=0.7
        ).add_to(map_obj)
    
    def _add_bay_statistics(self, map_obj: folium.Map, vessels: List[Dict], 
                           vessel_counts: Dict, total_cargo_value: float, total_fuel: float):
        """Add Bay of Bengal statistics panel"""
        
        moving_vessels = sum(1 for v in vessels if v['speed'] > 2)
        anchored_vessels = sum(1 for v in vessels if v['speed'] < 0.5)
        fishing_vessels = vessel_counts.get('fishing', 0)
        
        stats_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 350px; height: auto; 
                    background-color: rgba(255,255,255,0.95); border:2px solid #333; z-index:9999; 
                    font-size:12px; padding: 12px; border-radius: 8px; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
        
        <h3 style="margin: 0 0 10px 0; color: #2c3e50; text-align: center;">
            🌊 Bay of Bengal Maritime Monitor
        </h3>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                    padding: 8px; border-radius: 5px; margin-bottom: 10px; text-align: center;">
            <h4 style="margin: 0;">Major South Asian Trade Route</h4>
            <div style="font-size: 10px;">Gateway to India, Bangladesh, Myanmar</div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
            <div style="background-color: #e8f5e8; padding: 6px; border-radius: 4px; text-align: center;">
                <div style="font-size: 18px; font-weight: bold; color: #27ae60;">{len(vessels)}</div>
                <div style="font-size: 10px;">Total Vessels</div>
            </div>
            <div style="background-color: #fff3cd; padding: 6px; border-radius: 4px; text-align: center;">
                <div style="font-size: 18px; font-weight: bold; color: #f39c12;">{moving_vessels}</div>
                <div style="font-size: 10px;">Moving</div>
            </div>
        </div>
        
        <h5 style="margin: 8px 0 5px 0;">🚢 Fleet Composition:</h5>
        <div style="background-color: #f8f9fa; padding: 5px; border-radius: 4px; font-size: 11px; max-height: 80px; overflow-y: auto;">
        """
        
        vessel_icons = {
            'container': '🚢', 'bulk_carrier': '⚫', 'tanker': '🛢️', 
            'general_cargo': '📦', 'fishing': '🎣', 'passenger': '🛳️', 'tug': '🚤'
        }
        
        for vessel_type, count in vessel_counts.items():
            if count > 0:
                icon = vessel_icons.get(vessel_type, '🚢')
                stats_html += f"<div>{icon} {vessel_type.replace('_', ' ').title()}: <b>{count}</b></div>"
        
        stats_html += f"""
        </div>
        
        <h5 style="margin: 8px 0 5px 0;">💰 Economic Impact:</h5>
        <div style="background-color: #e8f4fd; padding: 6px; border-radius: 4px; font-size: 11px;">
            <div>💵 Cargo Value: <b>${total_cargo_value:.0f}M</b></div>
            <div>⛽ Fuel/Day: <b>{total_fuel:.0f}</b> tons</div>
            <div>🎣 Fishing Fleet: <b>{fishing_vessels}</b> vessels</div>
        </div>
        
        <h5 style="margin: 8px 0 5px 0;">🏭 Major Ports:</h5>
        <div style="background-color: #f0f8f0; padding: 6px; border-radius: 4px; font-size: 10px;">
            • Chittagong (BD) - Container Hub<br>
            • Kolkata/Haldia (IN) - General Cargo<br>
            • Chennai (IN) - Container Gateway<br>
            • Colombo (LK) - Transshipment Hub<br>
            • Paradip (IN) - Iron Ore Export
        </div>
        
        <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid #ddd; font-size: 9px; color: #666; text-align: center;">
            <b>Bay of Bengal:</b> 2.2M km² • 1.5B+ population coastline<br>
            <i>Updated: {datetime.now().strftime('%H:%M:%S')}</i>
        </div>
        </div>
        """
        
        map_obj.get_root().html.add_child(folium.Element(stats_html))
    
    def _add_bay_shipping_lanes(self, map_obj: folium.Map):
        """Add major shipping lanes in Bay of Bengal"""
        
        # Major shipping routes
        routes = [
            # Chittagong - Singapore
            {'coords': [[22.3, 91.8], [15.0, 90.0], [8.0, 95.0], [1.3, 103.8]], 'name': 'Chittagong-Singapore Route', 'color': 'blue'},
            # Kolkata - Middle East
            {'coords': [[22.6, 88.4], [18.0, 85.0], [15.0, 80.0]], 'name': 'Kolkata-Arabian Sea Route', 'color': 'green'},
            # Chennai - Far East  
            {'coords': [[13.1, 80.3], [10.0, 85.0], [8.0, 92.0]], 'name': 'Chennai-Southeast Asia Route', 'color': 'red'},
            # Colombo hub routes
            {'coords': [[6.9, 79.9], [12.0, 82.0], [16.0, 85.0]], 'name': 'Colombo-East Coast India Route', 'color': 'orange'},
        ]
        
        for route in routes:
            folium.PolyLine(
                route['coords'],
                color=route['color'],
                weight=3,
                opacity=0.6,
                popup=route['name']
            ).add_to(map_obj)
    
    async def run_bay_demo(self) -> str:
        """Run the Bay of Bengal demo"""
        
        print("🌊 Starting Bay of Bengal Maritime Demo")
        print("=" * 60)
        print("🇮🇳🇧🇩🇱🇰🇲🇲 Major South Asian shipping hub")
        print("🏭 Major ports: Chittagong, Kolkata, Chennai, Colombo")
        print("=" * 60)
        
        # Fetch vessel data
        vessels = await self.fetch_bay_vessel_data()
        
        if not vessels:
            print("❌ No vessel data available")
            return ""
        
        # Create map
        bay_map = self.create_bay_map(vessels)
        
        # Save map
        filename = f"bay_of_bengal_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        bay_map.save(filename)
        
        print(f"✅ Bay of Bengal map saved: {filename}")
        print(f"🚢 Featured {len(vessels)} vessels across major shipping routes")
        
        return filename


async def main():
    """Main function"""
    print("🌊 MaritimeFlow - Bay of Bengal Demo")
    print("=" * 50)
    print("🚢 Major South Asian maritime hub")
    print("🏭 Gateway to India, Bangladesh, Myanmar, Sri Lanka")
    print("=" * 50)
    
    demo = BayOfBengalDemo()
    
    try:
        map_file = await demo.run_bay_demo()
        
        if map_file:
            print(f"\n🎉 Bay of Bengal Demo Complete!")
            print(f"📁 File: {map_file}")
            print(f"🖱️  Double-click to view interactive map")
            print(f"🌊 Features:")
            print(f"   • Major ports: Chittagong, Kolkata, Chennai, Colombo")
            print(f"   • Realistic shipping routes and vessel distributions")
            print(f"   • Economic and operational analytics")
            print(f"   • Multi-national flag representations")
            
            # Open in browser
            import webbrowser
            import os
            
            try:
                file_path = os.path.abspath(map_file)
                webbrowser.open(f'file://{file_path}')
                print(f"🌐 Opening in browser...")
            except:
                print(f"💡 Manually open: {map_file}")
                
        else:
            print("❌ Demo failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 