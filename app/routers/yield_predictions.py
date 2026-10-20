from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import User, YieldPrediction, Farm, Crop, SoilRecord
from app.schemas import YieldPredictionCreate, YieldPredictionResponse
from app.auth import get_current_active_user
from app.integrations.weather import weather_service

router = APIRouter(prefix="/yield-predictions", tags=["yield-predictions"])


@router.post("/", response_model=YieldPredictionResponse, status_code=status.HTTP_201_CREATED)
def create_yield_prediction(
    prediction: YieldPredictionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new yield prediction."""
    # Verify farm exists and belongs to user
    farm = db.query(Farm).filter(Farm.id == prediction.farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create yield predictions for this farm"
        )
    
    # Verify crop exists and belongs to farm
    crop = db.query(Crop).filter(
        Crop.id == prediction.crop_id,
        Crop.farm_id == prediction.farm_id
    ).with_for_update().first()
    
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found on this farm"
        )
    
    # Use user-entered conditions first, then the latest saved soil test and farm weather.
    soil = db.query(SoilRecord).filter(SoilRecord.farm_id == farm.id).order_by(SoilRecord.test_date.desc()).first()
    weather = weather_service.get_weather_by_location(float(farm.latitude or 19.0), float(farm.longitude or 73.0))
    values = {
        "ph_level": prediction.ph_level if prediction.ph_level is not None else (soil.ph_level if soil else None),
        "nitrogen": prediction.nitrogen if prediction.nitrogen is not None else (soil.nitrogen if soil else None),
        "phosphorus": prediction.phosphorus if prediction.phosphorus is not None else (soil.phosphorus if soil else None),
        "potassium": prediction.potassium if prediction.potassium is not None else (soil.potassium if soil else None),
        "soil_moisture_percent": prediction.soil_moisture_percent if prediction.soil_moisture_percent is not None else (soil.moisture if soil else None),
    }
    rainfall_mm = float(prediction.rainfall_mm if prediction.rainfall_mm is not None else 700.0)
    rainfall_source = "user_input" if prediction.rainfall_mm is not None else "planning_default_700_mm"
    irrigation_mm = float(prediction.irrigation_mm or 0)
    temperature_c = float(prediction.temperature_c if prediction.temperature_c is not None else weather.get("temperature", 28.0))
    land_size_acres = float(prediction.land_size_acres)

    # Deterministic planning estimator. Baselines are quintals/acre; no validated model is present.
    baseline_yields = {"rice": 25.0, "wheat": 30.0, "cotton": 15.0, "tomato": 200.0, "sugarcane": 80.0, "soybean": 20.0, "onion": 150.0, "grape": 25.0, "maize": 35.0, "groundnut": 18.0, "chilli": 80.0, "potato": 180.0, "banana": 40.0, "mango": 15.0, "turmeric": 120.0}
    crop_key = crop.name.lower()
    baseline = baseline_yields.get(crop_key, 25.0)
    effective_rain = rainfall_mm + irrigation_mm * 0.75
    rain_factor = max(0.7, min(1.1, 1.0 - abs(effective_rain - 700.0) / 3000.0))
    temp_factor = 0.8 if temperature_c < 15 or temperature_c > 38 else 1.0 if 20 <= temperature_c <= 32 else 0.92
    soil_factor = 1.0
    ph_value = float(values["ph_level"]) if values["ph_level"] is not None else None
    if ph_value is not None:
        soil_factor *= 1.0 if 6.0 <= ph_value <= 7.5 else 0.85 if 5.0 <= ph_value <= 8.0 else 0.7
    for name, low, high in (("nitrogen", 40, 80), ("phosphorus", 20, 40), ("potassium", 30, 60)):
        if values[name] is not None:
            nutrient = float(values[name])
            soil_factor *= 1.0 if low <= nutrient <= high else 0.9 if nutrient < low else 0.95
    moisture = float(values["soil_moisture_percent"]) if values["soil_moisture_percent"] is not None else None
    if moisture is not None:
        soil_factor *= 0.8 if moisture < 20 else 0.85 if moisture > 80 else 1.0
    expected = baseline * land_size_acres * rain_factor * temp_factor * soil_factor
    yield_low, yield_high = expected * 0.8, expected * 1.2
    confidence_label = "low"

    from app.integrations.ml_yield import YieldModelLoader
    harvest_start, harvest_end = YieldModelLoader().estimate_harvest_window(crop.name, prediction.planting_date)
    last_prediction = db.query(YieldPrediction).filter(YieldPrediction.crop_id == prediction.crop_id).order_by(YieldPrediction.version.desc()).first()
    next_version = (last_prediction.version + 1) if last_prediction else 1
    snapshot = {
        "crop_name": crop.name, "farm_id": farm.id, "soil_type": farm.soil_type, "land_size_acres": land_size_acres,
        "planting_date": prediction.planting_date.isoformat(),
        **{key: (float(value) if value is not None else None) for key, value in values.items()},
        "rainfall_mm": rainfall_mm, "irrigation_mm": irrigation_mm, "temperature_c": temperature_c,
        "weather_source": weather.get("source", "fallback"), "rainfall_source": rainfall_source, "baseline_quintals_per_acre": baseline,
        "method": "crop-baseline-adjusted-v1", "limitations": "Indicative estimate; not validated against observed farm outcomes."
    }
    db_prediction = YieldPrediction(
        farm_id=prediction.farm_id, crop_id=prediction.crop_id, land_size_acres=prediction.land_size_acres,
        planting_date=prediction.planting_date, predicted_yield_low=Decimal(str(yield_low)),
        predicted_yield_expected=Decimal(str(expected)), predicted_yield_high=Decimal(str(yield_high)),
        confidence_label=confidence_label, harvest_window_start=harvest_start, harvest_window_end=harvest_end,
        version=next_version, input_snapshot=snapshot, model_version="crop-baseline-adjusted-v1"
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return db_prediction


@router.get("/", response_model=List[YieldPredictionResponse])
def get_yield_predictions(
    farm_id: int = None,
    crop_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all yield predictions for the current user's farms."""
    query = db.query(YieldPrediction).join(Farm).filter(Farm.owner_id == current_user.id)
    
    if farm_id:
        query = query.filter(YieldPrediction.farm_id == farm_id)
    
    if crop_id:
        query = query.filter(YieldPrediction.crop_id == crop_id)
    
    predictions = query.order_by(YieldPrediction.created_at.desc()).all()
    return predictions


@router.get("/{prediction_id}", response_model=YieldPredictionResponse)
def get_yield_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific yield prediction by ID."""
    prediction = db.query(YieldPrediction).join(Farm).filter(
        YieldPrediction.id == prediction_id,
        Farm.owner_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yield prediction not found"
        )
    
    return prediction


@router.get("/crop/{crop_id}/history", response_model=List[YieldPredictionResponse])
def get_yield_prediction_history(
    crop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get yield prediction history for a specific crop (all versions)."""
    # Verify crop belongs to user's farm
    crop = db.query(Crop).join(Farm).filter(
        Crop.id == crop_id,
        Farm.owner_id == current_user.id
    ).first()
    
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    
    predictions = db.query(YieldPrediction).filter(
        YieldPrediction.crop_id == crop_id
    ).order_by(YieldPrediction.created_at.asc(), YieldPrediction.id.asc()).all()
    
    return predictions
