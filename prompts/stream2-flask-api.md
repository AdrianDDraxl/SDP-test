We are building a Git Repo Analysis Tool (RAT). Your job is to implement ONLY the Flask API server. Another team is building the git engine at `/backend/engine/` and the React frontend at `/frontend/`.

The workspace is at /home/vmuser/Desktop/SDP-test (already scaffolded).
Read /home/vmuser/Desktop/SDP-test/PLAN.md for the full project plan.
You ONLY create/edit files in `/backend/` root, `/backend/routes/`, and `/backend/services/`. Do NOT touch `/backend/engine/`.

## What to build

A Flask REST API server. The engine module at `/backend/engine/` is being built separately - create STUB imports for it and use mock/placeholder data so the API is fully testable standalone.

### File structure (create ALL of these):
- `/backend/app.py` - Flask app entry point, CORS, error handlers
- `/backend/config.py` - Configuration (upload folder, repo storage path, etc.)
- `/backend/requirements.txt` - All Python dependencies (already exists, update if needed)
- `/backend/routes/__init__.py` - Blueprint registration
- `/backend/routes/repos.py` - Repository management endpoints
- `/backend/routes/metrics.py` - Metrics query endpoints
- `/backend/services/__init__.py`
- `/backend/services/repo_manager.py` - Handles cloning, zip extraction, repo storage

### API Endpoints (implement ALL):

**Repository Management:**
- `POST /api/repos/clone` - Body: `{"url": "https://..."}`. Clones repo to storage dir. Returns `{"id", "name", "url", "status"}`.
- `POST /api/repos/upload` - Multipart file upload (zip). Extracts to storage dir. Returns `{"id", "name", "status"}`.
- `GET /api/repos` - List all repos. Returns `[{"id", "name", "url", "created_at"}]`.
- `DELETE /api/repos/<id>` - Delete repo from storage.

**Data Queries:**
- `GET /api/repos/<id>/commits` - Query params: `from` (unix timestamp), `to` (unix timestamp). Returns commit list.
- `GET /api/repos/<id>/authors` - Returns author list.
- `GET /api/repos/<id>/tree` - Query param: `commit` (hash). Returns file tree.

**Metrics:**
- `GET /api/repos/<id>/metrics` - Query params: `path`, `author`, `from`, `to`, `commits` (comma-separated hashes). Returns full metrics response.

**Author Merging:**
- `GET /api/repos/<id>/author-groups` - Get current author merge groups.
- `POST /api/repos/<id>/author-groups` - Body: `{"groups": [[{"name", "email"}]]}`. Set merge groups.

### Implementation details:

**Repo Storage:**
- Store repos in `/tmp/rat_repos/` directory
- Each repo gets a UUID as its id
- Store repo metadata in a JSON file at `/tmp/rat_repos/metadata.json`
- Format: `{"id": {"name", "url", "path", "created_at"}}`

**Clone endpoint:**
- Use `git clone` (regular, not bare) to storage path via subprocess
- Do SYNCHRONOUS clone for simplicity. The test repos are not huge.

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

This will be wired up during integration. For now, the code should be structured to call these methods. If the import fails, that's OK - another conversation will wire it up.

**CORS:** Enable CORS for all routes (frontend runs on different port).

**Error Handling:**
- Return proper HTTP status codes (400, 404, 500)
- Wrap errors in JSON responses: `{"error": "message"}`
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
