import { Link, useParams } from 'react-router-dom';
import { GitBranch, ChevronDown } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import type { Repo } from '../types';
import { api } from '../services/api';

export default function Navbar() {
  const { id } = useParams();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getRepos().then(setRepos);
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const current = repos.find(r => r.id === id);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm">
      <Link to="/" className="flex items-center gap-2 text-lg font-bold text-gray-800 hover:text-blue-600 transition-colors">
        <GitBranch className="h-6 w-6 text-blue-600" />
        <span>RAT</span>
        <span className="hidden sm:inline text-gray-400 font-normal text-sm">Repo Analysis Tool</span>
      </Link>

      {repos.length > 0 && (
        <div className="relative" ref={ref}>
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
          >
            {current ? current.name : 'Select repository'}
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </button>
          {open && (
            <div className="absolute right-0 mt-1 w-64 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
              {repos.map(r => (
                <Link
                  key={r.id}
                  to={`/repo/${r.id}`}
                  onClick={() => setOpen(false)}
                  className={`block px-4 py-2 text-sm hover:bg-blue-50 transition-colors ${
                    r.id === id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                  }`}
                >
                  {r.name}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </header>
  );
}
