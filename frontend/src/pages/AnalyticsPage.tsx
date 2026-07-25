import { OccupancyChart } from '../components/charts/OccupancyChart';
import { TemperatureChart } from '../components/charts/TemperatureChart';
import { useLiveMetrics } from '../hooks/useLiveMetrics';

export function AnalyticsPage() {
  const { history, isLoading, error } = useLiveMetrics();

  if (isLoading) {
    return <p className="text-slate-300">Loading analytics...</p>;
  }

  if (error) {
    return <p className="text-rose-300">Unable to load analytics: {error}</p>;
  }

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <OccupancyChart data={history.occupancyHistory} />
      <TemperatureChart data={history.temperatureHistory} />
    </div>
  );
}
