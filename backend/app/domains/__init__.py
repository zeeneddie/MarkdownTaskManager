# Domains Module
# Domain-driven design structure for workflow separation
#
# Domains:
# - brown_paper: Analysis domain (code analysis, domain extraction, constitution)
# - migration: Execution domain (7-phase migration workflow)
# - quality: Validation domain (quality gates, scans, scheduling)
#
# Key Principle: Domains communicate via contracts, NOT direct dependencies.
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

__all__ = [
    "brown_paper",
    "migration",
    "quality",
]
