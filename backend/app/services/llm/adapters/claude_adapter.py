"""
Claude Adapter - Week 101

Transforms ProjectContext to Claude-optimized XML-structured format.
Output: .claude/CLAUDE.md
"""

from typing import TYPE_CHECKING
from .base import BaseAdapter

if TYPE_CHECKING:
    from ..project_context import ProjectContext


class ClaudeAdapter(BaseAdapter):
    """
    Claude-specific context adapter.

    Features:
    - XML-structured tags for clear section demarcation
    - <artifacts> tags for code examples
    - Detailed reasoning prompts
    - Step-by-step instruction format
    """

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def output_filename(self) -> str:
        return "CLAUDE.md"

    def transform(self, context: "ProjectContext") -> str:
        """Transform to Claude XML-structured format."""

        # Build domain vocabulary section
        vocab_items = ""
        if context.domain_vocabulary:
            vocab_items = "\n".join(
                f"  <term name=\"{t.term}\" entity=\"{t.code_entity}\">{t.definition}</term>"
                for t in context.domain_vocabulary
            )

        # Build implementation order
        impl_order = "\n".join(
            f"  <step number=\"{i+1}\">{step}</step>"
            for i, step in enumerate(context.implementation_order)
        ) if context.implementation_order else ""

        # Build compliance list
        compliance = "\n".join(
            f"  <framework>{c}</framework>"
            for c in context.security.compliance_requirements
        ) if context.security.compliance_requirements else ""

        return f"""<project-context>
  <identity>
    <name>{context.project_name}</name>
    <version>{context.version}</version>
    <status>{context.status}</status>
  </identity>

  <tech-stack>
    <language>{context.tech_stack.primary_language}</language>
    <framework>{context.tech_stack.framework}</framework>
    <database>{context.tech_stack.database}</database>
    <cache>{context.tech_stack.cache}</cache>
    <message-queue>{context.tech_stack.message_queue}</message-queue>
  </tech-stack>

  <architecture>
    <style>{context.architecture.style}</style>
    <layers>{context.architecture.layers}</layers>
    <api-style>{context.architecture.api_style}</api-style>
  </architecture>

  <security>
    <authentication>{context.security.authentication}</authentication>
    <authorization>{context.security.authorization}</authorization>
    <compliance>
{compliance}
    </compliance>
  </security>

  <naming-conventions>
    <classes>{context.naming_conventions.classes}</classes>
    <functions>{context.naming_conventions.functions}</functions>
    <files>{context.naming_conventions.files}</files>
    <constants>{context.naming_conventions.constants}</constants>
    <private-fields>{context.naming_conventions.private_fields}</private-fields>
  </naming-conventions>

  <domain-vocabulary>
{vocab_items}
  </domain-vocabulary>

  <implementation-order>
{impl_order}
  </implementation-order>

  <guidelines>
    <dos>
{self._format_xml_list(context.dos, "do")}
    </dos>
    <donts>
{self._format_xml_list(context.donts, "dont")}
    </donts>
  </guidelines>

  <questions-before-implementing>
{self._format_xml_list(context.questions_to_ask, "question")}
  </questions-before-implementing>
</project-context>

<instructions>
When implementing features for this project:

1. **Read context first**: Parse the <project-context> above before any implementation
2. **Follow implementation order**: Implement in the sequence defined in <implementation-order>
3. **Apply naming conventions**: Use the patterns from <naming-conventions>
4. **Consider security**: Check <compliance> requirements apply to your changes
5. **Use domain vocabulary**: Reference <domain-vocabulary> for consistent naming
6. **Check dos/donts**: Validate against <guidelines> before finalizing

Before making changes, verify:
- Is this feature already partially implemented?
- What existing services can be reused?
- Are there domain-specific rules to consider?
</instructions>
"""

    def _format_xml_list(self, items: list, tag: str) -> str:
        """Format list items as XML elements."""
        if not items:
            return ""
        return "\n".join(f"      <{tag}>{item}</{tag}>" for item in items)
