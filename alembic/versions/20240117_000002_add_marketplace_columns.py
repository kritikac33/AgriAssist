"""Add marketplace columns

Revision ID: 003
Revises: 002
Create Date: 2024-01-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import exc

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to listings table
    try:
        op.add_column('listings', sa.Column('unit', sa.String(length=50), nullable=False, server_default='quintal'))
    except exc.OperationalError:
        pass  # Column may already exist
    
    try:
        op.add_column('listings', sa.Column('latitude', sa.DECIMAL(precision=9, scale=6), nullable=True))
    except exc.OperationalError:
        pass
    
    try:
        op.add_column('listings', sa.Column('longitude', sa.DECIMAL(precision=9, scale=6), nullable=True))
    except exc.OperationalError:
        pass
    
    try:
        op.add_column('listings', sa.Column('photo_path', sa.String(length=500), nullable=True))
    except exc.OperationalError:
        pass
    
    # Update status default from 'active' to 'open'
    op.execute("UPDATE listings SET status = 'open' WHERE status = 'active'")
    
    # Add missing columns to transactions table
    try:
        op.add_column('transactions', sa.Column('razorpay_order_id', sa.String(length=255), nullable=True))
    except exc.OperationalError:
        pass
    
    try:
        op.add_column('transactions', sa.Column('razorpay_payment_id', sa.String(length=255), nullable=True))
    except exc.OperationalError:
        pass
    
    # Update status default from 'pending' to 'initiated'
    op.execute("UPDATE transactions SET status = 'initiated' WHERE status = 'pending'")
    
    # Add moisture column to soil_records table
    try:
        op.add_column('soil_records', sa.Column('moisture', sa.DECIMAL(precision=5, scale=2), nullable=True))
    except exc.OperationalError:
        pass
    
    # Add foreign key constraint for consent_record_id in diagnoses
    try:
        op.create_foreign_key('fk_diagnoses_consent_record_id', 'diagnoses', 'consent_records', ['consent_record_id'], ['id'], ondelete='SET NULL')
    except exc.OperationalError:
        pass
    
    # Add crop_id to irrigation_schedules
    try:
        op.add_column('irrigation_schedules', sa.Column('crop_id', sa.BigInteger(), nullable=True))
    except exc.OperationalError:
        pass
    
    try:
        op.create_foreign_key('fk_irrigation_schedules_crop_id', 'irrigation_schedules', 'crops', ['crop_id'], ['id'], ondelete='CASCADE')
    except exc.OperationalError:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint('fk_irrigation_schedules_crop_id', 'irrigation_schedules', type_='foreignkey')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('irrigation_schedules', 'crop_id')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_constraint('fk_diagnoses_consent_record_id', 'diagnoses', type_='foreignkey')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('soil_records', 'moisture')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('transactions', 'razorpay_payment_id')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('transactions', 'razorpay_order_id')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('listings', 'photo_path')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('listings', 'longitude')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('listings', 'latitude')
    except exc.OperationalError:
        pass
    
    try:
        op.drop_column('listings', 'unit')
    except exc.OperationalError:
        pass
