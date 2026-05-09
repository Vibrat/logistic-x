"""create orders table

Revision ID: 0001
Revises:
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("order_id",          sa.String(),  primary_key=True, nullable=False),
        sa.Column("client_id",         sa.String(),  nullable=False),
        sa.Column("order_date",        sa.Date(),    nullable=False),
        sa.Column("delivery_date",     sa.Date(),    nullable=True),
        sa.Column("carrier",           sa.String(),  nullable=False),
        sa.Column("origin_city",       sa.String(),  nullable=False),
        sa.Column("destination_city",  sa.String(),  nullable=False),
        sa.Column("status",            sa.String(),  nullable=False),
        sa.Column("sku",               sa.String(),  nullable=False),
        sa.Column("product_category",  sa.String(),  nullable=False),
        sa.Column("quantity",          sa.Integer(), nullable=False),
        sa.Column("unit_price_usd",    sa.Float(),   nullable=False),
        sa.Column("order_value_usd",   sa.Float(),   nullable=False),
        sa.Column("is_promo",          sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("promo_discount_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("region",            sa.String(),  nullable=False),
        sa.Column("warehouse",         sa.String(),  nullable=False),
    )

    # Indexes for common query patterns
    op.create_index("ix_orders_client_id",        "orders", ["client_id"])
    op.create_index("ix_orders_order_date",        "orders", ["order_date"])
    op.create_index("ix_orders_status",            "orders", ["status"])
    op.create_index("ix_orders_carrier",           "orders", ["carrier"])
    op.create_index("ix_orders_sku",               "orders", ["sku"])
    op.create_index("ix_orders_product_category",  "orders", ["product_category"])
    op.create_index("ix_orders_region",            "orders", ["region"])


def downgrade() -> None:
    op.drop_index("ix_orders_region",           table_name="orders")
    op.drop_index("ix_orders_product_category", table_name="orders")
    op.drop_index("ix_orders_sku",              table_name="orders")
    op.drop_index("ix_orders_carrier",          table_name="orders")
    op.drop_index("ix_orders_status",           table_name="orders")
    op.drop_index("ix_orders_order_date",       table_name="orders")
    op.drop_index("ix_orders_client_id",        table_name="orders")
    op.drop_table("orders")
