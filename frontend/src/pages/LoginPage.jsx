import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const PASSWORD_RULES = [
  { label: '8+ chars', test: (p) => p.length >= 8 },
  { label: 'Uppercase', test: (p) => /[A-Z]/.test(p) },
  { label: 'Lowercase', test: (p) => /[a-z]/.test(p) },
  { label: 'Number', test: (p) => /\d/.test(p) },
  { label: 'Symbol', test: (p) => /[^A-Za-z0-9\s]/.test(p) },
];

export default function LoginPage() {
  const [mode, setMode] = useState('login');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [cohort, setCohort] = useState('COG-DA-2026-Q4');
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, loginWithOtp, verifyEmailOtp } = useAuth();
  const navigate = useNavigate();

  const parseError = (err) => {
    const detail = err.response?.data?.detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg.replace('Value error, ', '')).join(' · ');
    return detail || 'Unable to connect to Cognis API';
  };

  const switchMode = (next) => {
    setMode(next);
    setError('');
    setInfo('');
    setOtpCode('');
    setOtpSent(false);
  };

  const routeByRole = (profile) => {
    navigate(profile.role === 'analyst_admin' ? '/analytics' : '/learn');
  };

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setLoading(true);
    try {
      const profile = await login(email, password);
      routeByRole(profile);
    } catch (err) {
      const msg = parseError(err);
      setError(msg);
      if (err.response?.status === 403) {
        setInfo('Account pending email verification. Switch to Register or Verify Email to enter your OTP.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/register', {
        full_name: fullName,
        email,
        password,
        role: 'student',
        cohort,
      });
      setMode('verify_email');
      setOtpSent(true);
      setInfo(
        data.delivery_mode === 'console_dev'
          ? `${data.message} (Dev mode: check your backend terminal for the 6-digit OTP)`
          : data.message
      );
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOtp = async (purpose) => {
    if (!email.trim()) {
      setError('Please enter your genuine email address first.');
      return;
    }
    setError('');
    setInfo('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/otp/request', { email, purpose });
      setOtpSent(true);
      setInfo(
        data.delivery_mode === 'console_dev'
          ? `${data.message} (Dev mode: check your backend terminal for the 6-digit OTP)`
          : data.message
      );
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmail = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const profile = await verifyEmailOtp(email, otpCode);
      routeByRole(profile);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleOtpLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const profile = await loginWithOtp(email, otpCode);
      routeByRole(profile);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/reset-password', {
        email,
        otp_code: otpCode,
        new_password: password,
      });
      switchMode('login');
      setPassword('');
      setInfo(data.message);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    'w-full rounded-lg bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none';

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/95 p-8 space-y-5 shadow-2xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
            <span className="text-xs font-semibold uppercase tracking-widest text-cyan-400">Cognis Suite</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-2">
            {mode === 'login' && 'Sign in to Cognis'}
            {mode === 'otp_login' && 'Passwordless OTP Sign In'}
            {mode === 'register' && 'Create Verified Account'}
            {mode === 'verify_email' && 'Verify Your Email'}
            {mode === 'forgot' && 'Reset Your Password'}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Unified LMS, Placement CRM &amp; Cohort Telemetry · Verified Credentials Only
          </p>
        </div>

        <div className="grid grid-cols-3 gap-1.5 rounded-xl bg-slate-950 p-1 border border-slate-800">
          {[
            { id: 'login', label: 'Password' },
            { id: 'otp_login', label: 'Login OTP' },
            { id: 'register', label: 'Register' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => switchMode(tab.id)}
              className={`py-1.5 rounded-lg text-xs font-medium transition ${
                mode === tab.id || (tab.id === 'register' && mode === 'verify_email')
                  ? 'bg-cyan-500 text-slate-950 font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="text-xs text-rose-300 bg-rose-950/60 border border-rose-800 p-3 rounded-lg">
            {error}
          </div>
        )}
        {info && (
          <div className="text-xs text-emerald-300 bg-emerald-950/50 border border-emerald-800 p-3 rounded-lg">
            {info}
          </div>
        )}

        {mode === 'login' && (
          <form onSubmit={handlePasswordLogin} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Email Address</label>
              <input
                type="email"
                placeholder="you@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputCls}
                required
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs text-slate-400">Password</label>
                <button
                  type="button"
                  onClick={() => switchMode('forgot')}
                  className="text-xs text-cyan-400 hover:text-cyan-300"
                >
                  Forgot password?
                </button>
              </div>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
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
          </form>
        )}

        {mode === 'otp_login' && (
          <form onSubmit={handleOtpLogin} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Registered Email Address</label>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="you@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputCls}
                  required
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleRequestOtp('login')}
                  className="px-3.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 text-xs font-medium whitespace-nowrap"
                >
                  {otpSent ? 'Resend' : 'Send OTP'}
                </button>
              </div>
            </div>
            {otpSent && (
              <>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">6-Digit OTP Code</label>
                  <input
                    type="text"
                    maxLength={6}
                    pattern="\d{6}"
                    placeholder="000000"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    className={`${inputCls} tracking-[0.35em] text-center font-mono text-base`}
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || otpCode.length !== 6}
                  className="w-full rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold py-2.5 text-sm transition disabled:opacity-50"
                >
                  {loading ? 'Verifying...' : 'Verify & Sign In'}
                </button>
              </>
            )}
          </form>
        )}

        {mode === 'register' && (
          <form onSubmit={handleRegister} className="space-y-3.5">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Full Name</label>
              <input
                type="text"
                placeholder="Your full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className={inputCls}
                required
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Genuine Email Address (Verified via OTP)</label>
              <input
                type="email"
                placeholder="yourname@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputCls}
                required
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cohort</label>
              <select value={cohort} onChange={(e) => setCohort(e.target.value)} className={inputCls}>
                <option value="COG-DA-2026-Q4">Data Analytics — Q4 2026</option>
                <option value="COG-AI-2026-Q4">Applied AI — Q4 2026</option>
                <option value="COG-NT-2026-Q4">Neural Systems — Q4 2026</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Strong Password</label>
              <input
                type="password"
                placeholder="Min 8 chars, mixed case, number & symbol"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
                required
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {PASSWORD_RULES.map((r) => {
                  const ok = r.test(password);
                  return (
                    <span
                      key={r.label}
                      className={`text-[10px] px-2 py-0.5 rounded-full border ${
                        ok
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                          : 'bg-slate-950 text-slate-500 border-slate-800'
                      }`}
                    >
                      {ok ? '✓' : '·'} {r.label}
                    </span>
                  );
                })}
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold py-2.5 text-sm transition disabled:opacity-50"
            >
              {loading ? 'Sending Verification OTP...' : 'Register & Send OTP'}
            </button>
          </form>
        )}

        {mode === 'verify_email' && (
          <form onSubmit={handleVerifyEmail} className="space-y-4">
            <p className="text-xs text-slate-300">
              Enter the 6-digit verification code sent to <span className="text-cyan-300 font-medium">{email}</span>.
            </p>
            <input
              type="text"
              maxLength={6}
              pattern="\d{6}"
              placeholder="000000"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
              className={`${inputCls} tracking-[0.35em] text-center font-mono text-base`}
              required
            />
            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="w-full rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold py-2.5 text-sm transition disabled:opacity-50"
            >
              {loading ? 'Activating Account...' : 'Verify Email & Enter Cognis'}
            </button>
            <button
              type="button"
              onClick={() => handleRequestOtp('verify_email')}
              className="w-full text-xs text-cyan-400 hover:text-cyan-300"
            >
              Resend Verification OTP
            </button>
          </form>
        )}

        {mode === 'forgot' && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Registered Email Address</label>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="you@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputCls}
                  required
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleRequestOtp('reset_password')}
                  className="px-3.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 text-xs font-medium whitespace-nowrap"
                >
                  {otpSent ? 'Resend' : 'Send OTP'}
                </button>
              </div>
            </div>
            {otpSent && (
              <>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">6-Digit Reset OTP</label>
                  <input
                    type="text"
                    maxLength={6}
                    pattern="\d{6}"
                    placeholder="000000"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    className={`${inputCls} tracking-[0.35em] text-center font-mono text-base`}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">New Strong Password</label>
                  <input
                    type="password"
                    placeholder="Min 8 chars, mixed case, number & symbol"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={inputCls}
                    required
                  />
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {PASSWORD_RULES.map((r) => {
                      const ok = r.test(password);
                      return (
                        <span
                          key={r.label}
                          className={`text-[10px] px-2 py-0.5 rounded-full border ${
                            ok
                              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                              : 'bg-slate-950 text-slate-500 border-slate-800'
                          }`}
                        >
                          {ok ? '✓' : '·'} {r.label}
                        </span>
                      );
                    })}
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading || otpCode.length !== 6}
                  className="w-full rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold py-2.5 text-sm transition disabled:opacity-50"
                >
                  {loading ? 'Updating Password...' : 'Reset Password'}
                </button>
              </>
            )}
            <button
              type="button"
              onClick={() => switchMode('login')}
              className="w-full text-xs text-slate-400 hover:text-white"
            >
              ← Back to Sign In
            </button>
          </form>
        )}

        {mode === 'login' && (
          <div className="pt-3 border-t border-slate-800">
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
        )}
      </div>
    </div>
  );
}
