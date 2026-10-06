import { TrendingUp, TrendingDown, ArrowUpDown, Flame, GitCommit, Activity, Percent } from 'lucide-react';
import type { MetricsSummary } from '../types';
import { fmt, fmtDec } from '../utils';

interface Props {
  summary: MetricsSummary;
  commitsUsed: number;
}

interface CardDef {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
  bg: string;
}

export default function SummaryCards({ summary, commitsUsed }: Props) {
  const cards: CardDef[] = [
    { label: 'Added Lines', value: fmt(summary.added_lines), icon: <TrendingUp className="h-5 w-5" />, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Removed Lines', value: fmt(summary.removed_lines), icon: <TrendingDown className="h-5 w-5" />, color: 'text-red-500', bg: 'bg-red-50' },
    { label: 'Growth', value: fmt(summary.growth), icon: <ArrowUpDown className="h-5 w-5" />, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Churn', value: fmt(summary.churn), icon: <Flame className="h-5 w-5" />, color: 'text-orange-500', bg: 'bg-orange-50' },
    { label: 'Total Commits', value: fmt(commitsUsed), icon: <GitCommit className="h-5 w-5" />, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Mod Frequency', value: fmtDec(summary.mod_frequency), icon: <Activity className="h-5 w-5" />, color: 'text-teal-600', bg: 'bg-teal-50' },
    { label: 'Churn Rate', value: fmtDec(summary.churn_rate), icon: <Percent className="h-5 w-5" />, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
      {cards.map(c => (
        <div key={c.label} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{c.label}</span>
            <div className={`rounded-lg p-1.5 ${c.bg} ${c.color}`}>{c.icon}</div>
          </div>
          <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}
