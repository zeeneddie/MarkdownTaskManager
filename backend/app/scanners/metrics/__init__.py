"""
Metrics Layer Scanners

Week 126-127: Code quality metrics analyzers for the MarQed AI Agent Platform.

Analyzers:
- ComplexityAnalyzer: Cyclomatic complexity per function
- InterfacingAnalyzer: Parameter count per function
- CouplingAnalyzer: Fan-in, fan-out, instability index
- BalanceAnalyzer: Code distribution across components (Gini coefficient)
- DuplicationAnalyzer: Type 1/2/3 code clone detection

All analyzers implement the BaseScanner interface and provide 5-star quality ratings.
"""

from .complexity_analyzer import ComplexityAnalyzer
from .interfacing_analyzer import InterfacingAnalyzer
from .coupling_analyzer import CouplingAnalyzer
from .balance_analyzer import BalanceAnalyzer
from .duplication_analyzer import DuplicationAnalyzer

__all__ = [
    'ComplexityAnalyzer',
    'InterfacingAnalyzer',
    'CouplingAnalyzer',
    'BalanceAnalyzer',
    'DuplicationAnalyzer',
]
