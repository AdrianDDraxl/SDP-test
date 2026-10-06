"""Manual integration test for the Git metrics engine using cJSON."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import GitAnalyzer

CJSON_URL = "https://github.com/DaveGamble/cJSON.git"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="rat-engine-") as temp_dir:
        repo_path = Path(temp_dir) / "cJSON"
        print(f"Cloning {CJSON_URL} ...", flush=True)
        subprocess.run(
            ["git", "clone", "--quiet", CJSON_URL, str(repo_path)],
            check=True,
        )

        analyzer = GitAnalyzer(str(repo_path))
        commits = analyzer.get_commits()
        authors = analyzer.get_authors()
        tree = analyzer.get_file_tree()
        metrics = analyzer.compute_metrics()

        assert commits, "expected at least one non-merge commit"
        assert authors, "expected at least one author"
        assert tree, "expected a non-empty HEAD tree"
        assert metrics.commits_used == len(commits)
        assert metrics.summary["churn"] == (
            metrics.summary["added_lines"] + metrics.summary["removed_lines"]
        )
        assert sum(author["churn"] for author in metrics.authors) == metrics.summary["churn"]

        print(
            json.dumps(
                {
                    "commits": len(commits),
                    "authors": len(authors),
                    "tree_entries": len(tree),
                    "files_with_changes": len(metrics.files),
                    "directories_with_changes": len(metrics.directories),
                    "summary": metrics.summary,
                },
                indent=2,
            )
        )
        print("cJSON engine verification passed.")


if __name__ == "__main__":
    main()
