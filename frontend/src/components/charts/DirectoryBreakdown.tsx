import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { DirectoryMetric } from '../../types';
import { fmt } from '../../utils';

interface Props {
  directories: DirectoryMetric[];
}

export default function DirectoryBreakdown({ directories }: Props) {
  const data = directories
    .filter(d => d.path !== '')
    .sort((a, b) => b.churn - a.churn)
    .slice(0, 12)
    .map(d => ({
      name: d.path || '(root)',
      churn: d.churn,
      growth: d.growth,
    }));

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">Directory Breakdown</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => fmt(Number(v))} />
          <Bar dataKey="churn" fill="#f97316" radius={[4, 4, 0, 0]} name="Churn" />
          <Bar dataKey="growth" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Growth" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
