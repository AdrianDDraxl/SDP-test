# RAT - Repo Analysis Tool

A web-app dashboard for analysing the evolution of git repositories. RAT ingests a repository
either as a remote clone URL or as an uploaded ZIP (containing `.git`), then computes a suite of
**file, directory, repository, commit-set and author metrics** that can be explored and filtered
interactively.

Built for COMS3011A (SDP) by Adrian Draxl.

---

## Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+, and `git` on your PATH.

From the repository root:

```bash
./start.sh
```

This script will:

1. Install the backend Python dependencies (`pip install -r backend/requirements.txt`)
2. Install the frontend Node dependencies (`npm install`)
3. Start the Flask API on **http://localhost:5000**
4. Start the React dev server on **http://localhost:3000**

Then open **http://localhost:3000** in your browser. Press `Ctrl+C` in the terminal to stop both servers.

### Manual setup (alternative)

Run each of these in a separate terminal:

```bash
# Terminal 1 - backend
cd backend
pip install -r requirements.txt
python app.py            # serves http://localhost:5000

# Terminal 2 - frontend
cd frontend
npm install
npm run dev              # serves http://localhost:3000
```

> The frontend dev server proxies `/api/*` requests to the backend on port 5000, so no extra
> CORS/URL configuration is needed.

---

## Using RAT

### 1. Add a repository (Home page)

- **Clone URL** - paste a public git URL (e.g. `https://github.com/DaveGamble/cJSON.git`) and
  press Clone. The backend performs a full clone.
- **Upload ZIP** - upload a zip of a repository that contains its `.git` directory.

Multiple repositories are supported; each is stored server-side and listed on the home page.
Metrics are computed lazily on first request and cached.

### 2. Explore the dashboard

Open a repository to see its dashboard, containing:

- **Summary cards** - added lines, removed lines, growth, churn, plus repository-level
  modification frequency and churn rate.
- **Charts** - churn over time, top files by churn, directory breakdown, author ownership
  (pie), and growth over time.
- **Tables** - sortable per-file, per-directory and per-author metric tables.

### 3. Filters

The dashboard can be filtered by:

- **Repository** (via the repository selector)
- **Author** (multi-select)
- **File or directory** (path filter, with autocomplete)
- **Commit set** - either a time period (from/to date) or a manually selected list of commits

### 4. Author merging

Open **Authors** for a repository to merge author identities:

- RAT automatically applies the repo's `.mailmap` when present.
- Authors with different names/emails can be merged manually via the UI (groups of
  `{name, email}` entries). Merged authors are treated as a single author in all metrics.

---

## Metrics Implemented

| Category | Metrics |
|---|---|
| **File** (per commit and over a commit set) | added lines, removed lines, growth, churn, modifications, modification frequency, churn rate |
| **Directory** (recursive over immediate children) | added lines, removed lines, growth, churn, modifications, modification frequency, churn rate |
| **Repository** | directory metrics evaluated at the repository root |
| **Commit set** | sums over a filtered set of commits: added/removed/growth/churn, modifications, modification frequency, churn rate |
| **Author** (per file/directory) | author modifications, author churn, author ownership |

Notes on the computation:

- Only **non-merge commits** reachable from the reference commit are considered.
- Rename detection is enabled at a **50% threshold** (`-M50%`), so a pure rename does not change
  an object's metrics; deleted files are recorded as line removals on their old path.
- **Binary files are excluded** (git's numstat reports `-`).
- Commit sets can be the full history, a time window (`from` inclusive, `to` exclusive), or a
  manually selected list of commit hashes.

### Validation

`reference-data/` contains expected metric values provided for the three test repositories
(cJSON, Redis, git) at specific reference SHAs. These can be used to verify the engine's output:

```bash
curl "http://localhost:5000/api/repos/<repo-id>/metrics"
```

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/repos/clone` | Clone a remote repository (`{"url": "..."}`) |
| `POST` | `/api/repos/upload` | Upload a repository ZIP (multipart) |
| `GET` | `/api/repos` | List stored repositories |
| `DELETE` | `/api/repos/<id>` | Delete a repository |
| `GET` | `/api/repos/<id>/commits` | List commits (`?from=<ts>&to=<ts>`) |
| `GET` | `/api/repos/<id>/authors` | List authors |
| `GET` | `/api/repos/<id>/tree` | File/directory tree (`?commit=<sha>`) |
| `GET` | `/api/repos/<id>/metrics` | Full metrics (`?path=&author=&from=&to=&commits=`) |
| `GET` | `/api/repos/<id>/author-groups` | Get author merge groups |
| `POST` | `/api/repos/<id>/author-groups` | Set author merge groups |

Repositories are stored under `/tmp/rat_repos/` by default (configurable via the
`RAT_REPO_STORAGE` environment variable).

---

## Project Structure

```
├── start.sh                  # One-command startup
├── backend/
│   ├── app.py                # Flask entry point (port 5000)
│   ├── config.py             # Configuration
│   ├── engine/               # Git metrics engine (GitAnalyzer)
│   ├── routes/               # REST endpoints (repos, metrics)
│   └── services/             # Repository clone/upload/storage
├── frontend/
│   └── src/
│       ├── pages/            # Home, Dashboard, Author Merge
│       ├── components/       # Charts, tables, filters, layout
│       └── services/api.ts   # API client
└── reference-data/           # Expected metrics for validation repos
```

---

## Troubleshooting

- **Port already in use** - stop whatever is on ports 3000/5000, or change the port in
  `frontend/vite.config.ts` (proxy target in `backend/app.py` uses 5000).
- **`pip` installation blocked (externally managed environment)** - create a virtualenv
  (`python3 -m venv .venv && source .venv/bin/activate`) before installing requirements.
- **Cloning large repositories** - the git clone timeout defaults to 600s and can be raised
  with the `RAT_GIT_CLONE_TIMEOUT` environment variable. Large repos (e.g. the Linux-adjacent
  git repo, ~60k commits) take a while to analyse on first load; results are cached afterwards.
