"""Metric aggregation helpers for the git analysis engine."""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath
from typing import Any

_COUNTER_KEYS = ("added_lines", "removed_lines", "growth", "churn")


def _empty_totals() -> dict[str, int]:
    return {
        "added_lines": 0,
        "removed_lines": 0,
        "growth": 0,
        "churn": 0,
        "modifications": 0,
    }


def _add_change(target: dict[str, int], change: Mapping[str, int]) -> None:
    for key in _COUNTER_KEYS:
        target[key] += change[key]


def _directory_paths(file_path: str) -> list[str]:
    """Return every ancestor directory, including the repository root."""
    parent = PurePosixPath(file_path).parent
    if str(parent) == ".":
        return [""]

    directories = [""]
    current = PurePosixPath()
    for part in parent.parts:
        current /= part
        directories.append(current.as_posix())
    return directories


def _finalize(path: str | None, totals: Mapping[str, int], commit_count: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if path is not None:
        result["path"] = path
    result.update(totals)
    result["mod_frequency"] = totals["modifications"] / commit_count if commit_count else 0.0
    result["churn_rate"] = totals["churn"] / commit_count if commit_count else 0.0
    return result


def aggregate_metrics(
    commit_records: Iterable[
        tuple[str, str, Mapping[str, Mapping[str, int]]]
    ],
    commit_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Aggregate per-commit file changes into file, directory, and author metrics.

    Each commit record contains canonical author name, canonical author email, and
    a mapping of file path to the four core counters. The supplied changes may
    already be path-filtered; repository-root and author metrics then describe
    exactly that selected scope.
    """
    file_totals: dict[str, dict[str, int]] = defaultdict(_empty_totals)
    directory_totals: dict[str, dict[str, int]] = defaultdict(_empty_totals)
    author_totals: dict[tuple[str, str], dict[str, int]] = defaultdict(_empty_totals)

    # The root exists even when no selected commit contains a text-file change.
    directory_totals[""]

    for author_name, author_email, raw_changes in commit_records:
        author_key = (author_name, author_email)
        author_totals[author_key]
        commit_directories: dict[str, dict[str, int]] = defaultdict(_empty_totals)

        for path, change in raw_changes.items():
            _add_change(file_totals[path], change)
            if change["churn"] > 0:
                file_totals[path]["modifications"] += 1

            for directory in _directory_paths(path):
                _add_change(commit_directories[directory], change)

        for directory, change in commit_directories.items():
            _add_change(directory_totals[directory], change)
            if change["churn"] > 0:
                directory_totals[directory]["modifications"] += 1

        root_change = commit_directories.get("")
        if root_change and root_change["churn"] > 0:
            author_totals[author_key]["modifications"] += 1
        if root_change:
            _add_change(author_totals[author_key], root_change)

    files = [
        _finalize(path, totals, commit_count)
        for path, totals in sorted(file_totals.items())
    ]
    directories = [
        _finalize(path, totals, commit_count)
        for path, totals in sorted(directory_totals.items())
    ]
    summary = _finalize(None, directory_totals[""], commit_count)

    total_churn = summary["churn"]
    authors = []
    for (name, email), totals in sorted(
        author_totals.items(), key=lambda item: (item[0][0].casefold(), item[0][1].casefold())
    ):
        author_entry = _finalize(None, totals, commit_count)
        author_entry["name"] = name
        author_entry["email"] = email
        author_entry["ownership"] = totals["churn"] / total_churn if total_churn else 0.0
        authors.append(author_entry)

    return summary, files, directories, authors
