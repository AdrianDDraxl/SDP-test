import { useState, useRef, useEffect } from 'react';
import { Filter, ChevronDown, Check, Search } from 'lucide-react';
import type { AuthorInfo, CommitInfo, TreeEntry, Filters } from '../types';
import { fmtDate } from '../utils';

interface Props {
  authors: AuthorInfo[];
  commits: CommitInfo[];
  tree: TreeEntry[];
  filters: Filters;
  onChange: (f: Filters) => void;
  onApply: () => void;
}

export default function FilterBar({ authors, commits, tree, filters, onChange, onApply }: Props) {
  const [authorOpen, setAuthorOpen] = useState(false);
  const [pathSuggestions, setPathSuggestions] = useState<string[]>([]);
  const authorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (authorRef.current && !authorRef.current.contains(e.target as Node)) setAuthorOpen(false);
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  const toggleAuthor = (email: string) => {
    const next = filters.authors.includes(email)
      ? filters.authors.filter(a => a !== email)
      : [...filters.authors, email];
    onChange({ ...filters, authors: next });
  };

  const toggleCommit = (hash: string) => {
    const next = filters.selectedCommits.includes(hash)
      ? filters.selectedCommits.filter(h => h !== hash)
      : [...filters.selectedCommits, hash];
    onChange({ ...filters, selectedCommits: next });
  };

  const onPathChange = (val: string) => {
    onChange({ ...filters, pathFilter: val });
    if (val.length > 0) {
      const paths = tree.map(t => t.path).filter(p => p.toLowerCase().includes(val.toLowerCase()));
      setPathSuggestions(paths.slice(0, 8));
    } else {
      setPathSuggestions([]);
    }
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Filter className="h-4 w-4 text-gray-500" />
        <span className="text-sm font-semibold text-gray-700">Filters</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Author multi-select */}
        <div className="relative" ref={authorRef}>
          <label className="mb-1 block text-xs font-medium text-gray-500">Authors</label>
          <button
            onClick={() => setAuthorOpen(!authorOpen)}
            className="flex w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            {filters.authors.length === 0 ? 'All authors' : `${filters.authors.length} selected`}
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </button>
          {authorOpen && (
            <div className="absolute z-20 mt-1 w-full rounded-lg border border-gray-200 bg-white py-1 shadow-lg max-h-48 overflow-y-auto">
              {authors.map(a => (
                <label key={a.email} onClick={() => toggleAuthor(a.email)} className="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-gray-50 cursor-pointer">
                  <div className={`flex h-4 w-4 items-center justify-center rounded border ${
                    filters.authors.includes(a.email) ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                  }`}>
                    {filters.authors.includes(a.email) && <Check className="h-3 w-3 text-white" />}
                  </div>
                  <span className="truncate">{a.name}</span>
                  <span className="ml-auto text-xs text-gray-400">{a.commit_count}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Date range */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">From Date</label>
          <input
            type="date"
            value={filters.fromDate}
            onChange={e => onChange({ ...filters, fromDate: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">To Date</label>
          <input
            type="date"
            value={filters.toDate}
            onChange={e => onChange({ ...filters, toDate: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Path filter */}
        <div className="relative">
          <label className="mb-1 block text-xs font-medium text-gray-500">Path Filter</label>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <input
              value={filters.pathFilter}
              onChange={e => onPathChange(e.target.value)}
              placeholder="e.g. src/..."
              className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          {pathSuggestions.length > 0 && (
            <div className="absolute z-20 mt-1 w-full rounded-lg border border-gray-200 bg-white py-1 shadow-lg max-h-40 overflow-y-auto">
              {pathSuggestions.map(p => (
                <button
                  key={p}
                  onClick={() => { onChange({ ...filters, pathFilter: p }); setPathSuggestions([]); }}
                  className="block w-full px-3 py-1.5 text-left text-sm text-gray-700 hover:bg-blue-50 truncate"
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Commit selector toggle */}
      <div className="mt-3 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">Commit Selector:</span>
          <button
            onClick={() => onChange({ ...filters, commitMode: 'range' })}
            className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
              filters.commitMode === 'range' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Time Range
          </button>
          <button
            onClick={() => onChange({ ...filters, commitMode: 'manual' })}
            className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
              filters.commitMode === 'manual' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Manual Select
          </button>
        </div>
        <button
          onClick={() => onChange({ authors: [], fromDate: '', toDate: '', commitMode: 'range', selectedCommits: [], pathFilter: '' })}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Reset
        </button>
        <button
          onClick={onApply}
          className="ml-auto rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          Apply Filters
        </button>
      </div>

      {/* Manual commit list */}
      {filters.commitMode === 'manual' && (
        <div className="mt-3 max-h-40 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-2">
          {commits.length === 0 ? (
            <p className="text-xs text-gray-400 py-2 text-center">No commits loaded</p>
          ) : (
            commits.map(c => (
              <label key={c.hash} onClick={() => toggleCommit(c.hash)} className="flex items-center gap-2 px-2 py-1 text-xs hover:bg-white rounded cursor-pointer">
                <div className={`flex h-3.5 w-3.5 items-center justify-center rounded border ${
                  filters.selectedCommits.includes(c.hash) ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                }`}>
                  {filters.selectedCommits.includes(c.hash) && <Check className="h-2.5 w-2.5 text-white" />}
                </div>
                <code className="text-gray-500 font-mono">{c.hash.slice(0, 7)}</code>
                <span className="text-gray-700 truncate flex-1">{c.message}</span>
                <span className="text-gray-400">{fmtDate(c.date)}</span>
              </label>
            ))
          )}
        </div>
      )}
    </div>
  );
}
