import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, MapPin, Activity, Map, FileText, ShieldAlert,
  LogOut, User, Newspaper, ClipboardList, Settings, KeyRound, X, Eye, EyeOff, CheckCircle, AlertCircle,
  Search, Table2, Users, Database, Upload, MessageSquare,
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { candidate, constituency } from '../data/mockData';
import { changePassword } from '../api/auth';

const navItems = [
  {
    section: 'OVERVIEW',
    links: [
      { to: '/command-centre',            label: 'Command Centre',      Icon: LayoutDashboard },
      { to: '/candidate-brief',           label: 'Candidate Brief',     Icon: FileText },
    ],
  },
  {
    section: 'INTELLIGENCE',
    links: [
      { to: '/constituency-intelligence', label: 'Constituency Intel',  Icon: MapPin },
      { to: '/ground-pulse',              label: 'Ground Pulse',        Icon: Activity },
      { to: '/opposition-intelligence',   label: 'Opposition Intel',    Icon: ShieldAlert },
      { to: '/news-intelligence',         label: 'News Intelligence',   Icon: Newspaper },
    ],
  },
  {
    section: 'OPERATIONS',
    links: [
      { to: '/booth-management',          label: 'Booth Management',    Icon: Map },
      { to: '/field-reports',             label: 'Field Reports',       Icon: ClipboardList },
    ],
  },
  {
    section: 'DATA',
    links: [
      { to: '/constituency-demographics', label: 'Demographics',        Icon: Users },
      { to: '/booth-intelligence',        label: 'Booth Raw Data',      Icon: Table2 },
      { to: '/data-sources',              label: 'Data Sources',        Icon: Database },
      { to: '/voter-roll-upload',         label: 'Voter Roll Upload',   Icon: Upload },
      { to: '/telegram-alerts',           label: 'Telegram Alerts',     Icon: MessageSquare },
    ],
  },
];

