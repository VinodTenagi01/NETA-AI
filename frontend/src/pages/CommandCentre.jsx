import { useState, useEffect, useCallback, useRef } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import StatCard from '../components/StatCard';
import WinGauge from '../components/WinGauge';
import BoothMapGrid from '../components/BoothMapGrid';
import AgentPanel from '../components/AgentPanel';
import {
  constituency, winProbability, workerSummary, mediaMonitoring, contentQueue,
  aiIntelligenceBrief, campaignRecommendations, predictionFactors,
} from '../data/mockData';
import { getCommandCentreOverview, getAlertsLive, markAlertDone, getWinProbability } from '../api/intelligence';
import { Clock, TrendingUp, AlertTriangle, CheckSquare, RefreshCw, Check, Zap, Radio } from 'lucide-react';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { useSSE } from '../hooks/useSSE';
import { useToast } from '../store/ToastContext';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{label}</div>
      <div style={{ color: 'var(--green)' }}>Win %: {payload[0]?.value}%</div>
    </div>
  );
};

const MoodTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{label}</div>
      <div style={{ color: 'var(--saffron)' }}>Avg Mood: {payload[0]?.value}/5</div>
    </div>
  );
};

const trendData = winProbability.trendLabels.map((date, i) => ({
  date,
  prob: winProbability.trend[i],
}));

function AlertItem({ alert, onDone }) {
  const [actioning, setActioning] = useState(false);
  const [done, setDone] = useState(alert.is_actioned || alert.action_done || false);

  const typeClass = {
    critical: 'critical',
    warning: 'warning',
    info: 'info',
    success: 'success',
  }[alert.alert_type || alert.type] || 'info';

  const agentName = (alert.agent || '').toUpperCase();
  const timeStr = alert.created_at
    ? new Date(alert.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    : alert.time || '';

  const handleDone = async () => {
    setActioning(true);
    try {
      await markAlertDone(alert.id);
      setDone(true);
      setTimeout(() => onDone?.(alert.id), 600);
    } catch {
      setDone(true); // optimistic — remove from feed even if API fails
      setTimeout(() => onDone?.(alert.id), 600);
    } finally {
      setActioning(false);
    }
  };

  return (
    <div className={`alert-item ${typeClass}`} style={{ opacity: done ? 0.45 : 1, transition: 'opacity 0.4s' }}>
      <div className="alert-header">
        <span className="alert-agent">{agentName}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="alert-time">{timeStr}</span>
          {!done && (
            <button
              onClick={handleDone}
              disabled={actioning}
              title="Mark as actioned"
              style={{
                background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)',
                borderRadius: 5, padding: '2px 6px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 3,
                fontSize: 9, fontWeight: 700, color: 'var(--green)',
              }}
            >
              <Check size={9} /> {actioning ? '…' : 'Done'}
            </button>
          )}
          {done && (
            <span style={{ fontSize: 9, color: 'var(--green)', fontWeight: 700 }}>✓ Actioned</span>
          )}
        </div>
      </div>
      <div className="alert-text">{alert.message}</div>
      {(alert.action_required || alert.action) && !done && (
        <div className="alert-action">→ {alert.action_required || alert.action}</div>
      )}
    </div>
  );
}

