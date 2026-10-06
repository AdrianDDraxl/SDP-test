"""Data models returned by the git analysis engine."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CommitInfo:
    """Metadata for a non-merge commit."""

    hash: str
    author_name: str
    author_email: str
    date: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorInfo:
    """A canonical author and their non-merge commit count."""

    name: str
    email: str
    commit_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TreeEntry:
    """A file or directory in a repository tree."""

    path: str
    type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MetricsResult:
    """Aggregated metrics for a selected set of commits."""

    summary: dict[str, Any]
    files: list[dict[str, Any]]
    directories: list[dict[str, Any]]
    authors: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    commits_used: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
