from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.database import get_db
from app.models import User, SoilRecord, Farm, CropNutrientRequirement, ProhibitedSubstance
from app.schemas import SoilRecordCreate, SoilRecordResponse, SoilAnalysis
from app.auth import get_current_active_user

router = APIRouter(prefix="/soil-records", tags=["soil-records"])


def analyze_soil_health(soil_record: SoilRecord, crop_name: str, db: Session) -> SoilAnalysis:
    """Analyze soil health against crop requirements."""
    # Get crop nutrient requirements
    requirements = db.query(CropNutrientRequirement).filter(
        CropNutrientRequirement.crop_name == crop_name
    ).first()
    
    if not requirements:
        # Default requirements if not found
        requirements = CropNutrientRequirement(
            ph_min=Decimal("6.0"),
            ph_max=Decimal("7.5"),
            nitrogen_min=Decimal("40"),
            nitrogen_max=Decimal("80"),
            phosphorus_min=Decimal("20"),
            phosphorus_max=Decimal("40"),
            potassium_min=Decimal("30"),
            potassium_max=Decimal("60")
        )
    
    # Analyze pH
    if soil_record.ph_level < requirements.ph_min:
        ph_status = "low"
        ph_explanation = f"Soil is acidic. Consider adding lime to raise pH to optimal range ({requirements.ph_min}-{requirements.ph_max})."
    elif soil_record.ph_level > requirements.ph_max:
        ph_status = "high"
        ph_explanation = f"Soil is alkaline. Consider adding sulfur to lower pH to optimal range ({requirements.ph_min}-{requirements.ph_max})."
    else:
        ph_status = "optimal"
        ph_explanation = f"pH level is within optimal range for {crop_name}."
    
    # Analyze nitrogen
    if soil_record.nitrogen < requirements.nitrogen_min:
        nitrogen_status = "low"
        nitrogen_explanation = f"Low nitrogen. Apply nitrogen-rich fertilizer (urea, DAP) to promote leaf growth."
    elif soil_record.nitrogen > requirements.nitrogen_max:
        nitrogen_status = "high"
        nitrogen_explanation = f"High nitrogen. Reduce nitrogen application to prevent excessive vegetative growth."
    else:
        nitrogen_status = "optimal"
        nitrogen_explanation = f"Nitrogen level is optimal for {crop_name}."
    
    # Analyze phosphorus
    if soil_record.phosphorus < requirements.phosphorus_min:
        phosphorus_status = "low"
        phosphorus_explanation = f"Low phosphorus. Apply phosphorus-rich fertilizer (DAP, SSP) to promote root development."
    elif soil_record.phosphorus > requirements.phosphorus_max:
        phosphorus_status = "high"
        phosphorus_explanation = f"High phosphorus. May interfere with micronutrient uptake. Monitor crop health."
    else:
        phosphorus_status = "optimal"
        phosphorus_explanation = f"Phosphorus level is optimal for {crop_name}."
    
    # Analyze potassium
    if soil_record.potassium < requirements.potassium_min:
        potassium_status = "low"
        potassium_explanation = f"Low potassium. Apply potassium-rich fertilizer (MOP, SOP) to improve disease resistance and fruit quality."
    elif soil_record.potassium > requirements.potassium_max:
        potassium_status = "high"
        potassium_explanation = f"High potassium. May affect magnesium and calcium uptake. Monitor crop health."
    else:
        potassium_status = "optimal"
        potassium_explanation = f"Potassium level is optimal for {crop_name}."
    
    return SoilAnalysis(
        ph_status=ph_status,
        ph_explanation=ph_explanation,
        nitrogen_status=nitrogen_status,
        nitrogen_explanation=nitrogen_explanation,
        phosphorus_status=phosphorus_status,
        phosphorus_explanation=phosphorus_explanation,
        potassium_status=potassium_status,
        potassium_explanation=potassium_explanation
    )


@router.post("/", response_model=SoilRecordResponse, status_code=status.HTTP_201_CREATED)
def create_soil_record(
    soil_record: SoilRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new soil record."""
    # Verify farm exists and belongs to user
    farm = db.query(Farm).filter(Farm.id == soil_record.farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add soil records for this farm"
        )
    
    # Create soil record
    db_soil_record = SoilRecord(**soil_record.model_dump())
    db.add(db_soil_record)
    db.commit()
    db.refresh(db_soil_record)
    
    return db_soil_record


@router.post("/from-sensor", response_model=SoilRecordResponse, status_code=status.HTTP_201_CREATED)
def create_soil_record_from_sensor(
    soil_record: SoilRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a soil record from sensor data (source='sensor')."""
    # Verify farm exists and belongs to user
    farm = db.query(Farm).filter(Farm.id == soil_record.farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add soil records for this farm"
        )
    
    # Override source to 'sensor'
    soil_record_data = soil_record.model_dump()
    soil_record_data['source'] = 'sensor'
    
    # Create soil record
    db_soil_record = SoilRecord(**soil_record_data)
    db.add(db_soil_record)
    db.commit()
    db.refresh(db_soil_record)
    
    return db_soil_record


@router.get("/", response_model=List[SoilRecordResponse])
def get_soil_records(
    farm_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all soil records for the current user's farms."""
    query = db.query(SoilRecord).join(Farm).filter(Farm.owner_id == current_user.id)
    
    if farm_id:
        query = query.filter(SoilRecord.farm_id == farm_id)
    
    records = query.order_by(SoilRecord.test_date.desc()).all()
    return records


@router.get("/{record_id}/analyze", response_model=SoilAnalysis)
def analyze_soil_record(
    record_id: int,
    crop_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze a soil record against crop requirements."""
    soil_record = db.query(SoilRecord).join(Farm).filter(
        SoilRecord.id == record_id,
        Farm.owner_id == current_user.id
    ).first()
    
    if not soil_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soil record not found"
        )
    
    return analyze_soil_health(soil_record, crop_name, db)
