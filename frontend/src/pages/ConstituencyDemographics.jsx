import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts';
import { Users, BookOpen, MapPin, Building2, TrendingUp, RefreshCw } from 'lucide-react';
import { getConstituencyDemographics } from '../api/demographics';

const PRIMARY_CID = '11111111-0052-4000-8000-000000000001';

const STATIC_DATA = {
  overview: {
    population: 398640,
    voters: 248432,
    literacy: 76.2,
    area: 52.4,
    gender_ratio: 944,
    urban_pct: 73.6,
    bpl_pct: 21.4,
    avg_income: 54800,
    census_year: 2021,
    constituency: 'Serilingampally',
    district: 'Rangareddy / GHMC',
    state: 'Telangana',
    assembly_no: 52,
    reserved: 'General (Unreserved)',
    total_booths: 225,
    male_voters: 127364,
    female_voters: 121068,
  },
  age_distribution: [
    { group: '18–25', voters: 54654, pct: 22.0 },
    { group: '26–35', voters: 69561, pct: 28.0 },
    { group: '46–45', voters: 47202, pct: 19.0 },
    { group: '46–55', voters: 39749, pct: 16.0 },
    { group: '56–65', voters: 24843, pct: 10.0 },
    { group: '65+',   voters: 12422, pct:  5.0 },
  ],
  occupation: [
    { name: 'IT & Technology',  pct: 29, color: 'var(--blue)' },
    { name: 'Business / Trade', pct: 20, color: 'var(--saffron)' },
    { name: 'Govt / PSU',       pct: 16, color: 'var(--purple)' },
    { name: 'Daily Labour',     pct: 17, color: 'var(--red)' },
    { name: 'Students',         pct: 11, color: 'var(--yellow)' },
    { name: 'Healthcare',       pct:  4, color: 'var(--green)' },
    { name: 'Other',            pct:  3, color: 'var(--text-muted)' },
  ],
  education: [
    { level: 'Post Graduate', pct: 15, color: 'var(--green)' },
    { level: 'Graduate',      pct: 22, color: 'var(--blue)' },
    { level: 'Sr Secondary',  pct: 24, color: 'var(--saffron)' },
    { level: 'Secondary',     pct: 20, color: 'var(--yellow)' },
    { level: 'Primary',       pct: 13, color: 'var(--red)' },
    { level: 'Illiterate',    pct:  6, color: 'var(--text-muted)' },
  ],
  community: [
    { group: 'OBC',          pct: 36, color: '#6366f1' },
    { group: 'General',      pct: 30, color: '#f97316' },
    { group: 'SC / Dalit',   pct: 20, color: '#10b981' },
    { group: 'ST / Adivasi', pct:  8, color: '#f59e0b' },
    { group: 'Minority',     pct:  6, color: '#3b82f6' },
  ],
  zones: [
    { zone: 'Central', booths: 34, voters: 71200, literacy: 80.4, urban: 96, main_issue: 'Roads & Infrastructure' },
    { zone: 'North',   booths: 32, voters: 64800, literacy: 72.1, urban: 62, main_issue: 'Water Supply' },
    { zone: 'South',   booths: 28, voters: 52400, literacy: 77.9, urban: 80, main_issue: 'Employment' },
    { zone: 'East',    booths: 26, voters: 34620, literacy: 68.4, urban: 51, main_issue: 'Electricity' },
    { zone: 'West',    booths: 30, voters: 25412, literacy: 78.2, urban: 68, main_issue: 'Drainage & Sanitation' },
  ],
  languages: [
    { lang: 'Telugu', pct: 68 },
    { lang: 'Urdu', pct: 14 },
    { lang: 'Hindi', pct: 10 },
    { lang: 'Other', pct: 8 },
  ],
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || 'var(--saffron)', fontSize: 11 }}>
          {p.name}: {p.value}{p.unit || ''}
        </div>
      ))}
    </div>
  );
};

