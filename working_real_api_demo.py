#!/usr/bin/env python3
"""
Working Real AIS Data Demo - MyShipTracking API
============================================

Simple demo showing live vessel data from MyShipTracking API
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def get_real_vessels():
    """Get real vessel data from MyShipTracking API"""
    
    api_key = "hK!NRGYELTwvO4vZnXt1jeIl4OWTx9LLLF"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("🚢 GETTING REAL VESSEL DATA FROM MYSHIPTRACKING API")
    print("=" * 60)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Get some known vessels (bulk request)
            url = "https://api.myshiptracking.com/api/v2/vessel/bulk"
            params = {
                'mmsi': '241087000,239923000,239924000',  # Known MMSIs from Greece
                'response': 'extended'
            }
            
            print(f"🌐 Requesting: {url}")
            print(f"📡 MMSIs: {params['mmsi']}")
            print(f"🔑 API Key: {api_key[:15]}...")
            print()
            
            async with session.get(url, params=params) as response:
                print(f"📊 Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'success':
                        vessels = data.get('data', [])
                        print(f"✅ SUCCESS! Found {len(vessels)} vessels")
                        print()
                        
                        for i, vessel in enumerate(vessels, 1):
                            print(f"🚢 VESSEL {i}: {vessel.get('vessel_name', 'Unknown')}")
                            print(f"   MMSI: {vessel.get('mmsi')}")
                            print(f"   IMO: {vessel.get('imo', 'Unknown')}")
                            print(f"   Position: {vessel.get('lat', 0):.4f}, {vessel.get('lng', 0):.4f}")
                            print(f"   Speed: {vessel.get('speed', 0)} knots")
                            print(f"   Course: {vessel.get('course', 0)}°")
                            print(f"   Flag: {vessel.get('flag', 'Unknown')}")
                            print(f"   Destination: {vessel.get('destination', 'Unknown')}")
                            print(f"   Last Update: {vessel.get('received', 'Unknown')}")
                            
                            # Navigation status
                            nav_status = vessel.get('nav_status', 15)
                            status_names = {
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
                            print(f"   Status: {status_names.get(nav_status, 'Unknown')}")
                            
                            # Vessel details if available
                            if vessel.get('vessel_type'):
                                print(f"   Type: {vessel.get('vessel_type')}")
                            if vessel.get('built'):
                                print(f"   Built: {vessel.get('built')}")
                            if vessel.get('gt'):
                                print(f"   Gross Tonnage: {vessel.get('gt')}")
                            if vessel.get('dwt'):
                                print(f"   Deadweight: {vessel.get('dwt')}")
                            
                            print("-" * 50)
                        
                        return vessels
                    
                    else:
                        print(f"❌ API Error: {data}")
                        return []
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return []
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []


async def get_single_vessel():
    """Get data for a single vessel"""
    
    api_key = "hK!NRGYELTwvO4vZnXt1jeIl4OWTx9LLLF"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("\n🎯 GETTING SINGLE VESSEL DETAILS")
    print("=" * 60)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Get single vessel with extended data
            url = "https://api.myshiptracking.com/api/v2/vessel"
            params = {
                'mmsi': '241087000',  # BLUE STAR DELOS
                'response': 'extended'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'success':
                        vessel = data.get('data', {})
                        
                        print(f"🚢 {vessel.get('vessel_name', 'Unknown')}")
                        print(f"📍 Current Position: {vessel.get('lat', 0):.6f}, {vessel.get('lng', 0):.6f}")
                        print(f"🧭 Course: {vessel.get('course', 0)}° | Speed: {vessel.get('speed', 0)} knots")
                        print(f"🏁 Destination: {vessel.get('destination', 'Unknown')}")
                        
                        # Current port information
                        if vessel.get('current_port'):
                            print(f"🏢 Current Port: {vessel.get('current_port')}")
                        if vessel.get('last_port'):
                            print(f"📍 Last Port: {vessel.get('last_port')}")
                        if vessel.get('next_port'):
                            print(f"➡️  Next Port: {vessel.get('next_port')}")
                        
                        # Weather data if available
                        if vessel.get('wind_knots'):
                            print(f"🌬️  Wind: {vessel.get('wind_knots')} knots {vessel.get('wind_direction', '')}")
                        if vessel.get('temperature'):
                            print(f"🌡️  Temperature: {vessel.get('temperature')}°C")
                        
                        print(f"⏰ Last Position Update: {vessel.get('received', 'Unknown')}")
                        
                        return vessel
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None


async def main():
    """Main demo function"""
    
    print("🌊 MARITIMEFLOW - REAL AIS DATA DEMO")
    print("🚢" * 30)
    print(f"⏰ Demo Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("This demo shows REAL vessel data from MyShipTracking API")
    print("All vessels shown are actually moving in real-time!")
    print()
    
    # Get multiple vessels
    vessels = await get_real_vessels()
    
    if vessels:
        print(f"\n📊 SUMMARY: Successfully retrieved {len(vessels)} real vessels")
        
        # Get detailed info for one vessel
        await get_single_vessel()
        
        print("\n🌍 GOOGLE MAPS LINKS")
        print("=" * 60)
        for vessel in vessels:
            lat = vessel.get('lat', 0)
            lng = vessel.get('lng', 0)
            name = vessel.get('vessel_name', 'Unknown')
            maps_url = f"https://www.google.com/maps?q={lat},{lng}"
            print(f"{name}: {maps_url}")
        
        print("\n✅ Demo completed successfully!")
        print("🔄 This data is live and updates every few minutes")
        
    else:
        print("❌ No vessels retrieved. Check API key and network connection.")


if __name__ == "__main__":
    asyncio.run(main()) 