"""initial_schema

Revision ID: initial_schema
Revises: 
Create Date: 2026-04-07 17:26:16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём ENUM-типы
    op.execute("CREATE TYPE runmode AS ENUM ('by_selectors', 'by_description', 'by_parent')")
    op.execute("CREATE TYPE locatorstage AS ENUM ('generated', 'fixed')")
    op.execute("CREATE TYPE changereason AS ENUM ('page_update', 'manual', 'auto_fix', 're_generation')")

    # Таблица projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_projects_name', 'projects', ['name'], unique=True)

    # Таблица pages
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('elements_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_pages_project_id', 'pages', ['project_id'])
    op.create_index('ix_pages_url', 'pages', ['url'])

    # Таблица locator_runs
    op.create_table(
        'locator_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page_id', sa.Integer(), sa.ForeignKey('pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_mode', postgresql.ENUM('by_selectors', 'by_description', 'by_parent', name='runmode', create_type=False), nullable=False),
        sa.Column('llm_config', postgresql.JSONB(), nullable=True),
        sa.Column('auth_config', postgresql.JSONB(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('timings', postgresql.JSONB(), nullable=True),
        sa.Column('total_elements', sa.Integer(), server_default='0', nullable=False),
        sa.Column('valid_locators', sa.Integer(), server_default='0', nullable=False),
        sa.Column('invalid_locators', sa.Integer(), server_default='0', nullable=False),
        sa.Column('fixed_locators', sa.Integer(), server_default='0', nullable=False),
        sa.Column('artifacts_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_locator_runs_page_id', 'locator_runs', ['page_id'])

    # Таблица locators
    op.create_table(
        'locators',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('locator_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('element_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('xpath', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stage', postgresql.ENUM('generated', 'fixed', name='locatorstage', create_type=False), nullable=False),
        sa.Column('validation', postgresql.JSONB(), nullable=True),
        sa.Column('selenide_element', sa.Text(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_locators_run_id', 'locators', ['run_id'])

    # Таблица elements
    op.create_table(
        'elements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('locator_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag', sa.String(50), nullable=False),
        sa.Column('attributes', postgresql.JSONB(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('own_text', sa.Text(), nullable=True),
        sa.Column('parent_info', postgresql.JSONB(), nullable=True),
        sa.Column('siblings', postgresql.JSONB(), nullable=True),
        sa.Column('bbox', postgresql.JSONB(), nullable=True),
        sa.Column('css_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_elements_run_id', 'elements', ['run_id'])
    op.create_index('ix_elements_tag', 'elements', ['tag'])

    # Таблица locator_history
    op.create_table(
        'locator_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('locator_id', sa.Integer(), sa.ForeignKey('locators.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_xpath', sa.Text(), nullable=True),
        sa.Column('new_xpath', sa.Text(), nullable=False),
        sa.Column('change_reason', postgresql.ENUM('page_update', 'manual', 'auto_fix', 're_generation', name='changereason', create_type=False), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('locator_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_locator_history_locator_id', 'locator_history', ['locator_id'])


def downgrade() -> None:
    op.drop_table('locator_history')
    op.drop_table('elements')
    op.drop_table('locators')
    op.drop_table('locator_runs')
    op.drop_table('pages')
    op.drop_table('projects')
    op.execute("DROP TYPE changereason")
    op.execute("DROP TYPE locatorstage")
    op.execute("DROP TYPE runmode")
