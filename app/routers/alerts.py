"""
Alerts router - pest outbreak alerts (REQ-17 to REQ-20).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import get_db
from app.models import (
    User, Diagnosis, OutbreakAlert, Treatment, ProhibitedSubstance,
    Farm, Crop, UserRole
)
from app.schemas import (
    OutbreakAlertCreate, OutbreakAlertResponse, OutbreakAlertListResponse
)
from app.auth import get_current_active_user, require_role
from app.utils import haversine_distance, get_outbreak_config
from app.integrations.notifications import send_email, log_notification

router = APIRouter(prefix="/alerts", tags=["alerts"])


def filter_treatments_by_prohibited_substances(treatments: List[Treatment], db: Session) -> List[str]:
    """Filter treatments to remove prohibited substances."""
    prohibited = db.query(ProhibitedSubstance).all()
    prohibited_names = {p.substance_name.lower() for p in prohibited}

    filtered_treatments = []
    for treatment in treatments:
        if treatment.treatment_name.lower() not in prohibited_names:
            filtered_treatments.append(f"{treatment.treatment_name}: {treatment.dosage or 'As directed'}")

    return filtered_treatments


def check_outbreak_conditions(
    db: Session,
    diagnosis: Diagnosis,
    config: dict
) -> Optional[dict]:
    """
    Check if this diagnosis should trigger an outbreak alert.
    Returns outbreak info dict if conditions met, None otherwise.
    """
    try:
        # Get farm location
        farm = db.query(Farm).join(Crop).filter(Crop.id == diagnosis.crop_id).first()
        if not farm or not farm.latitude or not farm.longitude:
            return None

        lat = float(farm.latitude)
        lon = float(farm.longitude)
        radius_km = config["radius_km"]
        days_window = config["days_window"]
        threshold_count = config["threshold_count"]

        # Calculate time window
        cutoff_date = datetime.utcnow() - timedelta(days=days_window)

        # Count diagnoses of same disease within radius and time window
        nearby_diagnoses = db.query(Diagnosis).join(Crop).join(Farm).filter(
            and_(
                Diagnosis.disease_name == diagnosis.disease_name,
                Diagnosis.diagnosed_at >= cutoff_date,
                Diagnosis.id != diagnosis.id  # Exclude current diagnosis
            )
        ).all()

        # Filter by distance
        count = 0
        center_lat = lat
        center_lon = lon
        for d in nearby_diagnoses:
            d_farm = d.crop.farm
            if d_farm.latitude and d_farm.longitude:
                distance = haversine_distance(
                    center_lat, center_lon,
                    float(d_farm.latitude), float(d_farm.longitude)
                )
                if distance <= radius_km:
                    count += 1

        # Include current diagnosis in count
        count += 1

        # Check if threshold met
        if count >= threshold_count:
            # Check cooldown period - prevent duplicate alerts
            cooldown_hours = config["cooldown_hours"]
            cutoff_cooldown = datetime.utcnow() - timedelta(hours=cooldown_hours)

            existing_alert = db.query(OutbreakAlert).filter(
                and_(
                    OutbreakAlert.disease_name == diagnosis.disease_name,
                    OutbreakAlert.center_latitude == str(center_lat),
                    OutbreakAlert.center_longitude == str(center_lon),
                    OutbreakAlert.radius_km == str(radius_km),
                    OutbreakAlert.is_active == 1,
                    OutbreakAlert.created_at >= cutoff_cooldown
                )
            ).first()

            if existing_alert:
                return None  # Already have recent alert for this region

            # Get preventive measures from treatments
            treatments = db.query(Treatment).filter(
                Treatment.disease_class == diagnosis.disease_name
            ).all()
            preventive_measures = filter_treatments_by_prohibited_substances(treatments, db)

            return {
                "disease_name": diagnosis.disease_name,
                "center_latitude": center_lat,
                "center_longitude": center_lon,
                "radius_km": radius_km,
                "case_count": count,
                "preventive_measures": preventive_measures
            }

        return None

    except Exception as e:
        import logging
        logging.error(f"Error checking outbreak conditions: {e}")
        return None


def create_outbreak_alert(
    db: Session,
    outbreak_info: dict,
    created_by: User
) -> OutbreakAlert:
    """Create an outbreak alert and notify affected farmers."""
    alert = OutbreakAlert(
        disease_name=outbreak_info["disease_name"],
        region_description=f"Region within {outbreak_info['radius_km']} km of outbreak center",
        center_latitude=outbreak_info["center_latitude"],
        center_longitude=outbreak_info["center_longitude"],
        radius_km=outbreak_info["radius_km"],
        severity="high" if outbreak_info["case_count"] >= 5 else "medium",
        case_count=outbreak_info["case_count"],
        preventive_measures=", ".join(outbreak_info["preventive_measures"]) if outbreak_info["preventive_measures"] else None,
        is_active=1
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Notify affected farmers
    notify_affected_farmers(db, alert)

    return alert


def notify_affected_farmers(db: Session, alert: OutbreakAlert):
    """Send email notifications to farmers within the alert radius."""
    try:
        center_lat = float(alert.center_latitude)
        center_lon = float(alert.center_longitude)
        radius_km = float(alert.radius_km)

        # Find farmers with farms within radius
        farmers = db.query(User).join(Farm).filter(
            User.role == UserRole.FARMER,
            Farm.latitude.isnot(None),
            Farm.longitude.isnot(None)
        ).distinct().all()

        notified_count = 0
        for farmer in farmers:
            for farm in farmer.farms:
                if farm.latitude and farm.longitude:
                    distance = haversine_distance(
                        center_lat, center_lon,
                        float(farm.latitude), float(farm.longitude)
                    )
                    if distance <= radius_km:
                        # Send email
                        subject = f"⚠️ Pest Outbreak Alert: {alert.disease_name}"
                        body = f"""
