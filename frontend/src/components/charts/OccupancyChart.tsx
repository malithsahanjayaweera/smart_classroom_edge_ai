import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type OccupancyChartProps = {
  data: { timestamp: string; occupancyCount: number }[];
};

export function OccupancyChart({ data }: OccupancyChartProps) {
  return (
    <section className="glass-card p-5">
      <h3 className="text-lg font-medium text-white">Occupancy History</h3>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
            <XAxis dataKey="timestamp" hide />
            <YAxis stroke="#93c5fd" />
            <Tooltip />
            <Line type="monotone" dataKey="occupancyCount" stroke="#60a5fa" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
