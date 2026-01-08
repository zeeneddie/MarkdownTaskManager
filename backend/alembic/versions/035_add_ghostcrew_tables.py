"""Add GhostCrew Security tables for Week 80-82

Revision ID: 035
Revises: 034
Create Date: 2025-12-16

Tables:
- ghostcrew_scans: Security scan sessions
- security_findings: Individual vulnerability findings
- shadow_patterns: Learned vulnerability patterns (ShadowGraph)
- vulnerability_learnings: False positive tracking and learning
- compliance_checks: Compliance audit results (GDPR, SOC2, etc.)
- security_knowledge: OWASP/CWE knowledge base entries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '035'
down_revision = '034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GhostCrew Scans - Security scan sessions
    op.create_table(
        'ghostcrew_scans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('workflow_type', sa.String(50), nullable=True),  # QUALITY_AUDIT, BROWN_PAPER, MIGRATION, etc.
        sa.Column('workflow_session_id', sa.String(100), nullable=True),  # Link to workflow session
        sa.Column('scan_mode', sa.String(50), nullable=False),  # assist, autonomous, crew
        sa.Column('scan_type', sa.String(50), nullable=False),  # full, quick, targeted, compliance
        sa.Column('target_path', sa.String(500), nullable=True),  # Path being scanned
        sa.Column('target_type', sa.String(50), nullable=True),  # repository, directory, file, url
        sa.Column('status', sa.String(50), default='pending'),  # pending, running, completed, failed, cancelled
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        # Findings summary
        sa.Column('total_findings', sa.Integer, default=0),
        sa.Column('critical_count', sa.Integer, default=0),
        sa.Column('high_count', sa.Integer, default=0),
        sa.Column('medium_count', sa.Integer, default=0),
        sa.Column('low_count', sa.Integer, default=0),
        sa.Column('info_count', sa.Integer, default=0),
        # Security score
        sa.Column('security_score', sa.Float, nullable=True),  # 0-100
        sa.Column('risk_level', sa.String(20), nullable=True),  # critical, high, medium, low
        # Scan configuration
        sa.Column('scan_config', JSONB, default={}),
        sa.Column('agents_used', JSONB, default=[]),  # List of security agents used
        sa.Column('tools_used', JSONB, default=[]),  # terminal, browser, notes, websearch
        # Results
        sa.Column('scan_summary', sa.Text, nullable=True),
        sa.Column('recommendations', JSONB, default=[]),
        sa.Column('scan_metadata', JSONB, default={}),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
    )
    op.create_index('ix_ghostcrew_scans_project', 'ghostcrew_scans', ['project_id'])
    op.create_index('ix_ghostcrew_scans_status', 'ghostcrew_scans', ['status'])
    op.create_index('ix_ghostcrew_scans_workflow', 'ghostcrew_scans', ['workflow_type', 'workflow_session_id'])
    op.create_index('ix_ghostcrew_scans_risk', 'ghostcrew_scans', ['risk_level'])

    # Security Findings - Individual vulnerability findings
    op.create_table(
        'security_findings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('scan_id', UUID(as_uuid=True), sa.ForeignKey('ghostcrew_scans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        # Finding classification
        sa.Column('finding_type', sa.String(100), nullable=False),  # sql_injection, xss, hardcoded_secret, etc.
        sa.Column('category', sa.String(50), nullable=False),  # injection, auth, crypto, config, etc.
        sa.Column('severity', sa.String(20), nullable=False),  # critical, high, medium, low, info
        sa.Column('confidence', sa.String(20), nullable=False),  # high, medium, low
        # OWASP/CWE mapping
        sa.Column('owasp_category', sa.String(50), nullable=True),  # A01:2021, A02:2021, etc.
        sa.Column('cwe_id', sa.String(20), nullable=True),  # CWE-89, CWE-79, etc.
        sa.Column('cvss_score', sa.Float, nullable=True),  # 0-10
        # Location
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('line_number', sa.Integer, nullable=True),
        sa.Column('column_number', sa.Integer, nullable=True),
        sa.Column('code_snippet', sa.Text, nullable=True),
        sa.Column('function_name', sa.String(200), nullable=True),
        sa.Column('class_name', sa.String(200), nullable=True),
        # Description
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('impact', sa.Text, nullable=True),
        sa.Column('remediation', sa.Text, nullable=True),
        sa.Column('references', JSONB, default=[]),  # Links to docs, CVEs, etc.
        # Status tracking
        sa.Column('status', sa.String(50), default='open'),  # open, confirmed, false_positive, fixed, accepted_risk
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('fixed_at', sa.DateTime, nullable=True),
        sa.Column('fixed_in_commit', sa.String(40), nullable=True),
        # Agent info
        sa.Column('detected_by_agent', sa.String(100), nullable=True),
        sa.Column('detection_method', sa.String(100), nullable=True),  # static_analysis, pattern_match, llm_analysis
        sa.Column('finding_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_security_findings_scan', 'security_findings', ['scan_id'])
    op.create_index('ix_security_findings_project', 'security_findings', ['project_id'])
    op.create_index('ix_security_findings_severity', 'security_findings', ['severity'])
    op.create_index('ix_security_findings_type', 'security_findings', ['finding_type'])
    op.create_index('ix_security_findings_status', 'security_findings', ['status'])
    op.create_index('ix_security_findings_owasp', 'security_findings', ['owasp_category'])
    op.create_index('ix_security_findings_cwe', 'security_findings', ['cwe_id'])

    # Shadow Patterns - Learned vulnerability patterns (ShadowGraph)
    op.create_table(
        'shadow_patterns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('pattern_name', sa.String(200), nullable=False),
        sa.Column('pattern_type', sa.String(50), nullable=False),  # vulnerability, false_positive, secure_pattern
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('language', sa.String(50), nullable=True),  # python, javascript, java, etc.
        sa.Column('framework', sa.String(100), nullable=True),  # django, fastapi, react, etc.
        # Pattern definition
        sa.Column('pattern_regex', sa.Text, nullable=True),  # Regex pattern
        sa.Column('ast_pattern', JSONB, nullable=True),  # AST-based pattern
        sa.Column('semantic_pattern', sa.Text, nullable=True),  # Natural language description
        sa.Column('code_examples', JSONB, default=[]),  # Example code snippets
        # Classification
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('owasp_mapping', sa.String(50), nullable=True),
        sa.Column('cwe_mapping', sa.String(20), nullable=True),
        # Learning metrics
        sa.Column('times_detected', sa.Integer, default=0),
        sa.Column('true_positives', sa.Integer, default=0),
        sa.Column('false_positives', sa.Integer, default=0),
        sa.Column('accuracy_score', sa.Float, nullable=True),  # TP / (TP + FP)
        sa.Column('last_detection', sa.DateTime, nullable=True),
        # Source
        sa.Column('source', sa.String(50), default='learned'),  # learned, manual, imported
        sa.Column('learned_from_scans', JSONB, default=[]),  # List of scan IDs
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('pattern_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_shadow_patterns_type', 'shadow_patterns', ['pattern_type'])
    op.create_index('ix_shadow_patterns_category', 'shadow_patterns', ['category'])
    op.create_index('ix_shadow_patterns_language', 'shadow_patterns', ['language'])
    op.create_index('ix_shadow_patterns_active', 'shadow_patterns', ['is_active'])

    # Vulnerability Learnings - False positive tracking and continuous learning
    op.create_table(
        'vulnerability_learnings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('finding_id', UUID(as_uuid=True), sa.ForeignKey('security_findings.id', ondelete='CASCADE'), nullable=True),
        sa.Column('pattern_id', UUID(as_uuid=True), sa.ForeignKey('shadow_patterns.id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        # Learning type
        sa.Column('learning_type', sa.String(50), nullable=False),  # false_positive, confirmed_vuln, new_pattern, pattern_refinement
        sa.Column('original_classification', sa.String(50), nullable=True),
        sa.Column('corrected_classification', sa.String(50), nullable=True),
        # Context
        sa.Column('code_context', sa.Text, nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('framework', sa.String(100), nullable=True),
        # Feedback
        sa.Column('feedback_source', sa.String(50), nullable=False),  # human, agent, automated
        sa.Column('feedback_reason', sa.Text, nullable=True),
        sa.Column('feedback_by', sa.String(100), nullable=True),
        # Impact
        sa.Column('applied_to_pattern', sa.Boolean, default=False),
        sa.Column('pattern_updated_at', sa.DateTime, nullable=True),
        sa.Column('prevents_future_fp', sa.Boolean, default=False),
        sa.Column('learning_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_vulnerability_learnings_finding', 'vulnerability_learnings', ['finding_id'])
    op.create_index('ix_vulnerability_learnings_pattern', 'vulnerability_learnings', ['pattern_id'])
    op.create_index('ix_vulnerability_learnings_type', 'vulnerability_learnings', ['learning_type'])
    op.create_index('ix_vulnerability_learnings_project', 'vulnerability_learnings', ['project_id'])

    # Compliance Checks - Compliance audit results
    op.create_table(
        'compliance_checks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('scan_id', UUID(as_uuid=True), sa.ForeignKey('ghostcrew_scans.id', ondelete='CASCADE'), nullable=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        # Compliance framework
        sa.Column('framework', sa.String(50), nullable=False),  # GDPR, SOC2, HIPAA, PCI_DSS, ISO27001
        sa.Column('framework_version', sa.String(20), nullable=True),
        sa.Column('check_type', sa.String(100), nullable=False),  # Full audit, specific control, gap analysis
        # Results
        sa.Column('status', sa.String(50), default='pending'),  # pending, passed, failed, partial, not_applicable
        sa.Column('overall_score', sa.Float, nullable=True),  # 0-100
        sa.Column('controls_total', sa.Integer, default=0),
        sa.Column('controls_passed', sa.Integer, default=0),
        sa.Column('controls_failed', sa.Integer, default=0),
        sa.Column('controls_partial', sa.Integer, default=0),
        sa.Column('controls_na', sa.Integer, default=0),
        # Details
        sa.Column('control_results', JSONB, default=[]),  # Detailed control-by-control results
        sa.Column('gaps_identified', JSONB, default=[]),
        sa.Column('recommendations', JSONB, default=[]),
        sa.Column('evidence_collected', JSONB, default=[]),
        # Audit info
        sa.Column('audited_by_agent', sa.String(100), nullable=True),
        sa.Column('audit_notes', sa.Text, nullable=True),
        sa.Column('next_audit_date', sa.DateTime, nullable=True),
        sa.Column('compliance_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_compliance_checks_scan', 'compliance_checks', ['scan_id'])
    op.create_index('ix_compliance_checks_project', 'compliance_checks', ['project_id'])
    op.create_index('ix_compliance_checks_framework', 'compliance_checks', ['framework'])
    op.create_index('ix_compliance_checks_status', 'compliance_checks', ['status'])

    # Security Knowledge - OWASP/CWE knowledge base
    op.create_table(
        'security_knowledge',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('knowledge_type', sa.String(50), nullable=False),  # owasp, cwe, best_practice, pattern
        sa.Column('identifier', sa.String(50), nullable=False),  # A01:2021, CWE-89, etc.
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        # Risk info
        sa.Column('severity_default', sa.String(20), nullable=True),
        sa.Column('likelihood', sa.String(20), nullable=True),  # high, medium, low
        sa.Column('impact_description', sa.Text, nullable=True),
        # Remediation
        sa.Column('remediation_guidance', sa.Text, nullable=True),
        sa.Column('code_examples_vulnerable', JSONB, default=[]),
        sa.Column('code_examples_secure', JSONB, default=[]),
        sa.Column('prevention_techniques', JSONB, default=[]),
        # References
        sa.Column('external_references', JSONB, default=[]),
        sa.Column('related_cwes', JSONB, default=[]),
        sa.Column('related_owasp', JSONB, default=[]),
        # Metadata
        sa.Column('languages_affected', JSONB, default=[]),
        sa.Column('frameworks_affected', JSONB, default=[]),
        sa.Column('detection_methods', JSONB, default=[]),
        sa.Column('last_updated', sa.DateTime, server_default=sa.func.now()),
        sa.Column('source', sa.String(100), nullable=True),  # owasp.org, cwe.mitre.org, custom
        sa.Column('is_active', sa.Boolean, default=True),
    )
    op.create_index('ix_security_knowledge_type', 'security_knowledge', ['knowledge_type'])
    op.create_index('ix_security_knowledge_identifier', 'security_knowledge', ['identifier'], unique=True)
    op.create_index('ix_security_knowledge_category', 'security_knowledge', ['category'])


def downgrade() -> None:
    op.drop_table('security_knowledge')
    op.drop_table('compliance_checks')
    op.drop_table('vulnerability_learnings')
    op.drop_table('shadow_patterns')
    op.drop_table('security_findings')
    op.drop_table('ghostcrew_scans')
