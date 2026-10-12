"""Add ML-related tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add consent_record_id to diagnoses table
    op.add_column('diagnoses', sa.Column('consent_record_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_diagnoses_consent_record', 'diagnoses', 'consent_records', ['consent_record_id'], ['id'], ondelete='SET NULL')
    
    # Add source column to soil_records table
    op.add_column('soil_records', sa.Column('source', sa.String(length=50), nullable=False, server_default='manual'))
    
    # Create treatments table
    op.create_table(
        'treatments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('disease_class', sa.String(length=255), nullable=False),
        sa.Column('treatment_type', sa.String(length=50), nullable=False),
        sa.Column('treatment_name', sa.String(length=255), nullable=False),
        sa.Column('dosage', sa.String(length=255), nullable=True),
        sa.Column('application_method', sa.Text(), nullable=True),
        sa.Column('safety_warning', sa.Text(), nullable=True),
        sa.Column('organic', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_treatments'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_treatments_disease_class'), 'treatments', ['disease_class'])
    
    # Create prohibited_substances table
    op.create_table(
        'prohibited_substances',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('substance_name', sa.String(length=255), nullable=False),
        sa.Column('prohibited_reason', sa.Text(), nullable=True),
        sa.Column('regulatory_body', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_prohibited_substances'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_prohibited_substances_substance_name'), 'prohibited_substances', ['substance_name'], unique=True)
    
    # Create crop_nutrient_requirements table
    op.create_table(
        'crop_nutrient_requirements',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('crop_name', sa.String(length=255), nullable=False),
        sa.Column('ph_min', sa.DECIMAL(precision=4, scale=2), nullable=False),
        sa.Column('ph_max', sa.DECIMAL(precision=4, scale=2), nullable=False),
        sa.Column('nitrogen_min', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('nitrogen_max', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('phosphorus_min', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('phosphorus_max', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('potassium_min', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('potassium_max', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_crop_nutrient_requirements'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_crop_nutrient_requirements_crop_name'), 'crop_nutrient_requirements', ['crop_name'], unique=True)
    
    # Create yield_predictions table
    op.create_table(
        'yield_predictions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.BigInteger(), nullable=False),
        sa.Column('crop_id', sa.BigInteger(), nullable=False),
        sa.Column('land_size_acres', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('planting_date', sa.DateTime(), nullable=False),
        sa.Column('predicted_yield_low', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('predicted_yield_expected', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('predicted_yield_high', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('confidence_label', sa.String(length=50), nullable=False),
        sa.Column('harvest_window_start', sa.DateTime(), nullable=True),
        sa.Column('harvest_window_end', sa.DateTime(), nullable=True),
        sa.Column('version', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_yield_predictions'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('yield_predictions')
    op.drop_index(op.f('ix_crop_nutrient_requirements_crop_name'), table_name='crop_nutrient_requirements')
    op.drop_table('crop_nutrient_requirements')
    op.drop_index(op.f('ix_prohibited_substances_substance_name'), table_name='prohibited_substances')
    op.drop_table('prohibited_substances')
    op.drop_index(op.f('ix_treatments_disease_class'), table_name='treatments')
    op.drop_table('treatments')
    op.drop_column('soil_records', 'source')
    op.drop_constraint('fk_diagnoses_consent_record', 'diagnoses', type_='foreignkey')
    op.drop_column('diagnoses', 'consent_record_id')
