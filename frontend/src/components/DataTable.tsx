import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import type { SortConfig, SortDir } from '../types';
import { fmt, fmtDec, fmtPct } from '../utils';

interface Column {
  key: string;
  label: string;
  type?: 'string' | 'number' | 'percent';
  width?: string;
}

interface Props {
  columns: Column[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<string, any>[];
  pageSize?: number;
}

export default function DataTable({ columns, data, pageSize = 20 }: Props) {
  const [sort, setSort] = useState<SortConfig>({ key: '', direction: 'desc' });
  const [page, setPage] = useState(0);

  const toggleSort = (key: string) => {
    let dir: SortDir = 'desc';
    if (sort.key === key && sort.direction === 'desc') dir = 'asc';
    setSort({ key, direction: dir });
    setPage(0);
  };

  const sorted = useMemo(() => {
    if (!sort.key) return data;
    return [...data].sort((a, b) => {
      const aVal = a[sort.key];
      const bVal = b[sort.key];
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sort.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const cmp = String(aVal).localeCompare(String(bVal));
      return sort.direction === 'asc' ? cmp : -cmp;
    });
  }, [data, sort]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize);

  const formatCell = (col: Column, value: unknown) => {
    if (value == null) return '-';
    if (col.type === 'percent' && typeof value === 'number') return fmtPct(value);
    if (col.type === 'number' && typeof value === 'number') {
      return Number.isInteger(value) ? fmt(value) : fmtDec(value);
    }
    return String(value);
  };

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  className="cursor-pointer px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 hover:text-gray-700 select-none"
                  style={col.width ? { width: col.width } : undefined}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sort.key === col.key ? (
                      sort.direction === 'asc' ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronsUpDown className="h-3.5 w-3.5 text-gray-300" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-400">
                  No data available
                </td>
              </tr>
            ) : (
              paged.map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-gray-100 last:border-0 hover:bg-gray-50/50 transition-colors"
                >
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-2.5 text-gray-700 whitespace-nowrap">
                      {col.key === 'path' ? (
                        <code className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">{String(row[col.key])}</code>
                      ) : (
                        formatCell(col, row[col.key])
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-2.5">
          <span className="text-xs text-gray-500">
            Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, sorted.length)} of {sorted.length}
          </span>
          <div className="flex gap-1">
            <button
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
              className="rounded-lg px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
              className="rounded-lg px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
