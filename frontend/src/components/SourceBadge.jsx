import { DATA_SOURCES, CREDIBILITY_STYLE } from '../utils/sourceLabels';

// SourceBadge — displays data provenance: "Source: Census India 2011"
// Usage: <SourceBadge source={DATA_SOURCES.CENSUS_2011} />
// Usage: <SourceBadge credibility="A" name="Deccan Chronicle" />
export default function SourceBadge({ source, credibility, name, style: extraStyle }) {
  if (credibility) {
    const cred = CREDIBILITY_STYLE[credibility] || CREDIBILITY_STYLE.B;
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
        color: cred.color, background: cred.bg, border: `1px solid ${cred.border}`,
        textTransform: 'uppercase', letterSpacing: 0.5, whiteSpace: 'nowrap',
        ...extraStyle,
      }}>
        {credibility} · {cred.label}
      </span>
    );
  }

  if (!source) return null;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      fontSize: 9, fontWeight: 600, padding: '2px 7px', borderRadius: 5,
      color: source.color, background: source.bg, border: `1px solid ${source.border}`,
      letterSpacing: 0.3, whiteSpace: 'nowrap',
      ...extraStyle,
    }}>
      <span style={{ fontSize: 8, opacity: 0.7 }}>Source:</span>
      {name || source.shortLabel}
    </span>
  );
}

// Inline text version for use inside table cells / tight spaces
export function SourceTag({ label, color = 'var(--text-muted)' }) {
  return (
    <span style={{ fontSize: 9, color, fontWeight: 600, letterSpacing: 0.3 }}>
      ↳ {label}
    </span>
  );
}

function _relTime(ts) {
  if (!ts) return 'just now';
  const diff = (Date.now() - new Date(ts)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

// DataSourceStrip — horizontal attribution bar for page/panel footers
// Usage: <DataSourceStrip sources={[DATA_SOURCES.ECI, DATA_SOURCES.VAYU]} live={isLive} lastSync={syncTs} />
export function DataSourceStrip({ sources = [], live = false, lastSync = null, confidence = null }) {
  const syncLabel = live ? `Live · synced ${_relTime(lastSync)}` : `Demo data · backend offline`;
  const dotColor  = live ? 'var(--green)' : 'var(--yellow)';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
      padding: '6px 14px', borderTop: '1px solid var(--border)',
      background: 'var(--bg-elevated)',
    }}>
      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginRight: 2 }}>
        Sources
      </span>
      {sources.map(src => (
        <SourceBadge key={src.id} source={src} />
      ))}
      {confidence != null && (
        <span style={{
          fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
          background: confidence >= 80 ? 'rgba(16,185,129,0.12)' : confidence >= 60 ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
          color: confidence >= 80 ? 'var(--green)' : confidence >= 60 ? 'var(--yellow)' : 'var(--red)',
          border: `1px solid ${confidence >= 80 ? 'rgba(16,185,129,0.3)' : confidence >= 60 ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)'}`,
        }}>
          {confidence}% confidence
        </span>
      )}
      <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 5, fontSize: 9, color: 'var(--text-muted)' }}>
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: dotColor, display: 'inline-block', flexShrink: 0 }} />
        {syncLabel}
      </span>
    </div>
  );
}
