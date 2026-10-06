// ── Repository ──
export interface Repo {
  id: string;
  name: string;
  url?: string;
  created_at: string; // ISO date string
  status?: 'ready' | 'cloning' | 'error';
}

// ── Commits ──
export interface CommitInfo {
  hash: string;
  author_name: string;
  author_email: string;
  date: number; // unix timestamp
  message: string;
}

// ── Authors ──
export interface AuthorInfo {
  name: string;
  email: string;
  commit_count: number;
}

// ── File tree ──
export interface TreeEntry {
  path: string;
  type: 'file' | 'dir';
}

// ── Metrics ──
export interface MetricParams {
  path?: string;
  author?: string;
  from?: number;
  to?: number;
  commits?: string; // comma-separated hashes
}

export interface MetricsSummary {
  added_lines: number;
  removed_lines: number;
  growth: number;
  churn: number;
  modifications: number;
  mod_frequency: number;
  churn_rate: number;
}

export interface FileMetric {
  path: string;
  added_lines: number;
  removed_lines: number;
  growth: number;
  churn: number;
  modifications: number;
  mod_frequency: number;
  churn_rate: number;
}

export interface DirectoryMetric {
  path: string;
  added_lines: number;
  removed_lines: number;
  growth: number;
  churn: number;
  modifications: number;
  mod_frequency: number;
  churn_rate: number;
}

export interface AuthorMetric {
  name: string;
  email: string;
  modifications: number;
  churn: number;
  ownership: number; // 0-1 fraction
}

export interface MetricsResult {
  summary: MetricsSummary;
  files: FileMetric[];
  directories: DirectoryMetric[];
  authors: AuthorMetric[];
  commits_used: number;
}

// ── Author Merge ──
export interface AuthorGroup {
  name: string;
  email: string;
}

// ── Sort ──
export type SortDir = 'asc' | 'desc';

export interface SortConfig {
  key: string;
  direction: SortDir;
}
