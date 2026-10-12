"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('FARMER', 'BUYER', 'OFFICER', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create farms table
    op.create_table(
        'farms',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.DECIMAL(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.DECIMAL(precision=9, scale=6), nullable=True),
        sa.Column('area_hectares', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_farms'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create crops table
    op.create_table(
        'crops',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('variety', sa.String(length=255), nullable=True),
        sa.Column('planting_date', sa.DateTime(), nullable=True),
        sa.Column('expected_harvest_date', sa.DateTime(), nullable=True),
        sa.Column('area_hectares', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_crops'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create diagnoses table
    op.create_table(
        'diagnoses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('crop_id', sa.BigInteger(), nullable=False),
        sa.Column('disease_name', sa.String(length=255), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('symptoms', sa.Text(), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('image_path', sa.String(length=500), nullable=True),
        sa.Column('diagnosed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_diagnoses'),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create soil_records table
    op.create_table(
        'soil_records',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.BigInteger(), nullable=False),
        sa.Column('ph_level', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('nitrogen', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('phosphorus', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('potassium', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('organic_matter', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('test_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_soil_records'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create irrigation_schedules table
    op.create_table(
        'irrigation_schedules',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.BigInteger(), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('duration_hours', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('water_amount_liters', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_irrigation_schedules'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create listings table
    op.create_table(
        'listings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('seller_id', sa.BigInteger(), nullable=False),
        sa.Column('crop_name', sa.String(length=255), nullable=False),
        sa.Column('quantity_quintals', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('price_per_quintal', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_listings'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('listing_id', sa.BigInteger(), nullable=True),
        sa.Column('buyer_id', sa.BigInteger(), nullable=True),
        sa.Column('seller_id', sa.BigInteger(), nullable=True),
        sa.Column('quantity_quintals', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('transaction_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_transactions'),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='SET NULL'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_alerts'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create scheme_matches table
    op.create_table(
        'scheme_matches',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('scheme_name', sa.String(length=255), nullable=False),
        sa.Column('eligibility_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('benefits', sa.Text(), nullable=True),
        sa.Column('application_link', sa.String(length=500), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='matched'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_scheme_matches'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create consent_records table
    op.create_table(
        'consent_records',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('consent_type', sa.String(length=100), nullable=False),
        sa.Column('is_granted', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_consent_records'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.BigInteger(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_audit_logs'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='sent'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_notification_logs'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create market_prices table
    op.create_table(
        'market_prices',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('crop_id', sa.BigInteger(), nullable=True),
        sa.Column('crop_name', sa.String(length=255), nullable=False),
        sa.Column('market_region', sa.String(length=255), nullable=False),
        sa.Column('price_per_quintal', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('date_recorded', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_market_prices'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('market_prices')
    op.drop_table('notification_logs')
    op.drop_table('audit_logs')
    op.drop_table('consent_records')
    op.drop_table('scheme_matches')
    op.drop_table('alerts')
    op.drop_table('transactions')
    op.drop_table('listings')
    op.drop_table('irrigation_schedules')
    op.drop_table('soil_records')
    op.drop_table('diagnoses')
    op.drop_table('crops')
    op.drop_table('farms')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