function StatCard({ icon: Icon, label, value, sub, color = 'var(--saffron)' }) {
  return (
    <div className="stat-card" style={{ '--accent-color': color }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 7,
          background: `${color}18`, border: `1px solid ${color}33`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={13} color={color} />
        </div>
        <div className="stat-label">{label}</div>
      </div>
      <div className="stat-value" style={{ fontSize: 26, color, fontFamily: 'var(--font-mono)' }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function mergeWithLive(live) {
  if (!live) return STATIC_DATA;
  const s = live.social_indicators || {};
  const caste = live.caste_composition || {};
  const religion = live.religious_composition || {};
  const voters = live.total_voters || STATIC_DATA.overview.voters;
  const malePct = s.male_pct ?? (STATIC_DATA.overview.male_voters / STATIC_DATA.overview.voters * 100);
  const femalePct = s.female_pct ?? (STATIC_DATA.overview.female_voters / STATIC_DATA.overview.voters * 100);

  const communityColors = ['#6366f1', '#f97316', '#10b981', '#f59e0b', '#3b82f6'];
  const communityFromLive = [
    { group: 'OBC',          pct: caste.obc     ?? STATIC_DATA.community[0].pct, color: communityColors[0] },
    { group: 'General',      pct: caste.general  ?? STATIC_DATA.community[1].pct, color: communityColors[1] },
    { group: 'SC / Dalit',   pct: caste.sc       ?? STATIC_DATA.community[2].pct, color: communityColors[2] },
    { group: 'ST / Adivasi', pct: caste.st       ?? STATIC_DATA.community[3].pct, color: communityColors[3] },
    { group: 'Minority',     pct: (religion.muslim ?? 0) + (religion.christian ?? 0) + (religion.other ?? 0) || STATIC_DATA.community[4].pct, color: communityColors[4] },
  ];

  return {
    ...STATIC_DATA,
    overview: {
      ...STATIC_DATA.overview,
      voters,
      literacy: s.literacy_rate    ?? STATIC_DATA.overview.literacy,
      urban_pct: s.urban_pct       ?? STATIC_DATA.overview.urban_pct,
      bpl_pct: s.bpl_pct           ?? STATIC_DATA.overview.bpl_pct,
      total_booths: live.total_booths ?? STATIC_DATA.overview.total_booths,
      constituency: live.constituency_name ?? STATIC_DATA.overview.constituency,
      male_voters: Math.round(voters * malePct / 100),
      female_voters: Math.round(voters * femalePct / 100),
    },
    community: communityFromLive,
  };
}

export default function ConstituencyDemographics() {
  const [liveData, setLiveData] = useState(null);
  const [dataSource, setDataSource] = useState('static');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getConstituencyDemographics(PRIMARY_CID)
      .then(res => {
        setLiveData(res);
        setDataSource(res.data_source === 'db_aggregate' ? 'live' : 'estimate');
      })
      .catch(() => setDataSource('offline'))
      .finally(() => setLoading(false));
  }, []);

  const d = mergeWithLive(liveData);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Constituency Demographics</div>
          <div className="page-subtitle">
            Census 2021 · {d.overview.constituency}, {d.overview.district} · Assembly Seat #{d.overview.assembly_no} · VICHAR Analysis
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: 'var(--text-muted)' }}>
              <RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} /> Loading live data…
            </span>
          ) : (
            <span style={{
              fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 10,
              color: dataSource === 'live' ? 'var(--green)' : dataSource === 'estimate' ? 'var(--yellow)' : 'var(--text-muted)',
              background: dataSource === 'live' ? 'rgba(16,185,129,0.1)' : 'rgba(217,119,6,0.1)',
              border: `1px solid ${dataSource === 'live' ? 'rgba(16,185,129,0.3)' : 'rgba(217,119,6,0.3)'}`,
            }}>
              {dataSource === 'live' ? 'Live · DB Aggregate' : dataSource === 'estimate' ? 'Static Estimate' : 'Offline · Static'}
            </span>
          )}
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 10,
            color: 'var(--blue)', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)',
          }}>
            Census 2021
          </span>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 10,
            color: 'var(--purple)', background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.3)',
          }}>
            {d.overview.reserved}
          </span>
        </div>
      </div>

      <div className="page-body">

        {/* ── Primary Stats ── */}
        <div className="grid-4 section-gap">
          <StatCard icon={Users}    label="Total Population"     value={d.overview.population.toLocaleString('en-IN')}  sub={`${d.overview.state} · ${d.overview.district}`} color="var(--blue)" />
          <StatCard icon={Users}    label="Registered Voters"    value={d.overview.voters.toLocaleString('en-IN')}      sub={`${((d.overview.voters/d.overview.population)*100).toFixed(1)}% of population`} color="var(--saffron)" />
          <StatCard icon={BookOpen} label="Literacy Rate"        value={`${d.overview.literacy}%`}                     sub="Age 7+ population" color="var(--green)" />
          <StatCard icon={MapPin}   label="Constituency Area"    value={`${d.overview.area} km²`}                      sub={`${d.overview.total_booths} booths · ${d.zones.length} zones`} color="var(--purple)" />
        </div>

        {/* ── Secondary Stats ── */}
        <div className="grid-4 section-gap">
          <StatCard icon={Users}    label="Gender Ratio"         value={`${d.overview.gender_ratio}F`}                 sub="per 1000 males" color="var(--purple)" />
          <StatCard icon={Building2} label="Urban Population"    value={`${d.overview.urban_pct}%`}                    sub={`${(100 - d.overview.urban_pct).toFixed(1)}% rural`} color="var(--blue)" />
          <StatCard icon={TrendingUp} label="BPL Households"     value={`${d.overview.bpl_pct}%`}                      sub="Below poverty line" color="var(--red)" />
          <StatCard icon={TrendingUp} label="Avg Annual Income"  value={`₹${(d.overview.avg_income/1000).toFixed(0)}K`} sub="Per household" color="var(--green)" />
        </div>

        {/* ── Voter Gender Split + Language ── */}
        <div className="grid-2 section-gap">
          {/* Voter gender split */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Voter Gender Distribution</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Electoral roll 2026</span>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 24, marginBottom: 20 }}>
                <div>
                  <div style={{ fontSize: 32, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--blue)' }}>
                    {d.overview.male_voters.toLocaleString('en-IN')}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Male voters</div>
                </div>
                <div style={{ fontSize: 22, color: 'var(--border-bright)', marginBottom: 8 }}>vs</div>
                <div>
                  <div style={{ fontSize: 32, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--purple)' }}>
                    {d.overview.female_voters.toLocaleString('en-IN')}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Female voters</div>
                </div>
              </div>
              <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', marginBottom: 6 }}>
                <div style={{ flex: d.overview.male_voters, background: 'var(--blue)', opacity: 0.8 }} />
                <div style={{ flex: d.overview.female_voters, background: 'var(--purple)', opacity: 0.8 }} />
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--blue)' }} />
                  <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Male {((d.overview.male_voters/d.overview.voters)*100).toFixed(1)}%</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--purple)' }} />
                  <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Female {((d.overview.female_voters/d.overview.voters)*100).toFixed(1)}%</span>
                </div>
              </div>

              <div className="divider" />

              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Language Composition</div>
              {d.languages.map(({ lang, pct }) => (
                <div key={lang} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{lang}</span>
                    <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--saffron)' }}>{pct}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${pct}%`, background: 'var(--saffron)' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Zone summary */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Zone-Level Breakdown</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>5 electoral zones</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Zone</th>
                    <th style={{ textAlign: 'right' }}>Booths</th>
                    <th style={{ textAlign: 'right' }}>Voters</th>
                    <th style={{ textAlign: 'right' }}>Literacy</th>
                    <th style={{ textAlign: 'right' }}>Urban %</th>
                    <th>Main Issue</th>
                  </tr>
                </thead>
                <tbody>
                  {d.zones.map(z => (
                    <tr key={z.zone}>
                      <td><span className={`zone-pill zone-${z.zone.toLowerCase()}`}>{z.zone}</span></td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12 }}>{z.booths}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12 }}>{z.voters.toLocaleString('en-IN')}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12, color: z.literacy >= 75 ? 'var(--green)' : 'var(--yellow)' }}>{z.literacy}%</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12 }}>{z.urban}%</td>
                      <td style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{z.main_issue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Age Distribution + Occupation ── */}
        <div className="grid-2 section-gap">
          {/* Age distribution */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Voter Age Distribution</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Registered voters by age group</span>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={d.age_distribution} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="group" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => `${Math.round(v/1000)}K`} />
                  <Tooltip content={<CustomTooltip />} formatter={(v) => [v.toLocaleString('en-IN'), 'Voters']} />
                  <Bar dataKey="voters" radius={[4, 4, 0, 0]}>
                    {d.age_distribution.map((_, i) => (
                      <Cell key={i} fill={i <= 1 ? 'var(--green)' : i <= 3 ? 'var(--saffron)' : 'var(--blue)'} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--green)' }} /><span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Youth (18–35)</span></div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--saffron)' }} /><span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Middle (36–55)</span></div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--blue)' }} /><span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Senior (56+)</span></div>
              </div>
            </div>
          </div>

          {/* Occupation */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Occupation Profile</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Working population · Census 2021</span>
            </div>
            <div className="card-body">
              {d.occupation.map(({ name, pct, color }) => (
                <div key={name} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{name}</span>
                    <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>{pct}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Education + Community ── */}
        <div className="grid-2 section-gap">
          {/* Education */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Education Levels</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Population 15+ years · Census 2021</span>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={d.education}
                  layout="vertical"
                  margin={{ top: 0, right: 40, left: 8, bottom: 0 }}
                >
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} domain={[0, 30]} tickFormatter={v => `${v}%`} />
                  <YAxis type="category" dataKey="level" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} width={88} />
                  <Tooltip formatter={(v) => [`${v}%`, 'Share']} contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                  <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                    {d.education.map((e, i) => (
                      <Cell key={i} fill={e.color} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Community composition */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Community Composition</span>
              <span style={{ fontSize: 9, color: 'var(--yellow)', padding: '1px 6px', borderRadius: 8, background: 'rgba(217,119,6,0.1)', border: '1px solid rgba(217,119,6,0.3)' }}>
                Indicative Only
              </span>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                <div style={{ flexShrink: 0 }}>
                  <ResponsiveContainer width={140} height={140}>
                    <PieChart>
                      <Pie
                        data={d.community}
                        cx={68} cy={68}
                        innerRadius={38} outerRadius={64}
                        dataKey="pct" paddingAngle={2}
                      >
                        {d.community.map((c, i) => (
                          <Cell key={i} fill={c.color} fillOpacity={0.85} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => [`${v}%`, 'Share']} contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ flex: 1 }}>
                  {d.community.map(({ group, pct, color }) => (
                    <div key={group} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 9 }}>
                      <div style={{ width: 10, height: 10, borderRadius: 2, background: color, flexShrink: 0 }} />
                      <div style={{ flex: 1, fontSize: 11, color: 'var(--text-primary)' }}>{group}</div>
                      <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color }}>{pct}%</div>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{
                marginTop: 12, padding: '8px 10px', borderRadius: 6,
                background: 'rgba(217,119,6,0.08)', border: '1px solid rgba(217,119,6,0.2)',
                fontSize: 10, color: 'var(--yellow)', lineHeight: 1.5,
              }}>
                Community data is indicative based on district averages. Exact constituency-level caste census data is not publicly released by GoI.
              </div>
            </div>
          </div>
        </div>

        {/* ── Economic Indicators ── */}
        <div className="card section-gap">
          <div className="card-header">
            <span className="card-title">Economic Indicators</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>NSSO · Census 2021 · State Planning Board</span>
          </div>
          <div className="card-body">
            <div className="grid-4">
              {[
                { label: 'Avg Household Income', value: `₹${(d.overview.avg_income/1000).toFixed(1)}K`, sub: 'Per annum · 2023 est.', color: 'var(--green)' },
                { label: 'BPL Households',        value: `${d.overview.bpl_pct}%`,    sub: '~21,000 households',   color: 'var(--red)' },
                { label: 'Unemployment Rate',      value: '8.4%',                      sub: 'Urban youth 18–35',    color: 'var(--yellow)' },
                { label: 'Mobile Penetration',     value: '82.3%',                     sub: 'Smartphone ownership', color: 'var(--blue)' },
              ].map(({ label, value, sub, color }) => (
                <div key={label} style={{ padding: '14px 16px', background: 'var(--bg-elevated)', borderRadius: 8, border: `1px solid ${color}22` }}>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>{label}</div>
                  <div style={{ fontSize: 26, fontWeight: 900, fontFamily: 'var(--font-mono)', color }}>{value}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Source attribution */}
        <div style={{
          padding: '10px 14px', borderRadius: 8, marginTop: 8,
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
          fontSize: 10, color: 'var(--text-dim)', display: 'flex', gap: 16, flexWrap: 'wrap',
        }}>
          <span>Sources:</span>
          {['Census of India 2021', 'Election Commission of India', 'NSSO 2022–23', 'State Planning Board Telangana', 'VICHAR Constituency Profiler v1.0'].map(s => (
            <span key={s} style={{ color: 'var(--text-muted)', padding: '1px 6px', borderRadius: 4, background: 'var(--bg-base)', border: '1px solid var(--border)' }}>{s}</span>
          ))}
        </div>

      </div>
    </div>
  );
}
