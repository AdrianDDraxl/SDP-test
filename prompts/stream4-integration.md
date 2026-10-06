We have built a Git Repo Analysis Tool (RAT) with 3 separate teams. Everything is in the repo at /home/vmuser/Desktop/SDP-test. Now we need to integrate and polish.

The structure is:
- `/backend/engine/` - Git metrics engine (Python module with GitAnalyzer class)
- `/backend/app.py` + `/backend/routes/` + `/backend/services/` - Flask API server
- `/frontend/` - React + Vite dashboard

Read /home/vmuser/Desktop/SDP-test/PLAN.md for the full project plan and API contract.

## Tasks (in order):

### 1. Wire up the engine into Flask routes
- In `/backend/routes/metrics.py` and `/backend/routes/repos.py`, replace any stub/mock code with real calls to `engine.analyzer.GitAnalyzer`
- Make sure the engine is imported correctly: `from engine.analyzer import GitAnalyzer`
- Ensure all query parameters (path, author, from, to, commits) are properly passed through to `analyzer.compute_metrics()`
- The `commits` param comes as comma-separated string - split it into a list

### 2. Fix any import/integration issues
- Run `cd /home/vmuser/Desktop/SDP-test/backend && pip install -r requirements.txt`
- Run `cd /home/vmuser/Desktop/SDP-test/backend && python app.py` and fix any import errors
- Run `cd /home/vmuser/Desktop/SDP-test/frontend && npm install && npm run build` and fix any build errors

### 3. Test with cJSON repository
- Start the backend: `cd /home/vmuser/Desktop/SDP-test/backend && python app.py`
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
- If large repo queries are slow, add caching in the engine (cache per-commit diff data in memory after first computation)
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
