# RAT (Repo Analysis Tool) - Parallel Build Plan

## Architecture Overview

- **Frontend**: React + Vite + TypeScript + Tailwind CSS + Recharts
- **Backend**: Python 3 + Flask + GitPython
- **Structure**: Monorepo with `/frontend/` and `/backend/` directories
- **Repo**: `https://github.com/AdrianDDraxl/SDP-test.git`

```
/
├── backend/
│   ├── engine/           # Stream 1 owns this
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── metrics.py
│   │   └── author_merge.py
│   ├── app.py            # Stream 2 owns this
│   ├── config.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── repos.py
│   │   └── metrics.py
│   └── services/
│       └── repo_manager.py
├── frontend/             # Stream 3 owns this
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   ├── components/
│   │   └── services/
│   ├── package.json
│   └── vite.config.ts
├── start.sh              # Stream 4 creates
└── README.md             # Stream 4 creates
```

---

## Shared API Contract (give to ALL streams)

All streams must develop against this exact API contract:

```
# Repository Management
POST   /api/repos/clone          Body: {url: string}              -> {id, name, url, status}
POST   /api/repos/upload         Multipart: file (zip)            -> {id, name, status}
GET    /api/repos                                                  -> [{id, name, url, created_at}]
DELETE /api/repos/<id>                                             -> {ok: true}

# Data Queries
GET /api/repos/<id>/commits     ?from=unix_ts&to=unix_ts          -> [{hash, author_name, author_email, date, message}]
GET /api/repos/<id>/authors                                        -> [{name, email, commit_count}]
GET /api/repos/<id>/tree        ?commit=hash                      -> [{path, type: "file"|"dir"}]

# Metrics (the main endpoint)
GET /api/repos/<id>/metrics     ?path=string                      -> {
                                 &author=email                        summary: {added_lines, removed_lines, growth, churn,
                                 &from=unix_ts                                  modifications, mod_frequency, churn_rate},
                                 &to=unix_ts                          files: [{path, added_lines, removed_lines, growth,
                                 &commits=hash1,hash2,...                       churn, modifications, mod_frequency, churn_rate}],
                                                                      directories: [{path, ...same fields}],
                                                                      authors: [{name, email, modifications, churn, ownership}],
                                                                      commits_used: int
                                                                   }

# Author Merging
GET  /api/repos/<id>/author-groups                                 -> {groups: [[{name, email}]]}
POST /api/repos/<id>/author-groups   Body: {groups: [[{name,email}]]} -> {ok: true}
```

---

## PHASE 0: Scaffold (This Conversation)

Before launching the 3 parallel streams, set up the shared project skeleton so every conversation starts from a consistent base.

### Steps:
1. **Copy this plan** into the project root at `/PLAN.md` so all conversations can reference it
2. **Create backend directory structure** with placeholder `__init__.py` files:
   - `/backend/engine/__init__.py`
   - `/backend/routes/__init__.py`
   - `/backend/services/__init__.py`
3. **Create `/backend/requirements.txt`** with shared dependencies (flask, flask-cors, gitpython, gunicorn)
4. **Initialize frontend** with Vite + React + TypeScript:
   - `npm create vite@latest frontend -- --template react-ts`
5. **Install frontend dependencies**: tailwindcss, postcss, autoprefixer, react-router-dom, recharts, axios, lucide-react
6. **Configure Tailwind** (tailwind.config.js, postcss.config.js, update index.css with directives)
7. **Configure Vite proxy** in `vite.config.ts` to forward `/api` to `http://localhost:5000`
8. **Commit the scaffold** so all parallel conversations can pull it

### After scaffold, each parallel Qoder conversation will:
- `git pull` to get the scaffold
- Implement ONLY their assigned files (no overlap)
- `git commit && git push` when done

---

## PHASE 1: Parallel Implementation (3 Conversations)

### Stream 1: Backend Git Metrics Engine

**Files owned**: ONLY `/backend/engine/` directory

**Prompt for Qoder conversation:**

```
We are building a Git Repo Analysis Tool (RAT). Your job is to implement ONLY the 
Python git metrics engine module at `/backend/engine/`. Do NOT create any Flask 
server code - another team handles that.

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

Create a test script at `/backend/engine/test_engine.py` that clones cJSON 
(https://github.com/DaveGamble/cJSON.git) to a temp dir and runs basic metric 
computations to verify correctness. Print results.

IMPORTANT: Make sure the engine handles edge cases:
- Initial commit (no parent)
- Deleted files
- Renamed files (rename detection -M50%)
- Empty commits
- Binary files (skip them)
- Repos with no .mailmap
```

---

### Stream 2: Backend Flask API Server

**Files owned**: `/backend/` root files + `/backend/routes/` + `/backend/services/` (NOT `/backend/engine/`)

