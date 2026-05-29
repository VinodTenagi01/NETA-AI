import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  LineChart, Line, ReferenceLine,
} from 'recharts';
import { oppositionCandidates, mediaMonitoring, constituency } from '../data/mockData';
import { getOppositionIntelligence } from '../api/intelligence';
import { getNewsSentimentTrends } from '../api/news';
import { ShieldAlert, TrendingDown, RefreshCw, AlertTriangle } from 'lucide-react';
import { safeText } from '../utils/safeText';
import { DataSourceStrip } from '../components/SourceBadge';
import { DATA_SOURCES } from '../utils/sourceLabels';

const THREAT_COLORS = { High: 'var(--red)', Medium: 'var(--yellow)', Low: 'var(--green)' };
const ZONE_COLORS = { Central: 'var(--purple)', North: 'var(--blue)', South: 'var(--green)', East: 'var(--red)', West: 'var(--yellow)' };

const RISK_BADGE = {
  critical: 'badge-red',
  high: 'badge-red',
  medium: 'badge-yellow',
  low: 'badge-green',
};

function WinProbBar({ value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div className="progress-bar" style={{ flex: 1 }}>
        <div className="progress-fill" style={{ width: `${value}%`, background: color }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 16, color, minWidth: 40 }}>{value}%</span>
    </div>
  );
}

