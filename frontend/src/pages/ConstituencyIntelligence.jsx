import { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, CartesianGrid,
  LineChart, Line, ReferenceLine,
} from 'recharts';
import {
  demographics, historicalResults, issueMatrix, candidateScoring, swingAnalysis,
  constituency,
} from '../data/mockData';
import { AlertCircle, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getTrendingIssues } from '../api/vayu';
import { getSentimentTrends } from '../api/intelligence';
import { DataSourceStrip } from '../components/SourceBadge';
import { DATA_SOURCES } from '../utils/sourceLabels';
import { lazy, Suspense } from 'react';

const ConstituencyMap = lazy(() => import('../components/ConstituencyMap'));

const TABS = ['Demographics', 'Historical Analysis', 'Issue Matrix', 'Candidate Fit', 'Sentiment Trends', 'Booth Map'];

function riskLevelFromSalience(pct) {
  if (pct >= 65) return 'high';
  if (pct >= 35) return 'medium';
  return 'low';
}

function normalizeLiveIssues(raw) {
  if (!Array.isArray(raw) || raw.length === 0) return null;
  const maxCount = Math.max(...raw.map(i => i.mention_count || i.count || 1));
  return raw.map((issue, idx) => {
    const name = issue.issue_name || issue.issue || issue.name || `Issue ${idx + 1}`;
    const count = issue.mention_count || issue.count || 0;
    const salience = issue.salience_score != null
      ? Math.round(issue.salience_score * 100)
      : Math.round((count / maxCount) * 100);
    const riskLevel = issue.risk_level || riskLevelFromSalience(salience);
    return {
      rank: idx + 1,
      issue: name,
      salience,
      riskLevel,
      boothCount: issue.booth_count,
      mentionCount: count,
      trend: issue.trend_direction || issue.trend,
    };
  });
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {p.value}%</div>
      ))}
    </div>
  );
};

