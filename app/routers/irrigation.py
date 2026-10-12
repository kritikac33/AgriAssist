from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import get_db
from app.models import User, IrrigationSchedule, Farm, NotificationLog, Crop
from app.schemas import IrrigationScheduleCreate, IrrigationScheduleResponse, IrrigationScheduleUpdate
from app.auth import get_current_active_user
from app.integrations.weather import weather_service

router = APIRouter(prefix="/irrigation-schedules", tags=["irrigation-schedules"])

# Crop coefficients (Kc) for common crops
CROP_COEFFICIENTS = {
    "rice": 1.2,
    "wheat": 1.0,
    "cotton": 1.1,
    "tomato": 0.85,
    "sugarcane": 1.25,
    "soybean": 0.95,
    "onion": 0.9,
    "grape": 0.75,
    "maize": 1.05,
    "groundnut": 0.9,
    "chilli": 0.95,
    "potato": 0.85,
    "banana": 1.0,
    "mango": 0.8,
    "turmeric": 0.95
}


def calculate_irrigation_water(
    farm_area_hectares: Decimal,
    crop_name: str,
    temperature: float,
    rainfall_mm: float
) -> Decimal:
    """
    Calculate irrigation water requirement using Hargreaves method (simplified).
    Returns water amount in liters.
    """
    # Get crop coefficient
    kc = CROP_COEFFICIENTS.get(crop_name.lower(), 1.0)
    
    # Reference evapotranspiration (simplified Hargreaves)
    # ETo = 0.0023 * Ra * (T + 17.8) * sqrt(Tmax - Tmin)
    # Simplified: base 5mm/day adjusted by temperature
    base_et = 5.0 * (temperature / 25.0)
    
    # Crop evapotranspiration
    etc = base_et * kc
    
    # Subtract effective rainfall (assume 70% effective)
    effective_rainfall = rainfall_mm * 0.7
    
    # Net irrigation requirement
    nir = max(0, etc - effective_rainfall)
    
    # Convert to liters for the farm area (1 hectare = 10,000 m²)
    # 1 mm = 10 m³ per hectare = 10,000 liters per hectare
    water_liters = Decimal(str(nir * 10000 * float(farm_area_hectares)))
    
    return water_liters


