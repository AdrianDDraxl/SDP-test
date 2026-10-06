import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, ExternalLink, Calendar } from 'lucide-react';
import type { Repo } from '../types';
import { api, getErrorMessage } from '../services/api';
import AddRepoModal from '../components/AddRepoModal';
import ConfirmDialog from '../components/ConfirmDialog';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';
import EmptyState from '../components/EmptyState';
import { fmtISODate } from '../utils';

export default function HomePage() {
  const navigate = useNavigate();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Repo | null>(null);

  const fetchRepos = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getRepos();
      setRepos(data);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Failed to load repositories.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRepos(); }, []);

  const handleClone = async (url: string) => {
    const repo = await api.cloneRepo(url);
    setRepos(prev => [...prev, repo]);
  };

  const handleUpload = async (file: File) => {
    const repo = await api.uploadRepo(file);
    setRepos(prev => [...prev, repo]);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setError('');
    try {
      await api.deleteRepo(deleteTarget.id);
      setRepos(prev => prev.filter(r => r.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Failed to delete repository.'));
    }
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
          <p className="text-sm text-gray-500">Manage your git repositories for analysis</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Repository
        </button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

      {loading ? (
        <LoadingSpinner text="Loading repositories..." />
      ) : repos.length === 0 ? (
        <EmptyState
          title="No repositories yet"
          message="Add a repository by cloning from a URL or uploading a ZIP archive."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {repos.map(repo => (
            <div
              key={repo.id}
              className="group relative rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-blue-200 transition-all cursor-pointer"
              onClick={() => navigate(`/repo/${repo.id}`)}
            >
              <div className="mb-3 flex items-start justify-between">
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                  {repo.name}
                </h3>
                <button
                  onClick={e => { e.stopPropagation(); setDeleteTarget(repo); }}
                  className="rounded-lg p-1.5 text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
                  title="Delete repository"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {repo.url && (
                <div className="mb-2 flex items-center gap-1.5 text-xs text-gray-500 truncate">
                  <ExternalLink className="h-3 w-3 flex-shrink-0" />
                  <span className="truncate">{repo.url}</span>
                </div>
              )}

              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <Calendar className="h-3 w-3" />
                Added {fmtISODate(repo.created_at)}
              </div>

              {repo.status && repo.status !== 'ready' && (
                <span className={`mt-3 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  repo.status === 'cloning' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                }`}>
                  {repo.status}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      <AddRepoModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onClone={handleClone}
        onUpload={handleUpload}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Repository"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
