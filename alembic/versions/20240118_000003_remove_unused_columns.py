"""Remove unused columns from database

Revision ID: 004
Revises: 003
Create Date: 2024-01-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import exc

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove unused payment_id column from transactions (replaced by razorpay_payment_id)
    try:
        op.drop_column('transactions', 'payment_id')
    except exc.OperationalError:
        pass  # Column may not exist

    # Remove unused moisture column from soil_records
    try:
        op.drop_column('soil_records', 'moisture')
    except exc.OperationalError:
        pass  # Column may not exist

    # Remove unused crop_id column from irrigation_schedules
    try:
        op.drop_constraint('fk_irrigation_schedules_crop_id', 'irrigation_schedules', type_='foreignkey')
    except exc.OperationalError:
        pass  # Constraint may not exist

    try:
        op.drop_column('irrigation_schedules', 'crop_id')
    except exc.OperationalError:
        pass  # Column may not exist


def downgrade() -> None:
    # Re-add crop_id to irrigation_schedules
    try:
        op.add_column('irrigation_schedules', sa.Column('crop_id', sa.BigInteger(), nullable=True))
    except exc.OperationalError:
        pass

    try:
        op.create_foreign_key('fk_irrigation_schedules_crop_id', 'irrigation_schedules', 'crops', ['crop_id'], ['id'], ondelete='CASCADE')
    except exc.OperationalError:
        pass

    # Re-add moisture to soil_records
    try:
        op.add_column('soil_records', sa.Column('moisture', sa.DECIMAL(precision=5, scale=2), nullable=True))
    except exc.OperationalError:
        pass

    # Re-add payment_id to transactions
    try:
        op.add_column('transactions', sa.Column('payment_id', sa.String(length=255), nullable=True))
    except exc.OperationalError:
        pass
