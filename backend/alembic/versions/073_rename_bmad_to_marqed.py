"""Rename BMAD tables to MarQed

Revision ID: 073
Revises: 072
Create Date: 2026-01-20

Week 158: Rename BMAD to MarQed branding
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '073'
down_revision = '072'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop all foreign key constraints FIRST
    op.drop_constraint('bmad_answers_session_id_fkey', 'bmad_answers', type_='foreignkey')
    op.drop_constraint('bmad_session_events_session_id_fkey', 'bmad_session_events', type_='foreignkey')

    # Try to drop intake constraint if it exists
    try:
        op.drop_constraint('intake_legacy_systems_brown_paper_session_id_fkey', 'intake_legacy_systems', type_='foreignkey')
    except Exception:
        pass  # Table or constraint may not exist

    # Step 2: Rename tables
    op.rename_table('bmad_sessions', 'marqed_sessions')
    op.rename_table('bmad_answers', 'marqed_answers')
    op.rename_table('bmad_session_events', 'marqed_session_events')

    # Step 3: Recreate foreign key constraints with new names
    op.create_foreign_key(
        'marqed_answers_session_id_fkey',
        'marqed_answers',
        'marqed_sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'marqed_session_events_session_id_fkey',
        'marqed_session_events',
        'marqed_sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Recreate intake constraint if table exists
    try:
        op.create_foreign_key(
            'intake_legacy_systems_brown_paper_session_id_fkey',
            'intake_legacy_systems',
            'marqed_sessions',
            ['brown_paper_session_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass


def downgrade() -> None:
    # Step 1: Drop new foreign key constraints
    op.drop_constraint('marqed_answers_session_id_fkey', 'marqed_answers', type_='foreignkey')
    op.drop_constraint('marqed_session_events_session_id_fkey', 'marqed_session_events', type_='foreignkey')

    # Step 2: Rename tables back
    op.rename_table('marqed_session_events', 'bmad_session_events')
    op.rename_table('marqed_answers', 'bmad_answers')
    op.rename_table('marqed_sessions', 'bmad_sessions')

    # Step 3: Recreate original foreign key constraints
    op.create_foreign_key(
        'bmad_answers_session_id_fkey',
        'bmad_answers',
        'bmad_sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'bmad_session_events_session_id_fkey',
        'bmad_session_events',
        'bmad_sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )
