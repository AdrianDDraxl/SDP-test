"""Git repository analyzer and public engine API."""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from .author_merge import AuthorMerger
from .metrics import aggregate_metrics
from .models import AuthorInfo, CommitInfo, MetricsResult, TreeEntry

EMPTY_TREE_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_HASH_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")


class GitAnalyzer:
    """Analyze non-merge commits and text-file changes in a Git repository."""

    def __init__(self, repo_path: str):
        """Initialize with a path to a non-bare Git repository."""
        path = Path(repo_path).expanduser().resolve()
        if not path.is_dir() or not (path / ".git").exists():
            raise ValueError(f"not a Git repository with a .git directory: {path}")

        try:
            self.repo = Repo(path, search_parent_directories=False)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError(f"invalid Git repository: {path}") from exc
        if self.repo.bare:
            raise ValueError("bare repositories are not supported")

        self.repo_path = path
        self._author_merger = AuthorMerger(path)
        self._raw_commits: list[CommitInfo] | None = None
        self._parent_cache: dict[str, str] = {}
        self._diff_cache: dict[str, dict[str, dict[str, int]]] = {}
        self._empty_tree_ready = False

    def _run_git(
        self, *args: str, allow_failure: bool = False, input_data: str | None = None
    ) -> str:
        process = subprocess.run(
            ["git", "-C", str(self.repo_path), *args],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="surrogateescape",
            check=False,
        )
        if process.returncode and not allow_failure:
            message = process.stderr.strip() or "unknown Git error"
            raise RuntimeError(f"git {' '.join(args)} failed: {message}")
        return process.stdout

    def _load_raw_commits(self) -> list[CommitInfo]:
        if self._raw_commits is not None:
            return self._raw_commits

        if not self._run_git("rev-parse", "--verify", "HEAD", allow_failure=True).strip():
            self._raw_commits = []
            return self._raw_commits

        output = self._run_git(
            "log",
            "--no-merges",
            "--format=%H%x00%an%x00%ae%x00%ct%x00%P%x00%s%x1e",
            "HEAD",
        )
        commits: list[CommitInfo] = []
        for record in output.split("\x1e"):
            record = record.strip("\r\n")
            if not record:
                continue
            fields = record.split("\x00", 5)
            if len(fields) != 6:
                continue
            commit_hash, name, email, timestamp, parents, message = fields
            commits.append(
                CommitInfo(
                    hash=commit_hash,
                    author_name=name,
                    author_email=email,
                    date=int(timestamp),
                    message=message,
                )
            )
            parent_list = parents.split()
            self._parent_cache[commit_hash] = parent_list[0] if parent_list else EMPTY_TREE_HASH

        self._raw_commits = commits
        return commits

    def _resolve_requested_hashes(
        self, commit_hashes: Iterable[str] | None, commits: list[CommitInfo]
    ) -> set[str] | None:
        if commit_hashes is None:
            return None
        if isinstance(commit_hashes, (str, bytes)):
            raise ValueError("commit_hashes must be an iterable of hashes")

        all_hashes = [commit.hash for commit in commits]
        requested: set[str] = set()
        for value in commit_hashes:
            if not isinstance(value, str) or not _HASH_RE.fullmatch(value.strip()):
                raise ValueError(f"invalid commit hash: {value!r}")
            prefix = value.strip().casefold()
            matches = [commit_hash for commit_hash in all_hashes if commit_hash.startswith(prefix)]
            if not matches:
                raise ValueError(f"commit is not a non-merge ancestor of HEAD: {value}")
            if len(matches) > 1:
                raise ValueError(f"ambiguous commit hash: {value}")
            requested.add(matches[0])
        return requested

    def _select_raw_commits(
        self,
        from_ts: int | float | str | None = None,
        to_ts: int | float | str | None = None,
        commit_hashes: Iterable[str] | None = None,
    ) -> list[CommitInfo]:
        commits = self._load_raw_commits()
        requested = self._resolve_requested_hashes(commit_hashes, commits)
        try:
            lower = int(from_ts) if from_ts is not None else None
            upper = int(to_ts) if to_ts is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("from_ts and to_ts must be Unix timestamps") from exc

        return [
            commit
            for commit in commits
            if (requested is None or commit.hash in requested)
            and (lower is None or commit.date >= lower)
            and (upper is None or commit.date < upper)
        ]

    def get_commits(
        self, from_ts=None, to_ts=None, commit_hashes=None
    ) -> list[CommitInfo]:
        """Get canonicalized non-merge commits with optional filters."""
        results = []
        for commit in self._select_raw_commits(from_ts, to_ts, commit_hashes):
            name, email = self._author_merger.resolve(
                commit.author_name, commit.author_email
            )
            results.append(
                CommitInfo(
                    hash=commit.hash,
                    author_name=name,
                    author_email=email,
                    date=commit.date,
                    message=commit.message,
                )
            )
        return results

    def get_authors(self) -> list[AuthorInfo]:
        """Get canonical authors and their non-merge commit counts."""
        counts: Counter[tuple[str, str]] = Counter()
        for commit in self._load_raw_commits():
            counts[self._author_merger.resolve(commit.author_name, commit.author_email)] += 1
        return [
            AuthorInfo(name=name, email=email, commit_count=count)
            for (name, email), count in sorted(
                counts.items(),
                key=lambda item: (item[0][0].casefold(), item[0][1].casefold()),
            )
        ]

    def _resolve_tree_commit(self, commit_hash: str | None) -> str | None:
        if commit_hash is None:
            resolved = self._run_git(
                "rev-parse", "--verify", "HEAD", allow_failure=True
            ).strip()
            return resolved or None
        if not isinstance(commit_hash, str) or not _HASH_RE.fullmatch(commit_hash.strip()):
            raise ValueError("commit_hash must be a hexadecimal commit hash")
        resolved = self._run_git(
            "rev-parse", "--verify", f"{commit_hash.strip()}^{{commit}}", allow_failure=True
        ).strip()
        if not resolved:
            raise ValueError(f"unknown commit: {commit_hash}")
        return resolved

    def get_file_tree(self, commit_hash=None) -> list[TreeEntry]:
        """Get all file and directory entries at a commit (default HEAD)."""
        resolved = self._resolve_tree_commit(commit_hash)
        if resolved is None:
            return []

        output = self._run_git("ls-tree", "-r", "-t", "--full-tree", "-z", resolved)
        entries: list[TreeEntry] = []
        for raw_entry in output.split("\x00"):
            if not raw_entry or "\t" not in raw_entry:
                continue
            metadata, path = raw_entry.split("\t", 1)
            fields = metadata.split()
            if len(fields) < 2:
                continue
            entries.append(TreeEntry(path=path, type="dir" if fields[1] == "tree" else "file"))
        return entries

    @staticmethod
    def _parse_numstat(output: str) -> dict[str, dict[str, int]]:
        changes: dict[str, dict[str, int]] = {}
        tokens = output.split("\x00")
        index = 0
        while index < len(tokens):
            token = tokens[index]
            index += 1
            if not token:
                continue
            fields = token.split("\t", 2)
            if len(fields) != 3:
                continue
            added, removed, path = fields
            if path == "":
                # With -z, rename records store old and new paths separately.
                if index + 1 >= len(tokens):
                    break
                index += 1  # The old path is intentionally not attributed.
                path = tokens[index]
                index += 1
            if added == "-" or removed == "-":
                continue
            try:
                added_lines, removed_lines = int(added), int(removed)
            except ValueError:
                continue
            current = changes.setdefault(
                path,
                {"added_lines": 0, "removed_lines": 0, "growth": 0, "churn": 0},
            )
            current["added_lines"] += added_lines
            current["removed_lines"] += removed_lines
            current["growth"] += added_lines - removed_lines
            current["churn"] += added_lines + removed_lines
        return changes

    def _get_diff(self, commit_hash: str) -> dict[str, dict[str, int]]:
        cached = self._diff_cache.get(commit_hash)
        if cached is not None:
            return cached

        parent = self._parent_cache.get(commit_hash)
        if parent is None:
            parent_line = self._run_git("rev-list", "--parents", "-n", "1", commit_hash).split()
            parent = parent_line[1] if len(parent_line) > 1 else EMPTY_TREE_HASH
            self._parent_cache[commit_hash] = parent

        if parent == EMPTY_TREE_HASH and not self._empty_tree_ready:
            created_hash = self._run_git(
                "hash-object", "-w", "-t", "tree", "--stdin", input_data=""
            ).strip()
            if created_hash != EMPTY_TREE_HASH:
                raise RuntimeError("Git returned an unexpected empty tree hash")
            self._empty_tree_ready = True

        output = self._run_git(
            "diff",
            "--numstat",
            "-z",
            "-M50%",
            parent,
            commit_hash,
            "--",
        )
        changes = self._parse_numstat(output)
        self._diff_cache[commit_hash] = changes
        return changes

    @staticmethod
    def _normalize_filter_path(path: str | None) -> str | None:
        if path is None:
            return None
        if not isinstance(path, str):
            raise ValueError("path must be a string")
        normalized = path.replace("\\", "/").strip("/")
        if normalized in ("", "."):
            return None
        pure_path = PurePosixPath(normalized)
        if ".." in pure_path.parts:
            raise ValueError("path cannot contain '..'")
        return pure_path.as_posix()

    @staticmethod
    def _filter_changes(
        changes: Mapping[str, Mapping[str, int]], selected_path: str | None
    ) -> dict[str, Mapping[str, int]]:
        if selected_path is None:
            return dict(changes)
        prefix = f"{selected_path}/"
        return {
            path: change
            for path, change in changes.items()
            if path == selected_path or path.startswith(prefix)
        }

    def compute_metrics(
        self,
        path=None,
        author=None,
        from_ts=None,
        to_ts=None,
        commit_hashes=None,
    ) -> MetricsResult:
        """Compute metrics for commits selected by path, author, time, or hash."""
        selected_path = self._normalize_filter_path(path)
        commits = self._select_raw_commits(from_ts, to_ts, commit_hashes)

        if author is not None:
            if isinstance(author, str):
                requested_authors = [author]
            elif isinstance(author, (list, tuple, set)):
                requested_authors = list(author)
            else:
                raise ValueError("author must be a name or email string, or a list of them")
            if not all(isinstance(value, str) for value in requested_authors):
                raise ValueError("author entries must be name or email strings")
            author_filters = {
                value.strip().casefold() for value in requested_authors if value.strip()
            }
            commits = [
                commit
                for commit in commits
                if author_filters
                & {
                    value.casefold()
                    for value in self._author_merger.resolve(
                        commit.author_name, commit.author_email
                    )
                }
            ]

        records = []
        timeline = []
        for commit in commits:
            name, email = self._author_merger.resolve(
                commit.author_name, commit.author_email
            )
            changes = self._filter_changes(
                self._get_diff(commit.hash), selected_path
            )
            records.append((name, email, changes))
            timeline.append(
                {
                    "hash": commit.hash,
                    "date": commit.date,
                    "added_lines": sum(change["added_lines"] for change in changes.values()),
                    "removed_lines": sum(change["removed_lines"] for change in changes.values()),
                    "growth": sum(change["growth"] for change in changes.values()),
                    "churn": sum(change["churn"] for change in changes.values()),
                }
            )

        timeline.sort(key=lambda point: (point["date"], point["hash"]))
        summary, files, directories, authors = aggregate_metrics(records, len(commits))
        return MetricsResult(
            summary=summary,
            files=files,
            directories=directories,
            authors=authors,
            timeline=timeline,
            commits_used=len(commits),
        )

    def set_author_groups(self, groups: list[list[dict]]) -> None:
        """Set manual author merge groups."""
        self._author_merger.set_groups(groups)

    def get_author_groups(self) -> list[list[dict]]:
        """Get a defensive copy of the manual author merge groups."""
        return self._author_merger.get_groups()
