from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
from app.models import UserRole


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Farm Schemas
class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    area_hectares: Optional[Decimal] = None
    soil_type: Optional[str] = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    area_hectares: Optional[Decimal] = None
    soil_type: Optional[str] = None


class FarmResponse(FarmBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Crop Schemas
class CropBase(BaseModel):
    farm_id: int
    name: str
    variety: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    area_hectares: Optional[Decimal] = None
    status: str = "active"


class CropCreate(CropBase):
    pass


class CropUpdate(BaseModel):
    name: Optional[str] = None
    variety: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    area_hectares: Optional[Decimal] = None
    status: Optional[str] = None


class CropResponse(CropBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Diagnosis Schemas
class DiagnosisBase(BaseModel):
    crop_id: int
    disease_name: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    symptoms: Optional[str] = None
    recommended_action: Optional[str] = None
    image_path: Optional[str] = None
    consent_record_id: Optional[int] = None


class DiagnosisCreate(DiagnosisBase):
    pass


class DiagnosisResponse(DiagnosisBase):
    id: int
    diagnosed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TreatmentDetail(BaseModel):
    treatment_type: str
    description: str
    is_organic: bool


class DiagnosisWithTreatment(DiagnosisResponse):
    low_confidence: bool = False
    treatments: list[TreatmentDetail] = []
    disclaimer: str = "This is an AI-assisted diagnosis. Consult a local agricultural expert for confirmation."


# Soil Record Schemas
class SoilRecordBase(BaseModel):
    farm_id: int
    ph_level: Optional[Decimal] = Field(default=None, ge=0, le=14)
    nitrogen: Optional[Decimal] = Field(default=None, ge=0)
    phosphorus: Optional[Decimal] = Field(default=None, ge=0)
    potassium: Optional[Decimal] = Field(default=None, ge=0)
    organic_matter: Optional[Decimal] = Field(default=None, ge=0, le=100)
    moisture: Optional[Decimal] = Field(default=None, ge=0, le=100)
    source: str = "manual"


class SoilRecordCreate(SoilRecordBase):
    pass


class SoilRecordResponse(SoilRecordBase):
    id: int
    test_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SoilAnalysis(BaseModel):
    ph_status: str
    ph_explanation: str
    nitrogen_status: str
    nitrogen_explanation: str
    phosphorus_status: str
    phosphorus_explanation: str
    potassium_status: str
    potassium_explanation: str
    organic_matter_status: str = "unknown"
    organic_matter_explanation: str = "Organic matter status unavailable."
    moisture_status: str = "unknown"
    moisture_explanation: str = "Moisture status unavailable."


# Irrigation Schedule Schemas
class IrrigationScheduleBase(BaseModel):
    farm_id: int
    crop_id: Optional[int] = None
    area_hectares: Optional[Decimal] = Field(default=None, gt=0)
    soil_type: Optional[str] = Field(default=None, max_length=100)
    crop_stage: Optional[Literal["initial", "development", "mid", "late"]] = None
    soil_moisture_percent: Optional[Decimal] = Field(default=None, ge=0, le=100)
    rainfall_mm: Optional[Decimal] = Field(default=None, ge=0)
    temperature_c: Optional[Decimal] = Field(default=None, ge=-10, le=60)
    weather_source: Optional[str] = None
    scheduled_date: datetime
    duration_hours: Optional[Decimal] = None
    water_amount_liters: Optional[Decimal] = None
    status: str = "pending"
    notes: Optional[str] = None


class IrrigationScheduleCreate(IrrigationScheduleBase):
    pass


class IrrigationScheduleUpdate(BaseModel):
    crop_id: Optional[int] = None
    area_hectares: Optional[Decimal] = Field(default=None, gt=0)
    soil_type: Optional[str] = Field(default=None, max_length=100)
    crop_stage: Optional[Literal["initial", "development", "mid", "late"]] = None
    soil_moisture_percent: Optional[Decimal] = Field(default=None, ge=0, le=100)
    rainfall_mm: Optional[Decimal] = Field(default=None, ge=0)
    temperature_c: Optional[Decimal] = Field(default=None, ge=-10, le=60)
    scheduled_date: Optional[datetime] = None
    duration_hours: Optional[Decimal] = None
    water_amount_liters: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class IrrigationScheduleResponse(IrrigationScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Listing Schemas
class ListingBase(BaseModel):
    crop_name: str
    quantity_quintals: Decimal
    price_per_quintal: Decimal
    location: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    crop_name: Optional[str] = None
    quantity_quintals: Optional[Decimal] = None
    price_per_quintal: Optional[Decimal] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ListingResponse(ListingBase):
    id: int
    seller_id: int
    created_at: datetime
    updated_at: datetime
    seller_name: Optional[str] = None

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    listing_id: Optional[int] = None
    crop_name_snapshot: Optional[str] = None
    seller_name_snapshot: Optional[str] = None
    unit_price_snapshot: Optional[Decimal] = None
    buyer_id: Optional[int] = None
    seller_id: Optional[int] = None
    quantity_quintals: Decimal
    total_amount: Decimal
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    status: str = "initiated"


class TransactionCreate(BaseModel):
    listing_id: int
    quantity_quintals: Optional[Decimal] = Field(default=None, gt=0)
    delivery_method: Literal["delivery", "pickup"] = "pickup"
    delivery_address_id: Optional[int] = None
    delivery_instructions: Optional[str] = Field(default=None, max_length=2000)


class TransactionResponse(TransactionBase):
    razorpay_key_id: Optional[str] = None
    id: int
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime
    delivery_method: Optional[str] = None
    delivery_address_snapshot: Optional[dict] = None
    delivery_instructions: Optional[str] = None
    fulfillment_status: str = "awaiting_payment"
    cancellation_requested_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    alert_type: str
    title: str
    message: str


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Scheme Match Schemas
class SchemeMatchBase(BaseModel):
    scheme_name: str
    eligibility_score: Optional[Decimal] = None
    benefits: Optional[str] = None
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None
    status: str = "matched"


class SchemeMatchCreate(SchemeMatchBase):
    user_id: int


class SchemeMatchResponse(SchemeMatchBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Consent Record Schemas
class ConsentRecordBase(BaseModel):
    consent_type: str
    is_granted: bool = True


class ConsentRecordCreate(ConsentRecordBase):
    user_id: int


class ConsentRecordResponse(ConsentRecordBase):
    id: int
    user_id: int
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit Log Schemas
class AuditLogBase(BaseModel):
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Notification Log Schemas
class NotificationLogBase(BaseModel):
    channel: str
    subject: str
    content: str
    status: str = "sent"
    error_message: Optional[str] = None


class NotificationLogCreate(NotificationLogBase):
    user_id: int


class NotificationLogResponse(NotificationLogBase):
    id: int
    user_id: int
    sent_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Market Price Schemas
class MarketPriceBase(BaseModel):
    crop_id: Optional[int] = None
    crop_name: str
    market_region: str
    price_per_quintal: Decimal
    source: Optional[str] = None


class MarketPriceCreate(MarketPriceBase):
    pass


class MarketPriceResponse(MarketPriceBase):
    id: int
    date_recorded: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Treatment Schemas
class TreatmentBase(BaseModel):
    disease_class: str
    treatment_type: str
    treatment_name: str
    dosage: Optional[str] = None
    application_method: Optional[str] = None
    safety_warning: Optional[str] = None
    organic: bool = False


class TreatmentCreate(TreatmentBase):
    pass


class TreatmentResponse(TreatmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Prohibited Substance Schemas
class ProhibitedSubstanceBase(BaseModel):
    substance_name: str
    prohibited_reason: Optional[str] = None
    regulatory_body: Optional[str] = None


class ProhibitedSubstanceCreate(ProhibitedSubstanceBase):
    pass


class ProhibitedSubstanceResponse(ProhibitedSubstanceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Crop Nutrient Requirement Schemas
class CropNutrientRequirementBase(BaseModel):
    crop_name: str
    ph_min: Decimal
    ph_max: Decimal
    nitrogen_min: Decimal
    nitrogen_max: Decimal
    phosphorus_min: Decimal
    phosphorus_max: Decimal
    potassium_min: Decimal
    potassium_max: Decimal


class CropNutrientRequirementCreate(CropNutrientRequirementBase):
    pass


class CropNutrientRequirementResponse(CropNutrientRequirementBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Yield Prediction Schemas
class YieldPredictionBase(BaseModel):
    farm_id: int
    crop_id: int
    land_size_acres: Decimal = Field(gt=0, le=100000)
    planting_date: datetime
    ph_level: Optional[Decimal] = Field(default=None, ge=0, le=14)
    nitrogen: Optional[Decimal] = Field(default=None, ge=0)
    phosphorus: Optional[Decimal] = Field(default=None, ge=0)
    potassium: Optional[Decimal] = Field(default=None, ge=0)
    soil_moisture_percent: Optional[Decimal] = Field(default=None, ge=0, le=100)
    rainfall_mm: Optional[Decimal] = Field(default=None, ge=0)
    irrigation_mm: Optional[Decimal] = Field(default=None, ge=0)
    temperature_c: Optional[Decimal] = Field(default=None, ge=-10, le=60)


class YieldPredictionCreate(YieldPredictionBase):
    pass


class YieldPredictionResponse(YieldPredictionBase):
    id: int
    predicted_yield_low: Decimal
    predicted_yield_expected: Decimal
    predicted_yield_high: Decimal
    confidence_label: str
    harvest_window_start: Optional[datetime] = None
    harvest_window_end: Optional[datetime] = None
    version: int
    input_snapshot: Optional[dict] = None
    model_version: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Outbreak Alert Schemas
class OutbreakAlertBase(BaseModel):
    disease_name: str
    region_description: str
    center_latitude: Decimal
    center_longitude: Decimal
    radius_km: Decimal
    severity: str = "medium"
    preventive_measures: Optional[str] = None


class OutbreakAlertCreate(OutbreakAlertBase):
    pass


class OutbreakAlertResponse(OutbreakAlertBase):
    id: int
    case_count: int
    is_active: bool
    retracted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutbreakAlertListResponse(BaseModel):
    id: int
    disease_name: str
    region_description: str
    severity: str
    case_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Listing Schemas
class ListingBase(BaseModel):
    crop_name: str
    quantity_quintals: Decimal
    price_per_quintal: Decimal
    unit: str = "quintal"
    location: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    status: Optional[str] = None
    price_per_quintal: Optional[Decimal] = None
    quantity_quintals: Optional[Decimal] = None
    description: Optional[str] = None


class ListingResponse(ListingBase):
    id: int
    seller_id: int
    status: str
    photo_path: Optional[str] = None
    market_price_benchmark: Optional[Decimal] = None
    price_label: Optional[str] = None
    market_price_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    seller_name: Optional[str] = None

    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    content: str = Field(min_length=1, max_length=5000)
    recipient_buyer_id: Optional[int] = None


class MessageResponse(MessageBase):
    id: int
    listing_id: int
    sender_id: int
    buyer_id: Optional[int] = None
    sender_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionUpdate(BaseModel):
    status: str


class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# Scheme Schemas
class SchemeBase(BaseModel):
    name: str
    description: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    min_land_hectares: Optional[Decimal] = None
    max_land_hectares: Optional[Decimal] = None
    eligible_crops: Optional[str] = None
    eligible_states: Optional[str] = None
    benefits: Optional[str] = None
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None


class SchemeCreate(SchemeBase):
    pass


class SchemeResponse(SchemeBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchemeMatchRequest(BaseModel):
    farm_id: int
    crop_name: Optional[str] = None
    state: Optional[str] = None


class SchemeMatchResponse(BaseModel):
    scheme_id: int
    scheme_name: str
    eligibility_reason: str
    benefits: Optional[str] = None
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None


# Finance Entry Schemas
class FinanceEntryBase(BaseModel):
    farm_id: int
    entry_type: str
    category: str
    amount: Decimal
    date: datetime
    notes: Optional[str] = None


class FinanceEntryCreate(FinanceEntryBase):
    pass


class FinanceEntryResponse(FinanceEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinanceSummaryResponse(BaseModel):
    farm_id: int
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    category_breakdown: dict
    monthly_breakdown: dict


# System Config Schemas
class SystemConfigUpdate(BaseModel):
    config_value: str
    description: Optional[str] = None


class SystemConfigResponse(BaseModel):
    id: int
    config_key: str
    config_value: Optional[str] = None
    description: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# Admin Dashboard Schemas
class AdminDashboardResponse(BaseModel):
    total_users: int
    users_by_role: dict
    total_diagnoses: int
    low_confidence_diagnoses: int
    top_diseases: list
    active_alerts: int
    total_listings: int
    open_listings: int
    closed_listings: int
    total_transaction_volume: Decimal
    total_farms: int


# Audit Log Schema
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

