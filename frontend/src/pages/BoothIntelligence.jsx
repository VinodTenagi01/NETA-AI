import { useState, useMemo, useEffect } from 'react';
import { Search, X, RefreshCw, Download, TrendingUp, TrendingDown, Minus, Database, ChevronLeft, ChevronRight } from 'lucide-react';
import { getBoothIntelligence } from '../api/booths';

const PAGE_SIZE = 8;

const MOCK_BOOTHS = [
  { id: 'CHD-001', constituency: 'Serilingampally', area: 'Miyapur Colony', zone: 'North', total_voters: 1456, male_voters: 748, female_voters: 708, mood_score: 3.9, main_issue: 'Water Supply', support_trend: 'rising', last_updated: '2026-05-12T08:45:00' },
  { id: 'CHD-002', constituency: 'Serilingampally', area: 'Kondapur Phase 2', zone: 'Central', total_voters: 1823, male_voters: 941, female_voters: 882, mood_score: 2.4, main_issue: 'Unemployment', support_trend: 'falling', last_updated: '2026-05-12T07:30:00' },
  { id: 'CHD-003', constituency: 'Serilingampally', area: 'Nallagandla Sector 3', zone: 'West', total_voters: 967, male_voters: 503, female_voters: 464, mood_score: 3.2, main_issue: 'Roads', support_trend: 'stable', last_updated: '2026-05-11T18:20:00' },
  { id: 'CHD-004', constituency: 'Serilingampally', area: 'HITEC City Extension', zone: 'Central', total_voters: 2145, male_voters: 1134, female_voters: 1011, mood_score: 4.1, main_issue: 'Candidate Visibility', support_trend: 'rising', last_updated: '2026-05-12T09:10:00' },
  { id: 'CHD-005', constituency: 'Serilingampally', area: 'Chandanagar Main Ward', zone: 'Central', total_voters: 1378, male_voters: 712, female_voters: 666, mood_score: 3.0, main_issue: 'Drainage', support_trend: 'stable', last_updated: '2026-05-12T06:55:00' },
  { id: 'CHD-006', constituency: 'Serilingampally', area: 'Gachibowli Ward 7', zone: 'South', total_voters: 1654, male_voters: 859, female_voters: 795, mood_score: 2.8, main_issue: 'Electricity', support_trend: 'falling', last_updated: '2026-05-11T21:40:00' },
  { id: 'CHD-007', constituency: 'Serilingampally', area: 'Hafeezpet Layout', zone: 'West', total_voters: 1102, male_voters: 567, female_voters: 535, mood_score: 4.3, main_issue: 'Candidate Visibility', support_trend: 'rising', last_updated: '2026-05-12T10:00:00' },
  { id: 'CHD-008', constituency: 'Serilingampally', area: 'Nizampet Cross Roads', zone: 'North', total_voters: 1289, male_voters: 661, female_voters: 628, mood_score: 2.1, main_issue: 'Opposition Activity', support_trend: 'falling', last_updated: '2026-05-12T05:30:00' },
  { id: 'CHD-009', constituency: 'Serilingampally', area: 'Bachupally Sector 5', zone: 'North', total_voters: 1567, male_voters: 809, female_voters: 758, mood_score: 3.6, main_issue: 'Roads', support_trend: 'stable', last_updated: '2026-05-11T16:45:00' },
  { id: 'CHD-010', constituency: 'Serilingampally', area: 'Bowrampet Village', zone: 'West', total_voters: 878, male_voters: 456, female_voters: 422, mood_score: 3.4, main_issue: 'Water Supply', support_trend: 'rising', last_updated: '2026-05-12T07:15:00' },
  { id: 'CHD-011', constituency: 'Serilingampally', area: 'RC Puram Sector 2', zone: 'West', total_voters: 1923, male_voters: 998, female_voters: 925, mood_score: 2.7, main_issue: 'Healthcare', support_trend: 'falling', last_updated: '2026-05-11T20:00:00' },
  { id: 'CHD-012', constituency: 'Serilingampally', area: 'Sanath Nagar Ward 4', zone: 'South', total_voters: 1344, male_voters: 694, female_voters: 650, mood_score: 3.8, main_issue: 'Education', support_trend: 'rising', last_updated: '2026-05-12T08:00:00' },
  { id: 'SRL-001', constituency: 'Serilingampally', area: 'Serilingampally Old Town', zone: 'South', total_voters: 1876, male_voters: 967, female_voters: 909, mood_score: 3.1, main_issue: 'Roads', support_trend: 'stable', last_updated: '2026-05-12T08:30:00' },
  { id: 'SRL-002', constituency: 'Serilingampally', area: 'Patancheru Township', zone: 'West', total_voters: 2234, male_voters: 1154, female_voters: 1080, mood_score: 2.3, main_issue: 'Unemployment', support_trend: 'falling', last_updated: '2026-05-11T22:10:00' },
  { id: 'SRL-003', constituency: 'Serilingampally', area: 'Chandanagar Market Road', zone: 'Central', total_voters: 1123, male_voters: 580, female_voters: 543, mood_score: 3.7, main_issue: 'Water Supply', support_trend: 'rising', last_updated: '2026-05-12T09:45:00' },
  { id: 'SRL-004', constituency: 'Serilingampally', area: 'Tellapur Junction', zone: 'West', total_voters: 1456, male_voters: 751, female_voters: 705, mood_score: 3.5, main_issue: 'Roads', support_trend: 'stable', last_updated: '2026-05-11T17:20:00' },
  { id: 'SRL-005', constituency: 'Serilingampally', area: 'Ramachandrapuram Ext', zone: 'North', total_voters: 1098, male_voters: 566, female_voters: 532, mood_score: 4.0, main_issue: 'Candidate Visibility', support_trend: 'rising', last_updated: '2026-05-12T07:50:00' },
  { id: 'KUK-001', constituency: 'Kukatpally', area: 'KPHB Colony Phase 6', zone: 'North', total_voters: 2456, male_voters: 1267, female_voters: 1189, mood_score: 2.9, main_issue: 'Traffic & Parking', support_trend: 'stable', last_updated: '2026-05-12T06:00:00' },
  { id: 'KUK-002', constituency: 'Kukatpally', area: 'Kukatpally Housing Board', zone: 'Central', total_voters: 1987, male_voters: 1026, female_voters: 961, mood_score: 3.3, main_issue: 'Sanitation', support_trend: 'stable', last_updated: '2026-05-11T19:30:00' },
  { id: 'KUK-003', constituency: 'Kukatpally', area: 'Moosapet Junction', zone: 'South', total_voters: 1543, male_voters: 796, female_voters: 747, mood_score: 4.2, main_issue: 'Parks & Recreation', support_trend: 'rising', last_updated: '2026-05-12T09:20:00' },
];

