"""Manual integration test for the Git metrics engine using cJSON."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import GitAnalyzer

CJSON_URL = "https://github.com/DaveGamble/cJSON.git"
CJSON_REFERENCE_SHA = "6d9f2443ab071f86e5d9b43025a40929ec41c46c"
REFERENCE_CSV = Path(__file__).resolve().parents[2] / "reference-data" / "cJSON_6d9f2443ab07.csv"


def load_expected_summary() -> dict[str, str]:
    """Load the repository-wide cJSON baseline supplied with the project."""
    with REFERENCE_CSV.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            if row["commit_set"] == "all" and row["object_type"] == "repository" and row["author"] == "ALL":
                return row
    raise AssertionError("cJSON repository summary is missing from the reference CSV")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="rat-engine-") as temp_dir:
        repo_path = Path(temp_dir) / "cJSON"
        print(f"Cloning {CJSON_URL} ...", flush=True)
        subprocess.run(
            ["git", "clone", "--quiet", CJSON_URL, str(repo_path)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "checkout", "--quiet", CJSON_REFERENCE_SHA],
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
        expected = load_expected_summary()
        assert len(commits) == int(expected["commit_count"])
        assert metrics.commits_used == len(commits)
        assert metrics.summary["added_lines"] == int(expected["added"])
        assert metrics.summary["removed_lines"] == int(expected["removed"])
        assert metrics.summary["growth"] == int(expected["growth"])
        assert metrics.summary["churn"] == int(expected["churn"])
        assert metrics.summary["modifications"] == int(expected["modifications"])
        assert abs(metrics.summary["mod_frequency"] - float(expected["modification_frequency"])) < 1e-12
        assert abs(metrics.summary["churn_rate"] - float(expected["churn_rate"])) < 1e-12
        assert len(metrics.timeline) == metrics.commits_used
        assert sum(point["churn"] for point in metrics.timeline) == metrics.summary["churn"]
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
