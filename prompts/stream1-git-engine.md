We are building a Git Repo Analysis Tool (RAT). Your job is to implement ONLY the Python git metrics engine module at `/backend/engine/`. Do NOT create any Flask server code - another team handles that.

The workspace is at /home/vmuser/Desktop/SDP-test (already scaffolded).
Read /home/vmuser/Desktop/SDP-test/PLAN.md for the full project plan.
You ONLY create/edit files under `/backend/engine/`.

## What to build

A Python module that analyzes a git repository and computes metrics per the spec below.
It must expose a main class `GitAnalyzer` that is initialized with a repo path.

### File structure:
- `__init__.py` - exports GitAnalyzer
- `analyzer.py` - Main GitAnalyzer class
- `metrics.py` - Metric computation/aggregation functions
- `author_merge.py` - Mailmap parsing + manual author merge logic
- `models.py` - Dataclasses for results

### GitAnalyzer class interface:

```python
class GitAnalyzer:
    def __init__(self, repo_path: str):
        """Initialize with path to a git repo (must have .git)"""

    def get_commits(self, from_ts=None, to_ts=None, commit_hashes=None) -> list[CommitInfo]:
        """Get non-merge commits, optionally filtered by time range or specific hashes"""

    def get_authors(self) -> list[AuthorInfo]:
        """Get all unique authors (after merging)"""

    def get_file_tree(self, commit_hash=None) -> list[TreeEntry]:
        """Get file/directory tree at a commit (default HEAD)"""

    def compute_metrics(self, path=None, author=None, from_ts=None, to_ts=None,
                        commit_hashes=None) -> MetricsResult:
        """Compute all metrics with optional filters. This is the main method."""

    def set_author_groups(self, groups: list[list[dict]]):
        """Manually merge authors. groups is list of lists of {name, email}"""

    def get_author_groups(self) -> list[list[dict]]:
        """Get current author merge groups"""
```

### Metric Definitions (MUST be exact):

**Core per-commit per-file data:**
Use `git diff --numstat -M50% <parent>..<commit>` for each non-merge commit.
- For the initial commit, use empty tree hash `4b825dc642cb6eb9a060e54bf899d4e56d88bb47` as parent.
- Binary files show `-` in numstat output - EXCLUDE these.
- Rename detection is enabled at 50% threshold (-M50%).
- Only process non-merge commits (`git rev-list --no-merges HEAD`).

**File Metrics (per commit h, per file f):**
- added_lines (l+): lines added
- removed_lines (l-): lines removed
- growth (delta): l+ - l-
- churn (lambda): l+ + l-

**Directory Metrics (per commit h, per directory d):**
Recursive sum of ALL immediate children (files + subdirectories):
- dir_added = sum(file_added for files in d) + sum(subdir_added for subdirs in d)
- Same for removed, growth, churn
- A file f is in directory d if it is an IMMEDIATE child of d.
- Repository metrics = directory metrics on root directory "".

**Commit Set Metrics (over set H of commits, per file/dir o):**
- added_lines_H = sum over h in H of added_lines(h, o)
- removed_lines_H = sum over h in H
- growth_H = sum over h in H
- churn_H = sum over h in H
- modifications_H = count of commits in H where churn(h, o) > 0
- mod_frequency_H = modifications_H / |H| (or 0 if |H|=0)
- churn_rate_H = churn_H / |H| (or 0 if |H|=0)

**Author Metrics (over set H, per file/dir o, per author a):**
- author_modifications = count of commits in H where author=a AND churn(h,o)>0
- author_churn = sum of churn(h,o) for commits in H where author=a
- author_ownership = author_churn / total_churn (or 0 if total_churn=0)

**Author Merging:**
1. Parse .mailmap file if present in repo root (standard git mailmap format)
2. Support manual merge: groups of {name, email} that should be treated as same author
3. After merging, use the first entry in each group as canonical name/email

**MetricsResult dataclass:**

```python
@dataclass
class MetricsResult:
    summary: dict        # {added_lines, removed_lines, growth, churn, modifications, mod_frequency, churn_rate}
    files: list[dict]    # [{path, added_lines, removed_lines, growth, churn, modifications, mod_frequency, churn_rate}]
    directories: list[dict]  # same fields as files
    authors: list[dict]  # [{name, email, modifications, churn, ownership}]
    commits_used: int    # |H|
```

### Performance requirements:
- Must handle cJSON (~700 commits), Redis (~15000 commits), Git (~80000 commits)
- Cache raw per-commit diff data after first computation
- Use subprocess calls to git CLI for speed (GitPython's porcelain commands can be slow)
- For large repos, consider batching git operations

### Dependencies:
- gitpython (for repo object access)
- subprocess (for fast git CLI calls)
- Standard library only otherwise

Create a test script at `/backend/engine/test_engine.py` that clones cJSON (https://github.com/DaveGamble/cJSON.git) to a temp dir and runs basic metric computations to verify correctness. Print results.

IMPORTANT: Make sure the engine handles edge cases:
- Initial commit (no parent)
- Deleted files
- Renamed files (rename detection -M50%)
- Empty commits
- Binary files (skip them)
- Repos with no .mailmap