export default function CommandCentre() {
  const [overview, setOverview] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [apiError, setApiError] = useState(false);
  const [approvedIds, setApprovedIds] = useState(new Set());
  const [sseConnected, setSseConnected] = useState(false);
  const [winProb, setWinProb] = useState(null);
  const alertSeenIdsRef = useRef(new Set());
  const { addToast } = useToast();

  // SSE — live alert push from server
  useSSE('/sse/alerts', {
    connected: () => setSseConnected(true),
    alert: (data) => {
      if (!alertSeenIdsRef.current.has(data.id)) {
        alertSeenIdsRef.current.add(data.id);
        setAlerts(prev => {
          const exists = prev.some(a => a.id === data.id);
          if (exists) return prev;
          return [data, ...prev].slice(0, 20);
        });
        if (data.type === 'critical') {
          addToast(`⚡ ${data.title || data.message}`, 'error');
        }
      }
    },
    error: () => setSseConnected(false),
  }, { enabled: !apiError });

  const fetchData = useCallback(async () => {
    setLoadingOverview(true);
    try {
      const [ovRes, alRes, wpRes] = await Promise.allSettled([
        getCommandCentreOverview(),
        getAlertsLive(),
        getWinProbability(),
      ]);
      if (ovRes.status === 'fulfilled') setOverview(ovRes.value);
      if (alRes.status === 'fulfilled') setAlerts(alRes.value?.items || []);
      if (wpRes.status === 'fulfilled') setWinProb(wpRes.value);
      setLastUpdated(new Date());
      setApiError(ovRes.status === 'rejected' && alRes.status === 'rejected');
    } catch {
      setApiError(true);
    } finally {
      setLoadingOverview(false);
      setInitialized(true);
    }
  }, []);

  const { countdown, triggerNow } = useAutoRefresh(fetchData, 60);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAlertDone = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  }, []);

  // Derive stats from API overview, fall back to mock
  const boothsCovered = overview?.today?.booths_covered ?? workerSummary.boothsCovered;
  const totalBooths = overview?.today?.total_booths ?? constituency.totalBooths;
  const avgMood = overview?.today?.avg_mood;
  const newAlerts = overview?.today?.new_alerts ?? 0;
  const coveragePct = totalBooths > 0 ? Math.round((boothsCovered / totalBooths) * 100) : 0;

  const criticalAlerts = alerts.filter(a => a.alert_type === 'critical' || a.type === 'critical').length;

  // Win probability — live API values with mock fallback
  const liveProb = winProb != null ? Math.round(winProb.overall_probability * 10) / 10 : null;
  const liveConf = winProb?.confidence_interval
    ? Math.max(0, Math.min(100, Math.round(100 - (winProb.confidence_interval[1] - winProb.confidence_interval[0]))))
    : null;
  const wpTrendDir = winProb ? (winProb.trend === 'declining' ? 'down' : 'up') : 'up';
  const wpTrendLabel = winProb
    ? ({ improving: 'Trending up', stable: 'Trend stable', declining: 'Trending down' }[winProb.trend] ?? 'Stable')
    : '+3 pts from yesterday';
  const wpBadgeText = winProb
    ? ({ improving: '↑ Improving', declining: '↓ Declining', stable: '→ Stable' }[winProb.trend] ?? 'Stable')
    : '+9 pts / 14 days';

  // Build mood trend from API overview or fall back to win probability trend
  const moodTrendData = overview?.mood_7d_trend?.map(p => ({
    date: p.date?.slice(5), // "05-07"
    mood: p.avg_mood != null ? Math.round(p.avg_mood * 10) / 10 : null,
  })).filter(p => p.mood != null) || [];

  const now = lastUpdated
    ? lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    : constituency.lastUpdated;

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="page-title">Command Centre</div>
          <div className="page-subtitle">
            {constituency.fullName} · {constituency.state} Assembly
            {apiError && <span style={{ color: 'var(--yellow)', marginLeft: 8 }}>· API unavailable — showing cached data</span>}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)' }}>
            <Clock size={12} />
            {now}
          </div>
          <button
            onClick={triggerNow}
            disabled={loadingOverview}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}
          >
            <RefreshCw size={12} style={{ animation: loadingOverview ? 'spin 1s linear infinite' : 'none' }} />
            {loadingOverview ? 'Refreshing…' : `Refresh (${countdown}s)`}
          </button>
          <span className="live-badge">
            <span className="live-dot" /> NETA-CORE LIVE
          </span>
          {sseConnected && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--blue)', padding: '2px 8px', borderRadius: 10, background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.25)' }}>
              <Radio size={10} /> SSE
            </span>
          )}
        </div>
      </div>

      <div className="page-body">
        {/* ─── Stat Row ─────────────────────────────────────── */}
        {!initialized && loadingOverview ? (
          <div className="grid-5 section-gap">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="stat-card">
                <div className="skeleton" style={{ height: 11, width: '55%', borderRadius: 4, marginBottom: 10 }} />
                <div className="skeleton" style={{ height: 34, width: '70%', borderRadius: 6, marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 10, width: '45%', borderRadius: 4 }} />
              </div>
            ))}
          </div>
        ) : (
        <div className="grid-5 section-gap">
          <StatCard
            label="Win Probability"
            value={`${liveProb ?? winProbability.current}%`}
            sub={`Confidence: ${liveConf ?? winProbability.confidence}%`}
            trend={wpTrendLabel}
            trendDir={wpTrendDir}
            accentColor="var(--green)"
          />
          <StatCard
            label="Booths Covered"
            value={`${boothsCovered}/${totalBooths}`}
            sub={`${coveragePct}% coverage`}
            trend={`${totalBooths - boothsCovered} booths uncovered`}
            trendDir="down"
            accentColor="var(--yellow)"
          />
          <StatCard
            label="Ground Mood"
            value={avgMood != null ? `${avgMood.toFixed(1)}/5` : `${workerSummary.avgContactRate}%`}
            sub={avgMood != null ? 'avg mood score' : 'avg contact rate'}
            accentColor="var(--blue)"
          />
          <StatCard
            label="Active Alerts"
            value={criticalAlerts || overview?.today?.new_alerts || 0}
            sub="critical alerts open"
            trend="Needs immediate action"
            trendDir={criticalAlerts > 0 ? 'down' : 'up'}
            accentColor="var(--red)"
          />
          <StatCard
            label="Days to Election"
            value={Math.max(0, Math.round((new Date('2026-05-28') - new Date()) / 86400000))}
            sub="28 May 2026"
            accentColor="var(--saffron)"
          />
        </div>
        )}

        {/* ─── Main 3-column layout ──────────────────────────── */}
        <div className="cols-main section-gap">

          {/* LEFT: Win Gauge + Trend */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Win Probability</span>
              <span className="badge badge-green">
                <TrendingUp size={9} /> {wpBadgeText}
              </span>
            </div>
            <div className="card-body" style={{ paddingTop: 8 }}>
              <WinGauge probability={liveProb ?? winProbability.current} size={250} />

              {/* Show mood trend from API if available, else win probability trend */}
              <div style={{ marginTop: 16 }}>
                {moodTrendData.length > 0 ? (
                  <>
                    <div className="card-title" style={{ marginBottom: 8 }}>7-Day Ground Mood</div>
                    <ResponsiveContainer width="100%" height={90}>
                      <LineChart data={moodTrendData}>
                        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="date" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                        <YAxis domain={[1, 5]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={20} />
                        <Tooltip content={<MoodTooltip />} />
                        <Line type="monotone" dataKey="mood" stroke="var(--saffron)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'var(--saffron)' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </>
                ) : (
                  <>
                    <div className="card-title" style={{ marginBottom: 8 }}>14-Day Trend</div>
                    <ResponsiveContainer width="100%" height={90}>
                      <LineChart data={trendData}>
                        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="date" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} interval={3} />
                        <YAxis domain={[50, 75]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={26} />
                        <Tooltip content={<CustomTooltip />} />
                        <Line type="monotone" dataKey="prob" stroke="var(--green)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'var(--green)' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </>
                )}
              </div>

              {/* Intelligence scores from API */}
              {overview && (
                <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {[
                    { label: 'Opposition', value: overview.opposition_momentum_score, color: 'var(--red)' },
                    { label: 'Anti-incumbency', value: overview.anti_incumbency_score, color: 'var(--yellow)' },
                    { label: 'Voter Engagement', value: overview.voter_engagement_score, color: 'var(--green)' },
                    { label: 'Issue Severity', value: overview.issue_severity_score, color: 'var(--saffron)' },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '8px 10px' }}>
                      <div style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
                      <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'var(--font-mono)', color }}>
                        {Math.round((value || 0) * 100)}
                      </div>
                      <div className="progress-bar" style={{ marginTop: 4, height: 3 }}>
                        <div className="progress-fill" style={{ width: `${(value || 0) * 100}%`, background: color }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Margin range (static) */}
              {!overview && (
                <div style={{ marginTop: 14, padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>Projected Margin Range</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: 'var(--green)' }}>
                    +{winProbability.marginRange.low.toLocaleString()} — +{winProbability.marginRange.high.toLocaleString()}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginTop: 2 }}>votes lead (74% confidence)</div>
                </div>
              )}
            </div>
          </div>

          {/* MIDDLE: Booth Map */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Constituency Booth Map</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                {totalBooths} booths · 2,48,432 voters
              </span>
            </div>
            <BoothMapGrid compact />
            <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Overall Coverage</span>
                <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--yellow)' }}>
                  {boothsCovered}/{totalBooths}
                </span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${coveragePct}%`, background: 'var(--yellow)' }} />
              </div>

              {/* High-risk booths from API */}
              {overview?.high_risk_booths?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 700, letterSpacing: 0.5 }}>
                    HIGH-RISK BOOTHS
                  </div>
                  {overview.high_risk_booths.slice(0, 4).map(b => (
                    <div key={b.booth_id} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--red)' }}>{b.code}</span>
                      <span style={{ flex: 1, fontSize: 11, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.name}</span>
                      <span className={`badge badge-${b.risk_level === 'critical' ? 'red' : b.risk_level === 'high' ? 'yellow' : 'gray'}`}>
                        {Math.round((b.risk_score || 0) * 100)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: Alert Feed */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <span className="card-title">Alert Feed</span>
              <span className="badge badge-red">
                <AlertTriangle size={9} /> {criticalAlerts || alerts.length} Active
              </span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', maxHeight: 460 }}>
              {alerts.length > 0
                ? alerts.map(a => <AlertItem key={a.id} alert={a} onDone={handleAlertDone} />)
                : (
                  <div style={{ padding: '20px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                    {loadingOverview ? 'Loading alerts…' : 'No active alerts'}
                  </div>
                )
              }
            </div>
          </div>
        </div>

        {/* ─── Bottom 3-column row ──────────────────────────── */}
        <div className="grid-3">

          {/* AI Agents */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">NETA-CORE Agents</span>
              <span className="live-badge"><span className="live-dot" /> All Systems</span>
            </div>
            <div className="card-body" style={{ padding: '12px 12px' }}>
              <AgentPanel />
            </div>
          </div>

          {/* Top Issues from API */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Top Issues Today</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                {overview?.today?.reports_submitted ?? 0} reports
              </span>
            </div>
            <div className="card-body">
              {overview?.top_issues?.length > 0 ? (
                overview.top_issues.slice(0, 6).map((issue, i) => (
                  <div key={issue.slug} className="issue-row">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span className="issue-name" style={{ fontSize: 12 }}>
                        #{i + 1} {issue.slug.replace(/_/g, ' ')}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                          {issue.count}
                        </span>
                        <span className={`badge ${issue.trend === 'rising' ? 'badge-red' : issue.trend === 'falling' ? 'badge-green' : 'badge-gray'}`} style={{ fontSize: 9 }}>
                          {issue.trend === 'rising' ? '▲' : issue.trend === 'falling' ? '▼' : '—'}
                        </span>
                      </span>
                    </div>
                    <div className="issue-bar-track">
                      <div className="issue-bar-fill" style={{
                        width: `${Math.min(100, (issue.count / (overview.top_issues[0]?.count || 1)) * 100)}%`,
                        background: i === 0 ? 'var(--red)' : i === 1 ? 'var(--yellow)' : 'var(--saffron)',
                      }} />
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '12px 0' }}>
                  {loadingOverview ? 'Loading…' : 'No issue data yet'}
                </div>
              )}

              {/* News sentiment from API */}
              {overview?.news_sentiment && (
                <>
                  <div className="divider" />
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 8 }}>News Sentiment</div>
                  <div style={{ display: 'flex', gap: 2, borderRadius: 4, overflow: 'hidden', height: 20 }}>
                    <div style={{ flex: overview.news_sentiment.positive_count, background: 'var(--green)', opacity: 0.8 }} />
                    <div style={{ flex: overview.news_sentiment.negative_count, background: 'var(--red)', opacity: 0.8 }} />
                    <div style={{ flex: overview.news_sentiment.neutral_count, background: 'var(--border-bright)' }} />
                  </div>
                  <div style={{ display: 'flex', gap: 12, marginTop: 6 }}>
                    {[
                      { label: 'Positive', val: overview.news_sentiment.positive_count, color: 'var(--green)' },
                      { label: 'Negative', val: overview.news_sentiment.negative_count, color: 'var(--red)' },
                      { label: 'Neutral', val: overview.news_sentiment.neutral_count, color: 'var(--text-muted)' },
                    ].map(({ label, val, color }) => (
                      <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <div style={{ width: 8, height: 8, borderRadius: 2, background: color, flexShrink: 0 }} />
                        <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{label}: <b style={{ color }}>{val}</b></span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Fallback: media monitoring */}
              {!overview && (
                <>
                  <div className="divider" />
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 8 }}>Share of Voice — Last 24 hrs</div>
                  <div style={{ display: 'flex', gap: 2, borderRadius: 4, overflow: 'hidden', height: 20 }}>
                    <div style={{ flex: mediaMonitoring.coverageVolume.ours, background: 'var(--green)', opacity: 0.8 }} />
                    <div style={{ flex: mediaMonitoring.coverageVolume.opposition, background: 'var(--red)', opacity: 0.8 }} />
                    <div style={{ flex: mediaMonitoring.coverageVolume.neutral, background: 'var(--border-bright)' }} />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Content Approval Queue */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Content Approval Queue</span>
              <span className="badge badge-yellow">
                <CheckSquare size={9} /> {contentQueue.filter(c => c.status === 'pending_approval' && !approvedIds.has(c.id)).length} Pending
              </span>
            </div>
            <div>
              {contentQueue.filter(c => !approvedIds.has(c.id)).map((item) => (
                <div key={item.id} className="content-item">
                  <div className="content-type-icon" style={{
                    background: item.urgency === 'high' ? 'var(--red-dim)' : 'var(--saffron-dim)',
                    color: item.urgency === 'high' ? 'var(--red)' : 'var(--saffron)',
                  }}>
                    {item.type === 'Social Media' ? '📣' : item.type === 'Press Release' ? '📰' : item.type === 'WhatsApp Forward' ? '💬' : '🎤'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }} className="truncate">
                      {item.title}
                    </div>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <span style={{ fontSize: 9, color: 'var(--saffron)', fontWeight: 700 }}>{item.agent}</span>
                      <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>·</span>
                      <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{item.platform}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => {
                        setApprovedIds(prev => new Set([...prev, item.id]));
                        addToast(`"${item.title}" approved and queued for ${item.platform}.`, 'success');
                      }}
                    >
                      Approve
                    </button>
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => addToast('Content editor opens in war-room mode — feature in activation.', 'info')}
                    >
                      Edit
                    </button>
                  </div>
                </div>
              ))}
              {contentQueue.every(c => approvedIds.has(c.id)) && (
                <div style={{ padding: '20px 16px', textAlign: 'center', fontSize: 12, color: 'var(--green)' }}>
                  ✓ All content approved
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ─── Intelligence Brief + Campaign Actions ─────────────── */}
        <div className="grid-2 section-gap">

          {/* VICHARAK Brief */}
          <div style={{
            background: 'linear-gradient(160deg, #0d1b2a 0%, #0f2030 100%)',
            border: '1px solid rgba(239,68,68,0.18)',
            borderRadius: 14, padding: '20px 22px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.28)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Zap size={15} color="var(--red)" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--red)', letterSpacing: 1, textTransform: 'uppercase' }}>
                  {aiIntelligenceBrief.agent} · Course Correction
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                  {aiIntelligenceBrief.generated_at} · AI-generated
                </div>
              </div>
              <span className="live-badge">
                <span className="live-dot" /> Active
              </span>
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.9, whiteSpace: 'pre-line' }}>
              {aiIntelligenceBrief.text}
            </div>
          </div>

          {/* Campaign Action Items */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Campaign Action Items</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>VISHLESHAN · Ranked by urgency</span>
            </div>
            <div>
              {campaignRecommendations.map((rec, i) => (
                <div key={i} style={{
                  padding: '12px 16px',
                  borderBottom: i < campaignRecommendations.length - 1 ? '1px solid var(--border)' : 'none',
                  borderLeft: `3px solid ${rec.priority === 'critical' ? 'var(--red)' : rec.priority === 'high' ? 'var(--yellow)' : 'var(--saffron)'}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 5 }}>
                    <span className={`badge ${rec.priority === 'critical' ? 'badge-red' : rec.priority === 'high' ? 'badge-yellow' : 'badge-gray'}`} style={{ flexShrink: 0, marginTop: 1 }}>
                      {rec.priority.toUpperCase()}
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{rec.action}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: 5 }}>{rec.detail}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                    ETA: <span style={{ color: 'var(--saffron)', fontWeight: 600 }}>{rec.eta}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── Win Probability Drivers (static fallback only) ──── */}
        {!overview && (
          <div className="card section-gap">
            <div className="card-header">
              <span className="card-title">Win Probability Drivers</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>VISHLESHAN model · 7 weighted factors</span>
            </div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
                {predictionFactors.map((f) => (
                  <div key={f.factor} style={{
                    background: 'var(--bg-elevated)', borderRadius: 8, padding: '10px 14px',
                    borderLeft: `3px solid ${f.impact === 'positive' ? 'var(--green)' : f.impact === 'negative' ? 'var(--red)' : 'var(--border-bright)'}`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600, flex: 1, paddingRight: 8 }}>{f.factor}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                        <span style={{ fontSize: 9, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>wt:{f.weight}%</span>
                        <span style={{ fontSize: 14, fontWeight: 800, fontFamily: 'var(--font-mono)', color: f.impact === 'positive' ? 'var(--green)' : f.impact === 'negative' ? 'var(--red)' : 'var(--text-muted)' }}>
                          {f.currentScore}
                        </span>
                      </div>
                    </div>
                    <div className="progress-bar" style={{ height: 4 }}>
                      <div className="progress-fill" style={{
                        width: `${f.currentScore}%`,
                        background: f.impact === 'positive' ? 'var(--green)' : f.impact === 'negative' ? 'var(--red)' : 'var(--saffron)',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