@router.post("/", response_model=IrrigationScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_irrigation_schedule(
    schedule: IrrigationScheduleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new irrigation schedule."""
    # Verify farm exists and belongs to user
    farm = db.query(Farm).filter(Farm.id == schedule.farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create irrigation schedules for this farm"
        )
    
    # Get farm's primary crop for calculation
    crop = db.query(Crop).filter(Crop.farm_id == farm.id).first()
    crop_name = crop.name if crop else "wheat"
    
    # Get weather data
    weather = weather_service.get_weather_by_location(
        float(farm.latitude or 19.0),
        float(farm.longitude or 73.0)
    )
    
    # Calculate water requirement
    area_hectares = farm.area_hectares or Decimal("1.0")
    water_amount = calculate_irrigation_water(
        area_hectares,
        crop_name,
        weather.get("temperature", 28.0),
        weather.get("rainfall_24h", 0.0)
    )
    
    # Set water amount if not provided
    schedule_data = schedule.model_dump()
    if not schedule_data.get("water_amount_liters"):
        schedule_data["water_amount_liters"] = water_amount
    
    # Create schedule
    db_schedule = IrrigationSchedule(**schedule_data)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    return db_schedule


@router.get("/", response_model=List[IrrigationScheduleResponse])
def get_irrigation_schedules(
    farm_id: int = None,
    status_filter: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all irrigation schedules for the current user's farms."""
    query = db.query(IrrigationSchedule).join(Farm).filter(Farm.owner_id == current_user.id)
    
    if farm_id:
        query = query.filter(IrrigationSchedule.farm_id == farm_id)
    
    if status_filter:
        query = query.filter(IrrigationSchedule.status == status_filter)
    
    schedules = query.order_by(IrrigationSchedule.scheduled_date.asc()).all()
    return schedules


@router.post("/{schedule_id}/recalculate", response_model=IrrigationScheduleResponse)
def recalculate_irrigation_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Recalculate irrigation schedule based on updated weather forecast."""
    schedule = db.query(IrrigationSchedule).join(Farm).filter(
        IrrigationSchedule.id == schedule_id,
        Farm.owner_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Irrigation schedule not found"
        )
    
    farm = schedule.farm
    
    # Get weather forecast
    forecast = weather_service.get_forecast_by_location(
        float(farm.latitude or 19.0),
        float(farm.longitude or 73.0),
        days=5
    )
    
    # Check for rain on scheduled date
    scheduled_date = schedule.scheduled_date.date()
    total_rainfall = 0.0
    
    for forecast_item in forecast.get("forecasts", []):
        if forecast_item["datetime"].date() == scheduled_date:
            total_rainfall += forecast_item.get("rainfall", 0.0)
    
    # If significant rain (>5mm), skip irrigation
    if total_rainfall > 5.0:
        schedule.status = "skipped"
        schedule.notes = f"Skipped due to forecasted rain ({total_rainfall:.1f}mm)"
    else:
        # Recalculate water amount
        crop = db.query(Crop).filter(Crop.farm_id == farm.id).first()
        crop_name = crop.name if crop else "wheat"
        
        weather = weather_service.get_weather_by_location(
            float(farm.latitude or 19.0),
            float(farm.longitude or 73.0)
        )
        
        area_hectares = farm.area_hectares or Decimal("1.0")
        water_amount = calculate_irrigation_water(
            area_hectares,
            crop_name,
            weather.get("temperature", 28.0),
            total_rainfall
        )
        
        schedule.water_amount_liters = water_amount
        schedule.status = "pending"
        schedule.notes = f"Recalculated based on forecast (rain: {total_rainfall:.1f}mm)"
    
    db.commit()
    db.refresh(schedule)
    
    # Log notification
    notification = NotificationLog(
        user_id=current_user.id,
        channel="in_app",
        subject="Irrigation Schedule Updated",
        content=f"Irrigation schedule for {scheduled_date} has been recalculated. Status: {schedule.status}"
    )
    db.add(notification)
    db.commit()
    
    return schedule


@router.put("/{schedule_id}", response_model=IrrigationScheduleResponse)
def update_irrigation_schedule(
    schedule_id: int,
    update_data: IrrigationScheduleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an irrigation schedule."""
    schedule = db.query(IrrigationSchedule).join(Farm).filter(
        IrrigationSchedule.id == schedule_id,
        Farm.owner_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Irrigation schedule not found"
        )
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    
    # Log notification if status changed
    if update_data.status:
        notification = NotificationLog(
            user_id=current_user.id,
            channel="in_app",
            subject="Irrigation Schedule Status Changed",
            content=f"Irrigation schedule status updated to: {update_data.status}"
        )
        db.add(notification)
        db.commit()
    
    return schedule


@router.post("/{schedule_id}/postpone", response_model=IrrigationScheduleResponse)
def postpone_irrigation_schedule(
    schedule_id: int,
    days: int = 1,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Postpone an irrigation schedule by specified days."""
    schedule = db.query(IrrigationSchedule).join(Farm).filter(
        IrrigationSchedule.id == schedule_id,
        Farm.owner_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Irrigation schedule not found"
        )
    
    # Postpone by days
    schedule.scheduled_date = schedule.scheduled_date + timedelta(days=days)
    schedule.status = "postponed"
    schedule.notes = f"Postponed by {days} days"
    
    db.commit()
    db.refresh(schedule)
    
    # Log notification
    notification = NotificationLog(
        user_id=current_user.id,
        channel="in_app",
        subject="Irrigation Schedule Postponed",
        content=f"Irrigation schedule postponed by {days} days to {schedule.scheduled_date}"
    )
    db.add(notification)
    db.commit()
    
    return schedule