**Prompt for Qoder conversation:**

```
We are building a Git Repo Analysis Tool (RAT). Your job is to implement ONLY the 
Flask API server. Another team is building the git engine at `/backend/engine/` and 
the React frontend at `/frontend/`.

The workspace is at /home/vmuser/Desktop/SDP-test (already scaffolded).
Read /home/vmuser/Desktop/SDP-test/PLAN.md for the full project plan.
You ONLY create/edit files in `/backend/` root, `/backend/routes/`, and `/backend/services/`. Do NOT touch `/backend/engine/`.

## What to build

A Flask REST API server. The engine module at `/backend/engine/` is being built 
separately - create STUB imports for it and use mock/placeholder data so the API 
is fully testable standalone.

### File structure (create ALL of these):
- `/backend/app.py` - Flask app entry point, CORS, error handlers
- `/backend/config.py` - Configuration (upload folder, repo storage path, etc.)
- `/backend/requirements.txt` - All Python dependencies
- `/backend/routes/__init__.py` - Blueprint registration
- `/backend/routes/repos.py` - Repository management endpoints  
- `/backend/routes/metrics.py` - Metrics query endpoints
- `/backend/services/__init__.py`
- `/backend/services/repo_manager.py` - Handles cloning, zip extraction, repo storage

### API Endpoints (implement ALL):

**Repository Management:**
- `POST /api/repos/clone` - Body: `{url: "https://..."}`. Clones repo to storage dir. Returns `{id, name, url, status}`.
- `POST /api/repos/upload` - Multipart file upload (zip). Extracts to storage dir. Returns `{id, name, status}`.
- `GET /api/repos` - List all repos. Returns `[{id, name, url, created_at}]`.
- `DELETE /api/repos/<id>` - Delete repo from storage.

**Data Queries:**
- `GET /api/repos/<id>/commits` - Query params: `from` (unix timestamp), `to` (unix timestamp). Returns commit list.
- `GET /api/repos/<id>/authors` - Returns author list.
- `GET /api/repos/<id>/tree` - Query param: `commit` (hash). Returns file tree.

**Metrics:**
- `GET /api/repos/<id>/metrics` - Query params: `path`, `author`, `from`, `to`, `commits` (comma-separated hashes). Returns full metrics response.

**Author Merging:**
- `GET /api/repos/<id>/author-groups` - Get current author merge groups.
- `POST /api/repos/<id>/author-groups` - Body: `{groups: [[{name, email}]]}`. Set merge groups.

### Implementation details:

**Repo Storage:**
- Store repos in `/tmp/rat_repos/` directory
- Each repo gets a UUID as its id
- Store repo metadata in a JSON file at `/tmp/rat_repos/metadata.json`
- Format: `{id: {name, url, path, created_at}}`

**Clone endpoint:**
- Use `git clone --bare` or regular clone to storage path
- Run in background if possible, return status "cloning" immediately, 
  or just do synchronous clone for simplicity
- Actually, do SYNCHRONOUS clone for simplicity. The test repos are not huge.

**Upload endpoint:**
- Accept zip file via multipart form
- Extract to storage dir
- Verify it contains a .git directory
- Use `werkzeug` or `flask` built-in file handling

**Engine Integration (STUB for now):**
In each metrics/data endpoint, import from the engine module like this:
```python
from engine.analyzer import GitAnalyzer
# Create analyzer
analyzer = GitAnalyzer(repo_path)
# Call methods
result = analyzer.compute_metrics(path=path, author=author, from_ts=from_ts, to_ts=to_ts, commit_hashes=commits)
```
This will be wired up during integration. For now, the code should be 
structured to call these methods. If the import fails, that's OK - 
another conversation will wire it up.

**CORS:** Enable CORS for all routes (frontend runs on different port).

**Error Handling:**
- Return proper HTTP status codes (400, 404, 500)
- Wrap errors in JSON responses: `{error: "message"}`
- Handle missing repos, invalid URLs, corrupt zips

### Dependencies (requirements.txt):
```
flask==3.0.0
flask-cors==4.0.0
gitpython==3.1.40
gunicorn==21.2.0
```

### Running:
The server should run with: `python app.py` on port 5000.
Include `if __name__ == '__main__': app.run(debug=True, port=5000)`.
```

---

### Stream 3: Frontend React Dashboard

**Files owned**: ENTIRE `/frontend/` directory

**Prompt for Qoder conversation:**

