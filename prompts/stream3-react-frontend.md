We are building a Git Repo Analysis Tool (RAT). Your job is to implement the complete React frontend dashboard. The backend API is being built separately.

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
- Use Tailwind with a clean dark/light professional theme (prefer light theme with subtle gray backgrounds, blue accents)

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

### Vite Proxy Config (already set up in `vite.config.ts`):
The proxy is already configured to forward `/api` to `http://localhost:5000`.

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
- Use realistic mock data in the API service as a fallback so the UI is demonstrable even without the backend.
- The mock data should match the API response shapes exactly.
