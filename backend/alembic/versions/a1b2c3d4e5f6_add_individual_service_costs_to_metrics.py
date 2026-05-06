"""add_individual_service_costs_to_metrics

Revision ID: a1b2c3d4e5f6
Revises: e8cb09eb222c
Create Date: 2026-05-06 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e8cb09eb222c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add openai_cost column
    op.add_column('metrics', sa.Column(
        'openai_cost',
        sa.Float(),
        nullable=False,
        server_default='0.0',
        comment='Actual OpenAI API cost in USD'
    ))

    # Add elevenlabs_cost column
    op.add_column('metrics', sa.Column(
        'elevenlabs_cost',
        sa.Float(),
        nullable=False,
        server_default='0.0',
        comment='Actual ElevenLabs API cost in USD'
    ))

    # Add check constraints for non-negative values
    op.create_check_constraint(
        'check_openai_cost_non_negative',
        'metrics',
        'openai_cost >= 0'
    )
    op.create_check_constraint(
        'check_elevenlabs_cost_non_negative',
        'metrics',
        'elevenlabs_cost >= 0'
    )


def downgrade() -> None:
    # Drop check constraints first
    op.drop_constraint('check_elevenlabs_cost_non_negative', 'metrics', type_='check')
    op.drop_constraint('check_openai_cost_non_negative', 'metrics', type_='check')

    # Drop columns
    op.drop_column('metrics', 'elevenlabs_cost')
    op.drop_column('metrics', 'openai_cost')