```
We are building a Git Repo Analysis Tool (RAT). Your job is to implement the 
complete React frontend dashboard. The backend API is being built separately.

The workspace is at /home/vmuser/Desktop/SDP-test (already scaffolded with Vite + React + TS + Tailwind + Recharts + Axios + lucide-react already installed).
Read /home/vmuser/Desktop/SDP-test/PLAN.md for the full project plan.
You ONLY create/edit files under `/frontend/src/` and `/frontend/index.html`. The scaffold (package.json, vite.config.ts, tailwind.config.js, etc.) is already set up.

## Already installed
Vite, React, TypeScript, Tailwind CSS v3, React Router, Recharts, Axios, lucide-react

## What to build

A polished, responsive web dashboard for analyzing git repositories.

### Pages & Components:

**1. Layout (App shell):**
- Top navbar with app name "RAT - Repo Analysis Tool" and repo selector dropdown
- Sidebar with navigation links
- Main content area
- Use Tailwind with a clean dark/light professional theme (prefer light theme with 
  subtle gray backgrounds, blue accents)

**2. Home / Repository List Page (`/`):**
- Card grid showing all added repositories
- Each card shows: name, URL (if cloned), date added, quick stats
- "Add Repository" button opens a modal with two tabs:
  - "Clone URL" tab: text input for git URL + "Clone" button
  - "Upload ZIP" tab: file drop zone for zip upload
- Delete button on each repo card (with confirmation)
- Loading states while cloning/uploading

**3. Dashboard Page (`/repo/:id`):**
This is the MAIN page. It has:

**Filter Bar (top of dashboard):**
- Author multi-select dropdown (checkboxes)
- Date range picker (from/to date inputs)  
- Commit selector toggle: "Time Range" or "Manual Select"
  - If manual: shows scrollable commit list with checkboxes
- Path filter: text input with autocomplete from file tree
- "Apply Filters" button

**Summary Cards Row:**
- 4 cards showing: Total Added Lines, Total Removed Lines, Growth, Churn
- Each with an icon and colored accent (green for added, red for removed, blue for growth, orange for churn)
- Also show: Total Commits, Modification Frequency, Churn Rate

**Charts Section (responsive grid):**
- **Churn Over Time**: Line chart (Recharts LineChart) showing churn per commit over time
- **Top Files by Churn**: Horizontal bar chart of top 15 files by churn
- **Directory Breakdown**: Treemap or bar chart showing churn by top-level directory
- **Author Ownership**: Pie chart showing ownership fractions
- **Growth Over Time**: Area chart showing cumulative growth

**Tables Section (tabbed):**
- **Files Tab**: Sortable table with columns: Path, Added, Removed, Growth, Churn, Modifications, Mod Frequency, Churn Rate
- **Directories Tab**: Same columns
- **Authors Tab**: Columns: Name, Email, Modifications, Churn, Ownership %
- Tables should be sortable by clicking column headers
- Pagination or virtual scroll for large lists

**4. Author Merge Page (`/repo/:id/authors`):**
- Shows current author groups
- Drag-and-drop or checkbox-based UI to merge authors
- "Auto-detect from .mailmap" button
- Save button to persist merge groups
- Table showing all unique author name/email combos

### API Client Service (`/frontend/src/services/api.ts`):
```typescript
const API_BASE = '/api';  // Will be proxied to backend

export const api = {
  // Repos
  getRepos: () => axios.get(`${API_BASE}/repos`),
  cloneRepo: (url: string) => axios.post(`${API_BASE}/repos/clone`, { url }),
  uploadRepo: (file: File) => {
    const fd = new FormData(); fd.append('file', file);
    return axios.post(`${API_BASE}/repos/upload`, fd);
  },
  deleteRepo: (id: string) => axios.delete(`${API_BASE}/repos/${id}`),
  
  // Data
  getCommits: (id: string, params?: {from?: number, to?: number}) => 
    axios.get(`${API_BASE}/repos/${id}/commits`, { params }),
  getAuthors: (id: string) => axios.get(`${API_BASE}/repos/${id}/authors`),
  getTree: (id: string, commit?: string) => 
    axios.get(`${API_BASE}/repos/${id}/tree`, { params: { commit } }),
  
  // Metrics
  getMetrics: (id: string, params?: MetricParams) => 
    axios.get(`${API_BASE}/repos/${id}/metrics`, { params }),
  
  // Author merge
  getAuthorGroups: (id: string) => axios.get(`${API_BASE}/repos/${id}/author-groups`),
  setAuthorGroups: (id: string, groups: AuthorGroup[][]) => 
    axios.post(`${API_BASE}/repos/${id}/author-groups`, { groups }),
};
```

### Vite Proxy Config (`vite.config.ts`):
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
});
```

### Key UX Requirements:
- Loading spinners/skeletons while data loads
- Error toasts/banners when API calls fail
- Empty states with helpful messages
- Responsive layout (works on 1920px and 1366px widths)
- Smooth transitions between pages
- Tables sortable by all numeric columns
- Number formatting (e.g., 1,234 not 1234)

