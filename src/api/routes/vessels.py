"""
Vessel API routes for vessel tracking and information
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta

from ...models.vessel import (
    VesselResponse, VesselPositionResponse, VesselTrack, 
    VesselSummary, VesselType
)
from ...data_ingestion.synthetic_generator import SyntheticDataGenerator

router = APIRouter()

# Initialize synthetic data generator for demo purposes
synthetic_generator = SyntheticDataGenerator(seed=42)


@router.get("/", response_model=List[VesselResponse])
async def get_vessels(
    limit: int = Query(100, description="Maximum number of vessels to return"),
    vessel_type: Optional[VesselType] = Query(None, description="Filter by vessel type"),
    flag_country: Optional[str] = Query(None, description="Filter by flag country")
):
    """Get list of vessels with optional filtering"""
    
    vessels = synthetic_generator.vessel_database[:limit]
    
    # Apply filters
    if vessel_type:
        vessels = [v for v in vessels if v.get('vessel_type') == vessel_type]
    
    if flag_country:
        vessels = [v for v in vessels if v.get('flag_country') == flag_country]
    
    # Convert to response models
    response_vessels = []
    for vessel in vessels:
        response_vessels.append(VesselResponse(
            mmsi=vessel['mmsi'],
            vessel_name=vessel['vessel_name'],
            vessel_type=vessel['vessel_type'],
            length=vessel['length'],
            max_speed=vessel['max_speed'],
            flag_country=vessel['flag_country'],
            first_seen=datetime.utcnow() - timedelta(days=30),
            last_updated=datetime.utcnow(),
            is_active=True
        ))
    
    return response_vessels


@router.get("/{mmsi}", response_model=VesselResponse)
async def get_vessel(mmsi: int):
    """Get detailed information about a specific vessel"""
    
    # Find vessel in synthetic database
    vessel = next((v for v in synthetic_generator.vessel_database if v['mmsi'] == mmsi), None)
    
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    return VesselResponse(
        mmsi=vessel['mmsi'],
        vessel_name=vessel['vessel_name'],
        vessel_type=vessel['vessel_type'],
        length=vessel['length'],
        max_speed=vessel['max_speed'],
        flag_country=vessel['flag_country'],
        first_seen=datetime.utcnow() - timedelta(days=30),
        last_updated=datetime.utcnow(),
        is_active=True
    )


@router.get("/{mmsi}/positions", response_model=List[VesselPositionResponse])
async def get_vessel_positions(
    mmsi: int,
    hours: int = Query(24, description="Number of hours of history to return"),
    limit: int = Query(1000, description="Maximum number of positions to return")
):
    """Get position history for a specific vessel"""
    
    # Find vessel in synthetic database
    vessel = next((v for v in synthetic_generator.vessel_database if v['mmsi'] == mmsi), None)
    
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    # Generate synthetic position history
    positions = []
    current_time = datetime.utcnow()
    
    for i in range(min(hours, limit)):
        position_time = current_time - timedelta(hours=i)
        position = synthetic_generator.generate_vessel_position(vessel, position_time)
        
        positions.append(VesselPositionResponse(
            id=i,
            mmsi=position.mmsi,
            latitude=position.latitude,
            longitude=position.longitude,
            course_over_ground=position.course_over_ground,
            speed_over_ground=position.speed_over_ground,
            true_heading=position.true_heading,
            navigation_status=position.navigation_status,
            timestamp=position.timestamp,
            message_timestamp=position.message_timestamp,
            received_timestamp=position_time,
            data_source=position.data_source
        ))
    
    return positions


@router.get("/{mmsi}/track", response_model=VesselTrack)
async def get_vessel_track(
    mmsi: int,
    start_time: Optional[datetime] = Query(None, description="Start time for track"),
    end_time: Optional[datetime] = Query(None, description="End time for track")
):
    """Get vessel track with calculated metrics"""
    
    # Find vessel in synthetic database
    vessel = next((v for v in synthetic_generator.vessel_database if v['mmsi'] == mmsi), None)
    
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    # Set default time range
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    # Generate vessel response
    vessel_response = VesselResponse(
        mmsi=vessel['mmsi'],
        vessel_name=vessel['vessel_name'],
        vessel_type=vessel['vessel_type'],
        length=vessel['length'],
        max_speed=vessel['max_speed'],
        flag_country=vessel['flag_country'],
        first_seen=datetime.utcnow() - timedelta(days=30),
        last_updated=datetime.utcnow(),
        is_active=True
    )
    
    # Generate position history
    positions = []
    hours_diff = int((end_time - start_time).total_seconds() / 3600)
    
    for i in range(hours_diff):
        position_time = start_time + timedelta(hours=i)
        position = synthetic_generator.generate_vessel_position(vessel, position_time)
        
        positions.append(VesselPositionResponse(
            id=i,
            mmsi=position.mmsi,
            latitude=position.latitude,
            longitude=position.longitude,
            course_over_ground=position.course_over_ground,
            speed_over_ground=position.speed_over_ground,
            true_heading=position.true_heading,
            navigation_status=position.navigation_status,
            timestamp=position.timestamp,
            message_timestamp=position.message_timestamp,
            received_timestamp=position_time,
            data_source=position.data_source
        ))
    
    # Calculate track metrics
    total_distance = len(positions) * 10.0  # Simplified calculation
    average_speed = sum(p.speed_over_ground or 0 for p in positions) / len(positions) if positions else 0
    
    return VesselTrack(
        vessel=vessel_response,
        positions=positions,
        start_time=start_time,
        end_time=end_time,
        total_distance=total_distance,
        average_speed=average_speed,
        ports_visited=["SINGAPORE", "SHANGHAI"],  # Example data
        route_efficiency=85.5
    )


@router.get("/{mmsi}/summary", response_model=VesselSummary)
async def get_vessel_summary(mmsi: int):
    """Get vessel operational summary and statistics"""
    
    # Find vessel in synthetic database
    vessel = next((v for v in synthetic_generator.vessel_database if v['mmsi'] == mmsi), None)
    
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    # Generate synthetic summary data
    return VesselSummary(
        mmsi=mmsi,
        vessel_name=vessel['vessel_name'],
        total_positions=1440,  # 24 hours * 60 positions
        first_position=datetime.utcnow() - timedelta(days=30),
        last_position=datetime.utcnow(),
        total_distance=12500.0,  # nautical miles
        average_speed=15.2,
        max_speed=vessel['max_speed'],
        ports_visited=8,
        time_at_sea=720.0,  # hours
        time_in_port=48.0,  # hours
        fuel_efficiency_score=82.5,
        route_optimization_score=78.3,
        safety_score=95.1
    )


@router.get("/live/positions", response_model=List[VesselPositionResponse])
async def get_live_positions(
    bounds: Optional[str] = Query(None, description="Geographic bounds as 'north,south,east,west'"),
    vessel_types: Optional[str] = Query(None, description="Comma-separated vessel types"),
    limit: int = Query(1000, description="Maximum number of positions to return")
):
    """Get live vessel positions within specified bounds"""
    
    current_time = datetime.utcnow()
    
    # Generate synthetic live positions
    positions = synthetic_generator.generate_batch_positions(limit, current_time)
    
    # Convert to response models
    response_positions = []
    for i, position in enumerate(positions):
        response_positions.append(VesselPositionResponse(
            id=i,
            mmsi=position.mmsi,
            latitude=position.latitude,
            longitude=position.longitude,
            course_over_ground=position.course_over_ground,
            speed_over_ground=position.speed_over_ground,
            true_heading=position.true_heading,
            navigation_status=position.navigation_status,
            timestamp=position.timestamp,
            message_timestamp=position.message_timestamp,
            received_timestamp=current_time,
            data_source=position.data_source
        ))
    
    return response_positions 