#!/usr/bin/env python3
"""Invariant tests for date-range and manual-commit filters."""
import json
import urllib.parse
import urllib.request

API = "http://localhost:5000"
REPO = "3b0ffa03-1d06-4f67-a3a1-44a249d9eca0"


def get(path):
    with urllib.request.urlopen(API + path, timeout=600) as r:
        return json.load(r)


full = get(f"/api/repos/{REPO}/metrics")
total_added = full["summary"]["added_lines"]
total_churn = full["summary"]["churn"]
timeline = sorted(full["timeline"], key=lambda p: (p["date"], p["hash"]))
print(f"full: commits={full['commits_used']} added={total_added} churn={total_churn}")

# --- date range invariant: split at median commit date ---
mid = timeline[len(timeline) // 2]["date"]
before = get(f"/api/repos/{REPO}/metrics?from=0&to={mid}")
after = get(f"/api/repos/{REPO}/metrics?from={mid}")
b, a = before["summary"], after["summary"]
print(f"\nDATE RANGE split at t={mid}:")
print(f"  before: commits={before['commits_used']} added={b['added_lines']} churn={b['churn']}")
print(f"  after : commits={after['commits_used']} added={a['added_lines']} churn={a['churn']}")
print(f"  commits sum ok: {before['commits_used'] + after['commits_used'] == full['commits_used']}")
print(f"  added sum ok:   {b['added_lines'] + a['added_lines'] == total_added}")
print(f"  churn sum ok:   {b['churn'] + a['churn'] == total_churn}")

# --- manual commit selection: pick 3 commits, verify sums against timeline ---
picks = [timeline[100], timeline[400], timeline[700]]
hashes = ",".join(p["hash"] for p in picks)
sel = get(f"/api/repos/{REPO}/metrics?commits={urllib.parse.quote(hashes)}")
exp_added = sum(p["added_lines"] for p in picks)
exp_churn = sum(p["churn"] for p in picks)
s = sel["summary"]
print(f"\nMANUAL SELECT {len(picks)} commits: commits_used={sel['commits_used']} (expect 3)")
print(f"  added: got={s['added_lines']} expect={exp_added} ok={s['added_lines'] == exp_added}")
print(f"  churn: got={s['churn']} expect={exp_churn} ok={s['churn'] == exp_churn}")
print(f"  mod_frequency: {s['mod_frequency']} (expect <= 1)")
print(f"  timeline len: {len(sel.get('timeline', []))} (expect 3)")
