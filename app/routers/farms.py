from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Farm
from app.schemas import FarmResponse, FarmCreate
from app.auth import get_current_active_user

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("/", response_model=List[FarmResponse])
def get_user_farms(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all farms for the current user."""
    farms = db.query(Farm).filter(Farm.owner_id == current_user.id).all()
    return farms


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific farm by ID."""
    farm = db.query(Farm).filter(
        Farm.id == farm_id,
        Farm.owner_id == current_user.id
    ).first()

    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    return farm


@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    farm: FarmCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new farm for the current user."""
    new_farm = Farm(
        owner_id=current_user.id,
        **farm.dict()
    )
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)
    return new_farm
