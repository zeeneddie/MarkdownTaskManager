"""
QuickSpecService - Fast spec templates for common work types

Week 60: Quick Spec Templates
Provides pre-filled templates for common scenarios:
- Bug Fix: Minimal template for bug reports
- Enhancement: Feature extension template
- Refactoring: Code quality improvement
- Hotfix: Emergency fix (stripped down)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QuickSpecType(str, Enum):
    """Types of quick spec templates."""
    BUG_FIX = "bug_fix"
    ENHANCEMENT = "enhancement"
    REFACTORING = "refactoring"
    HOTFIX = "hotfix"


@dataclass
class QuickSpecTemplate:
    """A quick spec template definition."""
    type: QuickSpecType
    name: str
    description: str
    estimated_time: str
    required_fields: List[str]
    optional_fields: List[str]
    template: str


# Template definitions
QUICK_SPEC_TEMPLATES: Dict[QuickSpecType, QuickSpecTemplate] = {
    QuickSpecType.BUG_FIX: QuickSpecTemplate(
        type=QuickSpecType.BUG_FIX,
        name="Bug Fix",
        description="Template for reporting and fixing bugs",
        estimated_time="1-4 hours",
        required_fields=["title", "reproduction_steps", "expected_behavior", "actual_behavior"],
        optional_fields=["environment", "screenshots", "logs", "priority"],
        template="""# Bug Fix: {title}

## Problem Statement
A bug has been identified that needs to be fixed.

## Reproduction Steps
{reproduction_steps}

## Expected Behavior
{expected_behavior}

## Actual Behavior
{actual_behavior}

## Environment
{environment}

## Technical Analysis
- **Root Cause**: [To be determined]
- **Affected Components**: [List affected files/modules]
- **Risk Level**: {priority}

## Solution Approach
1. Investigate root cause
2. Implement fix
3. Add regression test
4. Verify fix in staging

## Success Criteria
- [ ] Bug no longer reproducible
- [ ] Regression test added
- [ ] No new issues introduced
- [ ] Code reviewed and approved

## Action Items
- [ ] Reproduce the bug locally
- [ ] Identify root cause
- [ ] Implement fix
- [ ] Write test case
- [ ] Deploy and verify
"""
    ),

    QuickSpecType.ENHANCEMENT: QuickSpecTemplate(
        type=QuickSpecType.ENHANCEMENT,
        name="Enhancement",
        description="Template for feature enhancements and improvements",
        estimated_time="4-16 hours",
        required_fields=["title", "current_behavior", "desired_behavior", "user_benefit"],
        optional_fields=["acceptance_criteria", "technical_notes", "dependencies"],
        template="""# Enhancement: {title}

## Problem Statement
This enhancement improves existing functionality to better serve user needs.

## Current Behavior
{current_behavior}

## Desired Behavior
{desired_behavior}

## User Benefit
{user_benefit}

## Scope
### In Scope
- {title} implementation
- Related UI updates
- Documentation updates

### Out of Scope
- Major architectural changes
- Unrelated features

## Technical Approach
{technical_notes}

## Dependencies
{dependencies}

## Success Criteria
{acceptance_criteria}

## Action Items
- [ ] Review current implementation
- [ ] Design enhancement approach
- [ ] Implement changes
- [ ] Update tests
- [ ] Update documentation
- [ ] Deploy and verify
"""
    ),

    QuickSpecType.REFACTORING: QuickSpecTemplate(
        type=QuickSpecType.REFACTORING,
        name="Refactoring",
        description="Template for code quality improvements and technical debt",
        estimated_time="2-8 hours",
        required_fields=["title", "current_state", "target_state", "motivation"],
        optional_fields=["risk_assessment", "rollback_plan", "affected_tests"],
        template="""# Refactoring: {title}

## Problem Statement
Technical debt or code quality issue needs to be addressed.

## Current State
{current_state}

## Target State
{target_state}

## Motivation
{motivation}

## Scope
### In Scope
- Code restructuring as described
- Test updates as needed
- Documentation updates

### Out of Scope
- New features
- Behavioral changes
- API changes (unless specified)

## Risk Assessment
{risk_assessment}

## Rollback Plan
{rollback_plan}

## Technical Approach
1. Create feature branch
2. Apply refactoring incrementally
3. Run full test suite after each change
4. Update affected tests
5. Review and merge

## Success Criteria
- [ ] All existing tests pass
- [ ] Code meets quality standards
- [ ] No behavioral changes (unless intended)
- [ ] Performance not degraded
- [ ] Code reviewed and approved

## Affected Tests
{affected_tests}