function DemographicsTab() {
  return (
    <div>
      <div className="grid-2" style={{ marginBottom: 18 }}>
        <div className="card">
          <div className="card-header"><span className="card-title">Caste & Community Composition</span></div>
          <div className="card-body" style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={demographics.casteComposition} cx={88} cy={88} innerRadius={50} outerRadius={84} dataKey="value" paddingAngle={2}>
                  {demographics.casteComposition.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1 }}>
              {demographics.casteComposition.map((item) => (
                <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: item.color, flexShrink: 0 }} />
                  <div style={{ flex: 1, fontSize: 11, color: 'var(--text-primary)' }}>{item.name}</div>
                  <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: item.color }}>{item.value}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Economic Strata</span></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={demographics.economicStrata} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} width={100} />
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                <Bar dataKey="value" fill="var(--blue)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Age Group Distribution</span></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={demographics.ageGroups}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                <Bar dataKey="value" fill="var(--purple)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Key Community Influencers</span></div>
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr><th>Name</th><th>Role</th><th>Community</th><th>Alignment</th></tr>
              </thead>
              <tbody>
                {demographics.keyInfluencers.map((inf) => (
                  <tr key={inf.name}>
                    <td style={{ fontWeight: 600 }}>{inf.name}</td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{inf.role}</td>
                    <td><span className="badge badge-blue">{inf.community}</span></td>
                    <td>
                      <span className={`badge ${inf.alignment === 'Friendly' ? 'badge-green' : inf.alignment === 'Hostile' ? 'badge-red' : 'badge-gray'}`}>
                        {inf.alignment}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="grid-4" style={{ marginTop: 18 }}>
        {[
          { label: 'Literacy Rate',     value: `${demographics.literacy}%`,         color: 'var(--green)' },
          { label: 'Urban Voters',      value: `${demographics.urbanRural.urban}%`,  color: 'var(--blue)' },
          { label: 'Women Voters',      value: `${demographics.gender.female}%`,     color: 'var(--purple)' },
          { label: 'First-Time Voters', value: `${demographics.ageGroups[0].value}%`,color: 'var(--saffron)' },
        ].map(({ label, value, color }) => (
          <div key={label} className="stat-card" style={{ '--accent-color': color }}>
            <div className="stat-label">{label}</div>
            <div className="stat-value" style={{ fontSize: 32, color }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function HistoricalTab() {
  return (
    <div>
      <div className="grid-2" style={{ marginBottom: 18 }}>
        <div className="card">
          <div className="card-header"><span className="card-title">Historical Election Results</span></div>
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr><th>Year</th><th>Winner</th><th>Our Votes</th><th>Margin</th><th>Turnout</th><th>Result</th></tr>
              </thead>
              <tbody>
                {historicalResults.map((r) => (
                  <tr key={r.year}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{r.year}</td>
                    <td style={{ fontSize: 12 }}>{r.winner}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.ourVotes.toLocaleString()}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--red)' }}>{r.margin.toLocaleString()}</td>
                    <td>{r.turnout}%</td>
                    <td><span className="badge badge-red">{r.result}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ padding: '12px 16px', background: 'var(--bg-elevated)', borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                ⚠️ <b style={{ color: 'var(--yellow)' }}>New candidate context:</b> AK Reddy is contesting from Chandanagar for the first time under TRP. Historical losses were by previous TRP candidates. Baseline comparison applies but personal vote bank is being built fresh.
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Zone Swing Analysis (vs 2023)</span></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={swingAnalysis}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="zone" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} domain={[25, 70]} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                <Bar dataKey="lastElectionShare" name="2023 Share" fill="var(--border-bright)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="currentShare" name="Current Est." fill="var(--green)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 12 }}>
              {swingAnalysis.map((row) => (
                <div key={row.zone} style={{ display: 'flex', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ width: 60, fontSize: 11, fontWeight: 600 }}>{row.zone}</span>
                  <span style={{ flex: 1, fontSize: 11, color: 'var(--text-secondary)' }}>{row.lastElectionShare}% → {row.currentShare}%</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 12, color: row.direction === 'up' ? 'var(--green)' : 'var(--red)' }}>
                    {row.swing}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Booth Classification Summary</span></div>
        <div className="card-body">
          <div className="grid-3">
            {[
              { label: 'Fortress Booths', count: 42, desc: 'Expected >55% vote share. Low priority for intensive campaign.', color: '#059669', pct: 28 },
              { label: 'Swing Booths',    count: 71, desc: 'Battleground. 40–55% expected. Focus of intensive ground campaign.', color: '#d97706', pct: 47 },
              { label: 'Hostile Booths',  count: 37, desc: 'Opposition strongholds (<40% expected). Damage-limitation strategy.', color: '#dc2626', pct: 25 },
            ].map(({ label, count, desc, color, pct }) => (
              <div key={label} style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 10, border: `1px solid ${color}33` }}>
                <div style={{ fontSize: 32, fontWeight: 900, fontFamily: 'var(--font-mono)', color }}>{count}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color, marginBottom: 6 }}>{label}</div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{desc}</div>
                <div className="progress-bar" style={{ marginTop: 10 }}>
                  <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{pct}% of total booths</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function IssueMatrixTab({ liveIssues, issuesError, issuesLoading, onRefresh, refreshing }) {
  const isLive = liveIssues && liveIssues.length > 0;
  const displayIssues = isLive ? liveIssues : issueMatrix;

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="card-title">Ranked Issue Matrix — Electoral Salience</span>
            {isLive
              ? <span className="live-badge"><span className="live-dot" /> VAYU Live</span>
              : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 7px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Static</span>
            }
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {isLive ? 'Field reports · Last 7 days' : `Local analysis · ${constituency.name} 2026`}
            </span>
            <button
              className="btn btn-outline btn-sm"
              onClick={onRefresh}
              disabled={refreshing || issuesLoading}
              style={{ display: 'flex', alignItems: 'center', gap: 5 }}
            >
              <RefreshCw size={11} style={{ animation: (refreshing || issuesLoading) ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>
        </div>

        {issuesError && (
          <div style={{
            padding: '8px 16px', borderBottom: '1px solid var(--border)',
            background: 'rgba(217,119,6,0.08)', display: 'flex', alignItems: 'center', gap: 7,
            fontSize: 11, color: 'var(--yellow)',
          }}>
            <AlertCircle size={12} />
            {issuesError} Showing static analysis below.
          </div>
        )}

        <div className="card-body" style={{ padding: 0 }}>
          {displayIssues.map((item) => (
            <div key={item.rank} className="issue-row" style={{ padding: '14px 18px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 7, background: 'var(--bg-elevated)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 800, fontSize: 13, fontFamily: 'var(--font-mono)',
                  color: item.rank <= 3 ? 'var(--saffron)' : 'var(--text-muted)', flexShrink: 0,
                }}>
                  {item.rank}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                    <span className="issue-name">{item.issue}</span>
                    <span className={`badge ${item.riskLevel === 'low' ? 'badge-green' : item.riskLevel === 'medium' ? 'badge-yellow' : 'badge-red'}`}>
                      {item.riskLevel === 'low' ? 'Safe Promise' : item.riskLevel === 'medium' ? 'Moderate Risk' : 'High Risk'}
                    </span>
                    {item.communities && <span className="badge badge-gray">{item.communities}</span>}
                    {item.boothCount != null && (
                      <span className="badge badge-blue">{item.boothCount} booths</span>
                    )}
                    {item.mentionCount != null && (
                      <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{item.mentionCount} mentions</span>
                    )}
                    {item.trend && (
                      <span style={{ fontSize: 10, color: item.trend === 'rising' ? 'var(--red)' : item.trend === 'falling' ? 'var(--green)' : 'var(--text-muted)' }}>
                        {item.trend === 'rising' ? '↑ Rising' : item.trend === 'falling' ? '↓ Falling' : '→ Stable'}
                      </span>
                    )}
                    <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 700, color: 'var(--saffron)' }}>
                      {item.salience}%
                    </span>
                  </div>
                  <div className="issue-bar-track">
                    <div className="issue-bar-fill" style={{
                      width: `${item.salience}%`,
                      background: item.riskLevel === 'low' ? 'var(--green)' : item.riskLevel === 'medium' ? 'var(--yellow)' : 'var(--red)',
                    }} />
                  </div>
                  {item.recommendation && (
                    <div style={{ marginTop: 8, padding: '8px 10px', background: 'var(--bg-elevated)', borderRadius: 6, border: '1px solid var(--border)' }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--saffron)' }}>VICHAR RECOMMENDATION: </span>
                      <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{item.recommendation}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CandidateFitTab() {
  return (
    <div>
      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Candidate Suitability Score</span></div>
          <div className="card-body">
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <div style={{ fontSize: 80, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--green)', lineHeight: 1 }}>
                {candidateScoring.overall}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>out of 100 · VISHLESHAN assessment</div>
            </div>
            {candidateScoring.breakdown.map((item) => (
              <div key={item.factor} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{item.factor}</span>
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700, color: item.score >= 80 ? 'var(--green)' : item.score >= 60 ? 'var(--yellow)' : 'var(--red)' }}>
                    {item.score}
                  </span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${item.score}%`, background: item.score >= 80 ? 'var(--green)' : item.score >= 60 ? 'var(--yellow)' : 'var(--red)' }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="card-header"><span className="card-title">Candidate vs Primary Opposition</span></div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={candidateScoring.vsOpposition}>
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis dataKey="factor" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                  <Radar name="AK Reddy (TRP)" dataKey="ours" stroke="var(--green)" fill="var(--green)" fillOpacity={0.25} />
                  <Radar name="Priya Mehta (BNP)" dataKey="theirs" stroke="var(--red)" fill="var(--red)" fillOpacity={0.15} />
                  <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                </RadarChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                  <div style={{ width: 12, height: 3, background: 'var(--green)', borderRadius: 2 }} /> AK Reddy (TRP)
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                  <div style={{ width: 12, height: 3, background: 'var(--red)', borderRadius: 2 }} /> Priya Mehta (BNP)
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Candidate Strengths</span></div>
            <div className="card-body">
              {candidateScoring.greenFlags.map((flag) => (
                <div key={flag} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
                  <span style={{ color: 'var(--green)', flexShrink: 0, marginTop: 1 }}>✓</span>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{flag}</span>
                </div>
              ))}
              <div style={{ marginTop: 8, padding: '8px 10px', background: 'var(--green-dim)', borderRadius: 6, border: '1px solid rgba(16,185,129,0.2)' }}>
                <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                  <b style={{ color: 'var(--green)' }}>No red flags identified.</b> Candidate EC affidavit is clean. No criminal cases. Financial disclosure within normal bounds.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const MOCK_SENTIMENT_TRENDS = [
  { date: 'May 1', avg_score: 0.05, article_count: 5 },
  { date: 'May 2', avg_score: -0.12, article_count: 8 },
  { date: 'May 3', avg_score: -0.28, article_count: 11 },
  { date: 'May 4', avg_score: -0.18, article_count: 9 },
  { date: 'May 5', avg_score: 0.08, article_count: 6 },
  { date: 'May 6', avg_score: -0.05, article_count: 7 },
  { date: 'May 7', avg_score: -0.31, article_count: 13 },
  { date: 'May 8', avg_score: -0.22, article_count: 10 },
  { date: 'May 9', avg_score: 0.02, article_count: 7 },
  { date: 'May 10', avg_score: 0.15, article_count: 6 },
  { date: 'May 11', avg_score: 0.19, article_count: 5 },
  { date: 'May 12', avg_score: 0.24, article_count: 4 },
  { date: 'May 13', avg_score: 0.11, article_count: 6 },
  { date: 'May 14', avg_score: 0.28, article_count: 4 },
];

function normalizeTrends(raw) {
  const candidate = Array.isArray(raw) ? raw
    : raw?.timeline || raw?.trends || raw?.data || raw?.news_sentiment || [];
  const arr = Array.isArray(candidate) ? candidate : [];
  if (arr.length === 0) return null;
  return arr.map(t => ({
    date: t.date || (t.period_start ? new Date(t.period_start).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '—'),
    avg_score: t.polarity ?? t.avg_score ?? t.score ?? 0,
    article_count: t.article_count ?? t.count ?? t.sample_count
      ?? (t.positive != null ? (t.positive + t.negative + t.neutral) : 0),
  }));
}

function sentimentSummary(score) {
  if (score == null) return { label: '—', color: 'var(--text-muted)' };
  if (score >= 0.2) return { label: 'Positive', color: 'var(--green)' };
  if (score >= -0.2) return { label: 'Neutral', color: 'var(--yellow)' };
  return { label: 'Negative', color: 'var(--red)' };
}

function SentimentTrendsTab({ trends, isLive, loading, onRefresh, refreshing }) {
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 32, color: 'var(--text-muted)', fontSize: 13 }}>
        <div style={{ width: 16, height: 16, border: '2px solid var(--border)', borderTop: '2px solid var(--saffron)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
        Loading sentiment data…
      </div>
    );
  }

  const data = Array.isArray(trends) && trends.length > 0 ? trends : MOCK_SENTIMENT_TRENDS;
  const latest = data[data.length - 1]?.avg_score ?? null;
  const avg14 = data.reduce((s, t) => s + (t.avg_score ?? 0), 0) / data.length;
  const prev7 = data.slice(0, 7).reduce((s, t) => s + (t.avg_score ?? 0), 0) / Math.max(1, Math.min(7, data.length));
  const last7 = data.slice(-7).reduce((s, t) => s + (t.avg_score ?? 0), 0) / Math.max(1, Math.min(7, data.length));
  const trend = last7 - prev7;

  const latestInfo = sentimentSummary(latest);
  const avgInfo = sentimentSummary(avg14);

  return (
    <div>
      {/* Stats */}
      <div className="grid-4 section-gap">
        {[
          { label: 'Current Sentiment', value: latest != null ? (latest >= 0 ? '+' : '') + latest.toFixed(2) : '—', sub: latestInfo.label, color: latestInfo.color },
          { label: '14-Day Average', value: (avg14 >= 0 ? '+' : '') + avg14.toFixed(2), sub: avgInfo.label, color: avgInfo.color },
          { label: 'Recent Trend', value: trend >= 0.05 ? '▲ Rising' : trend <= -0.05 ? '▼ Falling' : '→ Stable', sub: `${Math.abs(trend * 100).toFixed(0)}pt shift`, color: trend >= 0.05 ? 'var(--green)' : trend <= -0.05 ? 'var(--red)' : 'var(--text-muted)' },
          { label: 'Data Points', value: data.length, sub: isLive ? 'Live · VANI' : 'Static sample', color: 'var(--blue)' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="stat-card" style={{ '--accent-color': color }}>
            <div className="stat-label">{label}</div>
            <div className="stat-value" style={{ fontSize: 26, color, fontFamily: 'var(--font-mono)' }}>{value}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="card section-gap">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="card-title">Media Sentiment — 14-Day Trend</span>
            {isLive
              ? <span className="live-badge"><span className="live-dot" /> Live · VANI</span>
              : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 7px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Static</span>
            }
          </div>
          <button
            className="btn btn-outline btn-sm"
            onClick={onRefresh}
            disabled={refreshing}
            style={{ display: 'flex', alignItems: 'center', gap: 5 }}
          >
            <RefreshCw size={11} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
        <div className="card-body">
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 8 }}>
            Scale: -1.0 (very negative) to +1.0 (very positive) · Neutral zone: -0.2 to +0.2
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <YAxis domain={[-1, 1]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => v.toFixed(1)} width={32} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
                formatter={(v, name) => [
                  name === 'avg_score' ? (v >= 0 ? '+' : '') + v.toFixed(2) : v,
                  name === 'avg_score' ? 'Sentiment' : 'Articles',
                ]}
              />
              <ReferenceLine y={0} stroke="var(--border-bright)" strokeDasharray="4 2" label={{ value: 'Neutral', position: 'insideRight', fill: 'var(--text-muted)', fontSize: 9 }} />
              <ReferenceLine y={0.2} stroke="var(--green)" strokeDasharray="2 4" strokeOpacity={0.4} />
              <ReferenceLine y={-0.2} stroke="var(--red)" strokeDasharray="2 4" strokeOpacity={0.4} />
              <Line
                type="monotone" dataKey="avg_score"
                stroke={latest != null ? (latest >= 0.2 ? 'var(--green)' : latest >= -0.2 ? 'var(--yellow)' : 'var(--red)') : 'var(--blue)'}
                strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls
              />
            </LineChart>
          </ResponsiveContainer>

          {/* Volume mini-chart */}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>Article Volume per Day</div>
            <ResponsiveContainer width="100%" height={52}>
              <BarChart data={data}>
                <Bar dataKey="article_count" fill="var(--border-bright)" radius={[2, 2, 0, 0]} />
                <XAxis dataKey="date" hide />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
                  formatter={(v) => [v, 'Articles']}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Interpretation */}
      <div className="card section-gap">
        <div className="card-header">
          <span className="card-title">VANI Interpretation</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {[
              {
                icon: latest != null && latest >= 0 ? <TrendingUp size={14} color="var(--green)" /> : <TrendingDown size={14} color="var(--red)" />,
                title: 'Current Media Climate',
                text: latest >= 0.2
                  ? 'Media coverage is trending positively. Constituency issues are receiving favorable attention.'
                  : latest >= -0.2
                  ? 'Media sentiment is mixed to neutral. Maintain consistent messaging to prevent negative drift.'
                  : 'Negative media cycle detected. Counter-narrative actions recommended by VANI.',
                color: latestInfo.color,
              },
              {
                icon: <Minus size={14} color="var(--text-muted)" />,
                title: 'Trend Direction',
                text: trend >= 0.05
                  ? 'Sentiment is improving compared to the prior 7 days. Recent campaign messaging appears to be working.'
                  : trend <= -0.05
                  ? 'Sentiment has declined vs. prior week. Review recent media coverage for negative triggers.'
                  : 'Sentiment is holding steady. No significant shift detected in the last 14 days.',
                color: trend >= 0.05 ? 'var(--green)' : trend <= -0.05 ? 'var(--red)' : 'var(--text-muted)',
              },
            ].map(({ icon, title, text, color }) => (
              <div key={title} style={{ padding: '14px 16px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-base)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  {icon}
                  <span style={{ fontSize: 12, fontWeight: 700, color }}>{title}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{text}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ConstituencyIntelligence() {
  const [tab, setTab] = useState(0);
  const [mapZone, setMapZone] = useState('All');
  const [mapRisk, setMapRisk] = useState('All');
  const [liveIssues, setLiveIssues] = useState(null);
  const [issuesLoading, setIssuesLoading] = useState(false);
  const [issuesError, setIssuesError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [sentimentTrends, setSentimentTrends] = useState(null);
  const [trendsLive, setTrendsLive] = useState(false);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [trendsRefreshing, setTrendsRefreshing] = useState(false);

  const loadIssues = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setIssuesLoading(true);
    try {
      const data = await getTrendingIssues();
      const normalized = normalizeLiveIssues(data);
      setLiveIssues(normalized);
      setIssuesError(null);
    } catch {
      setIssuesError('Could not load live issue data.');
    } finally {
      setIssuesLoading(false);
      setRefreshing(false);
    }
  };

  const loadTrends = async (isRefresh = false) => {
    if (isRefresh) setTrendsRefreshing(true);
    else setTrendsLoading(true);
    try {
      const data = await getSentimentTrends();
      const normalized = normalizeTrends(data);
      if (normalized?.length > 0) { setSentimentTrends(normalized); setTrendsLive(true); }
    } catch {}
    finally { setTrendsLoading(false); setTrendsRefreshing(false); }
  };

  useEffect(() => { loadIssues(); loadTrends(); }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Constituency Intelligence Engine</div>
          <div className="page-subtitle">VICHAR Agent · {constituency.fullName} · Deep constituency profiling</div>
        </div>
        <span className="live-badge"><span className="live-dot" /> VICHAR Active</span>
      </div>

      <div className="page-body">
        {/* ─── Data Source Attribution ─── */}
        <DataSourceStrip
          sources={[DATA_SOURCES.CENSUS_2011, DATA_SOURCES.ECI, DATA_SOURCES.GHMC, DATA_SOURCES.VISHLESHAN]}
          live={liveIssues && liveIssues.length > 0}
          confidence={liveIssues && liveIssues.length > 0 ? 92 : 80}
        />

        <div className="tab-bar section-gap">
          {TABS.map((t, i) => (
            <button key={t} className={`tab-btn${tab === i ? ' active' : ''}`} onClick={() => setTab(i)}>
              {t}
            </button>
          ))}
        </div>

        {tab === 0 && <DemographicsTab />}
        {tab === 1 && <HistoricalTab />}
        {tab === 2 && (
          <IssueMatrixTab
            liveIssues={liveIssues}
            issuesError={issuesError}
            issuesLoading={issuesLoading}
            onRefresh={() => loadIssues(true)}
            refreshing={refreshing}
          />
        )}
        {tab === 3 && <CandidateFitTab />}
        {tab === 4 && (
          <SentimentTrendsTab
            trends={sentimentTrends}
            isLive={trendsLive}
            loading={trendsLoading}
            onRefresh={() => loadTrends(true)}
            refreshing={trendsRefreshing}
          />
        )}
        {tab === 5 && (
          <div className="card section-gap">
            <div className="card-header">
              <span className="card-title">Booth Risk Map — Serilingampally AC-52</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>150 booths · click markers for details</span>
            </div>
            <div className="card-body">
              <Suspense fallback={
                <div style={{ height: 520, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                  Loading map…
                </div>
              }>
                <ConstituencyMap filterZone={mapZone} filterRisk={mapRisk} onZoneChange={setMapZone} onRiskChange={setMapRisk} />
              </Suspense>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
