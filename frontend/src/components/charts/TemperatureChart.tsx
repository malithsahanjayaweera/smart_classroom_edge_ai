import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type TemperatureChartProps = {
  data: { timestamp: string; temperatureC: number }[];
};

export function TemperatureChart({ data }: TemperatureChartProps) {
  return (
    <section className="glass-card p-5">
      <h3 className="text-lg font-medium text-white">AC Temperature History</h3>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
            <XAxis dataKey="timestamp" hide />
            <YAxis stroke="#67e8f9" />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="temperatureC"
              stroke="#22d3ee"
              fillOpacity={1}
              fill="url(#tempGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
