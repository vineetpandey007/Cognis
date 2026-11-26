import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  if (!user) return null;

  const linkCls = (path) =>
    `text-sm transition-colors ${
      pathname === path ? 'text-cyan-400 font-semibold' : 'text-slate-300 hover:text-white'
    }`;

  return (
    <nav className="sticky top-0 z-20 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center gap-7">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_10px_#22d3ee]" />
          <span className="font-bold text-lg tracking-wider text-white">COGNIS</span>
        </div>
        {user.role === 'student' ? (
          <Link to="/learn" className={linkCls('/learn')}>My Learning</Link>
        ) : (
          <>
            <Link to="/analytics" className={linkCls('/analytics')}>BI Command Center</Link>
            <Link to="/crm" className={linkCls('/crm')}>Placement CRM</Link>
          </>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-cyan-300">
          {user.full_name} · {user.role === 'analyst_admin' ? 'Analyst' : 'Learner'}
        </span>
        <button
          onClick={logout}
          className="text-xs px-3 py-1.5 rounded-md bg-rose-500/15 text-rose-300 border border-rose-500/30 hover:bg-rose-500/25"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
