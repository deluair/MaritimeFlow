# Real AIS Data Sources and API Integration

## Overview
This document provides information on integrating real AIS (Automatic Identification System) data into MaritimeFlow for live vessel tracking and animation.

## 🆓 Free AIS Data Sources

### 1. AIS Hub (Community-driven)
- **URL**: https://www.aishub.net/
- **Access**: Free registration required
- **Coverage**: Global
- **Rate Limits**: 100 requests/hour for free users
- **Data Format**: JSON, XML, CSV
- **API Endpoint**: `http://data.aishub.net/ws.php`

**Example Request:**
```bash
curl "http://data.aishub.net/ws.php?username=YOUR_USERNAME&format=1&output=json&compress=0&latmin=25.8&latmax=26.8&lonmin=55.8&lonmax=57.2"
```

### 2. Norwegian Coastal Administration
- **URL**: https://kystverket.no/
- **API**: https://api.kystverket.no/
- **Coverage**: Norwegian waters + North Sea
- **Access**: Free, no registration
- **Format**: JSON

**Example Request:**
```bash
curl "https://api.kystverket.no/ais/v1/last_known_vessel"
```

### 3. Finnish Transport Infrastructure Agency
- **URL**: https://digitraffic.fi/
- **API**: https://meri.digitraffic.fi/api/
- **Coverage**: Finnish waters + Baltic Sea
- **Access**: Free, no registration
- **Format**: JSON

**Example Request:**
```bash
curl "https://meri.digitraffic.fi/api/ais/v1/locations?loLat=24&hiLat=28&loLon=52&hiLon=60"
```

### 4. Danish Maritime Authority
- **URL**: https://web.ais.dk/
- **Coverage**: Danish waters + parts of North Sea
- **Access**: Free historical data available
- **Format**: JSONL, CSV

## 💰 Commercial AIS Data Sources

### 1. MarineTraffic
- **URL**: https://www.marinetraffic.com/
- **API**: https://services.marinetraffic.com/api/
- **Coverage**: Global
- **Pricing**: Starting from $99/month
- **Features**: Real-time, historical, vessel photos, port calls

**API Endpoint:**
```
https://services.marinetraffic.com/api/exportvessel/v:3/YOUR_API_KEY/timespan:20/protocol:json
```

### 2. VesselFinder
- **URL**: https://www.vesselfinder.com/
- **API**: https://api.vesselfinder.com/
- **Coverage**: Global
- **Pricing**: Starting from $50/month
- **Features**: Real-time positions, vessel details, port information

### 3. FleetMon
- **URL**: https://www.fleetmon.com/
- **API**: https://apidocs.fleetmon.com/
- **Coverage**: Global
- **Pricing**: Custom pricing
- **Features**: Real-time tracking, voyage data, predictive analytics

### 4. Spire Global
- **URL**: https://spire.com/
- **API**: https://spire.com/maritime/
- **Coverage**: Global (satellite-based)
- **Pricing**: Enterprise pricing
- **Features**: Real-time global coverage, weather data integration

## 🔧 Integration Examples

### Python Integration with AIS Hub

```python
import requests
import json
from typing import List, Dict, Any

class AISHubClient:
    def __init__(self, username: str, format_type: int = 1):
        self.username = username
        self.format_type = format_type
        self.base_url = "http://data.aishub.net/ws.php"
    
    def get_vessels_in_area(self, lat_min: float, lat_max: float, 
                           lon_min: float, lon_max: float) -> List[Dict[str, Any]]:
        """Get vessels in specified geographic area"""
        
        params = {
            'username': self.username,
            'format': self.format_type,
            'output': 'json',
            'compress': 0,
            'latmin': lat_min,
            'latmax': lat_max,
            'lonmin': lon_min,
            'lonmax': lon_max
        }
        
        response = requests.get(self.base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('vessels', [])
        else:
            raise Exception(f"API request failed: {response.status_code}")

# Usage example
client = AISHubClient('your_username')
strait_vessels = client.get_vessels_in_area(25.8, 26.8, 55.8, 57.2)
```

### Real-time Data Fetching for Strait of Hormuz

