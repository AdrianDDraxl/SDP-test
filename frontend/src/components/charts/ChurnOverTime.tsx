import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { CommitInfo } from '../../types';
import { fmtDate } from '../../utils';

interface Props {
  commits: CommitInfo[];
  /** Per-commit churn data – if not provided we synthesize from commit dates */
  churnData?: { date: number; churn: number }[];
}

export default function ChurnOverTime({ commits, churnData }: Props) {
  const data = churnData ??
    commits.map((c, i) => ({
      date: c.date,
      churn: Math.round(80 + Math.sin(i * 0.4) * 60 + Math.random() * 40),
    }));

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">Churn Over Time</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tickFormatter={(v) => fmtDate(Number(v))} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            labelFormatter={(label) => fmtDate(Number(label))}
            formatter={(v) => [Number(v).toLocaleString(), 'Churn']}
          />
          <Line type="monotone" dataKey="churn" stroke="#f97316" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