function ChangePasswordModal({ onClose }) {
  const [current, setCurrent]   = useState('');
  const [next, setNext]         = useState('');
  const [confirm, setConfirm]   = useState('');
  const [showCur, setShowCur]   = useState(false);
  const [showNew, setShowNew]   = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult]     = useState(null); // { ok, msg }

  const handleSubmit = async () => {
    if (!current || !next || !confirm) { setResult({ ok: false, msg: 'All fields are required.' }); return; }
    if (next.length < 8) { setResult({ ok: false, msg: 'New password must be at least 8 characters.' }); return; }
    if (next !== confirm) { setResult({ ok: false, msg: 'New passwords do not match.' }); return; }
    setSubmitting(true);
    setResult(null);
    try {
      await changePassword(current, next);
      setResult({ ok: true, msg: 'Password changed successfully.' });
      setCurrent(''); setNext(''); setConfirm('');
    } catch (e) {
      const detail = e.response?.data?.detail;
      setResult({ ok: false, msg: detail || 'Change failed. Check your current password.' });
    } finally {
      setSubmitting(false);
    }
  };

  const Field = ({ label, value, onChange, show, onToggle, placeholder }) => (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 5 }}>
        {label}
      </label>
      <div style={{ position: 'relative' }}>
        <input
          type={show ? 'text' : 'password'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '8px 36px 8px 10px', borderRadius: 7,
            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: 13, outline: 'none',
          }}
          onFocus={e => { e.target.style.borderColor = 'var(--saffron)'; }}
          onBlur={e => { e.target.style.borderColor = 'var(--border)'; }}
        />
        <button
          type="button"
          onClick={onToggle}
          style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
        >
          {show ? <EyeOff size={13} /> : <Eye size={13} />}
        </button>
      </div>
    </div>
  );

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24,
    }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{
        background: 'var(--bg-surface)', borderRadius: 14, border: '1px solid var(--border)',
        width: '100%', maxWidth: 380, boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <KeyRound size={15} color="var(--saffron)" />
            <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Change Password</span>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: '20px' }}>
          {result && (
            <div style={{
              padding: '8px 12px', marginBottom: 14, borderRadius: 6,
              background: result.ok ? 'rgba(16,185,129,0.1)' : 'rgba(220,38,38,0.1)',
              border: `1px solid ${result.ok ? 'rgba(16,185,129,0.3)' : 'rgba(220,38,38,0.3)'}`,
              display: 'flex', alignItems: 'center', gap: 6,
              fontSize: 12, color: result.ok ? 'var(--green)' : 'var(--red)',
            }}>
              {result.ok ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
              {result.msg}
            </div>
          )}

          <Field label="Current Password" value={current} onChange={setCurrent} show={showCur} onToggle={() => setShowCur(v => !v)} placeholder="••••••••" />
          <Field label="New Password" value={next} onChange={setNext} show={showNew} onToggle={() => setShowNew(v => !v)} placeholder="Min 8 characters" />
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 5 }}>
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Re-enter new password"
              style={{
                width: '100%', boxSizing: 'border-box',
                padding: '8px 10px', borderRadius: 7,
                background: 'var(--bg-elevated)', border: `1px solid ${confirm && confirm !== next ? 'var(--red)' : 'var(--border)'}`,
                color: 'var(--text-primary)', fontSize: 13, outline: 'none',
              }}
              onFocus={e => { e.target.style.borderColor = confirm !== next ? 'var(--red)' : 'var(--saffron)'; }}
              onBlur={e => { e.target.style.borderColor = confirm && confirm !== next ? 'var(--red)' : 'var(--border)'; }}
            />
            {confirm && confirm !== next && (
              <div style={{ fontSize: 10, color: 'var(--red)', marginTop: 4 }}>Passwords do not match</div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-outline" style={{ flex: 1, justifyContent: 'center' }} onClick={onClose} disabled={submitting}>Cancel</button>
            <button className="btn btn-primary" style={{ flex: 2, justifyContent: 'center' }} onClick={handleSubmit} disabled={submitting || result?.ok}>
              {submitting ? 'Changing…' : 'Change Password'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar({ onOpenPalette, mobileOpen = false, onMobileClose }) {
  const { user, logout } = useAuth();
  const [showChangePassword, setShowChangePassword] = useState(false);

  const daysLeft = Math.max(
    0,
    Math.round((new Date('2027-05-28') - new Date()) / (1000 * 60 * 60 * 24))
  );

  return (
    <>
      <aside className={`sidebar${mobileOpen ? ' sidebar--mobile-open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="logo-mark">NETA.AI</div>
          <div className="logo-sub">Election Intelligence Platform</div>
        </div>

        {/* Command Palette trigger */}
        <button
          onClick={onOpenPalette}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            margin: '0 12px 10px',
            padding: '7px 10px', borderRadius: 7,
            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
            cursor: 'pointer', color: 'var(--text-muted)',
            fontSize: 11, fontFamily: 'inherit',
            transition: 'border-color 0.15s',
            width: 'calc(100% - 24px)',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(249,115,22,0.4)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; }}
        >
          <Search size={11} />
          <span style={{ flex: 1, textAlign: 'left' }}>Search…</span>
          <kbd style={{
            fontSize: 8, padding: '1px 4px', borderRadius: 3,
            border: '1px solid var(--border)', background: 'var(--bg-base)',
            fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', flexShrink: 0,
          }}>⌘K</kbd>
        </button>

        {/* Campaign identity */}
        <div className="sidebar-campaign">
          <div className="cand-name">{candidate.name}</div>
          <div className="cand-meta">{constituency.fullName}</div>
          <span className="party-badge">
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: candidate.partyColor, display: 'inline-block' }} />
            {candidate.partyShort}
          </span>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          {navItems.map(({ section, links }) => (
            <div key={section}>
              <div className="sidebar-section-label">{section}</div>
              {links.map(({ to, label, Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
                >
                  <Icon size={14} className="link-icon" />
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
          {(user?.role === 'superuser' || user?.is_superuser) && (
            <div>
              <div className="sidebar-section-label">SYSTEM</div>
              <NavLink to="/admin" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
                <Settings size={14} className="link-icon" />
                Admin Dashboard
              </NavLink>
            </div>
          )}
        </nav>

        {/* Countdown footer */}
        <div className="sidebar-footer">
          <div className="election-countdown">
            <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Days to Election
            </span>
            <span className="days-value">{daysLeft}</span>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
              28 May 2027
            </div>
          </div>

          {/* Live indicator */}
          <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className="live-dot" />
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>NETA-CORE active</span>
            <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>v1.0</span>
          </div>

          {/* User section */}
          {user && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div style={{
                  width: 26, height: 26, borderRadius: 6,
                  background: 'var(--saffron-dim)', border: '1px solid var(--saffron)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <User size={12} color="var(--saffron)" />
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {user.email?.split('@')[0]}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    {user.role}
                  </div>
                </div>
                <button
                  onClick={() => setShowChangePassword(true)}
                  title="Change password"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', flexShrink: 0, padding: 2 }}
                  onMouseEnter={e => { e.currentTarget.style.color = 'var(--saffron)'; }}
                  onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; }}
                >
                  <KeyRound size={12} />
                </button>
              </div>
              <button
                onClick={logout}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  width: '100%', background: 'none', border: '1px solid var(--border)',
                  borderRadius: 6, padding: '6px 10px', cursor: 'pointer',
                  color: 'var(--text-secondary)', fontSize: 11, fontWeight: 600,
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--red)'; e.currentTarget.style.color = 'var(--red)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
              >
                <LogOut size={11} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </aside>

      {showChangePassword && <ChangePasswordModal onClose={() => setShowChangePassword(false)} />}
    </>
  );
}