```python
import asyncio
import aiohttp
from datetime import datetime

async def fetch_strait_vessels():
    """Fetch real-time vessel data for Strait of Hormuz"""
    
    # Strait of Hormuz coordinates
    bounds = {
        'lat_min': 25.8, 'lat_max': 26.8,
        'lon_min': 55.8, 'lon_max': 57.2
    }
    
    vessels = []
    
    # Try multiple free sources
    sources = [
        {
            'name': 'AISHub',
            'url': 'http://data.aishub.net/ws.php',
            'params': {
                'username': 'YOUR_USERNAME',
                'format': 1,
                'output': 'json',
                'latmin': bounds['lat_min'],
                'latmax': bounds['lat_max'],
                'lonmin': bounds['lon_min'],
                'lonmax': bounds['lon_max']
            }
        },
        {
            'name': 'Digitraffic',
            'url': 'https://meri.digitraffic.fi/api/ais/v1/locations',
            'params': {
                'loLat': bounds['lat_min'],
                'hiLat': bounds['lat_max'],
                'loLon': bounds['lon_min'],
                'hiLon': bounds['lon_max']
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for source in sources:
            try:
                async with session.get(source['url'], params=source['params']) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse data based on source format
                        if source['name'] == 'AISHub':
                            source_vessels = data.get('vessels', [])
                        elif source['name'] == 'Digitraffic':
                            source_vessels = []
                            for feature in data.get('features', []):
                                props = feature.get('properties', {})
                                geometry = feature.get('geometry', {})
                                coords = geometry.get('coordinates', [0, 0])
                                
                                vessel = {
                                    'mmsi': props.get('mmsi'),
                                    'latitude': coords[1],
                                    'longitude': coords[0],
                                    'speed': props.get('sog', 0),
                                    'course': props.get('cog', 0),
                                    'timestamp': props.get('timestampExternal'),
                                    'source': source['name']
                                }
                                source_vessels.append(vessel)
                        
                        vessels.extend(source_vessels)
                        print(f"✅ Fetched {len(source_vessels)} vessels from {source['name']}")
                        
            except Exception as e:
                print(f"❌ {source['name']} failed: {e}")
    
    return vessels

# Usage
vessels = asyncio.run(fetch_strait_vessels())
print(f"Total vessels found: {len(vessels)}")
```

## 🎬 Animation with Real Data

### Time-based Animation

```python
def create_animated_map_with_real_data():
    """Create animated map using real AIS data"""
    
    import folium
    from folium.plugins import TimestampedGeoJson
    
    # Fetch historical data for last 24 hours
    historical_data = fetch_historical_vessel_positions(hours=24)
    
    # Create map
    m = folium.Map(location=[26.3, 56.3], zoom_start=10)
    
    # Prepare time-stamped data
    features = []
    for vessel in historical_data:
        for position in vessel['positions']:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [position['longitude'], position['latitude']]
                },
                'properties': {
                    'time': position['timestamp'],
                    'popup': f"Vessel {vessel['mmsi']} - {position['speed']} knots",
                    'icon': 'circle',
                    'iconstyle': {
                        'fillColor': get_vessel_color(vessel['type']),
                        'fillOpacity': 0.8,
                        'stroke': 'true',
                        'radius': 8
                    }
                }
            }
            features.append(feature)
    
    # Add animated layer
    TimestampedGeoJson(
        {
            'type': 'FeatureCollection',
            'features': features
        },
        period='PT1H',  # 1 hour intervals
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=10,
        loop_button=True,
        date_options='YYYY/MM/DD HH:mm:ss',
        time_slider_drag_update=True
    ).add_to(m)
    
    return m
```

## 📊 Data Quality and Coverage

### Coverage Areas by Source

| Source | Global | Persian Gulf | Strait of Hormuz | Update Frequency |
|--------|--------|-------------|------------------|------------------|
| AIS Hub | ✅ | ✅ | ⚠️ Limited | 1-5 minutes |
| MarineTraffic | ✅ | ✅ | ✅ | Real-time |
| VesselFinder | ✅ | ✅ | ✅ | Real-time |
| Digitraffic | ❌ | ❌ | ❌ | 1 minute |
| Norwegian API | ❌ | ❌ | ❌ | 1 minute |

### Data Quality Factors

