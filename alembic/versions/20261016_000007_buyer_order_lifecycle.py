"""Add buyer delivery details, order timeline, notifications and support."""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("delivery_method", sa.String(20), nullable=True))
    op.add_column("transactions", sa.Column("delivery_address_snapshot", sa.JSON(), nullable=True))
    op.add_column("transactions", sa.Column("delivery_instructions", sa.Text(), nullable=True))
    op.add_column("transactions", sa.Column("fulfillment_status", sa.String(40), server_default="awaiting_payment", nullable=False))
    op.add_column("transactions", sa.Column("inventory_reserved", sa.BigInteger(), server_default="0", nullable=False))
    op.add_column("transactions", sa.Column("cancellation_reason", sa.Text(), nullable=True))
    op.add_column("transactions", sa.Column("cancellation_requested_at", sa.DateTime(), nullable=True))
    op.execute(sa.text("UPDATE transactions SET fulfillment_status = CASE WHEN status IN ('confirmed','completed') THEN 'confirmed' ELSE 'awaiting_payment' END"))
    op.add_column("messages", sa.Column("read_at", sa.DateTime(), nullable=True))
    op.add_column("notification_logs", sa.Column("related_type", sa.String(40), nullable=True))
    op.add_column("notification_logs", sa.Column("related_id", sa.BigInteger(), nullable=True))
    op.add_column("notification_logs", sa.Column("is_read", sa.BigInteger(), server_default="0", nullable=False))

    op.create_table(
        "buyer_addresses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.String(80), nullable=False, server_default="Home"),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("delivery_instructions", sa.Text(), nullable=True),
        sa.Column("is_default", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_buyer_addresses_buyer_id", "buyer_addresses", ["buyer_id"])

    op.create_table(
        "transaction_status_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_transaction_status_history_transaction_id", "transaction_status_history", ["transaction_id"])
    op.execute(sa.text("""
        INSERT INTO transaction_status_history (transaction_id, actor_id, event_type, note)
        SELECT id, buyer_id, status, 'Status before buyer lifecycle tracking was enabled'
        FROM transactions
    """))

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_support_tickets_buyer_id", "support_tickets", ["buyer_id"])
    op.create_index("ix_support_tickets_transaction_id", "support_tickets", ["transaction_id"])


def downgrade() -> None:
    op.drop_index("ix_support_tickets_transaction_id", table_name="support_tickets")
    op.drop_index("ix_support_tickets_buyer_id", table_name="support_tickets")
    op.drop_table("support_tickets")
    op.drop_index("ix_transaction_status_history_transaction_id", table_name="transaction_status_history")
    op.drop_table("transaction_status_history")
    op.drop_index("ix_buyer_addresses_buyer_id", table_name="buyer_addresses")
    op.drop_table("buyer_addresses")
    op.drop_column("notification_logs", "is_read")
    op.drop_column("notification_logs", "related_id")
    op.drop_column("notification_logs", "related_type")
    op.drop_column("messages", "read_at")
    op.drop_column("transactions", "cancellation_requested_at")
    op.drop_column("transactions", "cancellation_reason")
    op.drop_column("transactions", "inventory_reserved")
    op.drop_column("transactions", "fulfillment_status")
    op.drop_column("transactions", "delivery_instructions")
    op.drop_column("transactions", "delivery_address_snapshot")
    op.drop_column("transactions", "delivery_method")
