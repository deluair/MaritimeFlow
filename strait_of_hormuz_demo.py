#!/usr/bin/env python3
"""
Strait of Hormuz Live Demo
Interactive map showing real-time vessel traffic through the world's most critical oil chokepoint
"""

import folium
import random
import math
from datetime import datetime
from typing import List, Dict, Any

from src.data_ingestion.synthetic_generator import SyntheticDataGenerator
from src.models.vessel import VesselType, NavigationStatus, VesselPositionCreate


class StraitOfHormuzDemo:
    """Demo class for visualizing vessel traffic in the Strait of Hormuz"""
    
    # Strait of Hormuz geographic boundaries
    STRAIT_BOUNDS = {
        'north': 26.8,
        'south': 25.8,
        'east': 57.2,
        'west': 55.8
    }
    
    # Key locations in the Strait
    KEY_LOCATIONS = {
        'Bandar Abbas': (27.1833, 56.2667),  # Major Iranian port
        'Khasab': (26.1833, 56.2500),        # Oman port
        'Strait Center': (26.3, 56.3),       # Central chokepoint
        'Qeshm Island': (26.9500, 56.2667),  # Strategic island
        'Hormuz Island': (27.0667, 56.4667), # Historic island
    }
    
    def __init__(self):
        self.generator = SyntheticDataGenerator(seed=42)
        
    def generate_strait_vessels(self, count: int = 50) -> List[VesselPositionCreate]:
        """Generate realistic vessel positions in the Strait of Hormuz"""
        
        vessels = []
        current_time = datetime.now()
        
        # Generate different types of vessels with realistic distributions
        vessel_configs = [
            # Oil tankers (40% - primary traffic)
            {'type': VesselType.TANKER, 'count': int(count * 0.4), 'speed_range': (8, 15)},
            # Cargo ships (25%)
            {'type': VesselType.CARGO, 'count': int(count * 0.25), 'speed_range': (12, 20)},
            # High speed craft (15%)
            {'type': VesselType.HIGH_SPEED_CRAFT, 'count': int(count * 0.15), 'speed_range': (20, 35)},
            # Naval/patrol vessels (10%)
            {'type': VesselType.MILITARY, 'count': int(count * 0.1), 'speed_range': (15, 25)},
            # Fishing vessels (5%)
            {'type': VesselType.FISHING, 'count': int(count * 0.05), 'speed_range': (5, 12)},
            # Other vessels (5%)
            {'type': VesselType.TUG, 'count': int(count * 0.05), 'speed_range': (8, 14)},
        ]
        
        for config in vessel_configs:
            for _ in range(config['count']):
                # Generate position within strait boundaries
                lat = random.uniform(self.STRAIT_BOUNDS['south'], self.STRAIT_BOUNDS['north'])
                lon = random.uniform(self.STRAIT_BOUNDS['west'], self.STRAIT_BOUNDS['east'])
                
                # Generate realistic navigation patterns
                if config['type'] == VesselType.TANKER:
                    # Tankers often move slowly through the strait
                    nav_status = random.choice([
                        NavigationStatus.UNDER_WAY_USING_ENGINE,
                        NavigationStatus.RESTRICTED_MANEUVERABILITY,
                        NavigationStatus.CONSTRAINED_BY_DRAFT
                    ])
                elif config['type'] == VesselType.MILITARY:
                    # Military vessels patrol
                    nav_status = random.choice([
                        NavigationStatus.UNDER_WAY_USING_ENGINE,
                        NavigationStatus.FISHING  # Patrol activity
                    ])
                else:
                    nav_status = NavigationStatus.UNDER_WAY_USING_ENGINE
                
                # Generate MMSI and vessel details
                mmsi = random.randint(200000000, 799999999)
                speed = random.uniform(*config['speed_range'])
                course = random.uniform(0, 360)
                
                # Create position using VesselPositionCreate model
                position = VesselPositionCreate(
                    mmsi=mmsi,
                    latitude=lat,
                    longitude=lon,
                    speed_over_ground=speed,
                    course_over_ground=course,
                    true_heading=course + random.uniform(-10, 10),
                    navigation_status=nav_status,
                    timestamp=current_time,
                    message_timestamp=current_time,
                    data_source="strait_hormuz_demo"
                )
                
                # Add vessel type as additional metadata
                position.vessel_type = config['type']
                position.length = random.randint(50, 400)
                position.width = random.randint(10, 60)
                position.draft = random.uniform(5, 20)
                
                vessels.append(position)
        
        return vessels
    
    def create_interactive_map(self, vessels: List[VesselPositionCreate]) -> folium.Map:
        """Create an interactive Folium map of the Strait of Hormuz"""
        
        # Create map centered on the Strait
        center_lat = (self.STRAIT_BOUNDS['north'] + self.STRAIT_BOUNDS['south']) / 2
        center_lon = (self.STRAIT_BOUNDS['east'] + self.STRAIT_BOUNDS['west']) / 2
        
        strait_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add satellite imagery option
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(strait_map)
        
        # Add key locations
        for location_name, (lat, lon) in self.KEY_LOCATIONS.items():
            folium.Marker(
                [lat, lon],
                popup=f"<b>{location_name}</b>",
                tooltip=location_name,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(strait_map)
        
        # Define vessel type colors and icons
        vessel_styles = {
            VesselType.TANKER: {'color': 'darkred', 'icon': '🛢️'},
            VesselType.CARGO: {'color': 'blue', 'icon': '📦'},
            VesselType.HIGH_SPEED_CRAFT: {'color': 'lightblue', 'icon': '🚤'},
            VesselType.MILITARY: {'color': 'black', 'icon': '⚓'},
            VesselType.FISHING: {'color': 'green', 'icon': '🎣'},
            VesselType.TUG: {'color': 'orange', 'icon': '🚛'},
        }
        
        # Add vessels to map
        vessel_counts = {}
        for vessel in vessels:
            vessel_type = getattr(vessel, 'vessel_type', VesselType.UNKNOWN)
            style = vessel_styles.get(vessel_type, {'color': 'gray', 'icon': '🚢'})
            
            # Count vessels by type
            vessel_counts[vessel_type] = vessel_counts.get(vessel_type, 0) + 1
            
            # Create popup with vessel information
            popup_html = f"""
            <div style="width: 300px;">
                <h4>{style['icon']} Vessel {vessel.mmsi}</h4>
                <b>Type:</b> {vessel_type.value}<br>
                <b>Speed:</b> {vessel.speed_over_ground:.1f} knots<br>
                <b>Course:</b> {vessel.course_over_ground:.0f}°<br>
                <b>Status:</b> {vessel.navigation_status.value}<br>
                <b>Length:</b> {getattr(vessel, 'length', 'N/A')}m<br>
                <b>Draft:</b> {getattr(vessel, 'draft', 0):.1f}m<br>
                <b>Position:</b> {vessel.latitude:.4f}°, {vessel.longitude:.4f}°<br>
                <b>Time:</b> {vessel.timestamp.strftime('%H:%M:%S UTC')}
            </div>
            """
            
            # Add vessel marker
            folium.CircleMarker(
                location=[vessel.latitude, vessel.longitude],
                radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{style['icon']} {vessel_type.value} - {vessel.speed_over_ground:.1f}kn",
                color='white',
                weight=2,
                fillColor=style['color'],
                fillOpacity=0.8
            ).add_to(strait_map)
            
            # Add speed vector (direction arrow)
            if vessel.speed_over_ground > 2:  # Only show for moving vessels
                # Calculate arrow end point
                distance = 0.01  # degrees
                course_rad = math.radians(vessel.course_over_ground)
                end_lat = vessel.latitude + distance * math.cos(course_rad)
                end_lon = vessel.longitude + distance * math.sin(course_rad)
                
                folium.PolyLine(
                    locations=[[vessel.latitude, vessel.longitude], [end_lat, end_lon]],
                    color=style['color'],
                    weight=3,
                    opacity=0.8
                ).add_to(strait_map)
        
        # Add traffic statistics
        stats_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 250px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>🚢 Strait of Hormuz Traffic</h4>
        <p><b>Critical Chokepoint Monitor</b></p>
        <p><b>Total Vessels:</b> {len(vessels)}</p>
        """
        
        for vessel_type, count in vessel_counts.items():
            icon = vessel_styles.get(vessel_type, {}).get('icon', '🚢')
            stats_html += f"<p>{icon} {vessel_type.value}: {count}</p>"
        
        stats_html += f"""
        <p><b>Strategic Importance:</b><br>
        • 21% of global petroleum liquids<br>
        • $1.2 trillion annual trade value<br>
        • 21km width at narrowest point</p>
        <p><i>Last Update: {datetime.now().strftime('%H:%M:%S UTC')}</i></p>
        </div>
        """
        
        strait_map.get_root().html.add_child(folium.Element(stats_html))
        
        # Add layer control
        folium.LayerControl().add_to(strait_map)
        
        return strait_map
    
    def run_demo(self, vessel_count: int = 50) -> str:
        """Run the complete Strait of Hormuz demo"""
        
        print("🚢 Generating Strait of Hormuz Traffic Scenario...")
        print("=" * 60)
        
        # Generate vessels
        vessels = self.generate_strait_vessels(vessel_count)
        
        print(f"✅ Generated {len(vessels)} vessels in the Strait of Hormuz")
        
        # Analyze traffic
        vessel_types = {}
        total_speed = 0
        moving_vessels = 0
        
        for vessel in vessels:
            vessel_type = getattr(vessel, 'vessel_type', VesselType.UNKNOWN)
            vessel_types[vessel_type] = vessel_types.get(vessel_type, 0) + 1
            if vessel.speed_over_ground > 2:
                total_speed += vessel.speed_over_ground
                moving_vessels += 1
        
        print("\n📊 Traffic Analysis:")
        for vessel_type, count in vessel_types.items():
            percentage = (count / len(vessels)) * 100
            print(f"   {vessel_type.value}: {count} vessels ({percentage:.1f}%)")
        
        if moving_vessels > 0:
            avg_speed = total_speed / moving_vessels
            print(f"\n🎯 Average Speed: {avg_speed:.1f} knots")
        
        print(f"\n🌊 Strategic Significance:")
        print(f"   • World's most important oil transit chokepoint")
        print(f"   • 21% of global petroleum liquids pass through here")
        print(f"   • Annual trade value: $1.2 trillion")
        print(f"   • Narrowest point: 21 nautical miles wide")
        
        # Create interactive map
        print(f"\n🗺️  Creating interactive map...")
        strait_map = self.create_interactive_map(vessels)
        
        # Save map
        map_filename = "strait_of_hormuz_live_demo.html"
        strait_map.save(map_filename)
        
        print(f"✅ Interactive map saved as: {map_filename}")
        print(f"🌐 Open the file in your web browser to view the live demo!")
        
        return map_filename


def main():
    """Main demo function"""
    print("🚢 MaritimeFlow - Strait of Hormuz Live Demo")
    print("=" * 50)
    print("Monitoring the world's most critical shipping chokepoint")
    print("Real-time vessel traffic simulation with maritime intelligence")
    print("=" * 50)
    
    # Create and run demo
    demo = StraitOfHormuzDemo()
    map_file = demo.run_demo(vessel_count=60)
    
    print(f"\n🎉 Demo Complete!")
    print(f"📁 Map file: {map_file}")
    print(f"🌐 Double-click the HTML file to open in your browser")
    print(f"🔍 Click on vessels to see detailed information")
    print(f"📊 Traffic statistics are shown in the top-right corner")
    
    return map_file


if __name__ == "__main__":
    main() 