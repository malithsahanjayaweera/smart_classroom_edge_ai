import { motion } from 'framer-motion';
import { useLiveMetrics } from '../hooks/useLiveMetrics';

const blocks = [
  { label: 'Door', col: '1 / span 2', row: '1' },
  { label: 'Whiteboard', col: '3 / span 4', row: '1' },
  { label: 'Projector', col: '7 / span 2', row: '1' },
  { label: 'Teacher', col: '4 / span 2', row: '2' },
  { label: 'Students', col: '2 / span 6', row: '3 / span 2' },
  { label: 'Windows', col: '1 / span 2', row: '3' },
  { label: 'Fans', col: '8 / span 1', row: '3' },
  { label: 'AC Unit', col: '8 / span 1', row: '2' },
];

export function SimulatorPage() {
  const { live } = useLiveMetrics();

  return (
    <section className="glass-card p-5">
      <h2 className="text-xl font-medium text-white">Classroom Simulation</h2>
      <p className="mt-1 text-sm text-slate-300">
        Animated classroom layout with runtime state — occupancy {live?.occupancyCount ?? 0}, AC{' '}
        {live?.acState.power ?? 'OFF'}.
      </p>

      <div className="mt-5 grid aspect-video grid-cols-8 grid-rows-4 gap-3 rounded-2xl border border-white/10 bg-slate-900/60 p-4">
        {blocks.map((block, index) => (
          <motion.div
            key={block.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05, duration: 0.25 }}
            className="rounded-lg border border-blue-300/20 bg-blue-500/10 p-2 text-xs text-blue-100"
            style={{ gridColumn: block.col, gridRow: block.row }}
          >
            {block.label}
          </motion.div>
        ))}
      </div>
    </section>
  );
}
