export default function StatCard({ label, value, sub, trend, trendDir, accentColor = 'var(--saffron)' }) {
  const trendClass = trendDir === 'up' ? 'trend-up' : trendDir === 'down' ? 'trend-down' : 'trend-flat';
  const trendIcon  = trendDir === 'up' ? '▲' : trendDir === 'down' ? '▼' : '—';

  return (
    <div className="stat-card" style={{ '--accent-color': accentColor }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub   && <div className="stat-sub">{sub}</div>}
      {trend && <div className={`stat-trend ${trendClass}`}>{trendIcon} {trend}</div>}
    </div>
  );
}