1. **Signal Coverage**: Strait of Hormuz has good AIS coverage due to high traffic
2. **Satellite vs Terrestrial**: Satellite sources provide better coverage
3. **Military Vessels**: Often do not broadcast AIS signals
4. **Small Vessels**: May not be required to carry AIS transponders
5. **Signal Interference**: Can occur in congested areas

## 🔐 API Key Management

### Environment Variables Setup

```bash
# .env file
AISHUB_USERNAME=your_aishub_username
MARINETRAFFIC_API_KEY=your_marinetraffic_key
VESSELFINDER_API_KEY=your_vesselfinder_key
FLEETMON_API_KEY=your_fleetmon_key
```

### Secure Configuration

```python
import os
from typing import Dict, Optional

class APIKeyManager:
    def __init__(self):
        self.keys = {
            'aishub': os.getenv('AISHUB_USERNAME'),
            'marinetraffic': os.getenv('MARINETRAFFIC_API_KEY'),
            'vesselfinder': os.getenv('VESSELFINDER_API_KEY'),
            'fleetmon': os.getenv('FLEETMON_API_KEY')
        }
    
    def get_key(self, service: str) -> Optional[str]:
        return self.keys.get(service)
    
    def has_key(self, service: str) -> bool:
        return self.get_key(service) is not None
```

## 🚀 Production Deployment

### Rate Limiting and Caching

```python
import time
from functools import wraps
from typing import Callable, Any
import redis

# Redis cache for API responses
cache = redis.Redis(host='localhost', port=6379, db=0)

def rate_limit(max_calls: int, time_window: int):
    """Rate limiting decorator"""
    def decorator(func: Callable) -> Callable:
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            now = time.time()
            calls[:] = [call for call in calls if call > now - time_window]
            
            if len(calls) >= max_calls:
                sleep_time = time_window - (now - calls[0])
                time.sleep(sleep_time)
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

@rate_limit(max_calls=100, time_window=3600)  # 100 calls per hour
def fetch_ais_data(api_endpoint: str, params: dict):
    """Rate-limited AIS data fetching"""
    # Check cache first
    cache_key = f"ais:{hash(str(params))}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    response = requests.get(api_endpoint, params=params)
    data = response.json()
    
    # Cache for 5 minutes
    cache.setex(cache_key, 300, json.dumps(data))
    
    return data
```

## 🎯 Best Practices

### 1. Data Validation
- Always validate coordinates (lat: -90 to 90, lon: -180 to 180)
- Check timestamp formats and convert to standard ISO format
- Validate vessel MMSI numbers (9 digits)
- Sanitize vessel names and other text fields

### 2. Error Handling
- Implement retry logic with exponential backoff
- Handle API rate limits gracefully
- Provide fallback to synthetic data when APIs fail
- Log API errors for monitoring

### 3. Performance Optimization
- Use async/await for concurrent API calls
- Implement proper caching strategies
- Consider data compression for large datasets
- Use connection pooling for frequent requests

### 4. Real-time Updates
- Implement WebSocket connections for live updates
- Use server-sent events (SSE) for web interfaces
- Consider using message queues for high-volume data
- Implement proper error recovery for connection drops

## 📈 Monitoring and Analytics

### API Usage Tracking

```python
import logging
from datetime import datetime

class APIUsageTracker:
    def __init__(self):
        self.usage_stats = {}
        self.logger = logging.getLogger('api_usage')
    
    def track_request(self, service: str, endpoint: str, response_time: float, status_code: int):
        timestamp = datetime.now()
        
        usage_key = f"{service}:{endpoint}"
        if usage_key not in self.usage_stats:
            self.usage_stats[usage_key] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'last_request': None
            }
        
        stats = self.usage_stats[usage_key]
        stats['total_requests'] += 1
        stats['last_request'] = timestamp
        
        if 200 <= status_code < 300:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1
        
        # Update average response time
        stats['average_response_time'] = (
            (stats['average_response_time'] * (stats['total_requests'] - 1) + response_time) /
            stats['total_requests']
        )
        
        self.logger.info(f"API Request: {service} {endpoint} - {status_code} - {response_time:.2f}s")
```

This comprehensive guide provides everything needed to integrate real AIS data into your MaritimeFlow animations and visualizations! 