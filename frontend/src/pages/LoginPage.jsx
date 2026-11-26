import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('admin@cognis.dev');
  const [password, setPassword] = useState('Admin@1234');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const profile = await login(email, password);
      navigate(profile.role === 'analyst_admin' ? '/analytics' : '/learn');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to connect to Cognis API');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/95 p-8 space-y-5 shadow-2xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
            <span className="text-xs font-semibold uppercase tracking-widest text-cyan-400">Cognis Suite</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-2">Sign in to Cognis</h1>
          <p className="text-sm text-slate-400 mt-1">Unified LMS, Placement CRM & Cohort Telemetry</p>
        </div>

        {error && <div className="text-xs text-rose-300 bg-rose-950/60 border border-rose-800 p-3 rounded-lg">{error}</div>}

        <div>
          <label className="block text-xs text-slate-400 mb-1">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm focus:border-cyan-400 focus:outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm focus:border-cyan-400 focus:outline-none"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold py-2.5 text-sm transition disabled:opacity-50"
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </button>

        <div className="pt-2 border-t border-slate-800">
          <p className="text-[11px] text-slate-500 mb-2 text-center">Quick-Fill Demo Accounts</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => { setEmail('admin@cognis.dev'); setPassword('Admin@1234'); }}
              className="flex-1 text-xs py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Analyst / Admin
            </button>
            <button
              type="button"
              onClick={() => { setEmail('student@cognis.dev'); setPassword('Student@1234'); }}
              className="flex-1 text-xs py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Learner Portal
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
