"""Public interface for the RAT Git metrics engine."""

from .analyzer import GitAnalyzer
from .models import AuthorInfo, CommitInfo, MetricsResult, TreeEntry

__all__ = [
    "AuthorInfo",
    "CommitInfo",
    "GitAnalyzer",
    "MetricsResult",
    "TreeEntry",
]
