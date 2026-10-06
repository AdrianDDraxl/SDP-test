import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { FileMetric } from '../../types';
import { fmt } from '../../utils';

interface Props {
  files: FileMetric[];
}

export default function TopFilesByChurn({ files }: Props) {
  const data = [...files]
    .sort((a, b) => b.churn - a.churn)
    .slice(0, 15)
    .map(f => ({
      name: f.path.length > 30 ? '...' + f.path.slice(-27) : f.path,
      fullPath: f.path,
      churn: f.churn,
    }));

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">Top Files by Churn</h3>
      <ResponsiveContainer width="100%" height={Math.max(260, data.length * 28)}>
        <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => fmt(v)} />
          <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(v) => [fmt(Number(v)), 'Churn']}
            labelFormatter={(_, payload) => {
              const entry = payload?.[0] as { payload?: { fullPath?: string } } | undefined;
              return entry?.payload?.fullPath ?? '';
            }}
          />
          <Bar dataKey="churn" fill="#f97316" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
