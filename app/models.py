from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Numeric as Decimal
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    FARMER = "farmer"
    BUYER = "buyer"
    OFFICER = "officer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.FARMER)
    is_active = Column(BigInteger, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    farms = relationship("Farm", back_populates="owner")
    listings = relationship("Listing", back_populates="seller")
    transactions_as_buyer = relationship("Transaction", foreign_keys="Transaction.buyer_id", back_populates="buyer")
    transactions_as_seller = relationship("Transaction", foreign_keys="Transaction.seller_id", back_populates="seller")
    alerts = relationship("Alert", back_populates="user")
    consent_records = relationship("ConsentRecord", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    notification_logs = relationship("NotificationLog", back_populates="user")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id")


class Farm(Base):
    __tablename__ = "farms"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    latitude = Column(Decimal(9, 6), nullable=True)
    longitude = Column(Decimal(9, 6), nullable=True)
    area_hectares = Column(Decimal(10, 2), nullable=True)
    soil_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    owner = relationship("User", back_populates="farms")
    crops = relationship("Crop", back_populates="farm")
    soil_records = relationship("SoilRecord", back_populates="farm")
    irrigation_schedules = relationship("IrrigationSchedule", back_populates="farm")
    yield_predictions = relationship("YieldPrediction", back_populates="farm")


class Crop(Base):
    __tablename__ = "crops"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)
    planting_date = Column(DateTime, nullable=True)
    expected_harvest_date = Column(DateTime, nullable=True)
    area_hectares = Column(Decimal(10, 2), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    farm = relationship("Farm", back_populates="crops")
    diagnoses = relationship("Diagnosis", back_populates="crop")
    yield_predictions = relationship("YieldPrediction", back_populates="crop")


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    crop_id = Column(BigInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    disease_name = Column(String(255), nullable=True)
    confidence_score = Column(Decimal(5, 2), nullable=True)
    symptoms = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    consent_record_id = Column(BigInteger, ForeignKey("consent_records.id", ondelete="SET NULL"), nullable=True)
    diagnosed_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    crop = relationship("Crop", back_populates="diagnoses")
    consent_record = relationship("ConsentRecord", back_populates="diagnoses")


class SoilRecord(Base):
    __tablename__ = "soil_records"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    ph_level = Column(Decimal(4, 2), nullable=True)
    nitrogen = Column(Decimal(10, 2), nullable=True)
    phosphorus = Column(Decimal(10, 2), nullable=True)
    potassium = Column(Decimal(10, 2), nullable=True)
    organic_matter = Column(Decimal(5, 2), nullable=True)
    source = Column(String(50), default="manual", nullable=False)
    test_date = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    farm = relationship("Farm", back_populates="soil_records")


class IrrigationSchedule(Base):
    __tablename__ = "irrigation_schedules"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    duration_hours = Column(Decimal(5, 2), nullable=True)
    water_amount_liters = Column(Decimal(10, 2), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    farm = relationship("Farm", back_populates="irrigation_schedules")


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    seller_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(255), nullable=False)
    quantity_quintals = Column(Decimal(10, 2), nullable=False)
    price_per_quintal = Column(Decimal(10, 2), nullable=False)
    unit = Column(String(50), default="quintal", nullable=False)
    location = Column(String(255), nullable=True)
    latitude = Column(Decimal(9, 6), nullable=True)
    longitude = Column(Decimal(9, 6), nullable=True)
    photo_path = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open", nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    seller = relationship("User", back_populates="listings")
    transactions = relationship("Transaction", back_populates="listing")
    messages = relationship("Message", back_populates="listing")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    listing_id = Column(BigInteger, ForeignKey("listings.id", ondelete="SET NULL"), nullable=True)
    buyer_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    seller_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    razorpay_order_id = Column(String(255), nullable=True)
    razorpay_payment_id = Column(String(255), nullable=True)
    quantity_quintals = Column(Decimal(10, 2), nullable=False)
    total_amount = Column(Decimal(15, 2), nullable=False)
    status = Column(String(50), default="initiated", nullable=False)
    transaction_date = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    listing = relationship("Listing", back_populates="transactions")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="transactions_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="transactions_as_seller")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    user = relationship("User", back_populates="alerts")


class OutbreakAlert(Base):
    __tablename__ = "outbreak_alerts"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    disease_name = Column(String(255), nullable=False, index=True)
    region_description = Column(String(255), nullable=False)
    center_latitude = Column(Decimal(9, 6), nullable=False)
    center_longitude = Column(Decimal(9, 6), nullable=False)
    radius_km = Column(Decimal(10, 2), nullable=False)
    severity = Column(String(50), default="medium", nullable=False)
    case_count = Column(BigInteger, default=0, nullable=False)
    preventive_measures = Column(Text, nullable=True)
    is_active = Column(BigInteger, default=1, nullable=False)
    retracted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class SchemeMatch(Base):
    __tablename__ = "scheme_matches"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_name = Column(String(255), nullable=False)
    eligibility_score = Column(Decimal(5, 2), nullable=True)
    benefits = Column(Text, nullable=True)
    application_link = Column(String(500), nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(String(50), default="matched", nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_type = Column(String(100), nullable=False)
    is_granted = Column(BigInteger, default=1, nullable=False)
    granted_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    user = relationship("User", back_populates="consent_records")
    diagnoses = relationship("Diagnosis", back_populates="consent_record")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(BigInteger, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    user = relationship("User", back_populates="audit_logs")


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="sent", nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    user = relationship("User", back_populates="notification_logs")


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    crop_id = Column(BigInteger, nullable=True)
    crop_name = Column(String(255), nullable=False)
    market_region = Column(String(255), nullable=False)
    price_per_quintal = Column(Decimal(10, 2), nullable=False)
    date_recorded = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class Treatment(Base):
    __tablename__ = "treatments"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    disease_class = Column(String(255), nullable=False, index=True)
    treatment_type = Column(String(50), nullable=False)
    treatment_name = Column(String(255), nullable=False)
    dosage = Column(String(255), nullable=True)
    application_method = Column(Text, nullable=True)
    safety_warning = Column(Text, nullable=True)
    organic = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class ProhibitedSubstance(Base):
    __tablename__ = "prohibited_substances"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    substance_name = Column(String(255), nullable=False, unique=True)
    prohibited_reason = Column(Text, nullable=True)
    regulatory_body = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)


class CropNutrientRequirement(Base):
    __tablename__ = "crop_nutrient_requirements"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    crop_name = Column(String(255), nullable=False, unique=True, index=True)
    ph_min = Column(Decimal(4, 2), nullable=False)
    ph_max = Column(Decimal(4, 2), nullable=False)
    nitrogen_min = Column(Decimal(10, 2), nullable=False)
    nitrogen_max = Column(Decimal(10, 2), nullable=False)
    phosphorus_min = Column(Decimal(10, 2), nullable=False)
    phosphorus_max = Column(Decimal(10, 2), nullable=False)
    potassium_min = Column(Decimal(10, 2), nullable=False)
    potassium_max = Column(Decimal(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class YieldPrediction(Base):
    __tablename__ = "yield_predictions"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(BigInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    land_size_acres = Column(Decimal(10, 2), nullable=False)
    planting_date = Column(DateTime, nullable=False)
    predicted_yield_low = Column(Decimal(10, 2), nullable=False)
    predicted_yield_expected = Column(Decimal(10, 2), nullable=False)
    predicted_yield_high = Column(Decimal(10, 2), nullable=False)
    confidence_label = Column(String(50), nullable=False)
    harvest_window_start = Column(DateTime, nullable=True)
    harvest_window_end = Column(DateTime, nullable=True)
    version = Column(BigInteger, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    farm = relationship("Farm", back_populates="yield_predictions")
    crop = relationship("Crop", back_populates="yield_predictions")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    listing_id = Column(BigInteger, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    listing = relationship("Listing", back_populates="messages")


class Scheme(Base):
    __tablename__ = "schemes"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    min_land_hectares = Column(Decimal(10, 2), nullable=True)
    max_land_hectares = Column(Decimal(10, 2), nullable=True)
    eligible_crops = Column(Text, nullable=True)
    eligible_states = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    application_link = Column(String(500), nullable=True)
    deadline = Column(DateTime, nullable=True)
    is_active = Column(BigInteger, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class FinanceEntry(Base):
    __tablename__ = "finance_entries"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    entry_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Decimal(15, 2), nullable=False)
    date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class SystemConfig(Base):
    __tablename__ = "system_config"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True, index=True)
    config_value = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
