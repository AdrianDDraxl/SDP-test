import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Save, Wand2, Plus, X, Check } from 'lucide-react';
import type { AuthorGroup, AuthorInfo } from '../types';
import { api, getErrorMessage } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

export default function AuthorMergePage() {
  const { id } = useParams<{ id: string }>();
  const [groups, setGroups] = useState<AuthorGroup[][]>([]);
  const [allAuthors, setAllAuthors] = useState<AuthorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([api.getAuthorGroups(id), api.getAuthors(id)])
      .then(([g, a]) => {
        setGroups(g.groups);
        setAllAuthors(a);
      })
      .catch(requestError => setError(getErrorMessage(requestError, 'Failed to load author data.')))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSave = async () => {
    if (!id) return;
    setSaving(true);
    setError('');
    try {
      await api.setAuthorGroups(id, groups);
      setSuccess('Author groups saved successfully.');
      setTimeout(() => setSuccess(''), 3000);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Failed to save author groups.'));
    } finally {
      setSaving(false);
    }
  };

  const addGroup = () => {
    setGroups(prev => [...prev, []]);
  };

  const removeGroup = (gi: number) => {
    setGroups(prev => prev.filter((_, i) => i !== gi));
  };

  const toggleAuthorInGroup = (gi: number, author: AuthorInfo) => {
    setGroups(prev => {
      const next = prev.map(g => [...g]);
      const idx = next[gi].findIndex(a => a.email === author.email);
      if (idx >= 0) {
        next[gi].splice(idx, 1);
      } else {
        // Remove from other groups first
        for (let i = 0; i < next.length; i++) {
          next[i] = next[i].filter(a => a.email !== author.email);
        }
        next[gi].push({ name: author.name, email: author.email });
      }
      return next;
    });
  };

  const isInGroup = (email: string, gi: number) =>
    groups[gi]?.some(a => a.email === email) ?? false;

  const isInAnyGroup = (email: string) =>
    groups.some(g => g.some(a => a.email === email));

  const autoDetect = async () => {
    if (!id) return;
    // Simulate auto-detect – group authors with similar names
    const nameMap = new Map<string, AuthorInfo[]>();
    for (const a of allAuthors) {
      const key = a.name.toLowerCase().replace(/[^a-z]/g, '');
      const group = nameMap.get(key) || [];
      group.push(a);
      nameMap.set(key, group);
    }
    const detected: AuthorGroup[][] = [];
    for (const group of nameMap.values()) {
      if (group.length > 1) {
        detected.push(group.map(a => ({ name: a.name, email: a.email })));
      }
    }
    setGroups(prev => [...prev, ...detected]);
  };

  if (loading) return <LoadingSpinner text="Loading author data..." />;

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Author Merge</h1>
          <p className="text-sm text-gray-500">
            Group different author identities that belong to the same person
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={autoDetect}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Wand2 className="h-4 w-4" />
            Auto-detect
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save Groups'}
          </button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}
      {success && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          <Check className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* Author groups */}
      <div className="space-y-4 mb-8">
        {groups.map((group, gi) => (
          <div key={gi} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700">Group {gi + 1}</h3>
              <button
                onClick={() => removeGroup(gi)}
                className="rounded-lg p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              {group.map(a => (
                <span
                  key={a.email}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700"
                >
                  {a.name} &lt;{a.email}&gt;
                  <button
                    onClick={() => toggleAuthorInGroup(gi, { name: a.name, email: a.email, commit_count: 0 })}
                    className="ml-1 rounded-full hover:bg-blue-200 p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              {group.length === 0 && (
                <span className="text-xs text-gray-400 italic">Click an author below to add them to this group</span>
              )}
            </div>
            {/* Selectable authors */}
            <div className="flex flex-wrap gap-1">
              {allAuthors.map(a => (
                <button
                  key={a.email}
                  onClick={() => toggleAuthorInGroup(gi, a)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                    isInGroup(a.email, gi)
                      ? 'bg-blue-600 text-white'
                      : isInAnyGroup(a.email)
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  disabled={isInAnyGroup(a.email) && !isInGroup(a.email, gi)}
                >
                  {a.name}
                </button>
              ))}
            </div>
          </div>
        ))}

        <button
          onClick={addGroup}
          className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-300 py-4 text-sm font-medium text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Merge Group
        </button>
      </div>

      {/* All authors table */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
          <h3 className="text-sm font-semibold text-gray-700">All Authors ({allAuthors.length})</h3>
        </div>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/50">
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Name</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Email</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Commits</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Group</th>
            </tr>
          </thead>
          <tbody>
            {allAuthors.map(a => {
              const groupIdx = groups.findIndex(g => g.some(m => m.email === a.email));
              return (
                <tr key={a.email} className="border-b border-gray-100 last:border-0 hover:bg-gray-50/50">
                  <td className="px-4 py-2.5 font-medium text-gray-900">{a.name}</td>
                  <td className="px-4 py-2.5 text-gray-500">{a.email}</td>
                  <td className="px-4 py-2.5 text-gray-700">{a.commit_count.toLocaleString()}</td>
                  <td className="px-4 py-2.5">
                    {groupIdx >= 0 ? (
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                        Group {groupIdx + 1}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
