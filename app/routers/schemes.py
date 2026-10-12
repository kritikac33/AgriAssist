"""
Schemes router - subsidy/scheme eligibility checker.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.database import get_db
from app.models import User, Scheme, Farm, UserRole
from app.schemas import SchemeMatchRequest, SchemeMatchResponse, SchemeResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.post("/matches", response_model=List[SchemeMatchResponse])
def get_scheme_matches(
    match_request: SchemeMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get eligible schemes for a farm based on rule-based matching."""
    # Get farm
    farm = db.query(Farm).filter(Farm.id == match_request.farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )

    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check schemes for your own farms"
        )

    # Get all active schemes
    schemes = db.query(Scheme).filter(Scheme.is_active == 1).all()

    matches = []
    for scheme in schemes:
        eligibility_reason = None

        # Check land size eligibility
        if scheme.min_land_hectares and scheme.max_land_hectares:
            if farm.area_hectares:
                if scheme.min_land_hectares <= farm.area_hectares <= scheme.max_land_hectares:
                    eligibility_reason = f"Land size {farm.area_hectares} hectares is within eligible range ({scheme.min_land_hectares}-{scheme.max_land_hectares} hectares)"
            else:
                continue  # Cannot verify without land size
        elif scheme.min_land_hectares:
            if farm.area_hectares and farm.area_hectares >= scheme.min_land_hectares:
                eligibility_reason = f"Land size {farm.area_hectares} hectares meets minimum requirement of {scheme.min_land_hectares} hectares"
        elif scheme.max_land_hectares:
            if farm.area_hectares and farm.area_hectares <= scheme.max_land_hectares:
                eligibility_reason = f"Land size {farm.area_hectares} hectares is within maximum limit of {scheme.max_land_hectares} hectares"
        else:
            eligibility_reason = "No land size restrictions"

        # Check crop eligibility if specified
        if scheme.eligible_crops and match_request.crop_name:
            eligible_crops_list = [c.strip().lower() for c in scheme.eligible_crops.split(",")]
            if match_request.crop_name.lower() in eligible_crops_list:
                if eligibility_reason:
                    eligibility_reason += f"; Crop '{match_request.crop_name}' is eligible"
                else:
                    eligibility_reason = f"Crop '{match_request.crop_name}' is eligible"
            else:
                continue  # Crop not eligible
        elif scheme.eligible_crops and not match_request.crop_name:
            continue  # Scheme requires specific crop but none provided

        # Check state eligibility if specified
        if scheme.eligible_states and match_request.state:
            eligible_states_list = [s.strip().lower() for s in scheme.eligible_states.split(",")]
            if match_request.state.lower() in eligible_states_list:
                if eligibility_reason:
                    eligibility_reason += f"; State '{match_request.state}' is eligible"
                else:
                    eligibility_reason = f"State '{match_request.state}' is eligible"
            else:
                continue  # State not eligible
        elif scheme.eligible_states and not match_request.state:
            continue  # Scheme requires specific state but none provided

        # If we have an eligibility reason, add to matches
        if eligibility_reason:
            matches.append(SchemeMatchResponse(
                scheme_id=scheme.id,
                scheme_name=scheme.name,
                eligibility_reason=eligibility_reason,
                benefits=scheme.benefits,
                application_link=scheme.application_link,
                deadline=scheme.deadline
            ))

    return matches


@router.get("/", response_model=List[SchemeResponse])
def get_schemes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all active schemes."""
    schemes = db.query(Scheme).filter(Scheme.is_active == 1).all()
    return schemes
