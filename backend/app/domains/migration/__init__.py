# Migration Domain
# Execution domain: 7-phase migration workflow
#
# Exports:
# - AnalysisContractConsumer: Consumes AnalysisContract for migration context

from .contract_consumer import AnalysisContractConsumer

__all__ = [
    "AnalysisContractConsumer",
]
