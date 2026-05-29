import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer,
} from 'recharts';
import { groundPulse, workerDetails, zoneSentimentDetail, issueHeatmap, boothIntelligence, trendingTopics, sentimentTrends, fieldOpsMetrics, antiIncumbencySignals, volunteerZoneAttendance, followUpRecommendations } from '../data/mockData';
import { getMoodTrend, getVayuAlerts, getSentimentSummary, getReports, getGroundDashboard } from '../api/vayu';
import { getOppositionIntelligence } from '../api/intelligence';
import { Activity, AlertTriangle, RefreshCw } from 'lucide-react';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import {
  AlertBanners,
  FieldOpsMetricsBar,
  ZoneSentimentMonitor,
  IssueHeatmapPanel,
  TalkingTopicsPanel,
  BoothIntelligenceGrid,
  LiveFieldFeed,
  TrendComparisonPanel,
  AntiIncumbencyPanel,
  VolunteerAttendanceTracker,
  FollowUpRecommendations,
  OperationalCommandStrip,
} from '../components/GroundPulseWidgets';
import { DataSourceStrip } from '../components/SourceBadge';
import { DATA_SOURCES } from '../utils/sourceLabels';

// Ground Pulse module

const MOOD_LABELS = { 1: 'Very Negative', 2: 'Negative', 3: 'Neutral', 4: 'Positive', 5: 'Very Positive' };

function getMoodColor(score) {
  if (score >= 4.0) return 'var(--green)';
  if (score >= 3.5) return 'var(--yellow)';
  if (score >= 3.0) return 'var(--saffron)';
  return 'var(--red)';
}

const MoodTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{label}</div>
      <div style={{ color: 'var(--green)' }}>Ground Pulse: {payload[0]?.value}/5</div>
    </div>
  );
};

