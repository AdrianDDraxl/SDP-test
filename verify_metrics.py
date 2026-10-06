#!/usr/bin/env python3
"""Verify RAT API output against reference CSVs (lecturer-provided)."""
import csv
import json
import sys
import urllib.request

API = "http://localhost:5000"
REPO_ID = sys.argv[1] if len(sys.argv) > 1 else "3b0ffa03-1d06-4f67-a3a1-44a249d9eca0"
CSV_PATH = sys.argv[2] if len(sys.argv) > 2 else "reference-data/cJSON_6d9f2443ab07.csv"

with urllib.request.urlopen(f"{API}/api/repos/{REPO_ID}/metrics", timeout=600) as resp:
    data = json.load(resp)

summary = data.get("summary", {})
files = {row["path"]: row for row in data.get("files", [])}
dirs = {row["path"]: row for row in data.get("directories", [])}
authors = {f'{a["name"]} <{a["email"]}>': a for a in data.get("authors", [])}

TOL = 1e-6
errors = []
checked = 0

def close(a, b):
    try:
        return abs(float(a) - float(b)) <= TOL
    except (TypeError, ValueError):
        return False

with open(CSV_PATH) as fh:
    for row in csv.DictReader(fh):
        if row.get("commit_set") != "all":
            continue
        otype = row["object_type"]
        author = row.get("author", "")
        path = row["path"]

        # ALL rows only (per-author rows checked separately for repository level)
        if author == "ALL":
            if otype == "repository":
                target = summary
            elif otype == "file":
                target = files.get(path)
            elif otype == "directory":
                if path == "/":
                    target = summary
                else:
                    target = dirs.get(path)
            else:
                continue
            if target is None:
                errors.append(f"MISSING {otype} {path!r}")
                continue
            for csv_key, api_key in [
                ("added", "added_lines"), ("removed", "removed_lines"),
                ("growth", "growth"), ("churn", "churn"),
                ("modifications", "modifications"),
                ("modification_frequency", "mod_frequency"),
                ("churn_rate", "churn_rate"),
            ]:
                checked += 1
                if not close(row[csv_key], target.get(api_key, 0)):
                    errors.append(
                        f"{otype} {path!r} {csv_key}: csv={row[csv_key]} api={target.get(api_key)}"
                    )
        elif otype == "repository":
            # per-author ownership rows at repository level
            target = authors.get(author)
            checked += 1
            if target is None:
                errors.append(f"MISSING author {author!r}")
                continue
            for csv_key, api_key in [("churn", "churn"), ("ownership", "ownership"),
                                     ("modifications", "modifications")]:
                checked += 1
                if not close(row[csv_key], target.get(api_key, 0)):
                    errors.append(
                        f"author {author!r} {csv_key}: csv={row[csv_key]} api={target.get(api_key)}"
                    )

print(f"Checked {checked} values against {CSV_PATH}")
print(f"commits_used={data.get('commits_used')} (csv commit_count={row['commit_count']})")
print(f"files in API={len(files)}, dirs={len(dirs)}, authors={len(authors)}, timeline={len(data.get('timeline', []))}")
if errors:
    print(f"\n!! {len(errors)} MISMATCHES (first 30):")
    for e in errors[:30]:
        print("  -", e)
else:
    print("\nALL VALUES MATCH")
