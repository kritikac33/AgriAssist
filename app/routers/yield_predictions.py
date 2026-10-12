from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import User, YieldPrediction, Farm, Crop
from app.schemas import YieldPredictionCreate, YieldPredictionResponse
from app.auth import get_current_active_user
from app.integrations.ml_yield import predict_yield
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
    ).first()
    
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found on this farm"
        )
    
    # Get weather data for the farm location
    weather = weather_service.get_weather_by_location(
        float(farm.latitude or 19.0),
        float(farm.longitude or 73.0)
    )
    
    # Convert land size from hectares to acres (1 hectare = 2.471 acres)
    land_size_acres = float(prediction.land_size_acres or 1.0)
    
    # Run ML prediction
    yield_low, yield_expected, yield_high, confidence_label, is_stub = predict_yield(
        crop_name=crop.name,
        land_size_acres=land_size_acres,
        planting_date=prediction.planting_date,
        rainfall_mm=weather.get("rainfall_24h", 500.0),
        temperature_c=weather.get("temperature", 28.0)
    )
    
    # Estimate harvest window
    from app.integrations.ml_yield import YieldModelLoader
    model_loader = YieldModelLoader()
    harvest_start, harvest_end = model_loader.estimate_harvest_window(crop.name, prediction.planting_date)
    
    # Get next version number for this crop
    last_prediction = db.query(YieldPrediction).filter(
        YieldPrediction.crop_id == prediction.crop_id
    ).order_by(YieldPrediction.version.desc()).first()
    
    next_version = (last_prediction.version + 1) if last_prediction else 1
    
    # Create yield prediction
    db_prediction = YieldPrediction(
        farm_id=prediction.farm_id,
        crop_id=prediction.crop_id,
        land_size_acres=prediction.land_size_acres,
        planting_date=prediction.planting_date,
        predicted_yield_low=Decimal(str(yield_low)),
        predicted_yield_expected=Decimal(str(yield_expected)),
        predicted_yield_high=Decimal(str(yield_high)),
        confidence_label=confidence_label,
        harvest_window_start=harvest_start,
        harvest_window_end=harvest_end,
        version=next_version
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
    ).order_by(YieldPrediction.version.asc()).all()
    
    return predictions
