"""Verify multi-author filtering and persisted author merges against a running RAT backend.

Usage:
  python3 verify_multi_author.py pre    # reset merges, run filter + merge checks, dump expectations
  python3 verify_multi_author.py post   # run AFTER a backend restart; verifies persistence
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = "3b0ffa03-1d06-4f67-a3a1-44a249d9eca0"
BASE = f"http://localhost:5000/api/repos/{REPO}"
EXPECTED_FILE = "/tmp/rat_expected_after_restart.json"

MERGED_IDENTITIES = [
    ("Alanscut", "wp_scut@163.com"),
    ("Alan Wang", "wp_scut@163.com"),
    ("Alanscut", "948467222@qq.com"),
]


def get(url):
    with urllib.request.urlopen(url, timeout=600) as r:
        return json.load(r)


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def metrics(*authors):
    return get(f"{BASE}/metrics?author={urllib.parse.quote(','.join(authors))}")


def run_pre():
    fails = []

    # 1) single-author regression (known exact values)
    a = metrics("max@maxbruckner.de")
    print("single author:", a["commits_used"], a["summary"]["added_lines"], a["summary"]["churn"])
    if a["commits_used"] != 634 or a["summary"]["added_lines"] != 39192 or a["summary"]["churn"] != 48192:
        fails.append("single-author regression")

    # 2) multi-author union must equal the sum of disjoint single-author filters
    A, B = "max@maxbruckner.de", "wp_scut@163.com"
    ma, mb, mab = metrics(A), metrics(B), metrics(A, B)
    print("A:", ma["commits_used"], "B:", mb["commits_used"], "A+B:", mab["commits_used"])
    if mab["commits_used"] != ma["commits_used"] + mb["commits_used"]:
        fails.append("multi commits not additive")
    for k in ("added_lines", "removed_lines", "growth", "churn", "modifications"):
        expected = ma["summary"][k] + mb["summary"][k]
        got = mab["summary"][k]
        if abs(expected - got) > 1e-6:
            fails.append(f"multi {k}: expected {expected} got {got}")
    if len(mab["files"]) < max(len(ma["files"]), len(mb["files"])):
        fails.append("multi files union smaller than single")
    print("A+B added:", mab["summary"]["added_lines"], "churn:", mab["summary"]["churn"])

    # 3) reset merges, then compute expectations from raw per-identity author rows
    post(f"{BASE}/author-groups", {"groups": []})
    rows = get(f"{BASE}/authors")
    by_identity = {(row["name"], row["email"]): row for row in rows}
    exp_commits = 0
    exp_churn = None
    for identity in MERGED_IDENTITIES:
        row = by_identity.get(identity)
        if row is None:
            fails.append(f"identity missing from /authors: {identity}")
            continue
        print("identity", identity, "commits:", row.get("commit_count"), "churn:", row.get("churn"))
        exp_commits += row.get("commit_count", 0)
        if exp_churn is not None or "churn" in row:
            exp_churn = (exp_churn or 0) + row.get("churn", 0)

    # 4) merge the wp_scut group and verify consolidation against expectations
    groups = [[{"name": "Alanscut", "email": "wp_scut@163.com"},
               {"name": "Alan Wang", "email": "wp_scut@163.com"}]]
    post(f"{BASE}/author-groups", {"groups": groups})
    saved = get(f"{BASE}/author-groups")["groups"]
    print("saved groups roundtrip match:", saved == groups)
    if saved != groups:
        fails.append("group roundtrip")

    merged = metrics("Alanscut")
    got_commits = merged["commits_used"]
    got_churn = merged["summary"]["churn"]
    print(f"merged Alanscut: commits={got_commits} (expected {exp_commits}), churn={got_churn} (expected {exp_churn})")
    if got_commits != exp_commits:
        fails.append(f"merged commits: expected {exp_commits} got {got_commits}")
    if exp_churn is not None and abs(got_churn - exp_churn) > 1e-6:
        fails.append(f"merged churn: expected {exp_churn} got {got_churn}")

    # 5) blank author list must be rejected
    try:
        get(f"{BASE}/metrics?author=%20,%20")
        fails.append("blank author list should 400")
    except urllib.error.HTTPError as e:
        print("blank authors ->", e.code)
        if e.code != 400:
            fails.append("blank author wrong status")

    with open(EXPECTED_FILE, "w") as fh:
        json.dump({"groups": groups, "commits": got_commits, "churn": got_churn}, fh)
    print("phase pre FAILS:", fails if fails else "none")
    return not fails


def run_post():
    fails = []
    with open(EXPECTED_FILE) as fh:
        expected = json.load(fh)

    saved = get(f"{BASE}/author-groups")["groups"]
    print("persisted groups after restart match:", saved == expected["groups"])
    if saved != expected["groups"]:
        fails.append("groups not persisted across restart")

    merged = metrics("Alanscut")
    print("merged after restart: commits", merged["commits_used"], "churn", merged["summary"]["churn"])
    if merged["commits_used"] != expected["commits"]:
        fails.append("merged commits changed after restart")
    if abs(merged["summary"]["churn"] - expected["churn"]) > 1e-6:
        fails.append("merged churn changed after restart")

    print("phase post FAILS:", fails if fails else "none")
    return not fails


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "pre"
    ok = run_pre() if phase == "pre" else run_post()
    sys.exit(0 if ok else 1)
