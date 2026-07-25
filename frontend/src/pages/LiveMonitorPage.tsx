import { LiveFeedPanel } from '../components/live/LiveFeedPanel';
import { useLiveMetrics } from '../hooks/useLiveMetrics';

export function LiveMonitorPage() {
  const { live, isLoading, error } = useLiveMetrics();

  if (isLoading) {
    return <p className="text-slate-300">Loading camera and detection stream...</p>;
  }

  if (error || !live) {
    return <p className="text-rose-300">Unable to load live monitor: {error}</p>;
  }

  return (
    <div className="space-y-4">
      <div className="glass-card p-5">
        <h2 className="text-lg font-medium text-white">Live AI Detection</h2>
        <p className="mt-1 text-sm text-slate-300">
          Current activity: <span className="text-blue-200">{live.activity}</span>
        </p>
      </div>
      <LiveFeedPanel detections={live.detections} />
    </div>
  );
}
