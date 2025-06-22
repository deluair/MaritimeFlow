#!/usr/bin/env python3
"""
Strait of Hormuz Live Demo - Simplified Version
Interactive map showing vessel traffic through the critical oil chokepoint
"""

import folium
import random
import math
from datetime import datetime
from typing import List, Dict, Any


class StraitOfHormuzDemo:
    """Simplified demo for visualizing vessel traffic in the Strait of Hormuz"""
    
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
    
    # Vessel types and their characteristics
    VESSEL_TYPES = {
        'tanker': {'icon': '🛢️', 'color': 'darkred', 'speed_range': (8, 15), 'percentage': 40},
        'cargo': {'icon': '📦', 'color': 'blue', 'speed_range': (12, 20), 'percentage': 25},
        'container': {'icon': '🚢', 'color': 'green', 'speed_range': (15, 22), 'percentage': 15},
        'military': {'icon': '⚓', 'color': 'black', 'speed_range': (15, 30), 'percentage': 10},
        'fishing': {'icon': '🎣', 'color': 'orange', 'speed_range': (5, 12), 'percentage': 5},
        'patrol': {'icon': '🚤', 'color': 'purple', 'speed_range': (20, 35), 'percentage': 5},
    }
    
    def generate_strait_vessels(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate realistic vessel data for the Strait of Hormuz"""
        
        vessels = []
        current_time = datetime.now()
        
        # Generate vessels based on realistic distributions
        for vessel_type, config in self.VESSEL_TYPES.items():
            vessel_count = int(count * config['percentage'] / 100)
            
            for _ in range(vessel_count):
                # Generate position within strait boundaries
                lat = random.uniform(self.STRAIT_BOUNDS['south'], self.STRAIT_BOUNDS['north'])
                lon = random.uniform(self.STRAIT_BOUNDS['west'], self.STRAIT_BOUNDS['east'])
                
                # Generate vessel characteristics
                mmsi = random.randint(200000000, 799999999)
                speed = random.uniform(*config['speed_range'])
                course = random.uniform(0, 360)
                heading = course + random.uniform(-15, 15)
                
                # Determine navigation status
                if speed < 0.5:
                    nav_status = "At Anchor"
                elif speed < 2:
                    nav_status = "Restricted Maneuverability"
                elif vessel_type == 'tanker' and speed < 8:
                    nav_status = "Constrained by Draft"
                else:
                    nav_status = "Under Way Using Engine"
                
                # Generate vessel details
                vessel = {
                    'mmsi': mmsi,
                    'vessel_type': vessel_type,
                    'latitude': lat,
                    'longitude': lon,
                    'speed': speed,
                    'course': course,
                    'heading': heading,
                    'nav_status': nav_status,
                    'length': random.randint(50, 400),
                    'width': random.randint(10, 60),
                    'draft': random.uniform(5, 20),
                    'timestamp': current_time,
                    'flag': random.choice(['IR', 'AE', 'SA', 'KW', 'QA', 'OM', 'US', 'UK', 'NO', 'GR']),
                    'destination': random.choice(['Bandar Abbas', 'Dubai', 'Khasab', 'Transit', 'Kuwait'])
                }
                
                vessels.append(vessel)
        
        return vessels
    
    def create_interactive_map(self, vessels: List[Dict[str, Any]]) -> folium.Map:
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
                popup=f"<b>{location_name}</b><br>Strategic Location",
                tooltip=location_name,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(strait_map)
        
        # Add vessels to map
        vessel_counts = {}
        for vessel in vessels:
            vessel_type = vessel['vessel_type']
            config = self.VESSEL_TYPES[vessel_type]
            
            # Count vessels by type
            vessel_counts[vessel_type] = vessel_counts.get(vessel_type, 0) + 1
            
            # Create detailed popup
            popup_html = f"""
            <div style="width: 300px;">
                <h4>{config['icon']} Vessel {vessel['mmsi']}</h4>
                <b>Type:</b> {vessel_type.title()}<br>
                <b>Speed:</b> {vessel['speed']:.1f} knots<br>
                <b>Course:</b> {vessel['course']:.0f}°<br>
                <b>Heading:</b> {vessel['heading']:.0f}°<br>
                <b>Status:</b> {vessel['nav_status']}<br>
                <b>Length:</b> {vessel['length']}m<br>
                <b>Width:</b> {vessel['width']}m<br>
                <b>Draft:</b> {vessel['draft']:.1f}m<br>
                <b>Flag:</b> {vessel['flag']}<br>
                <b>Destination:</b> {vessel['destination']}<br>
                <b>Position:</b> {vessel['latitude']:.4f}°, {vessel['longitude']:.4f}°<br>
                <b>Time:</b> {vessel['timestamp'].strftime('%H:%M:%S UTC')}
            </div>
            """
            
            # Add vessel marker
            folium.CircleMarker(
                location=[vessel['latitude'], vessel['longitude']],
                radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{config['icon']} {vessel_type.title()} - {vessel['speed']:.1f}kn",
                color='white',
                weight=2,
                fillColor=config['color'],
                fillOpacity=0.8
            ).add_to(strait_map)
            
            # Add speed vector (direction arrow) for moving vessels
            if vessel['speed'] > 2:
                distance = 0.01  # degrees
                course_rad = math.radians(vessel['course'])
                end_lat = vessel['latitude'] + distance * math.cos(course_rad)
                end_lon = vessel['longitude'] + distance * math.sin(course_rad)
                
                folium.PolyLine(
                    locations=[[vessel['latitude'], vessel['longitude']], [end_lat, end_lon]],
                    color=config['color'],
                    weight=3,
                    opacity=0.8
                ).add_to(strait_map)
        
        # Add traffic statistics panel
        stats_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 280px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;">
        <h4>🚢 Strait of Hormuz Traffic Monitor</h4>
        <p><b>Critical Oil Chokepoint</b></p>
        <p><b>Total Vessels:</b> {len(vessels)}</p>
        <hr>
        """
        
        for vessel_type, count in vessel_counts.items():
            icon = self.VESSEL_TYPES[vessel_type]['icon']
            stats_html += f"<p>{icon} {vessel_type.title()}: <b>{count}</b></p>"
        
        # Calculate traffic metrics
        moving_vessels = sum(1 for v in vessels if v['speed'] > 2)
        anchored_vessels = sum(1 for v in vessels if v['speed'] < 0.5)
        avg_speed = sum(v['speed'] for v in vessels if v['speed'] > 2) / max(moving_vessels, 1)
        
        stats_html += f"""
        <hr>
        <p><b>Traffic Metrics:</b></p>
        <p>🚢 Moving: <b>{moving_vessels}</b></p>
        <p>⚓ Anchored: <b>{anchored_vessels}</b></p>
        <p>🎯 Avg Speed: <b>{avg_speed:.1f} knots</b></p>
        <hr>
        <p><b>Strategic Data:</b></p>
        <p>• 21% of global petroleum liquids</p>
        <p>• $1.2T annual trade value</p>
        <p>• 21 mile narrowest width</p>
        <p>• Iran-Oman border</p>
        <hr>
        <p style="font-size:12px; color:gray;">
        <i>Updated: {datetime.now().strftime('%H:%M:%S UTC')}</i>
        </p>
        </div>
        """
        
        strait_map.get_root().html.add_child(folium.Element(stats_html))
        
        # Add layer control
        folium.LayerControl().add_to(strait_map)
        
        return strait_map
    
    def run_demo(self, vessel_count: int = 50) -> str:
        """Run the complete Strait of Hormuz demo"""
        
        print("🛢️ Strait of Hormuz - Live Traffic Demo")
        print("=" * 60)
        print("🌊 The world's most critical oil transit chokepoint")
        print("📍 Between Iran and Oman - 21% of global petroleum")
        print("=" * 60)
        
        # Generate vessels
        print(f"🚢 Generating {vessel_count} vessels in the Strait...")
        vessels = self.generate_strait_vessels(vessel_count)
        print(f"✅ Generated {len(vessels)} vessels")
        
        # Analyze traffic
        print("\n📊 Traffic Analysis:")
        vessel_types = {}
        total_speed = 0
        moving_vessels = 0
        high_value_cargo = 0
        
        for vessel in vessels:
            vessel_type = vessel['vessel_type']
            vessel_types[vessel_type] = vessel_types.get(vessel_type, 0) + 1
            
            if vessel['speed'] > 2:
                total_speed += vessel['speed']
                moving_vessels += 1
            
            if vessel_type in ['tanker', 'cargo', 'container']:
                high_value_cargo += 1
        
        for vessel_type, count in vessel_types.items():
            percentage = (count / len(vessels)) * 100
            icon = self.VESSEL_TYPES[vessel_type]['icon']
            print(f"   {icon} {vessel_type.title()}: {count} vessels ({percentage:.1f}%)")
        
        if moving_vessels > 0:
            avg_speed = total_speed / moving_vessels
            print(f"\n⚡ Traffic Metrics:")
            print(f"   • Moving vessels: {moving_vessels}/{len(vessels)}")
            print(f"   • Average speed: {avg_speed:.1f} knots")
            print(f"   • High-value cargo: {high_value_cargo} vessels")
        
        print(f"\n🌊 Strategic Importance:")
        print(f"   • 21% of global petroleum liquids transit")
        print(f"   • $1.2 trillion in annual trade value")
        print(f"   • 15.5 million barrels/day oil flow")
        print(f"   • 21 nautical miles at narrowest point")
        print(f"   • Critical chokepoint for global energy")
        
        # Create interactive map
        print(f"\n🗺️  Creating interactive map...")
        strait_map = self.create_interactive_map(vessels)
        
        # Save map
        map_filename = "strait_of_hormuz_live_demo.html"
        strait_map.save(map_filename)
        
        print(f"✅ Interactive map saved: {map_filename}")
        print(f"🌐 Opening the file will show the live demo!")
        
        return map_filename


def main():
    """Main demo function"""
    print("🚢 MaritimeFlow - Strait of Hormuz Live Demo")
    print("=" * 50)
    print("Real-time maritime intelligence for the world's")
    print("most critical shipping and energy chokepoint")
    print("=" * 50)
    
    # Create and run demo
    demo = StraitOfHormuzDemo()
    map_file = demo.run_demo(vessel_count=60)
    
    print(f"\n🎉 Demo Complete!")
    print(f"📁 File: {map_file}")
    print(f"🖱️  Double-click to open in browser")
    print(f"🔍 Click vessels for detailed info")
    print(f"📊 Real-time statistics in top-right")
    print(f"🗺️  Toggle satellite/map view")
    
    # Try to open the file automatically
    import webbrowser
    import os
    
    try:
        file_path = os.path.abspath(map_file)
        webbrowser.open(f'file://{file_path}')
        print(f"🌐 Opening map in default browser...")
    except:
        print(f"💡 Manually open: {map_file}")
    
    return map_file


if __name__ == "__main__":
    main() 