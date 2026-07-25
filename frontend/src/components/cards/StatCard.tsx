import { motion } from 'framer-motion';

type StatCardProps = {
  title: string;
  value: string;
  helper: string;
};

export function StatCard({ title, value, helper }: StatCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="glass-card p-5"
    >
      <p className="text-sm text-blue-200">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{helper}</p>
    </motion.article>
  );
}
