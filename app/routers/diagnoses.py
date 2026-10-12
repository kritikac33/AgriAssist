from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os
import uuid
from PIL import Image
import io

from app.database import get_db
from app.models import User, Diagnosis, Treatment, ProhibitedSubstance, ConsentRecord, Crop
from app.schemas import DiagnosisCreate, DiagnosisResponse, DiagnosisWithTreatment, TreatmentDetail
from app.auth import get_current_active_user
from app.integrations.ml_disease import predict_disease
from app.config import settings
from app.utils import get_outbreak_config
from app.routers.alerts import check_outbreak_conditions, create_outbreak_alert

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])

# Upload directory
UPLOAD_DIR = "app/static/uploads/diagnoses"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CONFIDENCE_THRESHOLD = 0.6
DISCLAIMER = "This is an AI-assisted diagnosis. Consult a local agricultural expert for confirmation."


def save_uploaded_image(file: UploadFile) -> str:
    """Save uploaded image and return the file path."""
    # Read and validate image
    contents = file.file.read()
    
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Resize to max 1MB
    img = Image.open(io.BytesIO(contents))
    img.thumbnail((1024, 1024))
    
    # Compress
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    contents = output.read()
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    return file_path


def filter_treatments_by_prohibited_substances(treatments: List[Treatment], db: Session) -> List[TreatmentDetail]:
    """Filter treatments to remove prohibited substances."""
    prohibited = db.query(ProhibitedSubstance).all()
    prohibited_names = {p.substance_name.lower() for p in prohibited}

    filtered_treatments = []
    for treatment in treatments:
        if treatment.treatment_name.lower() not in prohibited_names:
            filtered_treatments.append(TreatmentDetail(
                treatment_type=treatment.treatment_type,
                description=f"{treatment.treatment_name}: {treatment.dosage or 'As directed'}. {treatment.application_method or ''}",
                is_organic=bool(treatment.organic)
            ))

    return filtered_treatments


@router.post("/", response_model=DiagnosisWithTreatment, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    crop_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new disease diagnosis with image upload."""
    # Verify crop exists and belongs to user's farm
    from app.models import Farm
    crop = db.query(Crop).join(Farm).filter(
        Crop.id == crop_id,
        Farm.owner_id == current_user.id
    ).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found or you do not have permission to access it"
        )
    
    # Save uploaded image
    image_path = save_uploaded_image(file)
    
    # Get image bytes for ML prediction
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Run ML prediction
    disease_name, confidence_score, is_stub = predict_disease(image_bytes)
    
    # Get treatments for the disease class
    treatments = db.query(Treatment).filter(Treatment.disease_class == disease_name).all()
    treatment_list = filter_treatments_by_prohibited_substances(treatments, db)
    
    # Create consent record for training data reuse
    consent_record = ConsentRecord(
        user_id=current_user.id,
        consent_type="training_data_reuse",
        is_granted=True
    )
    db.add(consent_record)
    db.commit()
    db.refresh(consent_record)
    
    # Create diagnosis record
    diagnosis = Diagnosis(
        crop_id=crop_id,
        disease_name=disease_name,
        confidence_score=confidence_score,
        symptoms=f"AI-detected: {disease_name}",
        recommended_action="Consult with agricultural expert for confirmation",
        image_path=image_path,
        consent_record_id=consent_record.id
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    # Check for outbreak conditions (REQ-17)
    config = get_outbreak_config(db)
    outbreak_info = check_outbreak_conditions(db, diagnosis, config)
    if outbreak_info:
        # Auto-create outbreak alert
        create_outbreak_alert(db, outbreak_info, current_user)

    # Check low confidence
    low_confidence = confidence_score < CONFIDENCE_THRESHOLD
    
    return DiagnosisWithTreatment(
        id=diagnosis.id,
        crop_id=diagnosis.crop_id,
        disease_name=diagnosis.disease_name,
        confidence_score=diagnosis.confidence_score,
        symptoms=diagnosis.symptoms,
        recommended_action=diagnosis.recommended_action,
        image_path=diagnosis.image_path,
        consent_record_id=diagnosis.consent_record_id,
        diagnosed_at=diagnosis.diagnosed_at,
        created_at=diagnosis.created_at,
        updated_at=diagnosis.updated_at,
        low_confidence=low_confidence,
        treatments=treatment_list,
        disclaimer=DISCLAIMER
    )


@router.get("/", response_model=List[DiagnosisResponse])
def get_diagnoses(
    crop_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all diagnoses for the current user's crops."""
    query = db.query(Diagnosis).join(Crop).join(User).filter(User.id == current_user.id)
    
    if crop_id:
        query = query.filter(Diagnosis.crop_id == crop_id)
    
    diagnoses = query.order_by(Diagnosis.diagnosed_at.desc()).all()
    return diagnoses


@router.get("/{diagnosis_id}", response_model=DiagnosisWithTreatment)
def get_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific diagnosis by ID."""
    diagnosis = db.query(Diagnosis).join(Crop).join(User).filter(
        Diagnosis.id == diagnosis_id,
        User.id == current_user.id
    ).first()
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )
    
    # Get treatments
    treatments = db.query(Treatment).filter(Treatment.disease_class == diagnosis.disease_name).all()
    treatment_list = filter_treatments_by_prohibited_substances(treatments, db)
    
    # Check low confidence
    low_confidence = diagnosis.confidence_score and diagnosis.confidence_score < CONFIDENCE_THRESHOLD
    
    return DiagnosisWithTreatment(
        **diagnosis.__dict__,
        low_confidence=low_confidence,
        treatments=treatment_list,
        disclaimer=DISCLAIMER
    )