Dear {farmer.full_name},

A pest outbreak has been detected in your area.

Disease: {alert.disease_name}
Region: {alert.region_description}
Severity: {alert.severity}
Cases Reported: {alert.case_count}

Preventive Measures:
{alert.preventive_measures or 'Consult local agricultural expert for guidance.'}

Please take appropriate precautions and monitor your crops closely.

Regards,
AgriAssist Team
"""
                        email_sent = send_email(farmer.email, subject, body)

                        # Log notification
                        log_notification(
                            user_id=farmer.id,
                            channel="email",
                            subject=subject,
                            content=body,
                            status="sent" if email_sent else "failed",
                            error_message=None if email_sent else "SMTP not configured",
                            db_session=db
                        )

                        notified_count += 1
                        break  # Only notify once per farmer

        import logging
        logging.info(f"Notified {notified_count} farmers about outbreak alert {alert.id}")

    except Exception as e:
        import logging
        logging.error(f"Error notifying affected farmers: {e}")


@router.post("/", response_model=OutbreakAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: OutbreakAlertCreate,
    current_user: User = Depends(require_role([UserRole.OFFICER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Manually create an outbreak alert (officer/admin only)."""
    # Get preventive measures from treatments
    treatments = db.query(Treatment).filter(
        Treatment.disease_class == alert_data.disease_name
    ).all()
    preventive_measures = filter_treatments_by_prohibited_substances(treatments, db)

    alert = OutbreakAlert(
        disease_name=alert_data.disease_name,
        region_description=alert_data.region_description,
        center_latitude=alert_data.center_latitude,
        center_longitude=alert_data.center_longitude,
        radius_km=alert_data.radius_km,
        severity=alert_data.severity,
        preventive_measures=", ".join(preventive_measures) if preventive_measures else alert_data.preventive_measures,
        is_active=1
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Notify affected farmers
    notify_affected_farmers(db, alert)

    return alert


@router.get("/", response_model=List[OutbreakAlertListResponse])
def get_alerts(
    lat: Optional[float] = Query(None, description="Latitude for location-based filtering"),
    lon: Optional[float] = Query(None, description="Longitude for location-based filtering"),
    radius_km: Optional[float] = Query(None, description="Radius in km for location-based filtering"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get alerts. If lat/lon provided, returns alerts within range."""
    query = db.query(OutbreakAlert).filter(OutbreakAlert.is_active == 1)

    # Location-based filtering for farmers
    if lat is not None and lon is not None:
        if radius_km is None:
            radius_km = 50.0  # Default radius

        alerts = query.all()
        filtered_alerts = []
        for alert in alerts:
            distance = haversine_distance(
                lat, lon,
                float(alert.center_latitude), float(alert.center_longitude)
            )
            if distance <= radius_km:
                filtered_alerts.append(alert)
        return filtered_alerts

    return query.order_by(OutbreakAlert.created_at.desc()).all()


@router.patch("/{alert_id}/retract", status_code=status.HTTP_200_OK)
def retract_alert(
    alert_id: int,
    current_user: User = Depends(require_role([UserRole.OFFICER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Retract an outbreak alert (officer/admin only)."""
    alert = db.query(OutbreakAlert).filter(OutbreakAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    alert.is_active = 0
    alert.retracted_at = datetime.utcnow()
    db.commit()

    return {"message": "Alert retracted successfully"}
