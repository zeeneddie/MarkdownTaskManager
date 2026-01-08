"""Add testing excellence tables for Week 134-135

Revision ID: 063
Revises: 062
Create Date: 2025-12-31

Tables:
- characterization_tests: Golden Master test definitions
- characterization_test_runs: Individual test run results
- visual_regression_tests: Visual regression test definitions
- visual_regression_runs: Visual regression test run results
- dual_run_comparisons: Dual-run session definitions
- dual_run_requests: Individual dual-run request results

Part of Fase 23 - Testing Excellence for migration validation.
Agent: Tessa (Test Engineer) + Vicky (Visual Designer)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '063'
down_revision = '062'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Characterization Tests - Golden Master test definitions
    op.create_table(
        'characterization_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=True, index=True),
        sa.Column('test_name', sa.String(512), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('legacy_endpoint', sa.String(1024), nullable=False),
        sa.Column('new_endpoint', sa.String(1024), nullable=True),
        sa.Column('method', sa.String(10), nullable=False, default='POST'),
        sa.Column('headers', JSONB, nullable=True),
        sa.Column('input_scenarios', JSONB, nullable=True),  # [{name, data, description}]
        sa.Column('ignored_fields', JSONB, nullable=True),  # ["timestamp", "id", ...]
        sa.Column('tolerance_rules', JSONB, nullable=True),  # {field: tolerance}
        sa.Column('baseline_data', JSONB, nullable=True),  # Golden Master output
        sa.Column('baseline_hash', sa.String(64), nullable=True),
        sa.Column('baseline_recorded_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),  # active, archived, disabled
        sa.Column('tags', JSONB, nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_characterization_tests_test_name', 'characterization_tests', ['test_name'])

    # Characterization Test Runs - individual test execution results
    op.create_table(
        'characterization_test_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('test_id', UUID(as_uuid=True), sa.ForeignKey('characterization_tests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('run_number', sa.Integer, nullable=False, default=1),
        sa.Column('input_scenario', sa.String(255), nullable=True),
        sa.Column('input_data', JSONB, nullable=True),
        sa.Column('legacy_output', JSONB, nullable=True),
        sa.Column('new_output', JSONB, nullable=True),
        sa.Column('result', sa.String(20), nullable=False),  # match, mismatch, error, new_baseline
        sa.Column('match_percentage', sa.Float, default=0.0),
        sa.Column('diff_count', sa.Integer, default=0),
        sa.Column('differences', JSONB, nullable=True),  # [{field_path, diff_type, expected, actual}]
        sa.Column('legacy_duration_ms', sa.Integer, nullable=True),
        sa.Column('new_duration_ms', sa.Integer, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('executed_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_characterization_test_runs_result', 'characterization_test_runs', ['result'])
    op.create_index('ix_characterization_test_runs_executed_at', 'characterization_test_runs', ['executed_at'])

    # Visual Regression Tests - visual baseline definitions
    op.create_table(
        'visual_regression_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=True, index=True),
        sa.Column('test_name', sa.String(512), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('legacy_url', sa.String(2048), nullable=False),
        sa.Column('new_url', sa.String(2048), nullable=True),
        sa.Column('viewport_width', sa.Integer, default=1920),
        sa.Column('viewport_height', sa.Integer, default=1080),
        sa.Column('full_page', sa.Boolean, default=False),
        sa.Column('wait_for_selector', sa.String(512), nullable=True),
        sa.Column('hide_selectors', JSONB, nullable=True),  # [".timestamp", "#random-id", ...]
        sa.Column('mask_selectors', JSONB, nullable=True),  # Elements to mask during comparison
        sa.Column('screenshot_tool', sa.String(50), default='playwright'),  # playwright, puppeteer, selenium
        sa.Column('diff_threshold', sa.Float, default=0.1),  # Max allowed diff percentage
        sa.Column('baseline_path', sa.String(1024), nullable=True),
        sa.Column('baseline_dimensions', JSONB, nullable=True),  # {width, height}
        sa.Column('baseline_captured_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('tags', JSONB, nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_visual_regression_tests_test_name', 'visual_regression_tests', ['test_name'])

    # Visual Regression Runs - individual visual comparison results
    op.create_table(
        'visual_regression_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('test_id', UUID(as_uuid=True), sa.ForeignKey('visual_regression_tests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('run_number', sa.Integer, nullable=False, default=1),
        sa.Column('baseline_path', sa.String(1024), nullable=True),
        sa.Column('new_screenshot_path', sa.String(1024), nullable=True),
        sa.Column('diff_image_path', sa.String(1024), nullable=True),
        sa.Column('result', sa.String(20), nullable=False),  # match, mismatch, error, new_baseline
        sa.Column('match_percentage', sa.Float, default=0.0),
        sa.Column('diff_percentage', sa.Float, default=0.0),
        sa.Column('diff_pixel_count', sa.Integer, default=0),
        sa.Column('total_pixel_count', sa.Integer, default=0),
        sa.Column('diff_regions', JSONB, nullable=True),  # [{x, y, width, height, diff_percentage}]
        sa.Column('baseline_dimensions', JSONB, nullable=True),
        sa.Column('new_dimensions', JSONB, nullable=True),
        sa.Column('dimension_match', sa.Boolean, default=True),
        sa.Column('legacy_duration_ms', sa.Integer, nullable=True),  # Capture time
        sa.Column('new_duration_ms', sa.Integer, nullable=True),
        sa.Column('comparison_duration_ms', sa.Integer, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('executed_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_visual_regression_runs_result', 'visual_regression_runs', ['result'])
    op.create_index('ix_visual_regression_runs_executed_at', 'visual_regression_runs', ['executed_at'])

    # Dual-Run Comparisons - parallel execution session definitions
    op.create_table(
        'dual_run_comparisons',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=True, index=True),
        sa.Column('session_name', sa.String(512), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('legacy_base_url', sa.String(1024), nullable=False),
        sa.Column('new_base_url', sa.String(1024), nullable=False),
        sa.Column('legacy_headers', JSONB, nullable=True),
        sa.Column('new_headers', JSONB, nullable=True),
        sa.Column('shadow_mode', sa.Boolean, default=True),  # New system doesn't serve responses
        sa.Column('traffic_percentage', sa.Float, default=100.0),  # % of traffic to compare
        sa.Column('ignored_fields', JSONB, nullable=True),
        sa.Column('tolerance_rules', JSONB, nullable=True),
        sa.Column('total_requests', sa.Integer, default=0),
        sa.Column('matches', sa.Integer, default=0),
        sa.Column('mismatches', sa.Integer, default=0),
        sa.Column('errors', sa.Integer, default=0),
        sa.Column('match_rate', sa.Float, default=0.0),
        sa.Column('avg_legacy_duration_ms', sa.Float, default=0.0),
        sa.Column('avg_new_duration_ms', sa.Float, default=0.0),
        sa.Column('status', sa.String(20), nullable=False, default='active'),  # active, paused, completed
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_dual_run_comparisons_session_name', 'dual_run_comparisons', ['session_name'])
    op.create_index('ix_dual_run_comparisons_status', 'dual_run_comparisons', ['status'])

    # Dual-Run Requests - individual parallel execution results
    op.create_table(
        'dual_run_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('comparison_id', UUID(as_uuid=True), sa.ForeignKey('dual_run_comparisons.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('request_number', sa.Integer, nullable=False, default=1),
        sa.Column('endpoint_path', sa.String(1024), nullable=False),
        sa.Column('method', sa.String(10), nullable=False, default='GET'),
        sa.Column('request_data', JSONB, nullable=True),
        sa.Column('query_params', JSONB, nullable=True),
        sa.Column('legacy_response', JSONB, nullable=True),
        sa.Column('new_response', JSONB, nullable=True),
        sa.Column('legacy_status', sa.Integer, nullable=True),
        sa.Column('new_status', sa.Integer, nullable=True),
        sa.Column('result', sa.String(20), nullable=False),  # match, mismatch, error
        sa.Column('match_percentage', sa.Float, default=0.0),
        sa.Column('diff_count', sa.Integer, default=0),
        sa.Column('differences', JSONB, nullable=True),
        sa.Column('legacy_duration_ms', sa.Integer, nullable=True),
        sa.Column('new_duration_ms', sa.Integer, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('executed_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_dual_run_requests_result', 'dual_run_requests', ['result'])
    op.create_index('ix_dual_run_requests_endpoint_path', 'dual_run_requests', ['endpoint_path'])
    op.create_index('ix_dual_run_requests_executed_at', 'dual_run_requests', ['executed_at'])

    # Testing Excellence Summary - aggregated metrics per project
    op.create_table(
        'testing_excellence_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('characterization_test_count', sa.Integer, default=0),
        sa.Column('characterization_pass_rate', sa.Float, default=0.0),
        sa.Column('characterization_last_run', sa.DateTime, nullable=True),
        sa.Column('visual_regression_test_count', sa.Integer, default=0),
        sa.Column('visual_regression_pass_rate', sa.Float, default=0.0),
        sa.Column('visual_regression_last_run', sa.DateTime, nullable=True),
        sa.Column('dual_run_session_count', sa.Integer, default=0),
        sa.Column('dual_run_match_rate', sa.Float, default=0.0),
        sa.Column('dual_run_total_requests', sa.Integer, default=0),
        sa.Column('overall_confidence', sa.Float, default=0.0),  # Weighted average
        sa.Column('migration_readiness', sa.String(20), nullable=True),  # not_ready, partial, ready
        sa.Column('recommendations', JSONB, nullable=True),
        sa.Column('last_updated', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('testing_excellence_summaries')
    op.drop_index('ix_dual_run_requests_executed_at', table_name='dual_run_requests')
    op.drop_index('ix_dual_run_requests_endpoint_path', table_name='dual_run_requests')
    op.drop_index('ix_dual_run_requests_result', table_name='dual_run_requests')
    op.drop_table('dual_run_requests')
    op.drop_index('ix_dual_run_comparisons_status', table_name='dual_run_comparisons')
    op.drop_index('ix_dual_run_comparisons_session_name', table_name='dual_run_comparisons')
    op.drop_table('dual_run_comparisons')
    op.drop_index('ix_visual_regression_runs_executed_at', table_name='visual_regression_runs')
    op.drop_index('ix_visual_regression_runs_result', table_name='visual_regression_runs')
    op.drop_table('visual_regression_runs')
    op.drop_index('ix_visual_regression_tests_test_name', table_name='visual_regression_tests')
    op.drop_table('visual_regression_tests')
    op.drop_index('ix_characterization_test_runs_executed_at', table_name='characterization_test_runs')
    op.drop_index('ix_characterization_test_runs_result', table_name='characterization_test_runs')
    op.drop_table('characterization_test_runs')
    op.drop_index('ix_characterization_tests_test_name', table_name='characterization_tests')
    op.drop_table('characterization_tests')
