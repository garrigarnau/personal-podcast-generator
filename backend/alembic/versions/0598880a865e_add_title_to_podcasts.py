"""add_title_to_podcasts

Revision ID: 0598880a865e
Revises: a1b2c3d4e5f6
Create Date: 2026-05-06 20:18:23.295204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0598880a865e'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add title column to podcasts table
    op.add_column('podcasts', sa.Column('title', sa.String(length=500), nullable=True, comment='AI-generated title for the podcast'))


def downgrade() -> None:
    # Remove title column from podcasts table
    op.drop_column('podcasts', 'title')
