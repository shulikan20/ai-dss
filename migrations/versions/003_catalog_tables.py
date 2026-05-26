"""
Revision ID: 003_catalog_tables
Revises: 002_auth_refresh_tokens
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_catalog_tables"
down_revision = "002_auth_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capabilities",
        sa.Column("capability_id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("use_case_category", sa.String(100), nullable=True),
        sa.Column("task_type_target", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bottleneck_keywords", postgresql.JSONB(), nullable=True),
        sa.Column("works_without_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("required_data_types", postgresql.JSONB(), nullable=True),
        sa.Column("min_history_months_gate", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("min_technical_capability", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("mapped_pain_points", postgresql.JSONB(), nullable=True),
        sa.Column("primary_outcome", sa.Text(), nullable=True),
        sa.Column("secondary_outcomes", postgresql.JSONB(), nullable=True),
        sa.Column("time_to_value_weeks_min", sa.Integer(), nullable=True),
        sa.Column("time_to_value_weeks_max", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_capabilities_domain", "capabilities", ["domain"])

    op.create_table(
        "products",
        sa.Column("product_id", sa.String(100), primary_key=True),
        sa.Column(
            "capability_id",
            sa.String(100),
            sa.ForeignKey("capabilities.capability_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("vendor", sa.String(255), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("integrations", postgresql.JSONB(), nullable=True),
        sa.Column("gdpr_compliant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deployment_model", sa.String(50), nullable=True),
        sa.Column("pricing_model", sa.String(50), nullable=True),
        sa.Column("has_free_tier", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cost_tier", sa.String(50), nullable=True),
        sa.Column("cost_notes", sa.Text(), nullable=True),
        sa.Column("implementation_effort", sa.String(50), nullable=True),
        sa.Column("min_technical_capability", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("setup_notes", sa.Text(), nullable=True),
        sa.Column("min_history_months", sa.Integer(), nullable=True),
        sa.Column("min_record_count", sa.Integer(), nullable=True),
        sa.Column("works_with_limited_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_requirement_notes", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_products_capability_id", "products", ["capability_id"])


def downgrade() -> None:
    op.drop_table("products")
    op.drop_table("capabilities")
