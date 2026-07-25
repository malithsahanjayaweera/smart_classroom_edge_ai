import type { Detection } from '../../types';

type LiveFeedPanelProps = {
  detections: Detection[];
};

export function LiveFeedPanel({ detections }: LiveFeedPanelProps) {
  return (
    <section className="glass-card p-5">
      <h2 className="text-lg font-medium text-white">Live Classroom Camera</h2>
      <p className="text-sm text-slate-300">Real-time AI bounding boxes</p>

      <div className="relative mt-4 aspect-video overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-blue-950 to-slate-900">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.2),_transparent_50%)]" />
        {detections.map((detection, index) => {
          const width = Math.max(8, detection.bbox.x2 - detection.bbox.x1);
          const height = Math.max(8, detection.bbox.y2 - detection.bbox.y1);
          return (
            <div
              key={`${detection.label}-${index}`}
              className="absolute border-2 border-emerald-400"
              style={{
                left: `${detection.bbox.x1}%`,
                top: `${detection.bbox.y1}%`,
                width: `${width}%`,
                height: `${height}%`,
              }}
            >
              <span className="bg-emerald-500/90 px-1 text-[10px] text-slate-950">
                {detection.label} {(detection.confidence * 100).toFixed(0)}%
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
