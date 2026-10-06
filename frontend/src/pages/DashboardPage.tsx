import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { defaultFilters } from '../types';
import type { MetricsResult, AuthorInfo, CommitInfo, TreeEntry, MetricParams, Filters } from '../types';
import { api, getErrorMessage } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';
import FilterBar from '../components/FilterBar';
import SummaryCards from '../components/SummaryCards';
import ChurnOverTime from '../components/charts/ChurnOverTime';
import TopFilesByChurn from '../components/charts/TopFilesByChurn';
import DirectoryBreakdown from '../components/charts/DirectoryBreakdown';
import AuthorOwnership from '../components/charts/AuthorOwnership';
import GrowthOverTime from '../components/charts/GrowthOverTime';
import DataTable from '../components/DataTable';

const FILE_COLS = [
  { key: 'path', label: 'Path', type: 'string' as const, width: '240px' },
  { key: 'added_lines', label: 'Added', type: 'number' as const },
  { key: 'removed_lines', label: 'Removed', type: 'number' as const },
  { key: 'growth', label: 'Growth', type: 'number' as const },
  { key: 'churn', label: 'Churn', type: 'number' as const },
  { key: 'modifications', label: 'Mods', type: 'number' as const },
  { key: 'mod_frequency', label: 'Mod Freq', type: 'number' as const },
  { key: 'churn_rate', label: 'Churn Rate', type: 'number' as const },
];

const DIR_COLS = [...FILE_COLS];

const AUTHOR_COLS = [
  { key: 'name', label: 'Name', type: 'string' as const },
  { key: 'email', label: 'Email', type: 'string' as const },
  { key: 'modifications', label: 'Mods', type: 'number' as const },
  { key: 'churn', label: 'Churn', type: 'number' as const },
  { key: 'ownership', label: 'Ownership', type: 'percent' as const },
];

type TableTab = 'files' | 'directories' | 'authors';

export default function DashboardPage() {
  const { id } = useParams<{ id: string }>();
  const [metrics, setMetrics] = useState<MetricsResult | null>(null);
  const [authors, setAuthors] = useState<AuthorInfo[]>([]);
  const [commits, setCommits] = useState<CommitInfo[]>([]);
  const [tree, setTree] = useState<TreeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [tableTab, setTableTab] = useState<TableTab>('files');

  const fetchData = async (params?: MetricParams) => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const [m, a, c, t] = await Promise.all([
        api.getMetrics(id, params),
        api.getAuthors(id),
        api.getCommits(id),
        api.getTree(id),
      ]);
      setMetrics(m);
      setAuthors(a);
      setCommits(c);
      setTree(t);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Failed to load dashboard data.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const applyFilters = () => {
    const params: MetricParams = {};
    // Comma-separated emails; backend treats multiple authors as a union filter.
    if (filters.authors.length > 0) params.author = filters.authors.join(',');
    if (filters.pathFilter) params.path = filters.pathFilter;
    if (filters.commitMode === 'range') {
      if (filters.fromDate) params.from = Math.floor(new Date(filters.fromDate).getTime() / 1000);
      // Backend treats `to` as exclusive; add one day so the selected end date is fully included.
      if (filters.toDate) params.to = Math.floor(new Date(filters.toDate).getTime() / 1000) + 86400;
    } else {
      if (filters.selectedCommits.length > 0) params.commits = filters.selectedCommits.join(',');
    }
    fetchData(params);
  };

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;

  return (
    <div className="mx-auto max-w-7xl">
      {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

      <FilterBar
        authors={authors}
        commits={commits}
        tree={tree}
        filters={filters}
        onChange={setFilters}
        onApply={applyFilters}
      />

      {metrics && (
        <>
          <SummaryCards summary={metrics.summary} commitsUsed={metrics.commits_used} />

          {/* Charts grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <ChurnOverTime data={metrics.timeline} />
            <TopFilesByChurn files={metrics.files} />
            <DirectoryBreakdown directories={metrics.directories} />
            <AuthorOwnership authors={metrics.authors} />
          </div>

          <div className="mb-6">
            <GrowthOverTime data={metrics.timeline} />
          </div>

          {/* Tables */}
          <div className="mb-6">
            <div className="flex gap-1 mb-3">
              {(['files', 'directories', 'authors'] as TableTab[]).map(tab => (
                <button
                  key={tab}
                  onClick={() => setTableTab(tab)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition-colors ${
                    tableTab === tab
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {tableTab === 'files' && <DataTable columns={FILE_COLS} data={metrics.files} />}
            {tableTab === 'directories' && <DataTable columns={DIR_COLS} data={metrics.directories} />}
            {tableTab === 'authors' && <DataTable columns={AUTHOR_COLS} data={metrics.authors} />}
          </div>
        </>
      )}
    </div>
  );
}
