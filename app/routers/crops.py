from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Crop, Farm
from app.schemas import CropBase, CropCreate, CropResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/crops", tags=["crops"])


@router.get("/", response_model=List[CropResponse])
def get_user_crops(
    farm_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all crops for the current user's farms."""
    query = db.query(Crop).join(Farm).filter(Farm.owner_id == current_user.id)

    if farm_id:
        query = query.filter(Crop.farm_id == farm_id)

    crops = query.all()
    return crops


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(
    crop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific crop by ID."""
    crop = db.query(Crop).join(Farm).filter(
        Crop.id == crop_id,
        Farm.owner_id == current_user.id
    ).first()

    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    return crop


@router.post("/", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(
    crop: CropCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new crop for the current user's farm."""
    # Verify farm exists and belongs to user
    farm = db.query(Farm).filter(
        Farm.id == crop.farm_id,
        Farm.owner_id == current_user.id
    ).first()

    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found or you do not have permission"
        )

    new_crop = Crop(
        **crop.dict()
    )
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)
    return new_crop
