#!/usr/bin/env python3
"""
MarQed AI Platform - Test File Mapper
Maps week-based test files to service-based directories
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple

TESTS_DIR = Path("/home/eddie/Projects/MarkdownTaskManager/backend/tests")

# Service domain mappings based on test file names and content
DOMAIN_PATTERNS: Dict[str, List[str]] = {
    # Extraction & Code Analysis
    "extraction": [
        "extraction", "extractor", "ast_", "aspx_", "vb6_", "php_",
        "business_rule", "requirements_", "hierarchical_story",
        "potpie", "rule_correlation"
    ],

    # Migration services
    "migration": [
        "migration", "migrate", "ora2pg", "sqlines", "strangler",
        "database_analyzer", "asis_architecture", "transformation"
    ],

    # Analysis services
    "analysis": [
        "analysis", "analyzer", "static_", "devops_", "code_coverage",
        "dead_code", "runtime_analysis", "program_slicer", "variable_classifier",
        "compliance_checker", "nfr_detector", "conflict_detector",
        "code_graph", "dependency_graph", "layered_analysis"
    ],

    # Quality services
    "quality": [
        "quality", "invest_validator", "traceability", "delta_tracking"
    ],

    # Observability
    "observability": [
        "observability", "cctrace", "metrics"
    ],

    # Council & Human Review
    "council": [
        "council", "llm_council", "human_review", "premium_synthesis"
    ],

    # Portal features
    "portal": [
        "portal", "chatbot", "roadmap", "voting", "feature_request",
        "gamification", "personalized_dashboard", "feedback_loop",
        "journey_analytics"
    ],

    # Estimation
    "estimation": [
        "estimation", "function_point", "story_point", "load_estimation",
        "effort"
    ],

    # External integrations
    "integration": [
        "mcp_proxy", "anytool", "memmachine", "bigagi", "playwriter",
        "claude_mem", "ghostcrew", "ccpm", "workflow_tool_integration",
        "graph_workflow", "tool_registry"
    ],

    # Data architecture
    "data": [
        "data_architecture", "data_lineage", "erd_generator", "cdc_",
        "graph_persistence", "knowledge_graph", "shadow_graph"
    ],

    # Security
    "security": [
        "security", "authorization_matrix", "auth"
    ],

    # Evolution & Experiments
    "evolution": [
        "evolution", "ab_testing", "experiment", "gradual_rollout",
        "trend_analysis", "continuous_learning", "rollback"
    ],

    # Workflows
    "workflows": [
        "workflow", "green_paper", "brown_paper", "spec_kit"
    ],

    # Agents
    "agents": [
        "agent", "stack_agent", "stack_detection"
    ],

    # Providers
    "providers": [
        "provider", "ollama", "openai", "anthropic", "gemini"
    ],

    # Core (default for unmatched)
    "core": [
        "sprint", "epic", "item", "project_", "customer", "tier_config",
        "version_tracker", "context_manager", "constraint_manager",
        "document_sync", "improve_skills", "quick_spec", "spec_verification",
        "design_os", "deep_extraction"
    ]
}

def get_domain_for_test(filename: str, filepath: str) -> str:
    """Determine the service domain for a test file."""
    name_lower = filename.lower()
    path_lower = filepath.lower()

    # Check each domain's patterns
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in name_lower or pattern in path_lower:
                return domain

    # Default to core
    return "core"

def get_test_type(filepath: str) -> str:
    """Determine if test is unit, integration, or e2e."""
    if "/e2e/" in filepath or "_e2e" in filepath:
        return "e2e"
    elif "/api/" in filepath:
        return "integration/api"
    else:
        return "unit"

def generate_new_filename(old_filename: str) -> str:
    """Remove week references from filename."""
    # Remove week prefixes/suffixes
    new_name = re.sub(r'_week\d+', '', old_filename)
    new_name = re.sub(r'week\d+_', '', new_name)
    return new_name

def map_tests() -> List[Tuple[Path, Path]]:
    """Generate mapping of old paths to new paths."""
    mappings = []

    # Find all test files
    for test_file in TESTS_DIR.rglob("test_*.py"):
        if ".backup" in str(test_file):
            continue
        if "/unit/" in str(test_file) or "/integration/" in str(test_file):
            continue  # Already in new structure

        rel_path = test_file.relative_to(TESTS_DIR)
        filename = test_file.name

        # Determine domain and test type
        domain = get_domain_for_test(filename, str(rel_path))
        test_type = get_test_type(str(rel_path))

        # Generate new filename (remove week references)
        new_filename = generate_new_filename(filename)

        # Build new path
        if test_type == "e2e":
            new_path = TESTS_DIR / "e2e" / new_filename
        elif test_type == "integration/api":
            new_path = TESTS_DIR / "integration" / "api" / domain / new_filename
        else:
            new_path = TESTS_DIR / "unit" / domain / new_filename

        mappings.append((test_file, new_path))

    return mappings

def print_mapping_summary(mappings: List[Tuple[Path, Path]]):
    """Print summary of the mapping."""
    print("\n" + "="*70)
    print("TEST FILE MAPPING SUMMARY")
    print("="*70 + "\n")

    # Group by destination domain
    by_domain = {}
    for old, new in mappings:
        parts = new.relative_to(TESTS_DIR).parts
        if len(parts) >= 2:
            domain = parts[1] if parts[0] in ("unit", "integration") else parts[0]
        else:
            domain = "root"

        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append((old, new))

    for domain in sorted(by_domain.keys()):
        files = by_domain[domain]
        print(f"\n{domain.upper()} ({len(files)} files):")
        for old, new in files[:5]:  # Show first 5
            old_rel = old.relative_to(TESTS_DIR)
            new_rel = new.relative_to(TESTS_DIR)
            print(f"  {old_rel}")
            print(f"    → {new_rel}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")

    print(f"\n{'='*70}")
    print(f"TOTAL: {len(mappings)} files to move")
    print(f"{'='*70}\n")

def execute_mapping(mappings: List[Tuple[Path, Path]], dry_run: bool = True):
    """Execute the file moves."""
    if dry_run:
        print("\n[DRY RUN] Would execute the following moves:\n")
    else:
        print("\n[EXECUTING] Moving files...\n")

    moved = 0
    errors = []

    for old_path, new_path in mappings:
        try:
            # Ensure destination directory exists
            new_path.parent.mkdir(parents=True, exist_ok=True)

            if dry_run:
                print(f"  MOVE: {old_path.name} → {new_path.relative_to(TESTS_DIR)}")
            else:
                # Check for conflicts
                if new_path.exists():
                    # Add suffix to avoid overwriting
                    base = new_path.stem
                    suffix = new_path.suffix
                    counter = 1
                    while new_path.exists():
                        new_path = new_path.parent / f"{base}_{counter}{suffix}"
                        counter += 1

                shutil.copy2(old_path, new_path)
                print(f"  ✅ {old_path.name} → {new_path.relative_to(TESTS_DIR)}")
                moved += 1

        except Exception as e:
            errors.append((old_path, str(e)))
            print(f"  ❌ {old_path.name}: {e}")

    print(f"\n{'='*70}")
    if dry_run:
        print(f"DRY RUN COMPLETE: {len(mappings)} files would be moved")
    else:
        print(f"EXECUTION COMPLETE: {moved} files moved, {len(errors)} errors")
    print(f"{'='*70}\n")

    return moved, errors

if __name__ == "__main__":
    import sys

    dry_run = "--execute" not in sys.argv

    print("\n" + "="*70)
    print("MARQED AI PLATFORM - TEST REORGANIZATION")
    print("="*70)

    mappings = map_tests()
    print_mapping_summary(mappings)

    if dry_run:
        print("\nThis is a DRY RUN. To execute, run with --execute flag.")
        print("Example: python map-tests.py --execute\n")

    execute_mapping(mappings, dry_run=dry_run)
