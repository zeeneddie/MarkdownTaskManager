"""
Knowledge Base Services - Famous Bugs & Post-Mortems

Provides curated knowledge bases for agent context enrichment:
- Famous Bugs: Historical software failures with lessons learned
- Post-Mortems: Real-world incident post-mortems from major companies
"""

from app.services.knowledge_base.famous_bugs_loader import FamousBugsLoader, FAMOUS_BUGS_DATA
from app.services.knowledge_base.post_mortems_loader import PostMortemsLoader, POST_MORTEMS_DATA
from app.services.knowledge_base.kb_context_provider import KBContextProvider

__all__ = [
    "FamousBugsLoader",
    "FAMOUS_BUGS_DATA",
    "PostMortemsLoader",
    "POST_MORTEMS_DATA",
    "KBContextProvider",
]
