"""
MaritimeFlow - Advanced Maritime Analytics and Supply Chain Intelligence Platform

Main entry point for the application.
"""

import uvicorn
import asyncio
import click
from datetime import datetime

from src.core.config import settings
from src.api.main import app
from src.data_ingestion.synthetic_generator import SyntheticDataGenerator


@click.group()
def cli():
    """MaritimeFlow CLI - Advanced Maritime Analytics Platform"""
    pass


@cli.command()
@click.option('--host', default=settings.api_host, help='Host to bind the server to')
@click.option('--port', default=settings.api_port, help='Port to bind the server to')
@click.option('--workers', default=settings.api_workers, help='Number of worker processes')
@click.option('--reload', default=settings.debug, help='Enable auto-reload for development')
def serve(host: str, port: int, workers: int, reload: bool):
    """Start the MaritimeFlow API server"""
    
    print(f"🚢 Starting MaritimeFlow v{settings.app_version}")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API Documentation at: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info"
    )


@cli.command()
@click.option('--count', default=100, help='Number of synthetic vessel positions to generate')
@click.option('--format', default='json', help='Output format (json, csv)')
def generate_data(count: int, format: str):
    """Generate synthetic AIS data for testing"""
    
    print(f"🌊 Generating {count} synthetic vessel positions...")
    
    generator = SyntheticDataGenerator(seed=42)
    current_time = datetime.utcnow()
    
    positions = generator.generate_batch_positions(count, current_time)
    
    if format == 'json':
        import json
        output = [pos.dict() for pos in positions]
        print(json.dumps(output, indent=2, default=str))
    
    elif format == 'csv':
        import csv
        import sys
        
        if positions:
            writer = csv.DictWriter(sys.stdout, fieldnames=positions[0].dict().keys())
            writer.writeheader()
            for pos in positions:
                writer.writerow(pos.dict())
    
    print(f"✅ Generated {len(positions)} vessel positions")


@cli.command()
@click.option('--port', default='SHANGHAI', help='Port name for congestion scenario')
@click.option('--level', default=0.8, help='Congestion level (0.0 - 1.0)')
def simulate_congestion(port: str, level: float):
    """Simulate port congestion scenario"""
    
    print(f"🚧 Simulating congestion at {port} (level: {level:.1f})")
    
    generator = SyntheticDataGenerator(seed=42)
    
    try:
        positions = generator.generate_port_congestion_scenario(port, level)
        
        print(f"📊 Generated congestion scenario:")
        print(f"   - Port: {port}")
        print(f"   - Congestion Level: {level:.1f}")
        print(f"   - Vessels in area: {len(positions)}")
        print(f"   - Vessels anchored: {sum(1 for p in positions if p.speed_over_ground < 0.5)}")
        print(f"   - Average wait time: {len(positions) * level * 2:.1f} hours")
        
    except ValueError as e:
        print(f"❌ Error: {e}")


@cli.command()
def status():
    """Show MaritimeFlow system status"""
    
    print("🚢 MaritimeFlow System Status")
    print("=" * 40)
    print(f"Version: {settings.app_version}")
    print(f"Environment: {'Development' if settings.debug else 'Production'}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"Database URL: {settings.database_url}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"Kafka Servers: {', '.join(settings.kafka_bootstrap_servers)}")
    print("=" * 40)
    
    # Test synthetic data generation
    generator = SyntheticDataGenerator()
    test_positions = generator.generate_batch_positions(10, datetime.utcnow())
    print(f"✅ Synthetic data generator: Working ({len(test_positions)} positions generated)")
    
    print("\n📋 Available APIs:")
    print("  - GET  /api/v1/vessels/")
    print("  - GET  /api/v1/vessels/{mmsi}")
    print("  - GET  /api/v1/vessels/{mmsi}/positions")
    print("  - GET  /api/v1/vessels/live/positions")
    print("  - GET  /health")
    print("  - GET  /docs")


@cli.command()
def test():
    """Run basic system tests"""
    
    print("🧪 Running MaritimeFlow system tests...")
    print("=" * 40)
    
    # Test 1: Synthetic data generation
    print("1. Testing synthetic data generation...")
    generator = SyntheticDataGenerator(seed=42)
    positions = generator.generate_batch_positions(5, datetime.utcnow())
    
    if len(positions) == 5:
        print("   ✅ PASS: Generated expected number of positions")
    else:
        print("   ❌ FAIL: Wrong number of positions generated")
    
    # Test 2: Port congestion simulation
    print("2. Testing port congestion simulation...")
    try:
        congestion_positions = generator.generate_port_congestion_scenario("SHANGHAI", 0.7)
        if len(congestion_positions) > 0:
            print("   ✅ PASS: Port congestion scenario generated")
        else:
            print("   ❌ FAIL: No congestion positions generated")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 3: Configuration loading
    print("3. Testing configuration...")
    if settings.app_name == "MaritimeFlow":
        print("   ✅ PASS: Configuration loaded correctly")
    else:
        print("   ❌ FAIL: Configuration not loaded correctly")
    
    print("\n🎉 Tests completed!")


if __name__ == "__main__":
    cli() 