function moodColor(score) {
  if (score >= 3.8) return 'var(--green)';
  if (score >= 2.8) return 'var(--yellow)';
  return 'var(--red)';
}

function moodBadgeClass(score) {
  if (score >= 3.8) return 'badge-green';
  if (score >= 2.8) return 'badge-yellow';
  return 'badge-red';
}

function TrendBadge({ trend }) {
  if (trend === 'rising')  return <span className="badge badge-green" style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><TrendingUp size={9} /> Rising</span>;
  if (trend === 'falling') return <span className="badge badge-red"   style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><TrendingDown size={9} /> Falling</span>;
  return <span className="badge badge-gray" style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><Minus size={9} /> Stable</span>;
}

function formatRelTime(ts) {
  if (!ts) return '—';
  const diff = (Date.now() - new Date(ts)) / 1000;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function SortArrow({ col, current, dir }) {
  if (col !== current) return <span style={{ color: 'var(--border-bright)', marginLeft: 3 }}>↕</span>;
  return <span style={{ color: 'var(--saffron)', marginLeft: 3 }}>{dir === 'asc' ? '↑' : '↓'}</span>;
}

function downloadCSV(data) {
  const headers = ['Booth ID', 'Constituency', 'Area/Ward', 'Zone', 'Total Voters', 'Male', 'Female', 'Mood Score', 'Main Issue', 'Support Trend', 'Last Updated'];
  const rows = data.map(b => [
    b.id, b.constituency, b.area, b.zone, b.total_voters,
    b.male_voters, b.female_voters,
    b.mood_score, b.main_issue, b.support_trend,
    b.last_updated ? new Date(b.last_updated).toLocaleString('en-IN') : '',
  ].map(v => `"${String(v).replace(/"/g, '""')}"`));
  const csv = [headers.map(h => `"${h}"`), ...rows].map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `booth-intelligence-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function BoothIntelligence() {
  const [booths, setBooths] = useState(MOCK_BOOTHS);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [search, setSearch] = useState('');
  const [filterConstituency, setFilterConstituency] = useState('All');
  const [filterTrend, setFilterTrend] = useState('All');
  const [sortCol, setSortCol] = useState('id');
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);

  useEffect(() => {
    getBoothIntelligence()
      .then(d => {
        const arr = Array.isArray(d) ? d : d.items || d.booths || [];
        if (arr.length > 0) { setBooths(arr); setIsLive(true); }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const constituencies = useMemo(() => ['All', ...new Set(booths.map(b => b.constituency).filter(Boolean))], [booths]);

  const filtered = useMemo(() => {
    let rows = booths.filter(b => {
      if (filterConstituency !== 'All' && b.constituency !== filterConstituency) return false;
      if (filterTrend !== 'All' && b.support_trend !== filterTrend.toLowerCase()) return false;
      if (search) {
        const q = search.toLowerCase();
        return (b.id || '').toLowerCase().includes(q) ||
               (b.constituency || '').toLowerCase().includes(q) ||
               (b.area || '').toLowerCase().includes(q) ||
               (b.main_issue || '').toLowerCase().includes(q) ||
               (b.zone || '').toLowerCase().includes(q);
      }
      return true;
    });

    rows = [...rows].sort((a, b) => {
      let va = a[sortCol] ?? '', vb = b[sortCol] ?? '';
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortDir === 'asc' ? va - vb : vb - va;
      }
      va = String(va).toLowerCase();
      vb = String(vb).toLowerCase();
      return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
    });

    return rows;
  }, [booths, filterConstituency, filterTrend, search, sortCol, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageData = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('asc'); }
    setPage(1);
  };

  const avgMood = booths.length ? (booths.reduce((s, b) => s + b.mood_score, 0) / booths.length).toFixed(1) : '—';
  const rising = booths.filter(b => b.support_trend === 'rising').length;
  const critical = booths.filter(b => b.mood_score < 2.5).length;

  const hasFilters = filterConstituency !== 'All' || filterTrend !== 'All' || search;

  const ThCol = ({ col, children, style = {} }) => (
    <th
      onClick={() => toggleSort(col)}
      style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap', ...style }}
    >
      {children}
      <SortArrow col={col} current={sortCol} dir={sortDir} />
    </th>
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Booth Intelligence Data</div>
          <div className="page-subtitle">
            Raw booth-level voter intelligence · {booths.length} booths across {constituencies.length - 1} constituencies
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isLive
            ? <span className="live-badge"><span className="live-dot" /> Live</span>
            : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 8px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Demo Data</span>
          }
          <button
            className="btn btn-outline btn-sm"
            onClick={() => downloadCSV(filtered)}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Download size={12} />
            Export CSV ({filtered.length})
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => {
              setLoading(true);
              getBoothIntelligence()
                .then(d => {
                  const arr = Array.isArray(d) ? d : d.items || d.booths || [];
                  if (arr.length > 0) { setBooths(arr); setIsLive(true); }
                })
                .catch(() => {})
                .finally(() => setLoading(false));
            }}
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      <div className="page-body">

        {/* Summary stats */}
        <div className="grid-4 section-gap">
          {[
            { label: 'Total Booths', value: booths.length, color: 'var(--text-primary)', sub: `${constituencies.length - 1} constituencies` },
            {
              label: 'Avg Mood Score',
              value: avgMood,
              color: moodColor(Number(avgMood)),
              sub: 'Across all booths',
            },
            {
              label: 'Rising Support',
              value: rising,
              color: 'var(--green)',
              sub: `${Math.round((rising / booths.length) * 100)}% of total`,
            },
            {
              label: 'Critical Booths',
              value: critical,
              color: critical > 0 ? 'var(--red)' : 'var(--green)',
              sub: 'Mood score < 2.5',
            },
          ].map(({ label, value, color, sub }) => (
            <div key={label} className="stat-card" style={{ '--accent-color': color }}>
              <div className="stat-label">{label}</div>
              <div className="stat-value" style={{ fontSize: 28, color, fontFamily: 'var(--font-mono)' }}>{value}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* Mood distribution bar */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title"><Database size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />Booth Mood Distribution</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{booths.length} booths · color = sentiment band</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', height: 32, borderRadius: 6, overflow: 'hidden', gap: 2 }}>
              {(() => {
                const pos = booths.filter(b => b.mood_score >= 3.8).length;
                const neu = booths.filter(b => b.mood_score >= 2.8 && b.mood_score < 3.8).length;
                const neg = booths.filter(b => b.mood_score < 2.8).length;
                const total = booths.length || 1;
                return [
                  { label: `Positive (≥3.8) · ${pos}`, pct: (pos / total) * 100, color: 'var(--green)' },
                  { label: `Neutral (2.8–3.8) · ${neu}`, pct: (neu / total) * 100, color: 'var(--yellow)' },
                  { label: `Negative (<2.8) · ${neg}`, pct: (neg / total) * 100, color: 'var(--red)' },
                ].map(({ label, pct, color }) => (
                  <div
                    key={label}
                    title={label}
                    style={{
                      flex: pct, background: color, display: 'flex', alignItems: 'center',
                      justifyContent: 'center', opacity: 0.85,
                      fontSize: 9, fontWeight: 700, color: '#fff', minWidth: pct > 5 ? undefined : 0,
                    }}
                  >
                    {pct > 8 ? `${Math.round(pct)}%` : ''}
                  </div>
                ));
              })()}
            </div>
            <div style={{ display: 'flex', gap: 18, marginTop: 8 }}>
              {[
                { label: 'Positive ≥ 3.8', color: 'var(--green)' },
                { label: 'Neutral 2.8–3.8', color: 'var(--yellow)' },
                { label: 'Negative < 2.8', color: 'var(--red)' },
              ].map(({ label, color }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
                  <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Table card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              Booth Directory
              <span style={{ marginLeft: 8, fontWeight: 400, fontSize: 11, color: 'var(--text-muted)' }}>
                {filtered.length} of {booths.length} booths
                {hasFilters && ' (filtered)'}
              </span>
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              Click column headers to sort
            </span>
          </div>

          {/* Filter bar */}
          <div style={{
            padding: '10px 16px', borderBottom: '1px solid var(--border)',
            display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
          }}>
            <div style={{ position: 'relative', flex: '1 1 220px' }}>
              <Search size={12} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                className="search-input"
                style={{ paddingLeft: 28 }}
                placeholder="Search booth ID, area, issue, zone…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
              />
            </div>

            <select
              className="select-input"
              value={filterConstituency}
              onChange={e => { setFilterConstituency(e.target.value); setPage(1); }}
            >
              {constituencies.map(c => (
                <option key={c} value={c}>{c === 'All' ? 'All Constituencies' : c}</option>
              ))}
            </select>

            <select
              className="select-input"
              value={filterTrend}
              onChange={e => { setFilterTrend(e.target.value); setPage(1); }}
            >
              <option value="All">All Trends</option>
              <option value="Rising">Rising</option>
              <option value="Stable">Stable</option>
              <option value="Falling">Falling</option>
            </select>

            {hasFilters && (
              <button
                className="btn btn-outline btn-sm"
                onClick={() => { setSearch(''); setFilterConstituency('All'); setFilterTrend('All'); setPage(1); }}
              >
                <X size={10} /> Clear
              </button>
            )}
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            {loading ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Booth ID</th><th>Constituency</th><th>Area/Ward</th><th>Zone</th>
                    <th>Total Voters</th><th>Male</th><th>Female</th>
                    <th>Mood Score</th><th>Main Issue</th><th>Trend</th><th>Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {[0,1,2,3,4,5].map(i => (
                    <tr key={i}>
                      {[55, 110, 130, 60, 70, 40, 40, 60, 100, 70, 80].map((w, j) => (
                        <td key={j}><div className="skeleton" style={{ height: 12, width: w, borderRadius: 4 }} /></td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : filtered.length === 0 ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                No booths match the current filters.
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <ThCol col="id">Booth ID</ThCol>
                    <ThCol col="constituency">Constituency</ThCol>
                    <ThCol col="area">Area / Ward</ThCol>
                    <ThCol col="zone">Zone</ThCol>
                    <ThCol col="total_voters" style={{ textAlign: 'right' }}>Total Voters</ThCol>
                    <ThCol col="male_voters" style={{ textAlign: 'right' }}>Male</ThCol>
                    <ThCol col="female_voters" style={{ textAlign: 'right' }}>Female</ThCol>
                    <ThCol col="mood_score" style={{ textAlign: 'center' }}>Mood</ThCol>
                    <ThCol col="main_issue">Main Issue</ThCol>
                    <ThCol col="support_trend" style={{ textAlign: 'center' }}>Trend</ThCol>
                    <ThCol col="last_updated">Last Updated</ThCol>
                  </tr>
                </thead>
                <tbody>
                  {pageData.map(b => (
                    <tr key={b.id}>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--saffron)', fontSize: 11 }}>{b.id}</span>
                      </td>
                      <td>
                        <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>{b.constituency}</span>
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-secondary)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {b.area}
                      </td>
                      <td>
                        <span className={`zone-pill zone-${(b.zone || '').toLowerCase()}`}>{b.zone}</span>
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600 }}>
                        {(b.total_voters ?? 0).toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--blue)' }}>
                        {(b.male_voters ?? 0).toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--purple)' }}>
                        {(b.female_voters ?? 0).toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className={`badge ${moodBadgeClass(b.mood_score)}`} style={{ fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                          {b.mood_score != null ? b.mood_score.toFixed(1) : '—'}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          fontSize: 11, color: 'var(--text-secondary)',
                          maxWidth: 130, display: 'inline-block',
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        }} title={b.main_issue}>
                          {b.main_issue}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <TrendBadge trend={b.support_trend} />
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                        {formatRelTime(b.last_updated)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination */}
          {!loading && filtered.length > PAGE_SIZE && (
            <div style={{
              padding: '10px 16px', borderTop: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: 'var(--bg-base)',
            }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length} booths
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  style={{ padding: '4px 8px', display: 'flex', alignItems: 'center' }}
                >
                  <ChevronLeft size={13} />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(pg => (
                  <button
                    key={pg}
                    onClick={() => setPage(pg)}
                    style={{
                      width: 28, height: 28, borderRadius: 5, border: '1px solid',
                      borderColor: pg === page ? 'var(--saffron)' : 'var(--border)',
                      background: pg === page ? 'var(--saffron-dim)' : 'none',
                      color: pg === page ? 'var(--saffron)' : 'var(--text-secondary)',
                      fontSize: 11, fontWeight: pg === page ? 700 : 400,
                      cursor: 'pointer', transition: 'all 0.1s',
                    }}
                  >
                    {pg}
                  </button>
                ))}
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  style={{ padding: '4px 8px', display: 'flex', alignItems: 'center' }}
                >
                  <ChevronRight size={13} />
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
