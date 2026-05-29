import { useState } from 'react';
import { AlertTriangle, Activity, Mic, Brain, ChevronDown, ChevronUp } from 'lucide-react';
import { safeText } from '../utils/safeText';

const ZONE_STATUS_STYLE = {
  'critical':     { color: 'var(--red)',    label: 'CRITICAL' },
  'at-risk':      { color: 'var(--yellow)', label: 'AT RISK' },
  'on-track':     { color: 'var(--blue)',   label: 'ON TRACK' },
  'above-target': { color: 'var(--green)',  label: 'ABOVE TGT' },
};

const ACTION_URGENCY = {
  critical: { color: 'var(--red)',    bg: 'var(--red-dim)',    border: 'rgba(239,68,68,0.3)' },
  high:     { color: 'var(--yellow)', bg: 'var(--yellow-dim)', border: 'rgba(245,158,11,0.3)' },
  medium:   { color: 'var(--blue)',   bg: 'var(--blue-dim)',   border: 'rgba(59,130,246,0.3)' },
};

// ── Reusable icon box ────────────────────────────────────────────────────────
function IconBox({ icon: Icon, color, colorRaw }) {
  return (
    <div style={{
      width: 28, height: 28, borderRadius: 7, flexShrink: 0,
      background: `${colorRaw || 'rgba(255,255,255,0.08)'}22`,
      border: `1px solid ${colorRaw || 'rgba(255,255,255,0.15)'}44`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <Icon size={13} color={color} />
    </div>
  );
}

// ── AlertCard ────────────────────────────────────────────────────────────────
export function AlertCard({ alert }) {
  if (!alert) return null;
  return (
    <div
      className="exec-alert-card"
      style={{
        padding: '16px 20px',
        background: 'linear-gradient(135deg, rgba(239,68,68,0.11) 0%, rgba(239,68,68,0.04) 100%)',
        borderRadius: 12,
        border: '1px solid rgba(239,68,68,0.4)',
        backdropFilter: 'blur(8px)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Accent glow bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: 'linear-gradient(90deg, transparent 0%, rgba(239,68,68,0.85) 50%, transparent 100%)',
      }} />

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
        {/* Pulsing dot */}
        <div style={{
          width: 10, height: 10, borderRadius: '50%', flexShrink: 0, marginTop: 4,
          background: 'var(--red)',
          animation: 'pulse-live-red 1.8s ease-in-out infinite',
        }} />

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Header row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
            <AlertTriangle size={13} color="var(--red)" />
            <span style={{
              fontSize: 10, fontWeight: 800, letterSpacing: 1.5,
              color: 'var(--red)', textTransform: 'uppercase',
            }}>
              {alert.priority || 'HIGH'} PRIORITY
            </span>
            <span style={{
              fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 20,
              background: 'var(--red-dim)', color: 'var(--red)',
              border: '1px solid rgba(239,68,68,0.3)',
            }}>
              ALERT
            </span>
            {alert.timestamp && (
              <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 'auto', fontFamily: 'var(--font-mono)' }}>
                {alert.timestamp}
              </span>
            )}
          </div>

          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, lineHeight: 1.4 }}>
            {safeText(alert.title)}
          </div>

          {alert.summary && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 12 }}>
              {safeText(alert.summary)}
            </div>
          )}

          {alert.action && (
            <div style={{
              display: 'flex', alignItems: 'flex-start', gap: 8,
              padding: '8px 12px', borderRadius: 8,
              background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
            }}>
              <span style={{
                fontSize: 9, fontWeight: 800, color: 'var(--red)',
                textTransform: 'uppercase', letterSpacing: 1, flexShrink: 0, paddingTop: 1,
              }}>
                ACTION →
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {safeText(alert.action)}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── OperationsCard ───────────────────────────────────────────────────────────
export function OperationsCard({ ops }) {
  if (!ops) return null;
  const zones = ops.zones || [];

  return (
    <div style={{
      padding: '16px 20px', height: '100%',
      background: 'linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.04) 100%)',
      borderRadius: 12, border: '1px solid rgba(59,130,246,0.3)',
      boxShadow: '0 0 24px rgba(59,130,246,0.07)',
      backdropFilter: 'blur(8px)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <IconBox icon={Activity} color="var(--blue)" colorRaw="rgba(59,130,246,0.6)" />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--blue)', letterSpacing: 0.5 }}>
              {ops.title || 'Ground Operations'}
            </div>
            {ops.subtitle && (
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{ops.subtitle}</div>
            )}
          </div>
        </div>
        {ops.lastUpdated && (
          <span style={{ fontSize: 9, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Updated {ops.lastUpdated}
          </span>
        )}
      </div>

      {/* Column headers */}
      <div style={{
        display: 'grid', gridTemplateColumns: '64px 1fr 54px 80px',
        gap: 8, paddingBottom: 7, marginBottom: 4,
        borderBottom: '1px solid var(--border)',
        fontSize: 9, fontWeight: 700, color: 'var(--text-muted)',
        textTransform: 'uppercase', letterSpacing: 0.8,
      }}>
        <span>Zone</span>
        <span>Contact Rate</span>
        <span style={{ textAlign: 'center' }}>Workers</span>
        <span style={{ textAlign: 'right' }}>Status</span>
      </div>

      {/* Zone rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
        {zones.map((z) => {
          const st = ZONE_STATUS_STYLE[z.status] || ZONE_STATUS_STYLE['on-track'];
          const pct = Math.min(100, z.contactRate || 0);
          const atTarget = pct >= (z.target || 75);
          const barColor = pct < 50
            ? 'linear-gradient(90deg, var(--red), rgba(239,68,68,0.5))'
            : atTarget
              ? 'linear-gradient(90deg, var(--green), rgba(16,185,129,0.5))'
              : 'linear-gradient(90deg, var(--yellow), rgba(245,158,11,0.5))';

          return (
            <div key={z.zone} style={{
              display: 'grid', gridTemplateColumns: '64px 1fr 54px 80px',
              gap: 8, alignItems: 'center',
            }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
                {z.zone}
              </span>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{
                    fontSize: 11, fontWeight: 800, fontFamily: 'var(--font-mono)',
                    color: atTarget ? 'var(--green)' : pct < 50 ? 'var(--red)' : 'var(--yellow)',
                  }}>
                    {pct}%
                  </span>
                  <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>tgt {z.target}%</span>
                </div>
                <div style={{ height: 4, borderRadius: 4, background: 'var(--bg-elevated)', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 4, width: `${pct}%`,
                    background: barColor, transition: 'width 0.5s ease',
                  }} />
                </div>
              </div>

              <div style={{ textAlign: 'center' }}>
                <span style={{
                  fontSize: 13, fontWeight: 800, fontFamily: 'var(--font-mono)',
                  color: 'var(--text-secondary)',
                }}>
                  {z.workers}
                </span>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{
                  fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                  color: st.color, background: `${st.color}1a`,
                  border: `1px solid ${st.color}35`,
                  textTransform: 'uppercase', letterSpacing: 0.3,
                  whiteSpace: 'nowrap',
                }}>
                  {st.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── BriefingPointsCard ───────────────────────────────────────────────────────
export function BriefingPointsCard({ briefing }) {
  const [collapsed, setCollapsed] = useState(false);
  if (!briefing) return null;
  const points = briefing.points || [];

  return (
    <div style={{
      padding: '16px 20px',
      background: 'linear-gradient(135deg, rgba(139,92,246,0.08) 0%, rgba(17,30,48,0.9) 100%)',
      borderRadius: 12, border: '1px solid rgba(139,92,246,0.25)',
      boxShadow: '0 0 20px rgba(139,92,246,0.06)',
      backdropFilter: 'blur(8px)',
    }}>
      {/* Collapsible header */}
      <div
        onClick={() => setCollapsed(v => !v)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          cursor: 'pointer', marginBottom: collapsed ? 0 : 16,
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <IconBox icon={Mic} color="var(--purple)" colorRaw="rgba(139,92,246,0.6)" />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--purple)', letterSpacing: 0.5 }}>
              {briefing.title || 'Talking Points'}
            </div>
            {briefing.subtitle && (
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{briefing.subtitle}</div>
            )}
          </div>
          <span style={{
            fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 20, marginLeft: 4,
            background: 'rgba(139,92,246,0.15)', color: 'var(--purple)',
            border: '1px solid rgba(139,92,246,0.3)',
          }}>
            {points.length} POINTS
          </span>
        </div>
        <div style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
          {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </div>
      </div>

      {!collapsed && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {points.map((pt, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: 12,
              padding: '11px 14px', borderRadius: 8,
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              borderLeft: '3px solid rgba(139,92,246,0.55)',
            }}>
              <span style={{
                fontSize: 10, fontWeight: 800, color: 'rgba(139,92,246,0.65)',
                fontFamily: 'var(--font-mono)', flexShrink: 0, paddingTop: 2, minWidth: 18,
              }}>
                {String(i + 1).padStart(2, '0')}
              </span>
              <span style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.65 }}>
                {safeText(pt)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── RecommendationCard ───────────────────────────────────────────────────────
export function RecommendationCard({ rec }) {
  if (!rec) return null;
  const actions = rec.actions || [];

  return (
    <div style={{
      padding: '16px 20px', height: '100%',
      background: 'linear-gradient(135deg, rgba(245,158,11,0.1) 0%, rgba(245,158,11,0.04) 100%)',
      borderRadius: 12, border: '1px solid rgba(245,158,11,0.35)',
      boxShadow: '0 0 24px rgba(245,158,11,0.07)',
      backdropFilter: 'blur(8px)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <IconBox icon={Brain} color="var(--yellow)" colorRaw="rgba(245,158,11,0.6)" />
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--yellow)', letterSpacing: 0.5 }}>
            {rec.title || 'Strategic Assessment'}
          </div>
          {rec.priority && (
            <div style={{ fontSize: 9, color: 'var(--yellow)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8 }}>
              PRIORITY: {rec.priority}
            </div>
          )}
        </div>
      </div>

      {/* Insight block */}
      {rec.insight && (
        <div style={{
          fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.75,
          marginBottom: 14, padding: '10px 12px', borderRadius: 8,
          background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.15)',
        }}>
          {rec.insight}
        </div>
      )}

      {/* Action list */}
      {actions.length > 0 && (
        <>
          <div style={{
            fontSize: 9, fontWeight: 700, color: 'var(--text-muted)',
            letterSpacing: 1.2, marginBottom: 8, textTransform: 'uppercase',
          }}>
            Recommended Actions
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {actions.map((a, i) => {
              const st = ACTION_URGENCY[a.urgency] || ACTION_URGENCY.medium;
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 8,
                  padding: '8px 10px', borderRadius: 7,
                  background: st.bg, border: `1px solid ${st.border}`,
                }}>
                  <span style={{
                    fontSize: 8, fontWeight: 800, padding: '2px 5px', borderRadius: 4, flexShrink: 0, marginTop: 1,
                    color: st.color, background: `${st.color}22`,
                    border: `1px solid ${st.border}`,
                    textTransform: 'uppercase', letterSpacing: 0.5,
                  }}>
                    {a.urgency || 'medium'}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {safeText(a.label)}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
