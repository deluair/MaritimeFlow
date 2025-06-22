#!/usr/bin/env python3
"""
Quick test script for MyShipTracking API
"""

import asyncio
import os
import aiohttp
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_myshiptracking_api():
    """Test the MyShipTracking API with provided credentials"""
    
    # Use the credentials you provided
    api_key = "hK!NRGYELTwvO4vZnXt1jeIl4OWTx9LLLF"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔑 Testing API Key: {api_key[:10]}...")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Test 1: Get single vessel by MMSI
        print("\n🚢 Test 1: Get Single Vessel by MMSI")
        try:
            # Known vessel MMSI from documentation example
            url = "https://api.myshiptracking.com/api/v2/vessel"
            params = {'mmsi': '241087000'}  # Example from docs
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                data = await response.json()
                print(f"Response: {data}")
                
                if response.status == 200 and data.get('status') == 'success':
                    print("✅ Single vessel API is working!")
                    vessel_data = data.get('data', {})
                    print(f"Vessel: {vessel_data.get('vessel_name', 'Unknown')}")
                    print(f"Position: {vessel_data.get('lat', 0)}, {vessel_data.get('lng', 0)}")
                else:
                    print(f"❌ API Error: {data}")
                    
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Get bulk vessels
        print("\n🚢 Test 2: Get Multiple Vessels (Bulk)")
        try:
            url = "https://api.myshiptracking.com/api/v2/vessel/bulk"
            params = {'mmsi': '241087000,239923000,239924000'}  # Multiple MMSIs
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        vessels = data.get('data', [])
                        print(f"✅ Found {len(vessels)} vessels")
                        for vessel in vessels[:3]:  # Show first 3
                            print(f"  - {vessel.get('vessel_name', 'Unknown')} at {vessel.get('lat', 0)}, {vessel.get('lng', 0)}")
                    else:
                        print(f"❌ Bulk API Error: {data}")
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"Error: {e}")
            
        # Test 3: Test with extended response
        print("\n🔍 Test 3: Extended Response")
        try:
            url = "https://api.myshiptracking.com/api/v2/vessel"
            params = {'mmsi': '241087000', 'response': 'extended'}
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        print("✅ Extended response working!")
                        vessel_data = data.get('data', {})
                        print(f"Vessel: {vessel_data.get('vessel_name', 'Unknown')}")
                        print(f"Destination: {vessel_data.get('destination', 'Unknown')}")
                        print(f"Flag: {vessel_data.get('flag', 'Unknown')}")
                    else:
                        print(f"❌ Extended API Error: {data}")
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_myshiptracking_api()) 