export default function GroundPulse() {
  const [moodTrend, setMoodTrend]       = useState(null);
  const [sentiment, setSentiment]       = useState(null);
  const [alerts, setAlerts]             = useState([]);
  const [liveReports, setLiveReports]   = useState([]);
  const [liveRumours, setLiveRumours]   = useState([]);
  const [loading, setLoading]           = useState(true);
  const [initialized, setInitialized]   = useState(false);

  const fetchData = async () => {
    setLoading(true);
    await Promise.allSettled([
      getMoodTrend().then(setMoodTrend).catch(() => {}),
      getSentimentSummary().then(data => {
        setSentiment(data);
      }).catch(() => {}),
      getVayuAlerts(10).then(al => setAlerts(Array.isArray(al) ? al : al?.items || [])).catch(() => {}),
      getReports(1, 8).then(d => {
        const arr = Array.isArray(d) ? d : d.items || [];
        if (arr.length > 0) setLiveReports(arr);
      }).catch(() => {}),
      getGroundDashboard().catch(() => {}),
      getOppositionIntelligence().then(d => {
        const rumours = d?.active_rumours || [];
        if (rumours.length > 0) setLiveRumours(rumours);
      }).catch(() => {}),
    ]);
    setLoading(false);
    setInitialized(true);
  };

  const { countdown, triggerNow } = useAutoRefresh(fetchData, 60);

  useEffect(() => { fetchData(); }, []);

  // Trend data — prefer API, fall back to mock
  const trendData = moodTrend?.length > 0
    ? moodTrend.map(p => ({
        date: p.date?.slice(5) || p.date || '',
        score: p.avg_mood != null ? Math.round(p.avg_mood * 10) / 10 : null,
      })).filter(p => p.score != null)
    : groundPulse.moodTrend;

  const overallMood   = sentiment?.avg_mood ?? groundPulse.today.overallMood;
  const totalReports  = sentiment?.total_reports ?? groundPulse.today.totalReports;
  const boothsCovered = sentiment?.booths_covered ?? fieldOpsMetrics.boothsCovered;

  // Alert items from API → mapped shape
  const alertItems = alerts.length > 0
    ? alerts.map(a => ({
        zone:     (a.metadata_ || a.metadata)?.zone || 'All',
        activity: a.message || a.title || '',
        severity: a.alert_type === 'critical' ? 'high' : a.alert_type === 'warning' ? 'medium' : 'low',
      }))
    : groundPulse.oppositionObserved;

  const now = new Date().toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  });

  return (
    <div>
      {/* ─── Page Header ─── */}
      <div className="page-header">
        <div>
          <div className="page-title">Ground Pulse</div>
          <div className="page-subtitle">
            VAYU Agent · Live field intelligence · {now}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {totalReports} worker reports aggregated
          </span>
          <button
            className="btn btn-outline btn-sm"
            onClick={triggerNow}
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            {loading ? 'Refreshing…' : `Refresh (${countdown}s)`}
          </button>
          <span className="live-badge"><span className="live-dot" /> VAYU Active</span>
        </div>
      </div>

      <div className="page-body">

        {/* ─── Data Source Attribution ─── */}
        <DataSourceStrip
          sources={[DATA_SOURCES.VAYU, DATA_SOURCES.VISHLESHAN, DATA_SOURCES.ECI]}
          live={liveReports.length > 0}
          confidence={liveReports.length > 0 ? 88 : 74}
        />

        {/* ─── Operational Command Strip ─── */}
        <OperationalCommandStrip priorities={followUpRecommendations} />

        {/* ─── Alert Banners ─── */}
        <AlertBanners zones={zoneSentimentDetail} />

        {/* ─── Field Ops Metrics Bar ─── */}
        <FieldOpsMetricsBar metrics={fieldOpsMetrics} />

        {/* ─── Volunteer Attendance Tracker ─── */}
        <div className="section-gap">
          <VolunteerAttendanceTracker attendance={volunteerZoneAttendance} />
        </div>

        {/* ─── Mood Gauge + 14-day Trend ─── */}
        {!initialized && loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 18, marginBottom: 18 }}>
            <div className="card">
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 20 }}>
                <div className="skeleton" style={{ height: 64, width: 100, margin: '0 auto' }} />
                <div className="skeleton" style={{ height: 12, width: '70%', margin: '0 auto' }} />
                <div style={{ display: 'flex', gap: 4, justifyContent: 'center', marginTop: 8 }}>
                  {[0,1,2,3,4].map(i => <div key={i} className="skeleton" style={{ width: 28, height: 6, borderRadius: 3 }} />)}
                </div>
                <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {[0,1,2].map(i => <div key={i} className="skeleton" style={{ height: 12 }} />)}
                </div>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <div className="skeleton" style={{ height: 200, borderRadius: 8 }} />
              </div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 18, marginBottom: 18 }}>

            {/* Mood Gauge */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Overall Mood Today</span>
                <Activity size={14} color="var(--text-muted)" />
              </div>
              <div className="card-body">
                <div className="mood-gauge">
                  <div className="mood-value" style={{ color: getMoodColor(overallMood) }}>
                    {typeof overallMood === 'number' ? overallMood.toFixed(1) : overallMood}
                    <span className="mood-max">/5</span>
                  </div>
                  <div className="mood-label">
                    {MOOD_LABELS[Math.round(overallMood)] || 'Neutral'}
                  </div>
                  <div style={{ marginTop: 12, display: 'flex', gap: 4 }}>
                    {[1, 2, 3, 4, 5].map(s => (
                      <div key={s} style={{
                        width: 28, height: 6, borderRadius: 3,
                        background: s <= Math.floor(overallMood) ? getMoodColor(overallMood) :
                                    s === Math.ceil(overallMood) ? `${getMoodColor(overallMood)}55` : 'var(--border)',
                      }} />
                    ))}
                  </div>
                </div>

                <div className="divider" />

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Booths covered:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--saffron)' }}>{boothsCovered}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginTop: 4 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Escalations:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--red)' }}>
                    {sentiment?.escalation_count ?? '—'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginTop: 4 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Reports collected:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--saffron)' }}>
                    {totalReports}
                  </span>
                </div>

                {sentiment?.opposition_sightings > 0 && (
                  <div style={{ marginTop: 10, padding: '8px 10px', background: 'var(--red-dim)', borderRadius: 6, border: '1px solid rgba(239,68,68,0.2)' }}>
                    <div style={{ fontSize: 10, color: 'var(--red)', fontWeight: 700 }}>
                      {sentiment.opposition_sightings} opposition sightings
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 14-day Trend Chart */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">14-Day Mood Trend</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Daily aggregated from field reports</span>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={trendData}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} interval={1} />
                    <YAxis domain={[1, 5]} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={30} />
                    <Tooltip content={<MoodTooltip />} />
                    <Line
                      type="monotone" dataKey="score" stroke="var(--green)"
                      strokeWidth={2.5} dot={{ fill: 'var(--green)', r: 3 }}
                      activeDot={{ r: 5, fill: 'var(--green)' }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                  {[
                    { color: 'var(--green)',   label: '≥ 4.0 Positive' },
                    { color: 'var(--yellow)',  label: '3.5–3.9 Stable' },
                    { color: 'var(--red)',     label: '< 3.0 Needs Action' },
                  ].map(({ color, label }) => (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <div style={{ width: 12, height: 3, borderRadius: 2, background: color }} />
                      <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ─── Zone Sentiment Monitor ─── */}
        <div className="section-gap">
          <ZoneSentimentMonitor zones={zoneSentimentDetail} />
        </div>

        {/* ─── Anti-Incumbency Panel ─── */}
        <div className="section-gap">
          <AntiIncumbencyPanel data={antiIncumbencySignals} />
        </div>

        {/* ─── Issue Heatmap + Trending Topics ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 18 }} className="section-gap">
          <IssueHeatmapPanel issues={issueHeatmap} />
          <TalkingTopicsPanel topics={trendingTopics} />
        </div>

        {/* ─── Booth Intelligence Grid ─── */}
        <div className="section-gap">
          <BoothIntelligenceGrid booths={boothIntelligence} />
        </div>

        {/* ─── Live Field Feed + Trend Comparison ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 18 }} className="section-gap">
          <LiveFieldFeed reports={liveReports.length > 0 ? liveReports : groundPulse.fieldReports} isLive={liveReports.length > 0} />
          <TrendComparisonPanel trends={sentimentTrends} />
        </div>

        {/* ─── Opposition Activity + Rumours ─── */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title">
              {alerts.length > 0 ? 'Live Alerts' : 'Opposition Activity Observed'}
            </span>
            <AlertTriangle size={14} color="var(--yellow)" />
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {alertItems.map((obs, i) => (
              <div key={i} style={{
                padding: '12px 16px', borderBottom: '1px solid var(--border)',
                borderLeft: `3px solid ${obs.severity === 'high' ? 'var(--red)' : obs.severity === 'medium' ? 'var(--yellow)' : 'var(--border-bright)'}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className={`zone-pill zone-${(obs.zone || '').toLowerCase()}`}>{obs.zone || 'All'}</span>
                  <span className={`badge ${obs.severity === 'high' ? 'badge-red' : obs.severity === 'medium' ? 'badge-yellow' : 'badge-gray'}`}>
                    {obs.severity?.toUpperCase() || 'INFO'}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{obs.activity}</div>
              </div>
            ))}

            {/* Rumours */}
            <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Active Rumours (Counter Required)</span>
                {liveRumours.length > 0
                  ? <span className="live-badge" style={{ fontSize: 9 }}><span className="live-dot" /> VIVEK</span>
                  : <span style={{ fontSize: 9, color: 'var(--text-muted)', padding: '1px 5px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Static</span>
                }
              </div>
              {liveRumours.length > 0
                ? liveRumours.slice(0, 4).map((r, i) => (
                    <div key={i} style={{ marginBottom: 8, padding: '8px 10px', background: 'var(--bg-elevated)', borderRadius: 6, borderLeft: '3px solid var(--red)' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.5 }}>
                        "{r.content || r.rumour || '—'}"
                      </div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {r.zone && <span className={`zone-pill zone-${r.zone.toLowerCase()}`}>{r.zone}</span>}
                        <span className="badge badge-red">ACTIVE</span>
                        {r.report_count > 0 && (
                          <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{r.report_count} reports</span>
                        )}
                      </div>
                    </div>
                  ))
                : groundPulse.rumours.map((r, i) => (
                    <div key={i} style={{ marginBottom: 8, padding: '8px 10px', background: 'var(--bg-elevated)', borderRadius: 6 }}>
                      <div style={{ fontSize: 11, color: 'var(--text-primary)', marginBottom: 4 }}>"{r.rumour}"</div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <span className={`zone-pill zone-${r.zone.toLowerCase()}`}>{r.zone}</span>
                        <span className={`badge ${r.status.includes('needed') ? 'badge-red' : 'badge-green'}`}>{r.status}</span>
                      </div>
                    </div>
                  ))
              }
            </div>
          </div>
        </div>

        {/* ─── Follow-Up Recommendations ─── */}
        <div className="section-gap">
          <FollowUpRecommendations recommendations={followUpRecommendations} />
        </div>

        {/* ─── Worker Leaderboard ─── */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title">Worker Performance Leaderboard</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Ranked by voter contact rate · Today</span>
              <span className="live-badge"><span className="live-dot" /> VAYU</span>
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 36 }}>#</th>
                  <th>Worker</th>
                  <th>Zone</th>
                  <th>Booths</th>
                  <th>Voters</th>
                  <th style={{ width: 160 }}>Contact Rate</th>
                  <th>Last Active</th>
                  <th>Rating</th>
                </tr>
              </thead>
              <tbody>
                {[...workerDetails]
                  .sort((a, b) => b.rate - a.rate)
                  .map((w, idx) => (
                    <tr key={w.id}>
                      <td>
                        <span style={{
                          fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)',
                          color: idx === 0 ? 'var(--yellow)' : idx === 1 ? 'var(--text-secondary)' : idx === 2 ? 'var(--saffron)' : 'var(--text-muted)',
                        }}>
                          {idx + 1}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{
                            width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 10, fontWeight: 700, color: 'var(--saffron)',
                          }}>
                            {(w.name || '?').split(' ').map(n => n[0]).join('').slice(0, 2)}
                          </div>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{w.name}</div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                              {w.status === 'active'
                                ? <span style={{ color: 'var(--green)' }}>● Active</span>
                                : <span style={{ color: 'var(--text-dim)' }}>● Offline</span>
                              }
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`zone-pill zone-${w.zone.toLowerCase()}`}>{w.zone}</span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
                        {w.booths}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
                        {w.voters.toLocaleString()}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div className="progress-bar" style={{ flex: 1, height: 5 }}>
                            <div className="progress-fill" style={{
                              width: `${w.rate}%`,
                              background: w.rate >= 80 ? 'var(--green)' : w.rate >= 60 ? 'var(--yellow)' : 'var(--red)',
                            }} />
                          </div>
                          <span style={{
                            fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)',
                            color: w.rate >= 80 ? 'var(--green)' : w.rate >= 60 ? 'var(--yellow)' : 'var(--red)',
                            minWidth: 32, textAlign: 'right',
                          }}>
                            {w.rate}%
                          </span>
                        </div>
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {w.lastSeen}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 3 }}>
                          {[1, 2, 3, 4, 5].map(s => (
                            <div key={s} style={{
                              width: 7, height: 7, borderRadius: 1,
                              background: s <= w.rating ? 'var(--yellow)' : 'var(--border)',
                            }} />
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
