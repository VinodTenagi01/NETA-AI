import { useState, useMemo, useEffect } from 'react';
import { workerSummary, constituency } from '../data/mockData';
import { Search, X, RefreshCw, AlertCircle, FileText, Activity, Download } from 'lucide-react';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { getBoothHeatmap } from '../api/intelligence';
import { getBoothPulse, getBoothReports } from '../api/vayu';

const STATUS_COLOR = {
  fortress: { color: '#059669', bg: 'rgba(5,150,105,0.12)', label: 'Fortress' },
  swing:    { color: '#d97706', bg: 'rgba(217,119,6,0.12)',  label: 'Swing' },
  hostile:  { color: '#dc2626', bg: 'rgba(220,38,38,0.12)',  label: 'Hostile' },
};

const RISK_COLOR = {
  critical: { color: '#dc2626', label: 'Critical' },
  high:     { color: '#d97706', label: 'High' },
  medium:   { color: '#2563eb', label: 'Medium' },
  low:      { color: '#059669', label: 'Low' },
};

function moodColor(mood) {
  if (!mood) return 'var(--text-muted)';
  if (mood >= 4) return 'var(--green)';
  if (mood >= 3) return 'var(--yellow)';
  return 'var(--red)';
}

function formatRelTime(ts) {
  if (!ts) return '—';
  const diff = (Date.now() - new Date(ts)) / 1000;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function BoothDetail({ booth, onClose }) {
  const [tab, setTab] = useState(0);
  const [pulse, setPulse] = useState(null);
  const [reports, setReports] = useState([]);
  const [liveLoading, setLiveLoading] = useState(false);

  const boothId = booth?.booth_id || booth?.id || booth?.code;

  useEffect(() => {
    if (!boothId) return;
    setLiveLoading(true);
    Promise.allSettled([
      getBoothPulse(boothId).then(setPulse).catch(() => {}),
      getBoothReports(boothId, 5).then(d => {
        const items = Array.isArray(d) ? d : d.items || [];
        setReports(items);
      }).catch(() => {}),
    ]).finally(() => setLiveLoading(false));
  }, [boothId]);

  if (!booth) return null;

  const s = STATUS_COLOR[booth.status] || STATUS_COLOR.swing;
  const r = RISK_COLOR[booth.risk_level] || RISK_COLOR.medium;

  const tabs = ['Overview', 'Live Pulse', 'Reports'];

  return (
    <div style={{
      position: 'fixed', top: 0, right: 0, width: 390, height: '100vh',
      background: 'var(--bg-surface)', borderLeft: '1px solid var(--border)',
      zIndex: 50, display: 'flex', flexDirection: 'column', boxShadow: '-8px 0 32px rgba(0,0,0,0.5)',
    }}>
      {/* Header */}
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 800, color: s.color }}>{booth.code}</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{booth.name}</div>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <X size={18} />
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        {tabs.map((t, i) => (
          <button key={t} onClick={() => setTab(i)} style={{
            flex: 1, padding: '9px 4px', background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 11, fontWeight: 600,
            color: tab === i ? 'var(--saffron)' : 'var(--text-muted)',
            borderBottom: tab === i ? '2px solid var(--saffron)' : '2px solid transparent',
            transition: 'all 0.15s',
          }}>
            {t}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 18 }}>
        {/* ── OVERVIEW TAB ── */}
        {tab === 0 && (
          <>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
              <span className={`badge ${booth.status === 'fortress' ? 'badge-green' : booth.status === 'swing' ? 'badge-yellow' : 'badge-red'}`}>
                {s.label}
              </span>
              <span className={`zone-pill zone-${(booth.zone || '').toLowerCase()}`}>{booth.zone} Zone</span>
              <span className={`badge ${booth.is_covered ? 'badge-green' : 'badge-gray'}`}>
                {booth.is_covered ? 'Covered' : 'Not Covered'}
              </span>
              {booth.risk_level && (
                <span className="badge" style={{ color: r.color, background: `${r.color}18`, border: `1px solid ${r.color}44` }}>
                  {r.label} Risk
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
              {[
                { label: 'Registered Voters', value: (booth.total_voters || 0).toLocaleString(), color: 'var(--text-primary)' },
                { label: 'Risk Score',         value: booth.risk_score != null ? `${Math.round(booth.risk_score * 100)}%` : '—', color: r.color },
                { label: 'Avg Mood',           value: booth.avg_mood != null ? `${booth.avg_mood.toFixed(1)}/5` : '—', color: moodColor(booth.avg_mood) },
                { label: 'Reports (7d)',        value: booth.report_count_7d ?? '—', color: 'var(--blue)' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: 'var(--bg-card)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>{label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--font-mono)', color }}>{value}</div>
                </div>
              ))}
            </div>

            {booth.risk_score != null && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Risk Score</span>
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{Math.round(booth.risk_score * 100)}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${Math.round(booth.risk_score * 100)}%`, background: r.color }} />
                </div>
              </div>
            )}

            <div className="divider" />
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Ground Details</div>
              {[
                { label: 'Top Issue',           value: booth.top_issue || '—' },
                { label: 'Opposition Activity', value: booth.opposition_activity || '—' },
                { label: 'Voter Engagement',    value: booth.voter_engagement || '—' },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{label}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: label === 'Opposition Activity' && (value === 'High' || value === true) ? 'var(--red)' : 'var(--text-primary)' }}>
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Schedule Candidate Visit</button>
              <button className="btn btn-outline" style={{ width: '100%', justifyContent: 'center' }}>Assign Additional Workers</button>
            </div>
          </>
        )}

        {/* ── LIVE PULSE TAB ── */}
        {tab === 1 && (
          <>
            {liveLoading && <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 12 }}>Fetching live pulse…</div>}
            {pulse ? (
              <div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                  <Activity size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                  Latest Ground Pulse · {formatRelTime(pulse.computed_at || pulse.created_at)}
                </div>
                {[
                  { label: 'Mood Score',          value: pulse.avg_mood != null ? `${Number(pulse.avg_mood).toFixed(1)}/5` : '—', color: moodColor(pulse.avg_mood) },
                  { label: 'Reports This Week',   value: pulse.report_count ?? pulse.report_count_7d ?? '—', color: 'var(--blue)' },
                  { label: 'Escalations',         value: pulse.escalation_count ?? '—', color: 'var(--red)' },
                  { label: 'Workers Active',      value: pulse.workers_active ?? pulse.worker_count ?? '—', color: 'var(--green)' },
                  { label: 'Opposition Activity', value: pulse.opposition_activity != null ? String(pulse.opposition_activity) : '—', color: pulse.opposition_activity ? 'var(--red)' : 'var(--text-muted)' },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{label}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color }}>{value}</span>
                  </div>
                ))}
                {pulse.top_issues?.length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Top Issues</div>
                    {pulse.top_issues.slice(0, 4).map((issue, i) => (
                      <span key={i} className="badge badge-blue" style={{ marginRight: 5, marginBottom: 5 }}>{issue}</span>
                    ))}
                  </div>
                )}
              </div>
            ) : !liveLoading && (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '16px 0' }}>
                No pulse data available for this booth.
              </div>
            )}
          </>
        )}

        {/* ── REPORTS TAB ── */}
        {tab === 2 && (
          <>
            {liveLoading && <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 12 }}>Loading reports…</div>}
            {reports.length > 0 ? (
              reports.map((rep, i) => (
                <div key={rep.id || i} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: i < reports.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 14, fontWeight: 900, fontFamily: 'var(--font-mono)', color: moodColor(rep.mood_score) }}>
                      {rep.mood_score != null ? Number(rep.mood_score).toFixed(1) : '—'}
                    </span>
                    {(rep.is_escalated || rep.opposition_activity_observed) && (
                      <span className="badge badge-red" style={{ fontSize: 9 }}>Escalated</span>
                    )}
                    <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {formatRelTime(rep.created_at)}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {rep.content || rep.notes || '—'}
                  </div>
                  {(rep.top_issues || rep.issues_reported || rep.issues || []).length > 0 && (
                    <div style={{ marginTop: 6, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {(rep.top_issues || rep.issues_reported || rep.issues).map((issue, j) => (
                        <span key={j} className="badge badge-blue" style={{ fontSize: 9 }}>{issue}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            ) : !liveLoading && (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '16px 0' }}>
                No recent reports for this booth.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function BoothManagement() {
  const [booths, setBooths] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [search, setSearch] = useState('');
  const [filterZone, setFilterZone] = useState('All');
  const [filterStatus, setFilterStatus] = useState('All');
  const [filterCoverage, setFilterCoverage] = useState('All');
  const [selected, setSelected] = useState(null);

  const loadBooths = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    try {
      const data = await getBoothHeatmap();
      setBooths(Array.isArray(data) ? data : data.booths || []);
      setError(null);
    } catch {
      setError('Could not load booth data from server.');
    } finally {
      setLoading(false);
      setRefreshing(false);
      setInitialized(true);
    }
  };

  const { countdown, triggerNow } = useAutoRefresh(() => loadBooths(true), 120);

  useEffect(() => { loadBooths(); }, []);

  const zones = useMemo(() => ['All', ...new Set(booths.map(b => b.zone).filter(Boolean))], [booths]);

  const fortress = booths.filter(b => b.status === 'fortress').length;
  const swing    = booths.filter(b => b.status === 'swing').length;
  const hostile  = booths.filter(b => b.status === 'hostile').length;
  const covered  = booths.filter(b => b.is_covered).length;

  const filtered = useMemo(() => booths.filter(b => {
    if (search && !b.code?.toLowerCase().includes(search.toLowerCase()) &&
        !b.name?.toLowerCase().includes(search.toLowerCase()) &&
        !(b.top_issue || '').toLowerCase().includes(search.toLowerCase())) return false;
    if (filterZone !== 'All' && b.zone !== filterZone) return false;
    if (filterStatus !== 'All' && b.status !== filterStatus) return false;
    if (filterCoverage === 'Covered' && !b.is_covered) return false;
    if (filterCoverage === 'Uncovered' && b.is_covered) return false;
    return true;
  }), [booths, search, filterZone, filterStatus, filterCoverage]);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Booth Management</div>
          <div className="page-subtitle">VAYU Agent · {booths.length || constituency.totalBooths} booths · Live ground intelligence</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="live-badge"><span className="live-dot" /> VAYU Active</span>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => {
              const headers = ['"Code"', '"Name"', '"Zone"', '"Status"', '"Voters"', '"Covered"', '"Risk"', '"Risk Score"', '"Avg Mood"', '"Reports 7d"', '"Top Issue"'];
              const rows = filtered.map(b => [
                b.code, b.name || '', b.zone || '', b.status || '',
                b.total_voters || 0, b.is_covered ? 'Yes' : 'No',
                b.risk_level || '', b.risk_score != null ? Math.round(b.risk_score * 100) + '%' : '',
                b.avg_mood != null ? b.avg_mood.toFixed(1) : '', b.report_count_7d ?? '',
                (b.top_issue || '').replace(/"/g, '""'),
              ].map(v => `"${v}"`));
              const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
              const blob = new Blob([csv], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url; a.download = `booths-${new Date().toISOString().slice(0,10)}.csv`; a.click();
              URL.revokeObjectURL(url);
            }}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Download size={12} />
            CSV
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={triggerNow}
            disabled={refreshing}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={12} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            {refreshing ? 'Refreshing…' : `Refresh (${countdown}s)`}
          </button>
        </div>
      </div>

      <div className="page-body">
        {error && (
          <div style={{
            padding: '10px 14px', marginBottom: 16, borderRadius: 8,
            background: 'rgba(217,119,6,0.1)', border: '1px solid rgba(217,119,6,0.3)',
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--yellow)',
          }}>
            <AlertCircle size={13} />
            {typeof error === 'string' ? error : String(error?.message || error || '')}
          </div>
        )}

        {/* Summary stats */}
        {!initialized ? (
          <div className="grid-5 section-gap">
            {[0,1,2,3,4].map(i => (
              <div key={i} className="stat-card">
                <div className="skeleton" style={{ height: 11, width: '60%', marginBottom: 10 }} />
                <div className="skeleton" style={{ height: 32, width: '45%' }} />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid-5 section-gap">
            {[
              { label: 'Total Booths', value: booths.length || '—', color: 'var(--text-primary)' },
              { label: 'Fortress',     value: fortress,              color: '#059669' },
              { label: 'Swing',        value: swing,                 color: '#d97706' },
              { label: 'Hostile',      value: hostile,               color: '#dc2626' },
              { label: 'Covered',      value: booths.length ? `${covered}/${booths.length}` : '—', color: 'var(--saffron)' },
            ].map(({ label, value, color }) => (
              <div key={label} className="stat-card" style={{ '--accent-color': color }}>
                <div className="stat-label">{label}</div>
                <div className="stat-value" style={{ fontSize: 28, color }}>{value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Worker deployment (static) */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title">Worker Deployment</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {workerSummary.active} of {workerSummary.total} workers active today
            </span>
          </div>
          <div className="card-body">
            <div className="grid-4">
              {[
                { label: 'Active Today',     value: workerSummary.active,    pct: (workerSummary.active/workerSummary.total)*100,    color: 'var(--green)' },
                { label: 'On Leave',         value: workerSummary.onLeave,   pct: (workerSummary.onLeave/workerSummary.total)*100,    color: 'var(--yellow)' },
                { label: 'Inactive',         value: workerSummary.inactive,  pct: (workerSummary.inactive/workerSummary.total)*100,   color: 'var(--red)' },
                { label: 'Avg Contact Rate', value: `${workerSummary.avgContactRate}%`, pct: workerSummary.avgContactRate, color: 'var(--saffron)' },
              ].map(({ label, value, pct, color }) => (
                <div key={label} style={{ padding: 12, background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>{label}</div>
                  <div style={{ fontSize: 24, fontWeight: 800, fontFamily: 'var(--font-mono)', color }}>{value}</div>
                  <div className="progress-bar" style={{ marginTop: 8 }}>
                    <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Filters + Table */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Booth Directory ({filtered.length} booths)</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Click any booth for details · Live VAYU data</span>
          </div>

          <div style={{
            padding: '12px 16px', borderBottom: '1px solid var(--border)',
            display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
          }}>
            <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
              <Search size={12} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                className="search-input"
                style={{ paddingLeft: 28 }}
                placeholder="Search booth code, name, top issue…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <select className="select-input" value={filterZone} onChange={e => setFilterZone(e.target.value)}>
              {zones.map(z => <option key={z} value={z}>{z === 'All' ? 'All Zones' : z}</option>)}
            </select>
            <select className="select-input" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
              <option value="All">All Status</option>
              <option value="fortress">Fortress</option>
              <option value="swing">Swing</option>
              <option value="hostile">Hostile</option>
            </select>
            <select className="select-input" value={filterCoverage} onChange={e => setFilterCoverage(e.target.value)}>
              <option value="All">All Coverage</option>
              <option value="Covered">Covered</option>
              <option value="Uncovered">Uncovered</option>
            </select>
            {(filterZone !== 'All' || filterStatus !== 'All' || filterCoverage !== 'All' || search) && (
              <button className="btn btn-outline btn-sm" onClick={() => { setSearch(''); setFilterZone('All'); setFilterStatus('All'); setFilterCoverage('All'); }}>
                <X size={10} /> Clear
              </button>
            )}
          </div>

          <div style={{ overflowY: 'auto', maxHeight: 520 }}>
            {!initialized ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th><th>Zone</th><th>Status</th><th>Voters</th>
                    <th>Coverage</th><th>Risk Level</th><th>Risk Score</th>
                    <th>Avg Mood</th><th>Reports 7d</th><th>Top Issue</th><th>Opp. Activity</th>
                  </tr>
                </thead>
                <tbody>
                  {[0,1,2,3,4,5].map(i => (
                    <tr key={i}>
                      {[40, 60, 70, 50, 50, 60, 50, 40, 40, 90, 50].map((w, j) => (
                        <td key={j}><div className="skeleton" style={{ height: 12, width: w, borderRadius: 4 }} /></td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : filtered.length === 0 ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                {booths.length === 0 ? 'No booth data available.' : 'No booths match the current filters.'}
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Zone</th>
                    <th>Status</th>
                    <th>Voters</th>
                    <th>Coverage</th>
                    <th>Risk Level</th>
                    <th>Risk Score</th>
                    <th>Avg Mood</th>
                    <th>Reports 7d</th>
                    <th>Top Issue</th>
                    <th>Opp. Activity</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((b) => {
                    const s = STATUS_COLOR[b.status] || STATUS_COLOR.swing;
                    const r = RISK_COLOR[b.risk_level] || RISK_COLOR.medium;
                    const oppActive = b.opposition_activity === true || b.opposition_activity === 'High' || b.opposition_activity === 'high';
                    return (
                      <tr
                        key={b.code}
                        onClick={() => setSelected(selected?.code === b.code ? null : b)}
                        style={{ cursor: 'pointer', background: selected?.code === b.code ? 'var(--saffron-dim)' : undefined }}
                      >
                        <td>
                          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--saffron)' }}>{b.code}</span>
                        </td>
                        <td>
                          <span className={`zone-pill zone-${(b.zone || '').toLowerCase()}`}>{b.zone}</span>
                        </td>
                        <td>
                          <span className={`badge ${b.status === 'fortress' ? 'badge-green' : b.status === 'swing' ? 'badge-yellow' : 'badge-red'}`}>
                            {s.label}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{(b.total_voters || 0).toLocaleString()}</td>
                        <td>
                          <span className={`badge ${b.is_covered ? 'badge-green' : 'badge-gray'}`}>
                            {b.is_covered ? 'Yes' : 'No'}
                          </span>
                        </td>
                        <td>
                          <span className="badge" style={{ color: r.color, background: `${r.color}18`, border: `1px solid ${r.color}44` }}>
                            {r.label}
                          </span>
                        </td>
                        <td>
                          {b.risk_score != null ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <div className="progress-bar" style={{ width: 44 }}>
                                <div className="progress-fill" style={{ width: `${Math.round(b.risk_score * 100)}%`, background: r.color }} />
                              </div>
                              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>{Math.round(b.risk_score * 100)}%</span>
                            </div>
                          ) : '—'}
                        </td>
                        <td>
                          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: moodColor(b.avg_mood) }}>
                            {b.avg_mood != null ? b.avg_mood.toFixed(1) : '—'}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--blue)' }}>{b.report_count_7d ?? '—'}</td>
                        <td style={{ fontSize: 11, color: 'var(--text-secondary)', maxWidth: 140 }}>
                          <span title={b.top_issue}>
                            {b.top_issue ? (b.top_issue.length > 22 ? b.top_issue.slice(0, 22) + '…' : b.top_issue) : '—'}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontSize: 11, color: oppActive ? 'var(--red)' : typeof b.opposition_activity === 'string' && b.opposition_activity.toLowerCase() === 'medium' ? 'var(--yellow)' : 'var(--text-muted)' }}>
                            {b.opposition_activity != null ? String(b.opposition_activity) : '—'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {selected && <BoothDetail booth={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
