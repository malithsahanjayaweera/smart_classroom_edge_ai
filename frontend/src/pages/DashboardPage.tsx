import { StatCard } from '../components/cards/StatCard';
import { LiveFeedPanel } from '../components/live/LiveFeedPanel';
import { useLiveMetrics } from '../hooks/useLiveMetrics';

export function DashboardPage() {
  const { live, isLoading, error } = useLiveMetrics();

  if (isLoading) {
    return <p className="text-slate-300">Loading live classroom telemetry...</p>;
  }

  if (error || !live) {
    return <p className="text-rose-300">Unable to load dashboard data: {error}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Occupancy" value={`${live.occupancyCount}`} helper={`${live.occupancyBand} density`} />
        <StatCard title="Activity" value={live.activity} helper="Detected classroom state" />
        <StatCard
          title="AC Automation"
          value={live.acState.power === 'OFF' ? 'OFF' : `${live.acState.temperatureC}°C`}
          helper={`Fan ${live.acState.fanSpeed}`}
        />
        <StatCard title="Model Confidence" value={`${(live.confidence * 100).toFixed(0)}%`} helper="YOLOv8 inference" />
      </div>

      <LiveFeedPanel detections={live.detections} />
    </div>
  );
}