### Important: 
- The backend is NOT available yet. Build the full UI anyway.
- Use realistic mock data in the API service as a fallback so the UI is 
  demonstrable even without the backend.
- The mock data should match the API response shapes exactly.
```

---

## PHASE 2: Integration & Merge (1 Conversation, after Phase 1)

### Stream 4: Merge, Integration, Polish

**Run this AFTER all 3 parallel streams are complete.**

**Prompt for Qoder conversation:**

```
We have built a Git Repo Analysis Tool (RAT) with 3 separate teams. Everything is in 
the repo at /home/vmuser/Desktop/SDP-test. Now we need to integrate and polish.

The structure is:
- `/backend/engine/` - Git metrics engine (Python module with GitAnalyzer class)
- `/backend/app.py` + `/backend/routes/` + `/backend/services/` - Flask API server
- `/frontend/` - React + Vite dashboard

## Tasks (in order):

### 1. Wire up the engine into Flask routes
- In `/backend/routes/metrics.py` and `/backend/routes/repos.py`, replace any 
  stub/mock code with real calls to `engine.analyzer.GitAnalyzer`
- Make sure the engine is imported correctly: `from engine.analyzer import GitAnalyzer`
- Ensure all query parameters (path, author, from, to, commits) are properly 
  passed through to `analyzer.compute_metrics()`
- The `commits` param comes as comma-separated string - split it into a list

### 2. Fix any import/integration issues
- Run `cd /backend && pip install -r requirements.txt`
- Run `cd /backend && python app.py` and fix any import errors
- Run `cd /frontend && npm install && npm run build` and fix any build errors

### 3. Test with cJSON repository
- Start the backend: `cd /backend && python app.py`
- Clone cJSON via the API: `curl -X POST http://localhost:5000/api/repos/clone -H "Content-Type: application/json" -d '{"url":"https://github.com/DaveGamble/cJSON.git"}'`
- Query metrics: `curl http://localhost:5000/api/repos/<id>/metrics`
- Verify the numbers look reasonable (cJSON has ~700 non-merge commits)

### 4. Remove mock data from frontend
- In the API service, remove any fallback mock data so it always hits the real backend
- Test the full flow: frontend -> backend -> engine

### 5. Create start.sh at project root
```bash
#!/bin/bash
# Install backend dependencies
cd backend
pip install -r requirements.txt
# Start backend in background
python app.py &
BACKEND_PID=$!
# Install frontend dependencies  
cd ../frontend
npm install
# Start frontend dev server
npm run dev &
FRONTEND_PID=$!
echo "RAT is running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:5000"
echo "Press Ctrl+C to stop"
wait
```

### 6. Update README.md at project root
Write clear instructions explaining:
- What RAT is
- How to run it (reference start.sh)
- Manual steps: `pip install`, `npm install`, `python app.py`, `npm run dev`
- Test repos to try: cJSON, Redis, Git URLs

### 7. Performance & Polish
- If large repo queries are slow, add caching in the engine (cache per-commit 
  diff data in memory after first computation)
- Add proper error messages in the UI for failed clones, timeouts
- Make sure CORS is working correctly
- Verify zip upload works end-to-end

### 8. Final verification
- Start both servers
- Open frontend in browser
- Clone cJSON from the UI
- Verify dashboard shows correct metrics
- Test filtering by author, date range
- Test author merging
- Take a screenshot for verification
```

---

## Summary Table

| Stream | Owns | Depends On | Est. Time |
|--------|------|------------|-----------|
| Stream 1: Git Engine | `/backend/engine/` | Nothing | 45-60 min |
| Stream 2: Flask API | `/backend/*.py`, `/backend/routes/`, `/backend/services/` | Nothing (stubs engine) | 30-40 min |
| Stream 3: React Frontend | `/frontend/` | Nothing (mocks API) | 45-60 min |
| Stream 4: Integration | Root files, wiring | Streams 1-3 done | 30-45 min |

Total wall-clock: ~90-105 min (Phase 1 parallel) + ~30-45 min (Phase 2) = ~2 hours

---

## Critical Notes

1. **No file overlap**: Each stream creates files in strictly separate directories. This makes git merge trivial.
2. **API contract is the glue**: All 3 streams develop against the same API shape. The merge step just connects the pieces.
3. **Mock data in frontend**: Stream 3 includes mock data so the UI is demonstrable standalone - Stream 4 removes it.
4. **Engine stubs in API**: Stream 2 writes the correct import statements and method calls to the engine, just the engine module doesn't exist yet - Stream 4 wires them.
5. **Test with cJSON first**: It's the smallest repo (~700 commits). Only try Redis/Git if performance allows.
6. **Commit early and often**: Each stream should commit its work before Stream 4 begins.