## Action Items
- [ ] Analyze current code
- [ ] Plan refactoring steps
- [ ] Implement changes incrementally
- [ ] Update tests
- [ ] Run full test suite
- [ ] Deploy and monitor
"""
    ),

    QuickSpecType.HOTFIX: QuickSpecTemplate(
        type=QuickSpecType.HOTFIX,
        name="Hotfix",
        description="Emergency fix template for production issues",
        estimated_time="30 min - 2 hours",
        required_fields=["title", "issue_description", "impact", "fix_description"],
        optional_fields=["root_cause", "prevention"],
        template="""# HOTFIX: {title}

## URGENT - Production Issue

## Issue Description
{issue_description}

## Impact
{impact}

## Fix Description
{fix_description}

## Root Cause (if known)
{root_cause}

## Immediate Actions
- [ ] Apply fix to production
- [ ] Verify fix works
- [ ] Monitor for issues
- [ ] Notify stakeholders

## Follow-up Actions
- [ ] Create proper bug ticket
- [ ] Add regression test
- [ ] Document incident
- [ ] Plan prevention measures

## Prevention
{prevention}

## Rollback
If fix causes issues:
1. Revert deployment
2. Restore previous version
3. Escalate to team lead
"""
    ),
}


class QuickSpecService:
    """
    Service for generating quick spec documents from templates.

    Provides fast, pre-filled templates for common work scenarios
    to speed up specification creation.
    """

    def __init__(self):
        """Initialize the quick spec service."""
        self.templates = QUICK_SPEC_TEMPLATES

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available quick spec templates.

        Returns:
            List of template metadata
        """
        return [
            {
                "type": template.type.value,
                "name": template.name,
                "description": template.description,
                "estimated_time": template.estimated_time,
                "required_fields": template.required_fields,
                "optional_fields": template.optional_fields,
            }
            for template in self.templates.values()
        ]

    def get_template(self, template_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by type.

        Args:
            template_type: The type of template to get

        Returns:
            Template details or None if not found
        """
        try:
            spec_type = QuickSpecType(template_type)
            template = self.templates.get(spec_type)
            if template:
                return {
                    "type": template.type.value,
                    "name": template.name,
                    "description": template.description,
                    "estimated_time": template.estimated_time,
                    "required_fields": template.required_fields,
                    "optional_fields": template.optional_fields,
                    "template": template.template,
                }
        except ValueError:
            pass
        return None

    def generate_spec(
        self,
        template_type: str,
        fields: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate a spec document from a template.

        Args:
            template_type: The type of template to use
            fields: Field values to fill in the template

        Returns:
            Generated spec document with metadata
        """
        try:
            spec_type = QuickSpecType(template_type)
        except ValueError:
            raise ValueError(f"Unknown template type: {template_type}")

        template = self.templates.get(spec_type)
        if not template:
            raise ValueError(f"Template not found: {template_type}")

        # Check required fields
        missing_fields = []
        for field in template.required_fields:
            if field not in fields or not fields[field]:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Fill in template
        spec_content = template.template

        # Replace all placeholders
        for field, value in fields.items():
            placeholder = "{" + field + "}"
            spec_content = spec_content.replace(placeholder, value or "[Not specified]")

        # Replace any remaining placeholders with defaults
        for field in template.optional_fields:
            placeholder = "{" + field + "}"
            if placeholder in spec_content:
                spec_content = spec_content.replace(placeholder, "[Not specified]")

        return {
            "type": template_type,
            "name": template.name,
            "generated_at": datetime.now().isoformat(),
            "content": spec_content,
            "fields_used": list(fields.keys()),
            "estimated_time": template.estimated_time,
        }

    def validate_fields(
        self,
        template_type: str,
        fields: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Validate fields against a template without generating.

        Args:
            template_type: The type of template
            fields: Field values to validate

        Returns:
            Validation result with any issues
        """
        try:
            spec_type = QuickSpecType(template_type)
        except ValueError:
            return {
                "valid": False,
                "error": f"Unknown template type: {template_type}",
                "missing_required": [],
                "extra_fields": [],
            }

        template = self.templates.get(spec_type)
        if not template:
            return {
                "valid": False,
                "error": f"Template not found: {template_type}",
                "missing_required": [],
                "extra_fields": [],
            }

        # Check required fields
        missing_required = [
            f for f in template.required_fields
            if f not in fields or not fields[f]
        ]

        # Check for extra fields
        all_fields = set(template.required_fields + template.optional_fields)
        extra_fields = [f for f in fields.keys() if f not in all_fields]

        return {
            "valid": len(missing_required) == 0,
            "error": None if len(missing_required) == 0 else "Missing required fields",
            "missing_required": missing_required,
            "extra_fields": extra_fields,
            "required_fields": template.required_fields,
            "optional_fields": template.optional_fields,
        }
