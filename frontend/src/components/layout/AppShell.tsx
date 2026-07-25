import { Activity, BarChart3, Camera, Cpu } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/live-monitor', label: 'Live Camera', icon: Camera },
  { to: '/analytics', label: 'Analytics', icon: Activity },
  { to: '/simulator', label: 'Simulator', icon: Cpu },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 lg:px-8">
        <header className="glass-card flex flex-wrap items-center justify-between gap-4 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-blue-300">Edge AI Platform</p>
            <h1 className="text-2xl font-semibold text-white">Smart Classroom Edge AI System</h1>
          </div>
          <span className="rounded-full border border-blue-400/40 bg-blue-500/10 px-4 py-2 text-xs font-medium text-blue-200">
            Production Monitoring
          </span>
        </header>

        <nav className="glass-card flex flex-wrap gap-2 p-3">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition ${
                  isActive
                    ? 'bg-blue-500/20 text-blue-200 ring-1 ring-blue-300/40'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
