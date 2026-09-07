"""add condition_category to samples

Revision ID: dac8c2535b09
Revises: 57cab40aacf9
Create Date: 2026-09-06 13:47:01.006012

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dac8c2535b09"
down_revision: str | Sequence[str] | None = "57cab40aacf9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "samples",
        sa.Column(
            "condition_category",
            sa.Enum(
                "CONTROL", "CASE", "EXCLUDED", "BASELINE",
                name="conditioncategory", native_enum=False,
            ),
            nullable=True,
        ),
    )
    # Every existing Sample row is GTEx data (no GEO ingestion has run yet), and GTEx's role is
    # always the non-contrastive population baseline -- this backfill is correct by construction,
    # not a guess.
    op.execute("UPDATE samples SET condition_category = 'BASELINE'")
    op.alter_column("samples", "condition_category", nullable=False)
    op.create_index(op.f("ix_samples_condition_category"), "samples", ["condition_category"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_samples_condition_category"), table_name="samples")
    op.drop_column("samples", "condition_category")
