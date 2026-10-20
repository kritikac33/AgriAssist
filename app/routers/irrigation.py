from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, time
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
    base_et = 5.0 * max(0.1, temperature / 25.0)

    # Crop evapotranspiration
    etc = base_et * kc

    # Subtract effective rainfall (assume 70% effective)
    effective_rainfall = rainfall_mm * 0.7

    # Net irrigation requirement
    nir = max(0, etc - effective_rainfall)

    # Convert to liters for the farm area (1 hectare = 10,000 mÂ²)
    # 1 mm = 10 mÂ³ per hectare = 10,000 liters per hectare
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

    scheduled_day = schedule.scheduled_date.date()
    crop = db.query(Crop).filter(Crop.id == schedule.crop_id, Crop.farm_id == farm.id).first() if schedule.crop_id else db.query(Crop).filter(Crop.farm_id == farm.id).first()
    if schedule.crop_id and not crop:
        raise HTTPException(status_code=404, detail="Crop not found on this farm")
    day_start = datetime.combine(scheduled_day, time.min)
    day_end = day_start + timedelta(days=1)
    existing = db.query(IrrigationSchedule).filter(
        IrrigationSchedule.farm_id == farm.id,
        IrrigationSchedule.crop_id == (crop.id if crop else None),
        IrrigationSchedule.scheduled_date >= day_start,
        IrrigationSchedule.scheduled_date < day_end,
        IrrigationSchedule.status.in_(["pending", "postponed"]),
    ).first()
    crop_name = crop.name if crop else "wheat"
    weather = weather_service.get_weather_by_location(float(farm.latitude or 19.0), float(farm.longitude or 73.0))
    area_hectares = schedule.area_hectares or (crop.area_hectares if crop and crop.area_hectares else farm.area_hectares) or Decimal("1.0")
    temperature = float(schedule.temperature_c if schedule.temperature_c is not None else weather.get("temperature", 28.0))
    rainfall = float(schedule.rainfall_mm if schedule.rainfall_mm is not None else weather.get("rainfall_24h", 0.0))
    moisture = float(schedule.soil_moisture_percent if schedule.soil_moisture_percent is not None else 30.0)
    kc = CROP_COEFFICIENTS.get(crop_name.lower(), 1.0)
    stage_factor = {"initial": 0.75, "development": 0.9, "mid": 1.0, "late": 0.8}.get((schedule.crop_stage or "").lower(), 1.0)
    soil_type = (schedule.soil_type or farm.soil_type or "unknown").lower()
    application_efficiency = 0.70 if "sand" in soil_type else 0.90 if "clay" in soil_type else 0.85
    water_amount = calculate_irrigation_water(area_hectares, crop_name, temperature, rainfall)
    water_amount *= Decimal(str(stage_factor * max(0.0, min(1.0, (100.0 - moisture) / 70.0)) / application_efficiency))
    schedule_data = schedule.model_dump()
    schedule_data.update({
        "scheduled_date": datetime.combine(scheduled_day, time(6, 0)),
        "crop_id": crop.id if crop else None,
        "area_hectares": area_hectares,
        "soil_type": soil_type,
        "temperature_c": temperature,
        "rainfall_mm": rainfall,
        "soil_moisture_percent": moisture,
        "weather_source": "user_input" if any(value is not None for value in (schedule.temperature_c, schedule.rainfall_mm, schedule.soil_moisture_percent)) else weather.get("source", "fallback"),
        "water_amount_liters": water_amount,
        "notes": (f"Estimate: ETc x 10,000 L/ha/mm x {area_hectares} ha; Kc {kc:.2f}, growth-stage factor {stage_factor:.2f}, {soil_type} soil application efficiency {application_efficiency:.0%}, temperature {temperature:.1f} C, rainfall {rainfall:.1f} mm, soil moisture {moisture:.0f}%. "
                  + ("Effective rainfall meets today's estimated crop water need; no irrigation is recommended. " if water_amount <= 0 else "")
                  + "Check crop and field conditions."),
    })
    # Duration requires a known system flow rate; do not invent one.
    schedule_data["duration_hours"] = schedule.duration_hours
    
    # Create schedule
    if existing:
        # Regenerate today's existing active schedule with the values currently
        # shown in the form. Otherwise stale rainfall inputs can leave a 0 L
        # recommendation in place even after the farmer corrects them.
        for field, value in schedule_data.items():
            setattr(existing, field, value)
        db_schedule = existing
    else:
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
    has_scheduled_forecast = False

    for forecast_item in forecast.get("forecasts", []):
        if forecast_item["datetime"].date() == scheduled_date:
            has_scheduled_forecast = True
            total_rainfall += forecast_item.get("rainfall", 0.0)

    # Avoid duplicate or zero-length updates; sum only forecast entries on schedule date.
    if total_rainfall > 5.0:
        schedule.status = "skipped"
        schedule.rainfall_mm = Decimal(str(total_rainfall))
        schedule.weather_source = forecast.get("source", "fallback")
        schedule.notes = f"Skipped due to forecasted rain ({total_rainfall:.1f} mm). Weather source: {schedule.weather_source}."
    else:
        # Recalculate water amount
        crop = schedule.crop or db.query(Crop).filter(Crop.farm_id == farm.id).first()
        crop_name = crop.name if crop else "wheat"

        weather = weather_service.get_weather_by_location(
            float(farm.latitude or 19.0),
            float(farm.longitude or 73.0)
        )

        area_hectares = schedule.area_hectares or (schedule.crop.area_hectares if schedule.crop and schedule.crop.area_hectares else farm.area_hectares) or Decimal("1.0")
        temperature = float(schedule.temperature_c if schedule.temperature_c is not None else weather.get("temperature", 28.0))
        rainfall = float(total_rainfall if has_scheduled_forecast else (schedule.rainfall_mm or 0))
        moisture = float(schedule.soil_moisture_percent if schedule.soil_moisture_percent is not None else 30.0)
        stage_factor = {"initial": 0.75, "development": 0.9, "mid": 1.0, "late": 0.8}.get((schedule.crop_stage or "").lower(), 1.0)
        soil_type = (schedule.soil_type or farm.soil_type or "unknown").lower()
        application_efficiency = 0.70 if "sand" in soil_type else 0.90 if "clay" in soil_type else 0.85
        schedule.water_amount_liters = calculate_irrigation_water(area_hectares, crop_name, temperature, rainfall) * Decimal(str(stage_factor * max(0.0, min(1.0, (100.0-moisture)/70.0)) / application_efficiency))
        schedule.weather_source = weather.get("source", "fallback")
        schedule.rainfall_mm = Decimal(str(rainfall))
        schedule.status = "pending"
        schedule.notes = f"Recalculated estimate: ETc x 10,000 L/ha/mm x {area_hectares} ha; soil {soil_type} (efficiency {application_efficiency:.0%}), {crop_name}, {temperature:.1f} C, {rainfall:.1f} mm rain, {moisture:.0f}% moisture. Weather source: {schedule.weather_source}."

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

    if update_data.crop_id is not None:
        crop = db.query(Crop).filter(Crop.id == update_data.crop_id, Crop.farm_id == schedule.farm_id).first()
        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found on this farm")
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

    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="Postpone days must be between 1 and 30")
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
