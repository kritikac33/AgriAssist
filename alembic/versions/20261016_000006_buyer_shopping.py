"""Add persistent buyer cart and saved listings.

Revision ID: 006
Revises: 005
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("crop_name_snapshot", sa.String(255), nullable=True))
    op.add_column("transactions", sa.Column("seller_name_snapshot", sa.String(255), nullable=True))
    op.add_column("transactions", sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=True))
    op.execute(sa.text("""
        UPDATE transactions AS t
        LEFT JOIN listings AS l ON l.id = t.listing_id
        LEFT JOIN users AS u ON u.id = t.seller_id
        SET t.crop_name_snapshot = COALESCE(t.crop_name_snapshot, l.crop_name),
            t.seller_name_snapshot = COALESCE(t.seller_name_snapshot, u.full_name),
            t.unit_price_snapshot = COALESCE(t.unit_price_snapshot, t.total_amount / NULLIF(t.quantity_quintals, 0))
    """))
    op.create_table(
        "saved_listings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("listing_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("buyer_id", "listing_id", name="uq_saved_listing_buyer_listing"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_saved_listings_buyer_id", "saved_listings", ["buyer_id"])
    op.create_index("ix_saved_listings_listing_id", "saved_listings", ["listing_id"])
    op.create_table(
        "buyer_cart_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("listing_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity_quintals", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("buyer_id", "listing_id", name="uq_buyer_cart_buyer_listing"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_buyer_cart_items_buyer_id", "buyer_cart_items", ["buyer_id"])
    op.create_index("ix_buyer_cart_items_listing_id", "buyer_cart_items", ["listing_id"])


def downgrade() -> None:
    op.drop_index("ix_buyer_cart_items_listing_id", table_name="buyer_cart_items")
    op.drop_index("ix_buyer_cart_items_buyer_id", table_name="buyer_cart_items")
    op.drop_table("buyer_cart_items")
    op.drop_index("ix_saved_listings_listing_id", table_name="saved_listings")
    op.drop_index("ix_saved_listings_buyer_id", table_name="saved_listings")
    op.drop_table("saved_listings")
    op.drop_column("transactions", "unit_price_snapshot")
    op.drop_column("transactions", "seller_name_snapshot")
    op.drop_column("transactions", "crop_name_snapshot")
