import axios from 'axios';
import type {
  Repo,
  CommitInfo,
  AuthorInfo,
  TreeEntry,
  MetricParams,
  MetricsResult,
  AuthorGroup,
} from '../types';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 610_000,
});

function requestData<T>(request: Promise<{ data: T }>): Promise<T> {
  return request.then(response => response.data);
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as { error?: unknown } | undefined;
    if (typeof responseData?.error === 'string') return responseData.error;
    if (error.code === 'ECONNABORTED') return 'The request timed out. Please try again.';
    if (!error.response) return 'Unable to reach the RAT backend. Make sure it is running.';
  }
  return error instanceof Error && error.message ? error.message : fallback;
}

// ─── API Client ─────────────────────────────────────────────────────
export const api = {
  // Repos
  getRepos: () => requestData(client.get<Repo[]>('/repos')),
  cloneRepo: (url: string) => requestData(client.post<Repo>('/repos/clone', { url })),
  uploadRepo: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return requestData(client.post<Repo>('/repos/upload', formData));
  },
  deleteRepo: (id: string) => requestData(client.delete<{ ok: boolean }>(`/repos/${id}`)),

  // Data
  getCommits: (id: string, params?: { from?: number; to?: number }) =>
    requestData(client.get<CommitInfo[]>(`/repos/${id}/commits`, { params })),
  getAuthors: (id: string) => requestData(client.get<AuthorInfo[]>(`/repos/${id}/authors`)),
  getTree: (id: string, commit?: string) =>
    requestData(client.get<TreeEntry[]>(`/repos/${id}/tree`, { params: { commit } })),

  // Metrics
  getMetrics: (id: string, params?: MetricParams) =>
    requestData(client.get<MetricsResult>(`/repos/${id}/metrics`, { params })),

  // Author merge
  getAuthorGroups: (id: string) =>
    requestData(client.get<{ groups: AuthorGroup[][] }>(`/repos/${id}/author-groups`)),
  setAuthorGroups: (id: string, groups: AuthorGroup[][]) =>
    requestData(client.post<{ ok: boolean }>(`/repos/${id}/author-groups`, { groups })),
};
