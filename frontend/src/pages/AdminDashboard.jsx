import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts';
import { RefreshCw, AlertCircle, CheckCircle, XCircle, Server, Cpu, Database, Layers, Activity } from 'lucide-react';
import { getAdminSystem, getAdminQueues, getAdminIngestion, getAdminScores, getAdminAlertStats } from '../api/admin';

function StatusDot({ ok }) {
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: ok ? 'var(--green)' : 'var(--red)',
      boxShadow: ok ? '0 0 6px var(--green)' : '0 0 6px var(--red)',
    }} />
  );
}

function formatTs(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function statusColor(status) {
  if (!status) return 'var(--text-muted)';
  const s = status.toLowerCase();
  if (s === 'success' || s === 'completed' || s === 'done') return 'var(--green)';
  if (s === 'running' || s === 'in_progress' || s === 'pending') return 'var(--yellow)';
  return 'var(--red)';
}

function statusBadgeClass(status) {
  if (!status) return 'badge-gray';
  const s = status.toLowerCase();
  if (s === 'success' || s === 'completed' || s === 'done') return 'badge-green';
  if (s === 'running' || s === 'in_progress' || s === 'pending') return 'badge-yellow';
  return 'badge-red';
}

const ALERT_COLORS = ['var(--red)', 'var(--yellow)', 'var(--blue)', 'var(--purple)', 'var(--green)'];

export default function AdminDashboard() {
  const [system, setSystem]     = useState(null);
  const [queues, setQueues]     = useState(null);
  const [ingestion, setIngestion] = useState(null);
  const [scores, setScores]     = useState(null);
  const [alertStats, setAlertStats] = useState(null);
  const [errors, setErrors]     = useState({});
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading]   = useState(true);

  const load = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    const errs = {};
    await Promise.allSettled([
      getAdminSystem().then(setSystem).catch(() => { errs.system = true; }),
      getAdminQueues().then(setQueues).catch(() => { errs.queues = true; }),
      getAdminIngestion().then(setIngestion).catch(() => { errs.ingestion = true; }),
      getAdminScores().then(setScores).catch(() => { errs.scores = true; }),
      getAdminAlertStats().then(setAlertStats).catch(() => { errs.alertStats = true; }),
    ]);
    setErrors(errs);
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => { load(); }, []);

  const isForbidden = Object.keys(errors).length === 5;

  // Normalise alert stats into chart-friendly array
  const alertChartData = (() => {
    if (!alertStats) return [];
    if (Array.isArray(alertStats)) return alertStats;
    // object keyed by agent/type
    return Object.entries(alertStats).map(([name, value]) => ({
      name,
      count: typeof value === 'number' ? value : (value?.count ?? value?.total ?? 0),
    }));
  })();

  // Normalise queue data
  const queueList = (() => {
    if (!queues) return [];
    if (Array.isArray(queues)) return queues;
    return Object.entries(queues).map(([name, depth]) => ({
      name,
      depth: typeof depth === 'number' ? depth : (depth?.messages ?? depth?.depth ?? 0),
    }));
  })();

  const ingestionItems = (() => {
    if (!ingestion) return [];
    return Array.isArray(ingestion) ? ingestion : ingestion.items || ingestion.jobs || [];
  })();

  const maxQueueDepth = Math.max(...queueList.map(q => q.depth), 1);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">System Administration</div>
          <div className="page-subtitle">
            NETA-CORE · Infrastructure health · Superuser access required
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 12,
            color: 'var(--red)', background: 'var(--red-dim)', border: '1px solid rgba(220,38,38,0.3)',
            letterSpacing: 0.5,
          }}>
            ADMIN ONLY
          </span>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => load(true)}
            disabled={refreshing}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={12} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      <div className="page-body">
        {isForbidden && (
          <div style={{
            padding: '20px 24px', borderRadius: 12,
            background: 'rgba(220,38,38,0.07)', border: '1px solid rgba(220,38,38,0.25)',
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <XCircle size={20} color="var(--red)" />
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--red)', marginBottom: 3 }}>Access Denied</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Admin endpoints require superuser role. Your account does not have sufficient privileges.
              </div>
            </div>
          </div>
        )}

        {!isForbidden && Object.keys(errors).length > 0 && (
          <div style={{
            padding: '10px 14px', marginBottom: 16, borderRadius: 8,
            background: 'rgba(217,119,6,0.1)', border: '1px solid rgba(217,119,6,0.3)',
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--yellow)',
          }}>
            <AlertCircle size={13} />
            Some admin sections unavailable — partial data shown.
          </div>
        )}

        {/* ── System Info ─────────────────────────────────────── */}
        <div className="grid-2 section-gap">
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Server size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />System Info</span>
              {system && <span className="live-badge"><span className="live-dot" />Running</span>}
            </div>
            <div className="card-body">
              {loading && !system ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                  {[0,1,2,3,4,5,6].map(i => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
                      <div className="skeleton" style={{ height: 11, width: 80 }} />
                      <div className="skeleton" style={{ height: 11, width: 120 }} />
                    </div>
                  ))}
                </div>
              ) : system ? (
                <div>
                  {[
                    { label: 'App Name',     value: system.app_name || system.name || 'NETA.AI' },
                    { label: 'Version',      value: system.version || system.app_version || '—' },
                    { label: 'Environment',  value: system.environment || system.env || '—' },
                    { label: 'Debug Mode',   value: system.debug != null ? String(system.debug) : '—' },
                    { label: 'Uptime',       value: system.uptime_seconds != null ? `${Math.round(system.uptime_seconds / 60)}m` : (system.uptime || '—') },
                    { label: 'DB Status',    value: <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><StatusDot ok={system.db_ok ?? system.database_ok ?? true} />{system.db_ok !== false ? 'Connected' : 'Error'}</span> },
                    { label: 'Redis Status', value: <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><StatusDot ok={system.redis_ok ?? true} />{system.redis_ok !== false ? 'Connected' : 'Error'}</span> },
                  ].map(({ label, value }) => (
                    <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                      <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{label}</span>
                      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', fontFamily: typeof value === 'string' ? 'var(--font-mono)' : undefined }}>
                        {value}
                      </span>
                    </div>
                  ))}
                  {/* Active agents */}
                  {(system.agents || system.active_agents) && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--text-muted)', marginBottom: 8 }}>Active Agents</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {(system.agents || system.active_agents || []).map(agent => (
                          <span key={agent} style={{
                            fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 20,
                            color: 'var(--green)', background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.3)',
                          }}>
                            {agent}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>System info unavailable.</div>
              )}
            </div>
          </div>

          {/* Queue depths */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Layers size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />Task Queues</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Celery / Redis</span>
            </div>
            <div className="card-body">
              {loading && !queues ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {[0,1,2,3].map(i => (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div className="skeleton" style={{ height: 11, width: 110 }} />
                        <div className="skeleton" style={{ height: 11, width: 55 }} />
                      </div>
                      <div className="skeleton" style={{ height: 6, borderRadius: 3 }} />
                    </div>
                  ))}
                </div>
              ) : queueList.length > 0 ? (
                <div>
                  {queueList.map((q) => (
                    <div key={q.name} style={{ marginBottom: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{q.name}</span>
                        <span style={{
                          fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)',
                          color: q.depth === 0 ? 'var(--green)' : q.depth < 10 ? 'var(--yellow)' : 'var(--red)',
                        }}>
                          {q.depth} tasks
                        </span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{
                          width: `${Math.min((q.depth / maxQueueDepth) * 100, 100)}%`,
                          background: q.depth === 0 ? 'var(--green)' : q.depth < 10 ? 'var(--yellow)' : 'var(--red)',
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {errors.queues ? 'Queue data unavailable.' : 'No queues found.'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Intelligence Scores ─────────────────────────────── */}
        {scores && (
          <div className="section-gap">
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Latest Intelligence Scores — Serilingampally AC-52
            </div>
            <div className="grid-4">
              {[
                { label: 'Win Probability',        key: 'win_probability',           color: 'var(--green)',  mult: 100 },
                { label: 'Opposition Momentum',    key: 'opposition_momentum_score', color: 'var(--red)',   mult: 100 },
                { label: 'Anti-Incumbency',        key: 'anti_incumbency_score',     color: 'var(--yellow)', mult: 100 },
                { label: 'Voter Engagement',       key: 'voter_engagement_score',    color: 'var(--blue)',  mult: 100 },
              ].map(({ label, key, color, mult }) => {
                const raw = scores[key];
                const val = raw != null ? (raw > 1 ? Math.round(raw) : Math.round(raw * mult)) : null;
                return (
                  <div key={key} className="stat-card" style={{ '--accent-color': color }}>
                    <div className="stat-label">{label}</div>
                    <div className="stat-value" style={{ fontSize: 28, color, fontFamily: 'var(--font-mono)' }}>
                      {val != null ? `${val}%` : '—'}
                    </div>
                    {scores.computed_at && (
                      <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4 }}>
                        {formatTs(scores.computed_at)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Alert Stats + Ingestion ─────────────────────────── */}
        <div className="grid-2 section-gap">
          {/* Alert stats chart */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Activity size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />Alert Volume by Agent</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>All time</span>
            </div>
            <div className="card-body">
              {loading && !alertStats ? (
                <div className="skeleton" style={{ height: 220, borderRadius: 8 }} />
              ) : alertChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={alertChartData} layout="vertical" margin={{ left: 8 }}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} width={70} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }}
                      formatter={(v) => [v, 'Alerts']}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {alertChartData.map((_, i) => (
                        <Cell key={i} fill={ALERT_COLORS[i % ALERT_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {errors.alertStats ? 'Alert stats unavailable.' : 'No alert data.'}
                </div>
              )}
            </div>
          </div>

          {/* Ingestion history */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Database size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />Ingestion Jobs</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Recent history</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {loading && !ingestion ? (
                <table className="data-table">
                  <thead>
                    <tr><th>Job Type</th><th>Status</th><th>Records</th><th>Started</th><th>Completed</th></tr>
                  </thead>
                  <tbody>
                    {[0,1,2,3].map(i => (
                      <tr key={i}>
                        {[90, 60, 45, 100, 100].map((w, j) => (
                          <td key={j}><div className="skeleton" style={{ height: 12, width: w, borderRadius: 4 }} /></td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : ingestionItems.length > 0 ? (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Job Type</th>
                      <th>Status</th>
                      <th>Records</th>
                      <th>Started</th>
                      <th>Completed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ingestionItems.slice(0, 10).map((job, i) => (
                      <tr key={job.id || i}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                          {job.job_type || job.type || job.name || '—'}
                        </td>
                        <td>
                          <span className={`badge ${statusBadgeClass(job.status)}`}>
                            {job.status || '—'}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                          {job.records_processed ?? job.count ?? '—'}
                        </td>
                        <td style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {formatTs(job.started_at || job.created_at)}
                        </td>
                        <td style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {formatTs(job.completed_at || job.finished_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: 12 }}>
                  {errors.ingestion ? 'Ingestion history unavailable.' : 'No ingestion jobs found.'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Agent health grid ───────────────────────────────── */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title"><Cpu size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />NETA-CORE Agent Registry</span>
          </div>
          <div className="card-body">
            <div className="grid-4">
              {[
                { name: 'VAYU',     desc: 'Ground Intelligence',       color: 'var(--green)' },
                { name: 'VANI',     desc: 'Media & Content Analysis',  color: 'var(--blue)' },
                { name: 'VIVEK',    desc: 'Opposition Intelligence',    color: 'var(--red)' },
                { name: 'VICHAR',   desc: 'Constituency Profiling',     color: 'var(--purple)' },
                { name: 'VISHLESHAN', desc: 'Candidate Assessment',    color: 'var(--saffron)' },
                { name: 'VICHARAK', desc: 'Strategic Advisory',        color: 'var(--yellow)' },
                { name: 'VAHAN',    desc: 'Campaign Logistics',         color: 'var(--blue)' },
                { name: 'CORE',     desc: 'Orchestration & Briefs',    color: 'var(--green)' },
              ].map(({ name, desc, color }) => (
                <div key={name} style={{
                  padding: '12px 14px', borderRadius: 8,
                  background: `${color}08`, border: `1px solid ${color}22`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, boxShadow: `0 0 5px ${color}`, display: 'inline-block' }} />
                    <span style={{ fontSize: 12, fontWeight: 800, color, letterSpacing: 0.5 }}>{name}</span>
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
