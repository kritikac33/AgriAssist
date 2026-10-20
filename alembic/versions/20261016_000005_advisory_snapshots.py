"""Persist advisory inputs and immutable yield inputs.

Revision ID: 005
Revises: 004
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_context().as_sql:
        # Offline SQL generation cannot inspect the target database. Emit the
        # complete fresh-install DDL in that mode; online upgrades below remain
        # resumable after MySQL's non-transactional partial DDL behavior.
        op.add_column("soil_records", sa.Column("moisture", sa.Numeric(5, 2), nullable=True))
        for column in (
            sa.Column("crop_id", sa.BigInteger(), nullable=True),
            sa.Column("area_hectares", sa.Numeric(10, 2), nullable=True),
            sa.Column("soil_type", sa.String(100), nullable=True),
            sa.Column("crop_stage", sa.String(50), nullable=True),
            sa.Column("soil_moisture_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("rainfall_mm", sa.Numeric(7, 2), nullable=True),
            sa.Column("temperature_c", sa.Numeric(5, 2), nullable=True),
            sa.Column("weather_source", sa.String(50), nullable=True),
        ):
            op.add_column("irrigation_schedules", column)
        op.create_foreign_key("fk_irrigation_schedules_crop_id", "irrigation_schedules", "crops", ["crop_id"], ["id"], ondelete="SET NULL")
        op.add_column("yield_predictions", sa.Column("input_snapshot", sa.JSON(), nullable=True))
        op.add_column("yield_predictions", sa.Column("model_version", sa.String(100), nullable=True))
        op.execute(sa.text("""
            UPDATE yield_predictions AS yp
            JOIN (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY crop_id ORDER BY created_at, id) AS new_version
                FROM yield_predictions
            ) AS ranked ON ranked.id = yp.id
            SET yp.version = ranked.new_version
        """))
        op.create_unique_constraint("uq_yield_predictions_crop_version", "yield_predictions", ["crop_id", "version"])
        op.add_column("messages", sa.Column("buyer_id", sa.BigInteger(), nullable=True))
        op.create_foreign_key("fk_messages_buyer_id", "messages", "users", ["buyer_id"], ["id"], ondelete="CASCADE")
        op.create_index("ix_messages_buyer_id", "messages", ["buyer_id"])
        op.execute("""UPDATE messages AS m JOIN users AS u ON u.id = m.sender_id SET m.buyer_id = m.sender_id WHERE m.buyer_id IS NULL AND u.role = 'BUYER'""")
        return

    # MySQL DDL is not transactional. These checks also let the revision resume
    # after a previous attempt applied some columns before failing.
    inspector = sa.inspect(op.get_bind())

    def add_column_if_missing(table: str, column: sa.Column) -> None:
        if column.name not in {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}:
            op.add_column(table, column)

    add_column_if_missing("soil_records", sa.Column("moisture", sa.Numeric(5, 2), nullable=True))
    for column in (
        sa.Column("crop_id", sa.BigInteger(), nullable=True),
        sa.Column("area_hectares", sa.Numeric(10, 2), nullable=True),
        sa.Column("soil_type", sa.String(100), nullable=True),
        sa.Column("crop_stage", sa.String(50), nullable=True),
        sa.Column("soil_moisture_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rainfall_mm", sa.Numeric(7, 2), nullable=True),
        sa.Column("temperature_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("weather_source", sa.String(50), nullable=True),
    ):
        add_column_if_missing("irrigation_schedules", column)
    inspector = sa.inspect(op.get_bind())
    irrigation_fks = {fk["name"] for fk in inspector.get_foreign_keys("irrigation_schedules")}
    if "fk_irrigation_schedules_crop_id" not in irrigation_fks:
        op.create_foreign_key("fk_irrigation_schedules_crop_id", "irrigation_schedules", "crops", ["crop_id"], ["id"], ondelete="SET NULL")
    add_column_if_missing("yield_predictions", sa.Column("input_snapshot", sa.JSON(), nullable=True))
    add_column_if_missing("yield_predictions", sa.Column("model_version", sa.String(100), nullable=True))

    # Existing projects can have several predictions for the same crop/version.
    # Keep every prediction and give them stable sequential version numbers.
    unique_constraints = {item["name"] for item in sa.inspect(op.get_bind()).get_unique_constraints("yield_predictions")}
    if "uq_yield_predictions_crop_version" not in unique_constraints:
        op.execute(sa.text("""
            UPDATE yield_predictions AS yp
            JOIN (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY crop_id ORDER BY created_at, id) AS new_version
                FROM yield_predictions
            ) AS ranked ON ranked.id = yp.id
            SET yp.version = ranked.new_version
        """))
        op.create_unique_constraint("uq_yield_predictions_crop_version", "yield_predictions", ["crop_id", "version"])

    add_column_if_missing("messages", sa.Column("buyer_id", sa.BigInteger(), nullable=True))
    inspector = sa.inspect(op.get_bind())
    message_fks = {fk["name"] for fk in inspector.get_foreign_keys("messages")}
    if "fk_messages_buyer_id" not in message_fks:
        op.create_foreign_key("fk_messages_buyer_id", "messages", "users", ["buyer_id"], ["id"], ondelete="CASCADE")
    if "ix_messages_buyer_id" not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("messages")}:
        op.create_index("ix_messages_buyer_id", "messages", ["buyer_id"])
    op.execute("""UPDATE messages AS m
        JOIN users AS u ON u.id = m.sender_id
        SET m.buyer_id = m.sender_id
        WHERE m.buyer_id IS NULL AND u.role = 'BUYER'""")



def downgrade() -> None:
    op.drop_index("ix_messages_buyer_id", table_name="messages")
    op.drop_constraint("fk_messages_buyer_id", "messages", type_="foreignkey")
    op.drop_column("messages", "buyer_id")
    op.drop_constraint("uq_yield_predictions_crop_version", "yield_predictions", type_="unique")
    op.drop_column("yield_predictions", "model_version")
    op.drop_column("yield_predictions", "input_snapshot")
    op.drop_constraint("fk_irrigation_schedules_crop_id", "irrigation_schedules", type_="foreignkey")
    for column in ("weather_source", "temperature_c", "rainfall_mm", "soil_moisture_percent", "crop_stage", "soil_type", "area_hectares", "crop_id"):
        op.drop_column("irrigation_schedules", column)
    op.drop_column("soil_records", "moisture")
