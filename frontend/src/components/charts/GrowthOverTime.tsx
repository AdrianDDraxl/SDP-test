import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { MetricTimelinePoint } from '../../types';
import { fmtDate } from '../../utils';

interface Props {
  data: MetricTimelinePoint[];
}

export default function GrowthOverTime({ data }: Props) {
  let cumulativeGrowth = 0;
  const cumulativeData = data.map(point => {
    cumulativeGrowth += point.growth;
    return { ...point, growth: cumulativeGrowth };
  });

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">Growth Over Time</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={cumulativeData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tickFormatter={(v) => fmtDate(Number(v))} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            labelFormatter={(label) => fmtDate(Number(label))}
            formatter={(v) => [Number(v).toLocaleString(), 'Growth']}
          />
          <Area type="monotone" dataKey="growth" stroke="#3b82f6" fill="#dbeafe" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
