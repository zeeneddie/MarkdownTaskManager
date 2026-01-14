"""
Metrics Layer Scanners

Week 126-129: Code quality metrics analyzers for the MarQed AI Agent Platform.

Analyzers (SIG TOP 10 Maintainability Model):
- ComplexityAnalyzer: Cyclomatic complexity per function (SIG #3)
- InterfacingAnalyzer: Parameter count per function (SIG #4)
- CouplingAnalyzer: Fan-in, fan-out, instability index (SIG #5 & #8)
- BalanceAnalyzer: Code distribution across components (SIG #6)
- DuplicationAnalyzer: Type 1/2/3 code clone detection (SIG #2)
- CommentsAnalyzer: Code comments ratio (SIG #9)

All analyzers implement the BaseScanner interface and provide 5-star quality ratings.
"""

from .complexity_analyzer import ComplexityAnalyzer
from .interfacing_analyzer import InterfacingAnalyzer
from .coupling_analyzer import CouplingAnalyzer
from .balance_analyzer import BalanceAnalyzer
from .duplication_analyzer import DuplicationAnalyzer
from .comments_analyzer import CommentsAnalyzer

__all__ = [
    'ComplexityAnalyzer',
    'InterfacingAnalyzer',
    'CouplingAnalyzer',
    'BalanceAnalyzer',
    'DuplicationAnalyzer',
    'CommentsAnalyzer',
]
