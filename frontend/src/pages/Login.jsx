import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';
import { useResponsive } from '../hooks/useResponsive';
import { LogIn, Eye, EyeOff, Activity, Newspaper, Shield, BarChart2, Map } from 'lucide-react';

const FEATURES = [
  { icon: Activity,   color: '#10b981', label: 'Ground Intelligence',     desc: 'VAYU aggregates 850+ field reports daily across 150 booths' },
  { icon: Newspaper,  color: '#3b82f6', label: 'Media Sentiment Analysis', desc: 'VANI tracks 40+ outlets for candidate and issue narratives' },
  { icon: Shield,     color: '#8b5cf6', label: 'Opposition Intelligence',  desc: 'VIVEK monitors rival campaigns and rumour networks 24/7' },
  { icon: BarChart2,  color: '#f59e0b', label: 'Win Probability Model',   desc: 'VISHLESHAN predicts outcomes with 74% confidence' },
  { icon: Map,        color: '#f97316', label: 'Booth-level Management',   desc: '248,432 voters · 150 booths · real-time contact tracking' },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/command-centre';

  const { isMobile } = useResponsive();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const daysLeft = Math.max(0, Math.round((new Date('2026-05-28') - new Date()) / 86400000));

  const handleSubmit = async e => {
    e.preventDefault();
    if (!email || !password) return;
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 429) {
        const retryAfter = err.response?.headers?.['retry-after'];
        const mins = retryAfter ? Math.ceil(Number(retryAfter) / 60) : 15;
        setError(`Too many login attempts. Try again in ${mins} minute${mins !== 1 ? 's' : ''}.`);
      } else {
        setError(
          typeof detail === 'string' ? detail :
          Array.isArray(detail) ? (detail[0]?.msg || 'Invalid request.') :
          (status === 401 ? 'Invalid email or password.' : 'Login failed. Check the backend is running.')
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      height: '100vh',
      background: 'var(--bg-base)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Ambient glows */}
      <div style={{ position: 'fixed', top: '15%', left: '20%', width: 500, height: 300, background: 'radial-gradient(ellipse, rgba(249,115,22,0.07) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', bottom: '20%', right: '15%', width: 400, height: 250, background: 'radial-gradient(ellipse, rgba(59,130,246,0.05) 0%, transparent 70%)', pointerEvents: 'none' }} />

      {/* Main container */}
      <div style={{
        width: '100%', maxWidth: 920,
        display: 'flex',
        borderRadius: 20, overflow: 'hidden',
        border: '1px solid var(--border)',
        boxShadow: '0 40px 120px rgba(0,0,0,0.65)',
        position: 'relative', zIndex: 1,
        flexDirection: isMobile ? 'column' : 'row',
      }}>

        {/* ── Left Panel: Branding — hidden on narrow mobile ── */}
        <div style={{
          flex: 1,
          background: 'linear-gradient(160deg, #0c1726 0%, #091322 50%, #0a1520 100%)',
          padding: '48px 44px',
          display: isMobile ? 'none' : 'flex',
          flexDirection: 'column',
          borderRight: '1px solid var(--border)',
        }}>
          {/* Logo */}
          <div style={{ marginBottom: 36 }}>
            <div style={{ fontSize: 34, fontWeight: 900, letterSpacing: -1.5, color: 'var(--saffron)', marginBottom: 4, lineHeight: 1 }}>
              NETA.AI
            </div>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 2.5, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Election Intelligence Platform
            </div>
          </div>

          {/* Tagline */}
          <div style={{ fontSize: 21, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 36 }}>
            AI-Powered Campaign<br />Intelligence for Modern<br />Indian Elections
          </div>

          {/* Feature list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18, flex: 1 }}>
            {FEATURES.map(({ icon: Icon, color, label, desc }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'flex-start', gap: 13 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                  background: `${color}18`, border: `1px solid ${color}35`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginTop: 1,
                }}>
                  <Icon size={14} color={color} />
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Election countdown */}
          <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div>
                <div style={{ fontSize: 40, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--saffron)', lineHeight: 1 }}>
                  {daysLeft}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1.2, marginTop: 3 }}>
                  Days to Election
                </div>
              </div>
              <div style={{ flex: 1, paddingLeft: 20, borderLeft: '1px solid var(--border)' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 2 }}>
                  Serilingampally Assembly Constituency (AC-52)
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Telangana State · 28 May 2026</div>
                <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span className="live-dot" />
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>NETA-CORE active</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right Panel: Form ── */}
        <div style={{
          width: isMobile ? '100%' : 400,
          flexShrink: 0,
          background: 'var(--bg-card)',
          padding: isMobile ? '32px 24px' : '48px 40px',
          display: 'flex', flexDirection: 'column', justifyContent: 'center',
        }}>
          {/* Form header */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>
              Campaign Access
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Serilingampally (AC-52) Campaign HQ · Authorised access only
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: 0.8, textTransform: 'uppercase' }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="search-input"
                style={{ width: '100%', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ marginBottom: 22 }}>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: 0.8, textTransform: 'uppercase' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="search-input"
                  style={{ width: '100%', boxSizing: 'border-box', paddingRight: 40 }}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  style={{
                    position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                    display: 'flex', padding: 0,
                  }}
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            {error && (
              <div style={{
                background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 8, padding: '10px 12px',
                fontSize: 12, color: 'var(--red)', marginBottom: 16,
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '12px 0', fontSize: 13, opacity: loading ? 0.75 : 1 }}
            >
              <LogIn size={14} />
              {loading ? 'Signing in…' : 'Sign in to Campaign HQ'}
            </button>
          </form>

          {/* Demo credentials — development only, never shown in production */}
          {import.meta.env.DEV && (
            <div style={{
              marginTop: 24,
              padding: '14px 16px',
              background: 'var(--bg-elevated)',
              border: '1px solid rgba(245,158,11,0.3)',
              borderRadius: 10,
            }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--yellow)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>
                Dev Mode · Demo Credentials
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {[
                  { role: 'Admin', cred: 'admin@netaai.in · Admin123!Secure' },
                  { role: 'API Test', cred: 'apitest.bm@gmail.com', muted: true },
                ].map(({ role, cred, muted }) => (
                  <div key={role} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 4,
                      background: 'var(--bg-base)', border: '1px solid var(--border)',
                      color: 'var(--text-muted)', textTransform: 'uppercase',
                    }}>{role}</span>
                    <span style={{ fontSize: 11, color: muted ? 'var(--text-muted)' : 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {cred}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: 20, textAlign: 'center', fontSize: 10, color: 'var(--text-dim)' }}>
            NETA.AI Phase 2 · Serilingampally AC-52 · 2026 Campaign
          </div>
        </div>
      </div>
    </div>
  );
}