function CandidateCard({ candidate: cand, expanded, onToggle }) {
  return (
    <div className="oppo-card" style={{ marginBottom: 18 }}>
      <div className="oppo-card-header" onClick={onToggle} style={{ cursor: 'pointer' }}>
        <div className="oppo-avatar" style={{ background: cand.avatar_bg, color: '#fff' }}>
          {cand.initials}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <span style={{ fontSize: 16, fontWeight: 800 }}>{cand.name}</span>
            <span className="badge badge-gray">{cand.partyShort}</span>
            <span className={`badge ${cand.threatLevel === 'High' ? 'badge-red' : cand.threatLevel === 'Medium' ? 'badge-yellow' : 'badge-green'}`}>
              {cand.threatLevel} Threat
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            {cand.profession} · Age {cand.age} · {cand.caste}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>Win Probability</div>
          <div style={{ fontSize: 28, fontWeight: 900, fontFamily: 'var(--font-mono)', color: THREAT_COLORS[cand.threatLevel] }}>
            {cand.winProbability}%
          </div>
        </div>
      </div>

      {expanded && (
        <div style={{ padding: '16px 18px' }}>
          <div className="grid-2" style={{ marginBottom: 16 }}>
            <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: 14, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>Strengths</div>
              {(cand.strengths || []).map((s) => (
                <div key={s} style={{ display: 'flex', gap: 6, marginBottom: 7, fontSize: 12 }}>
                  <span style={{ color: 'var(--red)', flexShrink: 0 }}>⚑</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{s}</span>
                </div>
              ))}
            </div>
            <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: 14, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>Vulnerabilities (VIVEK Analysis)</div>
              {(cand.weaknesses || []).map((w) => (
                <div key={w} style={{ display: 'flex', gap: 6, marginBottom: 7, fontSize: 12 }}>
                  <span style={{ color: 'var(--green)', flexShrink: 0 }}>✓</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{w}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>Recent Campaign Activity</div>
            {(cand.recentActivity || []).map((act, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', flexShrink: 0, minWidth: 50 }}>{act.date}</span>
                <span className={`zone-pill zone-${act.zone.toLowerCase()}`} style={{ flexShrink: 0 }}>{act.zone}</span>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{act.event}</span>
              </div>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>Promises & Our Counter-Narrative</div>
            {(cand.recentPromises || []).map((p, i) => (
              <div key={i} style={{ marginBottom: 10, padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>"{p.promise}"</span>
                  <span className={`badge ${p.feasibility === 'Low' || p.feasibility === 'Very Low' ? 'badge-red' : p.feasibility === 'Medium' ? 'badge-yellow' : 'badge-green'}`}>
                    Feasibility: {p.feasibility}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                  <span style={{ color: 'var(--green)', fontWeight: 700 }}>Our counter: </span>
                  {p.ourResponse}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', gap: 20, fontSize: 11 }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Criminal Cases: </span>
                <span style={{ fontWeight: 700, color: cand.criminalCases > 0 ? 'var(--red)' : 'var(--green)' }}>
                  {cand.criminalCases === 0 ? 'None' : cand.criminalCases}
                </span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>EC Filing: </span>
                <span style={{ fontWeight: 700, color: cand.ecFilingIssues === 'None' ? 'var(--green)' : 'var(--yellow)' }}>
                  {cand.ecFilingIssues}
                </span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Key Vulnerability: </span>
                <span style={{ color: 'var(--red)', fontWeight: 600 }}>{cand.vulnerabilities}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OppositionIntelligence() {
  const [expanded, setExpanded] = useState(new Set([1]));
  const [intel, setIntel] = useState(null);
  const [mediaTrends, setMediaTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    await Promise.allSettled([
      getOppositionIntelligence().then(setIntel).catch(() => {}),
      getNewsSentimentTrends().then(data => {
        const raw = data?.timeline || data?.trend_data || data?.data || [];
        const arr = Array.isArray(raw) ? raw : [];
        if (arr.length > 0) setMediaTrends(arr);
      }).catch(() => {}),
    ]);
    setLoading(false);
    setInitialized(true);
  };

  useEffect(() => { fetchData(); }, []);

  const toggle = (id) => {
    const next = new Set(expanded);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpanded(next);
  };

  const sentimentData = mediaMonitoring.sentimentTrend;

  const momentumPct = intel ? Math.round(intel.opposition_momentum_score * 100) : null;
  const riskLevel = intel?.risk_level || 'medium';

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Opposition Intelligence</div>
          <div className="page-subtitle">VIVEK Agent · Continuous opposition monitoring · {constituency.name}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={fetchData}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}
          >
            <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
          <span className="live-badge"><span className="live-dot" /> VIVEK Active</span>
        </div>
      </div>

      <div className="page-body">

        {/* ─── Data Source Attribution ─── */}
        <DataSourceStrip
          sources={[DATA_SOURCES.VIVEK, DATA_SOURCES.VANI, DATA_SOURCES.ECI]}
          live={initialized && !!intel}
          confidence={initialized && intel ? 85 : 71}
        />

        {/* Live Threat Overview */}
        {!initialized ? (
          <div className="grid-4 section-gap">
            {[0,1,2,3].map(i => (
              <div key={i} className="stat-card">
                <div className="skeleton" style={{ height: 11, width: '65%', marginBottom: 10 }} />
                <div className="skeleton" style={{ height: 32, width: '50%', marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 10, width: '55%' }} />
              </div>
            ))}
          </div>
        ) : intel ? (
          <div className="grid-4 section-gap">
            {[
              {
                label: 'Opposition Momentum',
                value: `${momentumPct}`,
                unit: '/100',
                color: momentumPct >= 70 ? 'var(--red)' : momentumPct >= 40 ? 'var(--yellow)' : 'var(--green)',
                sub: `Risk: ${riskLevel.toUpperCase()}`,
              },
              {
                label: 'Sightings (7 days)',
                value: intel.total_sightings ?? 0,
                unit: '',
                color: 'var(--yellow)',
                sub: `${(intel.sightings_by_zone || []).length} zones affected`,
              },
              {
                label: 'Active Rumours',
                value: (intel.active_rumours || []).length,
                unit: '',
                color: 'var(--red)',
                sub: 'Require counter-narrative',
              },
              {
                label: 'Opposition News',
                value: (intel.opposition_news || []).length,
                unit: '',
                color: 'var(--blue)',
                sub: 'Articles tracked',
              },
            ].map(({ label, value, unit, color, sub }) => (
              <div key={label} className="stat-card" style={{ '--accent-color': color }}>
                <div className="stat-label">{label}</div>
                <div className="stat-value" style={{ fontSize: 28, color }}>
                  {value}<span style={{ fontSize: 14, fontWeight: 400, color: 'var(--text-muted)' }}>{unit}</span>
                </div>
                <div className="stat-sub">{sub}</div>
              </div>
            ))}
          </div>
        ) : null}

        {/* Win probability comparison */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title">Seat Win Probability — All Candidates</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>VISHLESHAN model</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              {[
                { name: 'Arjun Kumar Reddy', party: 'TRP', prob: 67, color: 'var(--green)' },
                { name: 'Priya Mehta', party: 'BNP', prob: 24, color: 'var(--red)' },
                { name: 'Suresh Kumar Pillai', party: 'INC', prob: 9, color: 'var(--blue)' },
              ].map(({ name, party, prob, color }) => (
                <div key={name} style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 10, border: `1px solid ${color}33` }}>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ fontSize: 13, fontWeight: 700 }}>{name}</span>
                    <span className="badge badge-gray" style={{ marginLeft: 8 }}>{party}</span>
                  </div>
                  <WinProbBar value={prob} color={color} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 2-col: sightings by zone + active rumours */}
        {intel && (
          <div className="grid-2 section-gap">
            {/* Sightings by Zone */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Sightings by Zone (Live)</span>
                <span className={`badge ${RISK_BADGE[riskLevel]}`}>{riskLevel.toUpperCase()} RISK</span>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                {(intel.sightings_by_zone || []).length > 0 ? (intel.sightings_by_zone || []).map((z, i) => (
                  <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className={`zone-pill zone-${(z.zone || '').toLowerCase()}`}>{z.zone || 'Unknown'}</span>
                    <div style={{ flex: 1 }}>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{
                          width: `${Math.min(100, (z.sighting_count / (intel.total_sightings || 1)) * 100)}%`,
                          background: ZONE_COLORS[z.zone] || 'var(--saffron)',
                        }} />
                      </div>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 14, color: ZONE_COLORS[z.zone] || 'var(--text-primary)', minWidth: 24 }}>
                      {z.sighting_count}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>sightings</span>
                  </div>
                )) : (
                  <div style={{ padding: '20px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>No sightings recorded</div>
                )}
              </div>
              {(intel.recommended_actions || []).length > 0 && (
                <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--saffron)', letterSpacing: 1, marginBottom: 8 }}>VIVEK RECOMMENDATIONS</div>
                  {(intel.recommended_actions || []).slice(0, 3).map((action, i) => (
                    <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 6, fontSize: 11, color: 'var(--text-secondary)' }}>
                      <span style={{ color: 'var(--saffron)', flexShrink: 0 }}>→</span>
                      {safeText(action)}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Active Rumours */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Active Rumours (Live DB)</span>
                <span className="badge badge-red">
                  <AlertTriangle size={9} /> {intel.active_rumours.length} Active
                </span>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                {(intel.active_rumours || []).slice(0, 6).map((rumour, i) => (
                  <div key={i} style={{
                    padding: '11px 16px', borderBottom: '1px solid var(--border)',
                    borderLeft: '3px solid var(--red)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      {rumour.zone && <span className={`zone-pill zone-${rumour.zone.toLowerCase()}`}>{rumour.zone}</span>}
                      <span className="badge badge-red">ACTIVE</span>
                      <span style={{ marginLeft: 'auto', fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {rumour.report_count} reports
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      "{rumour.content}"
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                      First reported: {new Date(rumour.first_reported_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Media Sentiment Trend */}
        <div className="card section-gap">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="card-title">Media Sentiment — 7 Days</span>
              {Array.isArray(mediaTrends) && mediaTrends.length > 0
                ? <span className="live-badge"><span className="live-dot" /> VANI Live</span>
                : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 7px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Static</span>
              }
            </div>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>VANI media monitoring · -1 to +1</span>
          </div>
          <div className="card-body">
            {Array.isArray(mediaTrends) && mediaTrends.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={mediaTrends.map(t => ({
                    date: t.date || new Date(t.period_start || '').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
                    score: t.polarity ?? t.avg_score ?? t.score ?? 0,
                  }))}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis domain={[-1, 1]} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => v.toFixed(1)} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
                      formatter={(v) => [(v >= 0 ? '+' : '') + v.toFixed(2), 'Sentiment']}
                    />
                    <ReferenceLine y={0} stroke="var(--border-bright)" strokeDasharray="4 2" />
                    <Line type="monotone" dataKey="score" stroke="var(--blue)" strokeWidth={2.5} dot={{ r: 3, fill: 'var(--blue)' }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>
                  Overall media tone · positive = favorable coverage · negative = adverse coverage
                </div>
              </>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={mediaMonitoring.sentimentTrend}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} domain={[-0.6, 0.6]} />
                    <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                    <Bar dataKey="ours" name="Our Sentiment" fill="var(--green)" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="oppo" name="Opp. Sentiment" fill="var(--red)" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', gap: 20, marginTop: 8, justifyContent: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                    <div style={{ width: 12, height: 12, borderRadius: 3, background: 'var(--green)' }} />
                    Our media sentiment
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                    <div style={{ width: 12, height: 12, borderRadius: 3, background: 'var(--red)' }} />
                    Opposition sentiment
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Opposition news articles from API */}
        {Array.isArray(intel?.opposition_news) && intel.opposition_news.length > 0 && (
          <div className="card section-gap">
            <div className="card-header">
              <span className="card-title">Opposition News Coverage (Live)</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{intel.opposition_news.length} articles tracked</span>
            </div>
            <div>
              {intel.opposition_news.slice(0, 6).map((article, i) => (
                <div key={i} style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 6, background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 13,
                  }}>
                    📰
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 4 }}>
                      {article.headline}
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {article.published_at && (
                        <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          {new Date(article.published_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                        </span>
                      )}
                      {article.sentiment_score != null && (
                        <span className={`badge ${article.sentiment_score < -0.2 ? 'badge-red' : article.sentiment_score > 0.2 ? 'badge-green' : 'badge-gray'}`}>
                          Sentiment: {article.sentiment_score.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Opposition Candidate Profiles */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 12 }}>
            Opposition Candidate Profiles — Click to expand
          </div>
          {!initialized ? (
            [0,1].map(i => (
              <div key={i} className="oppo-card" style={{ marginBottom: 18, padding: 18, display: 'flex', gap: 14, alignItems: 'center' }}>
                <div className="skeleton" style={{ width: 42, height: 42, borderRadius: 10, flexShrink: 0 }} />
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <div className="skeleton" style={{ height: 16, width: 150 }} />
                    <div className="skeleton" style={{ height: 16, width: 50 }} />
                    <div className="skeleton" style={{ height: 16, width: 80 }} />
                  </div>
                  <div className="skeleton" style={{ height: 11, width: '60%' }} />
                </div>
                <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
                  <div className="skeleton" style={{ height: 11, width: 80 }} />
                  <div className="skeleton" style={{ height: 32, width: 60 }} />
                </div>
              </div>
            ))
          ) : (
            oppositionCandidates.map((cand) => (
              <CandidateCard key={cand.id} candidate={cand} expanded={expanded.has(cand.id)} onToggle={() => toggle(cand.id)} />
            ))
          )}
        </div>

        {/* VIVEK priority alert (static) */}
        <div style={{ padding: '16px 18px', background: 'var(--red-dim)', borderRadius: 10, border: '1px solid rgba(239,68,68,0.25)', display: 'flex', gap: 14, alignItems: 'flex-start' }}>
          <ShieldAlert size={18} color="var(--red)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--red)', marginBottom: 4 }}>
              VIVEK Priority Alert — Priya Mehta land deal controversy
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              VIVEK has documented evidence of a 2023 land encroachment case involving Priya Mehta in Balanagar.
              The case is in civil court. Two regional newspapers have the story. VIVEK recommends <b style={{ color: 'var(--text-primary)' }}>NOT proactively publicising this</b> —
              if it breaks in media, use it as a reinforcement of our "clean candidate" narrative.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
