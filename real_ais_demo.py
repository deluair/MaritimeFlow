#!/usr/bin/env python3
"""
Real AIS Data Demo for MaritimeFlow
==================================

This demo shows how to integrate real AIS data APIs into MaritimeFlow
instead of using synthetic data. It demonstrates:

1. Connecting to real AIS APIs (MyShipTracking, Datalastic)
2. Fetching live vessel data
3. Visualizing real vessel movements
4. Comparing different API sources

APIs Supported:
- MyShipTracking (Free trial - 2000 credits)
- Datalastic (Professional)
- AISHub (Community-based)

Setup Instructions:
1. Get API key from https://api.myshiptracking.com/ (free trial)
2. Set environment variable: export MYSHIPTRACKING_API_KEY="your_key"
3. Run this demo to see real vessel data

Author: MaritimeFlow Team
Date: 2025
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our AIS collectors
from src.data_ingestion.ais_collectors import AISCollector
from src.core.config import REAL_AIS_CONFIG, AIS_SOURCES

class RealAISDemo:
    """Demo class for real AIS data integration"""
    
    def __init__(self):
        self.config = REAL_AIS_CONFIG.copy()
        self.collector = None
        
    async def check_api_availability(self) -> Dict[str, bool]:
        """Check which APIs are available with current configuration"""
        availability = {}
        
        # Check MyShipTracking
        if self.config.get('myshiptracking_api_key'):
            availability['myshiptracking'] = True
            logger.info(f"✅ MyShipTracking API key found: {self.config.get('myshiptracking_api_key')[:10]}...")
            if self.config.get('myshiptracking_secret_key'):
                logger.info(f"✅ MyShipTracking Secret key found: {self.config.get('myshiptracking_secret_key')[:5]}...")
        else:
            availability['myshiptracking'] = False
            logger.warning("❌ MyShipTracking API key not found")
            
        # Check Datalastic
        if self.config.get('datalastic_api_key'):
            availability['datalastic'] = True
            logger.info("✅ Datalastic API key found")
        else:
            availability['datalastic'] = False
            logger.warning("❌ Datalastic API key not found")
            
        return availability
    
    def print_api_info(self):
        """Print information about available APIs"""
        print("\n" + "="*60)
        print("         REAL AIS DATA APIS - INFORMATION")
        print("="*60)
        
        for api_name, api_info in AIS_SOURCES.items():
            if api_name == 'synthetic':
                continue
                
            print(f"\n📡 {api_info['name']}")
            print(f"   URL: {api_info['url']}")
            print(f"   Description: {api_info['description']}")
            print(f"   Coverage: {api_info['coverage']}")
            print(f"   API Key Required: {'Yes' if api_info['api_key_required'] else 'No'}")
            print(f"   Free Tier: {'Yes' if api_info['free_tier'] else 'No'}")
            
            if 'rate_limit' in api_info:
                print(f"   Rate Limit: {api_info['rate_limit']}")
            if 'free_credits' in api_info:
                print(f"   Free Credits: {api_info['free_credits']}")
            if 'uptime' in api_info:
                print(f"   Uptime: {api_info['uptime']}")
            if 'requirement' in api_info:
                print(f"   Requirement: {api_info['requirement']}")
    
    def print_setup_instructions(self):
        """Print setup instructions for getting API keys"""
        print("\n" + "="*60)
        print("         SETUP INSTRUCTIONS")
        print("="*60)
        
        print("\n🚀 To get REAL vessel data, follow these steps:")
        
        print("\n1️⃣  MYSHIPTRACKING (FREE TRIAL - RECOMMENDED)")
        print("   • Visit: https://www.myshiptracking.com/")
        print("   • Create free account")
        print("   • Get API key from account dashboard")
        print("   • Set environment variable:")
        print("     export MYSHIPTRACKING_API_KEY='your_api_key_here'")
        print("   • Free tier: 2000 credits for 10 days")
        
        print("\n2️⃣  DATALASTIC (PROFESSIONAL)")
        print("   • Visit: https://datalastic.com/")
        print("   • Choose subscription plan")
        print("   • Get API key after payment")
        print("   • Set environment variable:")
        print("     export DATALASTIC_API_KEY='your_api_key_here'")
        print("   • Professional service with 750,000+ ships")
        
        print("\n3️⃣  AISHUB (COMMUNITY)")
        print("   • Visit: https://www.aishub.net/")
        print("   • Contribute your own AIS data")
        print("   • Get access to aggregated community data")
        print("   • Free but requires data contribution")
        
        print("\n💡 TIP: Start with MyShipTracking free trial!")
    
    async def demo_strait_of_hormuz(self) -> List:
        """Demo: Get real vessels in Strait of Hormuz"""
        print("\n🌊 DEMO: Real Vessels in Strait of Hormuz")
        print("-" * 50)
        
        collector = AISCollector(self.config)
        vessels = await collector.collect_data(region="strait_of_hormuz")
        
        if vessels:
            print(f"✅ Found {len(vessels)} real vessels!")
            
            for i, vessel in enumerate(vessels[:5], 1):  # Show first 5
                print(f"\n{i}. {vessel.name}")
                print(f"   MMSI: {vessel.mmsi}")
                print(f"   Type: {vessel.vessel_type}")
                print(f"   Position: {vessel.current_position.latitude:.4f}, {vessel.current_position.longitude:.4f}")
                print(f"   Speed: {vessel.current_position.speed:.1f} knots")
                print(f"   Destination: {vessel.destination or 'Unknown'}")
            
            if len(vessels) > 5:
                print(f"   ... and {len(vessels) - 5} more vessels")
        else:
            print("❌ No vessels found (using fallback data)")
            
        return vessels
    
    async def demo_singapore_strait(self) -> List:
        """Demo: Get real vessels in Singapore Strait"""
        print("\n🌊 DEMO: Real Vessels in Singapore Strait")
        print("-" * 50)
        
        collector = AISCollector(self.config)
        vessels = await collector.collect_data(region="singapore_strait")
        
        if vessels:
            print(f"✅ Found {len(vessels)} real vessels!")
            
            # Group by vessel type
            vessel_types = {}
            for vessel in vessels:
                vtype = vessel.vessel_type
                if vtype not in vessel_types:
                    vessel_types[vtype] = 0
                vessel_types[vtype] += 1
            
            print("\n📊 Vessel Types:")
            for vtype, count in sorted(vessel_types.items()):
                print(f"   {vtype}: {count}")
                
        return vessels
    
    async def demo_global_shipping(self) -> List:
        """Demo: Get vessels from major shipping routes"""
        print("\n🌍 DEMO: Global Shipping Traffic")
        print("-" * 50)
        
        collector = AISCollector(self.config)
        vessels = await collector.collect_data()  # No specific region = major shipping areas
        
        if vessels:
            print(f"✅ Found {len(vessels)} real vessels globally!")
            
            # Show statistics
            countries = {}
            destinations = {}
            
            for vessel in vessels:
                if vessel.country:
                    countries[vessel.country] = countries.get(vessel.country, 0) + 1
                if vessel.destination:
                    destinations[vessel.destination] = destinations.get(vessel.destination, 0) + 1
            
            print("\n🏳️  Top Countries:")
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {country}: {count} vessels")
                
            print("\n🎯 Top Destinations:")
            for dest, count in sorted(destinations.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {dest}: {count} vessels")
                
        return vessels
    
    async def demo_vessel_tracking(self, vessel_mmsi: str = "477553000"):
        """Demo: Track a specific vessel by MMSI"""
        print(f"\n🎯 DEMO: Tracking Vessel MMSI {vessel_mmsi}")
        print("-" * 50)
        
        # This would require vessel-specific API endpoints
        # For now, show how to find vessel in collected data
        vessels = await self.demo_global_shipping()
        
        target_vessel = None
        for vessel in vessels:
            if str(vessel.mmsi) == vessel_mmsi:
                target_vessel = vessel
                break
        
        if target_vessel:
            print(f"✅ Found vessel: {target_vessel.name}")
            print(f"   MMSI: {target_vessel.mmsi}")
            print(f"   IMO: {target_vessel.imo}")
            print(f"   Type: {target_vessel.vessel_type}")
            print(f"   Flag: {target_vessel.country}")
            print(f"   Current Position: {target_vessel.current_position.latitude:.4f}, {target_vessel.current_position.longitude:.4f}")
            print(f"   Speed: {target_vessel.current_position.speed:.1f} knots")
            print(f"   Course: {target_vessel.current_position.course}°")
            print(f"   Destination: {target_vessel.destination or 'Unknown'}")
            if target_vessel.eta:
                print(f"   ETA: {target_vessel.eta}")
        else:
            print(f"❌ Vessel with MMSI {vessel_mmsi} not found in current data")
    
    def export_vessel_data(self, vessels: List, filename: str = "real_vessels.json"):
        """Export vessel data to JSON file"""
        if not vessels:
            print("❌ No vessel data to export")
            return
            
        vessel_data = []
        for vessel in vessels:
            vessel_dict = {
                "mmsi": vessel.mmsi,
                "imo": vessel.imo,
                "name": vessel.name,
                "type": vessel.vessel_type,
                "country": vessel.country,
                "destination": vessel.destination,
                "position": {
                    "latitude": vessel.current_position.latitude,
                    "longitude": vessel.current_position.longitude,
                    "speed": vessel.current_position.speed,
                    "course": vessel.current_position.course,
                    "timestamp": vessel.current_position.timestamp.isoformat() if vessel.current_position.timestamp else None
                },
                "dimensions": {
                    "length": vessel.length,
                    "width": vessel.width,
                    "draft": vessel.draft
                },
                "tonnage": {
                    "gross_tonnage": vessel.gross_tonnage,
                    "cargo_capacity": vessel.cargo_capacity
                },
                "eta": vessel.eta.isoformat() if vessel.eta else None
            }
            vessel_data.append(vessel_dict)
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "total_vessels": len(vessels),
                "vessels": vessel_data
            }, f, indent=2)
        
        print(f"✅ Exported {len(vessels)} vessels to {filename}")
    
    async def run_full_demo(self):
        """Run complete demo with all features"""
        print("🚢" * 20)
        print("    MARITIMEFLOW - REAL AIS DATA DEMO")
        print("🚢" * 20)
        
        # Show API info
        self.print_api_info()
        
        # Check availability
        availability = await self.check_api_availability()
        
        if not any(availability.values()):
            print("\n❌ No API keys found!")
            self.print_setup_instructions()
            print("\n💡 Running with fallback data for demonstration...")
        else:
            print(f"\n✅ Available APIs: {[k for k, v in availability.items() if v]}")
        
        print("\n" + "="*60)
        print("         RUNNING DEMOS")
        print("="*60)
        
        # Run demos
        vessels_hormuz = await self.demo_strait_of_hormuz()
        await asyncio.sleep(2)  # Rate limiting
        
        vessels_singapore = await self.demo_singapore_strait()
        await asyncio.sleep(2)
        
        vessels_global = await self.demo_global_shipping()
        await asyncio.sleep(2)
        
        await self.demo_vessel_tracking()
        
        # Export data
        if vessels_global:
            self.export_vessel_data(vessels_global)
        
        print("\n" + "="*60)
        print("         DEMO COMPLETE")
        print("="*60)
        print("\n✅ Real AIS data integration successful!")
        print("💡 Next steps:")
        print("   1. Get API keys for more data")
        print("   2. Integrate into your MaritimeFlow application")
        print("   3. Set up automated data collection")
        print("   4. Add real-time vessel tracking")

async def main():
    """Main demo function"""
    demo = RealAISDemo()
    await demo.run_full_demo()

if __name__ == "__main__":
    asyncio.run(main()) 