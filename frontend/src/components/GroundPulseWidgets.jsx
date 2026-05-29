import { useState } from 'react';
import {
  AlertTriangle, ArrowUpRight, ArrowDownRight, Minus,
  Activity, Zap, MapPin, Users, Radio, MessageCircle,
  Thermometer, ShieldAlert, UserCheck, Lightbulb, Clock,
  TrendingUp, TrendingDown, Target, CheckCircle,
} from 'lucide-react';
import { useToast } from '../store/ToastContext';
import { generateStrategy } from '../data/responseStrategies';

// ── Shared style maps ─────────────────────────────────────────────────────────
const RISK_STYLE = {
  critical: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.4)',  label: 'CRITICAL' },
  high:     { color: 'var(--red)',    bg: 'rgba(239,68,68,0.07)',  border: 'rgba(239,68,68,0.3)',  label: 'HIGH'     },
  medium:   { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.3)', label: 'MEDIUM'   },
  low:      { color: 'var(--green)',  bg: 'rgba(16,185,129,0.07)', border: 'rgba(16,185,129,0.25)',label: 'LOW'      },
};

const URGENCY_HEAT = {
  CRITICAL: { bg: 'linear-gradient(135deg,rgba(239,68,68,0.14),rgba(239,68,68,0.04))',  border: 'rgba(239,68,68,0.4)',  barColor: 'var(--red)',     labelColor: 'var(--red)'     },
  HIGH:     { bg: 'linear-gradient(135deg,rgba(249,115,22,0.12),rgba(249,115,22,0.03))',border: 'rgba(249,115,22,0.38)',barColor: 'var(--saffron)', labelColor: 'var(--saffron)' },
  MEDIUM:   { bg: 'linear-gradient(135deg,rgba(245,158,11,0.1),rgba(245,158,11,0.02))', border: 'rgba(245,158,11,0.35)',barColor: 'var(--yellow)',  labelColor: 'var(--yellow)'  },
  LOW:      { bg: 'linear-gradient(135deg,rgba(59,130,246,0.09),rgba(59,130,246,0.02))',border: 'rgba(59,130,246,0.3)', barColor: 'var(--blue)',    labelColor: 'var(--blue)'    },
};

const BOOTH_FLAG = {
  stronghold: { label: 'FORTRESS', color: 'var(--green)',  bg: 'rgba(16,185,129,0.09)', border: 'rgba(16,185,129,0.28)' },
  safe:       { label: 'SAFE',     color: 'var(--blue)',   bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.25)' },
  watch:      { label: 'WATCH',    color: 'var(--yellow)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.3)'  },
  danger:     { label: 'DANGER',   color: 'var(--red)',    bg: 'rgba(239,68,68,0.09)',  border: 'rgba(239,68,68,0.32)'  },
};

const MOOD_LABEL  = { 5: 'Excellent', 4: 'Positive', 3: 'Neutral', 2: 'Negative', 1: 'Hostile' };
const MOOD_COLOR  = { 5: 'var(--green)', 4: 'var(--green)', 3: 'var(--yellow)', 2: 'var(--red)', 1: 'var(--red)' };

// ── AlertBanners ─────────────────────────────────────────────────────────────
export function AlertBanners({ zones }) {
  const criticals = (zones || []).filter(z => z.risk === 'critical' || z.risk === 'high');
  if (!criticals.length) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginBottom: 14 }}>
      {criticals.map(z => {
        const isCrit = z.risk === 'critical';
        return (
          <div key={z.zone} style={{
            padding: '10px 16px', borderRadius: 9,
            background: isCrit
              ? 'linear-gradient(135deg,rgba(239,68,68,0.12),rgba(239,68,68,0.04))'
              : 'linear-gradient(135deg,rgba(245,158,11,0.11),rgba(245,158,11,0.03))',
            border: isCrit ? '1px solid rgba(239,68,68,0.45)' : '1px solid rgba(245,158,11,0.4)',
            boxShadow: isCrit ? '0 0 20px rgba(239,68,68,0.1)' : '0 0 16px rgba(245,158,11,0.07)',
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0, background: isCrit ? 'var(--red)' : 'var(--yellow)', animation: 'pulse-live 1.5s ease-in-out infinite' }} />
            <AlertTriangle size={13} color={isCrit ? 'var(--red)' : 'var(--yellow)'} />
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: 11, fontWeight: 800, color: isCrit ? 'var(--red)' : 'var(--yellow)', marginRight: 8 }}>
                {isCrit ? '⚠ CRITICAL ALERT' : '⚠ HIGH RISK'}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {z.zone} Zone — {z.positive}% positive, {z.negative}% negative, {z.swing}% swing voters. Trend: {z.trend}.
              </span>
            </div>
            <span style={{
              fontSize: 9, fontWeight: 800, padding: '2px 8px', borderRadius: 10, letterSpacing: 0.8,
              color: isCrit ? 'var(--red)' : 'var(--yellow)',
              background: isCrit ? 'rgba(239,68,68,0.12)' : 'rgba(245,158,11,0.12)',
              border: isCrit ? '1px solid rgba(239,68,68,0.3)' : '1px solid rgba(245,158,11,0.3)',
            }}>
              {z.risk.toUpperCase()}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ── FieldOpsMetricsBar ────────────────────────────────────────────────────────
export function FieldOpsMetricsBar({ metrics }) {
  const items = [
    { label: 'Ground Teams Active', value: `${metrics.teamsActive ?? 0}`, sub: `of ${metrics.teamsTotal ?? 0}`,  color: 'var(--green)',   pct: Math.round(((metrics.teamsActive ?? 0) / Math.max(metrics.teamsTotal ?? 0, 1)) * 100) },
    { label: 'Booths Covered',      value: `${metrics.boothsCovered ?? 0}`, sub: `of ${metrics.boothsTotal ?? 0}`, color: 'var(--blue)',    pct: Math.round(((metrics.boothsCovered ?? 0) / Math.max(metrics.boothsTotal ?? 0, 1)) * 100) },
    { label: 'Volunteer Check-ins', value: `${metrics.volunteerCheckIns ?? 0}`, sub: `of ${metrics.volunteerTotal ?? 0}`, color: 'var(--purple)',  pct: Math.round(((metrics.volunteerCheckIns ?? 0) / Math.max(metrics.volunteerTotal ?? 0, 1)) * 100) },
    { label: 'Door-to-Door',        value: (metrics.doorToDoorCompleted ?? 0).toLocaleString(), sub: `/ ${(metrics.doorToDoorTarget ?? 0).toLocaleString()} target`, color: 'var(--saffron)', pct: Math.round(((metrics.doorToDoorCompleted ?? 0) / Math.max(metrics.doorToDoorTarget ?? 0, 1)) * 100) },
    { label: 'Coverage Progress',   value: `${metrics.coveragePct}%`, sub: `Last: ${metrics.lastCheckIn}`, color: metrics.coveragePct >= 80 ? 'var(--green)' : 'var(--yellow)', pct: metrics.coveragePct },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 14 }}>
      {items.map(m => (
        <div key={m.label} style={{ padding: '10px 14px', borderRadius: 10, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 5 }}>{m.label}</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 5, marginBottom: 5 }}>
            <span style={{ fontSize: 22, fontWeight: 900, fontFamily: 'var(--font-mono)', color: m.color, lineHeight: 1 }}>{m.value}</span>
            <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>{m.sub}</span>
          </div>
          <div style={{ height: 3, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${m.pct}%`, background: m.color, borderRadius: 3, transition: 'width 0.8s ease' }} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── ZoneSentimentMonitor ──────────────────────────────────────────────────────
export function ZoneSentimentMonitor({ zones }) {
  const { addToast } = useToast();
  const safeZones = zones || [];
  if (!safeZones.length) return null;
  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)', marginBottom: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Activity size={12} color="var(--blue)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Zone Sentiment Monitor
        </span>
        <span style={{ fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 10, background: 'rgba(16,185,129,0.15)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)', letterSpacing: 0.8 }}>LIVE</span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          {[{ color: 'var(--green)', label: 'Positive' }, { color: 'rgba(100,116,139,0.8)', label: 'Neutral' }, { color: 'var(--red)', label: 'Negative' }, { color: 'var(--yellow)', label: 'Swing' }].map(({ color, label }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: color }} />
              <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {safeZones.map(zone => {
          const rst = RISK_STYLE[zone.risk] || RISK_STYLE.low;
          return (
            <div key={zone.zone} style={{ padding: '12px 14px', borderRadius: 10, background: `linear-gradient(135deg,${rst.bg},var(--bg-elevated))`, border: `1px solid ${rst.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <div style={{ width: 30, height: 30, borderRadius: 8, flexShrink: 0, background: `${rst.color}15`, border: `1px solid ${rst.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 900, color: rst.color, fontFamily: 'var(--font-mono)' }}>
                  {zone.zone[0]}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-primary)' }}>{zone.zone} Zone</span>
                    <span style={{ fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 4, color: rst.color, background: `${rst.color}15`, border: `1px solid ${rst.border}`, textTransform: 'uppercase', letterSpacing: 0.8 }}>{rst.label}</span>
                    {zone.trend === 'up'   && <ArrowUpRight   size={12} color="var(--green)" />}
                    {zone.trend === 'down' && <ArrowDownRight size={12} color="var(--red)"   />}
                    {zone.trend === 'flat' && <Minus          size={12} color="var(--text-muted)" />}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 1 }}>{zone.reports} reports · {zone.booths} booths · score {zone.score}/5</div>
                </div>
                <div style={{ textAlign: 'right', marginRight: 10 }}>
                  <div style={{ fontSize: 24, fontWeight: 900, fontFamily: 'var(--font-mono)', color: rst.color, lineHeight: 1 }}>{zone.positive}%</div>
                  <div style={{ fontSize: 8, color: 'var(--text-muted)' }}>positive</div>
                </div>
                {(zone.risk === 'critical' || zone.risk === 'high') && (
                  <button onClick={() => addToast(`${zone.zone} Zone escalated to war room.`, 'error')} style={{ padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 10, fontWeight: 700, background: `${rst.color}15`, border: `1px solid ${rst.border}`, color: rst.color, flexShrink: 0 }}>
                    Escalate
                  </button>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {[
                  { label: 'Positive', pct: zone.positive, color: 'var(--green)' },
                  { label: 'Neutral',  pct: zone.neutral,  color: 'rgba(100,116,139,0.8)' },
                  { label: 'Negative', pct: zone.negative, color: 'var(--red)' },
                  { label: 'Swing',    pct: zone.swing,    color: 'var(--yellow)' },
                ].map(({ label, pct, color }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 9, color: 'var(--text-muted)', width: 50, flexShrink: 0 }}>{label}</span>
                    <div style={{ flex: 1, height: 5, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.8s ease' }} />
                    </div>
                    <span style={{ fontSize: 9, fontWeight: 700, fontFamily: 'var(--font-mono)', color, width: 30, textAlign: 'right' }}>{pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── IssueHeatmapPanel ────────────────────────────────────────────────────────
export function IssueHeatmapPanel({ issues }) {
  const { addToast } = useToast();
  const [expanded, setExpanded] = useState(null);

  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Thermometer size={12} color="var(--saffron)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>Issue Heatmap</span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>
          {issues.reduce((s, i) => s + i.count, 0).toLocaleString()} total mentions · click to expand
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
        {issues.map((issue, idx) => {
          const heat  = URGENCY_HEAT[issue.urgency] || URGENCY_HEAT.LOW;
          const isOpen = expanded === idx;
          const strategy = isOpen ? generateStrategy({ title: issue.issue }) : null;

          return (
            <div key={idx}>
              <div onClick={() => setExpanded(isOpen ? null : idx)} style={{ padding: '9px 12px', borderRadius: 8, cursor: 'pointer', background: heat.bg, border: `1px solid ${heat.border}`, boxShadow: isOpen ? `0 0 14px rgba(0,0,0,0.08)` : 'none', transition: 'box-shadow 0.2s' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                  <span style={{ fontSize: 8, fontWeight: 900, padding: '2px 7px', borderRadius: 4, color: heat.labelColor, background: `${heat.labelColor}18`, border: `1px solid ${heat.border}`, textTransform: 'uppercase', letterSpacing: 0.8, flexShrink: 0 }}>{issue.urgency}</span>
                  <span style={{ flex: 1, fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{issue.issue}</span>
                  <span style={{ fontSize: 13, fontWeight: 900, fontFamily: 'var(--font-mono)', color: heat.labelColor }}>{issue.count.toLocaleString()}</span>
                  {issue.trend === 'up'   && <ArrowUpRight   size={11} color="var(--red)"   />}
                  {issue.trend === 'down' && <ArrowDownRight size={11} color="var(--green)" />}
                  {issue.trend === 'flat' && <Minus          size={11} color="var(--text-muted)" />}
                  <span style={{ fontSize: 10, fontWeight: 700, color: issue.trend === 'up' ? 'var(--red)' : issue.trend === 'down' ? 'var(--green)' : 'var(--text-muted)', fontFamily: 'var(--font-mono)', width: 36, textAlign: 'right' }}>
                    {issue.delta > 0 ? `+${issue.delta}` : issue.delta}%
                  </span>
                  <div style={{ width: 56, height: 5, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden', flexShrink: 0 }}>
                    <div style={{ height: '100%', width: `${issue.pct}%`, background: heat.barColor, borderRadius: 3 }} />
                  </div>
                </div>
                {issue.zones && (
                  <div style={{ display: 'flex', gap: 4, marginTop: 5, paddingLeft: 1 }}>
                    {issue.zones.map(z => (
                      <span key={z} style={{ fontSize: 8, padding: '1px 5px', borderRadius: 3, background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>{z}</span>
                    ))}
                  </div>
                )}
              </div>

              {isOpen && strategy && (
                <div style={{ marginTop: 3, padding: '10px 13px', borderRadius: '0 0 8px 8px', background: 'rgba(6,182,212,0.04)', border: `1px solid ${heat.border}`, borderTop: 'none' }}>
                  <div style={{ fontSize: 9, fontWeight: 800, color: 'rgba(6,182,212,0.85)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 7 }}>
                    ⚡ Recommended Response — {strategy.category}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 8 }}>
                    {strategy.actions.slice(0, 3).map((a, i) => (
                      <div key={i} style={{ fontSize: 11, color: 'var(--text-secondary)', paddingLeft: 10, borderLeft: '2px solid rgba(6,182,212,0.3)' }}>{a}</div>
                    ))}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 10, color: 'var(--green)', fontWeight: 600 }}>{strategy.impactDesc}</span>
                    <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>· {strategy.deadline}</span>
                    <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>· {strategy.handlers.slice(0,2).join(', ')}</span>
                    {['Assign Team', 'Escalate', 'Add to Brief'].map(label => (
                      <button key={label} onClick={e => { e.stopPropagation(); addToast(`${label}: ${issue.issue}`, 'success'); }} style={{ padding: '3px 9px', borderRadius: 5, cursor: 'pointer', fontSize: 9, fontWeight: 700, background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── TalkingTopicsPanel ────────────────────────────────────────────────────────
export function TalkingTopicsPanel({ topics }) {
  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <MessageCircle size={12} color="var(--purple)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>What People Are Talking About</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {topics.map((t, i) => {
          const sentColor = t.sentiment === 'positive' ? 'var(--green)' : t.sentiment === 'negative' ? 'var(--red)' : 'var(--yellow)';
          const growthBad = t.sentiment === 'negative' && t.growth.startsWith('+');
          return (
            <div key={i} style={{ padding: '9px 12px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderLeft: `3px solid ${sentColor}` }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                    {t.hot && <span style={{ fontSize: 7, fontWeight: 900, padding: '1px 5px', borderRadius: 3, background: 'rgba(239,68,68,0.15)', color: 'var(--red)', border: '1px solid rgba(239,68,68,0.3)', letterSpacing: 0.8 }}>HOT</span>}
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{t.topic}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, color: sentColor }}>{t.mentions.toLocaleString()} mentions</span>
                    <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>{t.zone}</span>
                  </div>
                </div>
                <span style={{ fontSize: 11, fontWeight: 800, color: growthBad ? 'var(--red)' : 'var(--green)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>{t.growth}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── BoothIntelligenceGrid ─────────────────────────────────────────────────────
export function BoothIntelligenceGrid({ booths }) {
  const { addToast } = useToast();
  if (!booths?.length) return null;
  const sorted = [...booths].sort((a, b) => {
    const R = { critical: 0, high: 1, medium: 2, low: 3 };
    return (R[a.risk] ?? 9) - (R[b.risk] ?? 9);
  });

  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <MapPin size={12} color="var(--saffron)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>Booth Intelligence</span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 4 }}>sorted by risk · {booths.length} booths</span>
        <div style={{ display: 'flex', gap: 5, marginLeft: 'auto' }}>
          {Object.values(BOOTH_FLAG).map(f => (
            <span key={f.label} style={{ fontSize: 8, padding: '1px 6px', borderRadius: 4, color: f.color, background: f.bg, border: `1px solid ${f.border}`, fontWeight: 800 }}>{f.label}</span>
          ))}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        {sorted.map(booth => {
          const flag = BOOTH_FLAG[booth.flag] || BOOTH_FLAG.watch;
          const dangerous = booth.risk === 'critical' || booth.risk === 'high';
          return (
            <div key={booth.id} style={{ padding: '11px 13px', borderRadius: 9, background: flag.bg, border: `1px solid ${flag.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 900, fontFamily: 'var(--font-mono)', color: flag.color }}>{booth.id}</span>
                <span style={{ fontSize: 7, fontWeight: 900, padding: '1px 5px', borderRadius: 3, color: flag.color, background: `${flag.color}15`, border: `1px solid ${flag.border}`, letterSpacing: 0.8 }}>{flag.label}</span>
                <span style={{ marginLeft: 'auto', fontSize: 8, color: 'var(--text-muted)', padding: '1px 5px', borderRadius: 3, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>{booth.zone}</span>
              </div>
              <div style={{ marginBottom: 7 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>Support</span>
                  <span style={{ fontSize: 10, fontWeight: 800, fontFamily: 'var(--font-mono)', color: flag.color }}>{booth.support}%</span>
                </div>
                <div style={{ height: 4, borderRadius: 2, background: 'var(--bg-base)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${booth.support}%`, background: flag.color, borderRadius: 2 }} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5, marginBottom: 7 }}>
                <div>
                  <div style={{ fontSize: 8, color: 'var(--text-dim)', marginBottom: 1 }}>Volunteers</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: booth.volunteers >= 4 ? 'var(--green)' : booth.volunteers >= 2 ? 'var(--yellow)' : 'var(--red)' }}>{booth.volunteers} active</div>
                </div>
                <div>
                  <div style={{ fontSize: 8, color: 'var(--text-dim)', marginBottom: 1 }}>Oppo Risk</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: booth.oppoRisk === 'High' ? 'var(--red)' : booth.oppoRisk === 'Medium' ? 'var(--yellow)' : 'var(--green)' }}>{booth.oppoRisk}</div>
                </div>
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.4, marginBottom: dangerous ? 7 : 0 }}>{booth.note}</div>
              {dangerous && (
                <button onClick={() => addToast(`${booth.id} escalated — field team alerted.`, 'error')} style={{ width: '100%', padding: '4px', borderRadius: 5, cursor: 'pointer', fontSize: 9, fontWeight: 700, border: `1px solid ${flag.border}`, background: `${flag.color}10`, color: flag.color }}>
                  Escalate Booth
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── LiveFieldFeed ────────────────────────────────────────────────────────────
export function LiveFieldFeed({ reports }) {
  const { addToast } = useToast();
  const safeReports = reports || [];
  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Radio size={12} color="var(--green)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>Live Field Reports</span>
        <span style={{ fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 10, background: 'rgba(16,185,129,0.15)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)', letterSpacing: 0.8 }}>LIVE</span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>Panna Pramukhsa · {safeReports.length} reports</span>
      </div>
      {!safeReports.length && <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-muted)', fontSize: 11 }}>No field reports yet</div>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
        {safeReports.map((r, i) => {
          const moodColor = MOOD_COLOR[r.mood] || 'var(--text-muted)';
          const hasOppo = r.oppoActivity && r.oppoActivity !== 'None';
          return (
            <div key={r.id || i} style={{ padding: '10px 13px', borderRadius: 9, background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderLeft: `3px solid ${moodColor}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                <span style={{ fontSize: 12, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--saffron)' }}>{r.booth}</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)' }}>{r.worker}</span>
                <span style={{ fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 4, color: moodColor, background: `${moodColor}18`, border: `1px solid ${moodColor}40`, textTransform: 'uppercase', letterSpacing: 0.6 }}>{MOOD_LABEL[r.mood]}</span>
                {hasOppo && <span style={{ fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 4, color: 'var(--red)', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', letterSpacing: 0.6 }}>OPPO ACTIVE</span>}
                <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{r.time}</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: hasOppo ? 6 : 0 }}>{r.note}</div>
              {hasOppo && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle size={9} color="var(--red)" />
                  <span style={{ fontSize: 10, color: 'var(--red)', fontWeight: 600, flex: 1 }}>{r.oppoActivity}</span>
                  <button onClick={() => addToast(`Opposition activity at ${r.booth} escalated to war room.`, 'error')} style={{ padding: '2px 8px', borderRadius: 4, cursor: 'pointer', fontSize: 9, fontWeight: 700, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: 'var(--red)' }}>
                    Escalate
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── AntiIncumbencyPanel ───────────────────────────────────────────────────────
// Shows where voters are most likely to vote against the incumbent.
// Based on aggregated field report sentiment and complaint density.
// Helps identify zones needing remediation before polling day.
export function AntiIncumbencyPanel({ data }) {
  if (!data) return null;
  const { byZone = [], primaryDrivers = [], overallScore, trend, source } = data;

  const scoreColor = overallScore >= 50 ? 'var(--red)' : overallScore >= 30 ? 'var(--yellow)' : 'var(--green)';
  const sortedZones = [...byZone].sort((a, b) => b.score - a.score);
  const maxScore = Math.max(...sortedZones.map(z => z.score), 1);

  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <ShieldAlert size={13} color="var(--red)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Anti-Incumbency Signals
        </span>
        {trend === 'rising' && (
          <span style={{
            fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 4,
            background: 'rgba(239,68,68,0.12)', color: 'var(--red)', border: '1px solid rgba(239,68,68,0.3)',
          }}>
            ↑ RISING
          </span>
        )}
        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{source}</div>
        </div>
      </div>

      {/* Overall score */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16, padding: '12px 14px',
        borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        marginBottom: 14,
      }}>
        <div style={{ textAlign: 'center', flexShrink: 0 }}>
          <div style={{ fontSize: 36, fontWeight: 900, fontFamily: 'var(--font-mono)', color: scoreColor, lineHeight: 1 }}>
            {overallScore}
          </div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>/ 100</div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Overall Anti-Incumbency</div>
          <div style={{ height: 6, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden', marginBottom: 4 }}>
            <div style={{ height: '100%', width: `${overallScore}%`, background: scoreColor, borderRadius: 3, transition: 'width 0.8s ease' }} />
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
            {overallScore >= 50 ? 'High risk — remediation needed immediately'
            : overallScore >= 30 ? 'Moderate — monitor and address key issues'
            : 'Within manageable range — maintain current momentum'}
          </div>
        </div>
      </div>

      {/* Zone breakdown */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
          By Zone
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {sortedZones.map(z => {
            const pct = Math.round((z.score / maxScore) * 100);
            const zColor = z.score >= 50 ? 'var(--red)' : z.score >= 30 ? 'var(--yellow)' : 'var(--green)';
            return (
              <div key={z.zone} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', width: 54, flexShrink: 0 }}>
                  {z.zone}
                </span>
                <div style={{ flex: 1, height: 6, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, background: zColor, borderRadius: 3 }} />
                </div>
                <span style={{ fontSize: 10, fontWeight: 800, fontFamily: 'var(--font-mono)', color: zColor, width: 28, textAlign: 'right' }}>
                  {z.score}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Primary drivers */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
          Primary Drivers
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {primaryDrivers.map((d, i) => {
            const dColor = d.severity === 'high' ? 'var(--red)' : d.severity === 'medium' ? 'var(--yellow)' : 'var(--green)';
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 20, height: 20, borderRadius: 4, flexShrink: 0,
                  background: `${dColor}15`, border: `1px solid ${dColor}35`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 8, fontWeight: 900, color: dColor, fontFamily: 'var(--font-mono)',
                }}>
                  {d.weight}
                </div>
                <span style={{ flex: 1, fontSize: 12, color: 'var(--text-secondary)' }}>{d.issue}</span>
                <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{d.zone}</span>
                <span style={{
                  fontSize: 7, fontWeight: 800, padding: '1px 5px', borderRadius: 3,
                  color: dColor, background: `${dColor}15`, border: `1px solid ${dColor}35`,
                  textTransform: 'uppercase', letterSpacing: 0.5,
                }}>
                  {d.severity}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── VolunteerAttendanceTracker ─────────────────────────────────────────────────
// Shows per-zone volunteer check-in rate vs. deployment target.
// Critical for identifying where field coverage is falling short.
export function VolunteerAttendanceTracker({ attendance }) {
  if (!attendance?.length) return null;

  const total = attendance.reduce((s, z) => s + z.assigned, 0);
  const checkedIn = attendance.reduce((s, z) => s + z.checkedIn, 0);
  const overallPct = Math.round((checkedIn / total) * 100);

  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <UserCheck size={13} color="var(--blue)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Volunteer Attendance
        </span>
        <span style={{
          fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700,
          color: overallPct >= 85 ? 'var(--green)' : overallPct >= 70 ? 'var(--yellow)' : 'var(--red)',
          marginLeft: 4,
        }}>
          {checkedIn}/{total} ({overallPct}%)
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>Source: VAYU check-ins</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {attendance.map(z => {
          const atTarget = z.pct >= 85;
          const low = z.pct < 70;
          const color = atTarget ? 'var(--green)' : low ? 'var(--red)' : 'var(--yellow)';
          const gap = z.target - z.checkedIn;

          return (
            <div key={z.zone} style={{
              padding: '10px 12px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              borderLeft: `3px solid ${color}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 12, fontWeight: 800, color: 'var(--text-primary)', width: 54, flexShrink: 0 }}>
                  {z.zone}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
                      {z.checkedIn}/{z.assigned}
                    </span>
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>tgt {z.target}</span>
                  </div>
                  <div style={{ height: 5, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', width: `${z.pct}%`, background: color,
                      borderRadius: 3, transition: 'width 0.8s ease',
                    }} />
                  </div>
                </div>
                <span style={{ fontSize: 11, fontWeight: 800, fontFamily: 'var(--font-mono)', color, minWidth: 34, textAlign: 'right' }}>
                  {z.pct}%
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 3, flexShrink: 0 }}>
                  {z.trend === 'up' && <ArrowUpRight size={10} color="var(--green)" />}
                  {z.trend === 'down' && <ArrowDownRight size={10} color="var(--red)" />}
                  {z.trend === 'stable' && <Minus size={10} color="var(--text-muted)" />}
                </div>
              </div>
              {gap > 0 && (
                <div style={{ fontSize: 9, color: 'var(--red)', fontWeight: 600 }}>
                  ⚠ {gap} workers below target — redeploy or call backup
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── FollowUpRecommendations ───────────────────────────────────────────────────
// Auto-generated follow-up action items from the VISHLESHAN issue-to-action
// engine. Ties together issue heatmap, zone data, and anti-incumbency signals.
export function FollowUpRecommendations({ recommendations }) {
  const { addToast } = useToast();
  const [resolved, setResolved] = useState({});
  const items = recommendations || [];
  if (!items.length) return null;

  const PRIORITY_COLOR = {
    CRITICAL: 'var(--red)',
    HIGH:     'var(--yellow)',
    MEDIUM:   'var(--blue)',
    LOW:      'var(--green)',
  };

  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Lightbulb size={13} color="var(--yellow)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Follow-Up Recommendations
        </span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 4 }}>
          {items.filter(i => !resolved[i.id]).length} pending
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>Source: VISHLESHAN engine</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
        {items.map(item => {
          const done = !!resolved[item.id];
          const color = PRIORITY_COLOR[item.priority] || 'var(--text-muted)';
          return (
            <div key={item.id} style={{
              padding: '11px 14px', borderRadius: 9,
              background: done ? 'var(--bg-elevated)' : 'var(--bg-elevated)',
              border: `1px solid ${done ? 'var(--border)' : color}33`,
              borderLeft: `3px solid ${done ? 'var(--green)' : color}`,
              opacity: done ? 0.55 : 1,
              transition: 'opacity 0.3s',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 4 }}>
                    <span style={{
                      fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                      color, background: `${color}18`, border: `1px solid ${color}40`,
                      textTransform: 'uppercase', letterSpacing: 0.5,
                    }}>
                      {done ? 'DONE' : item.priority}
                    </span>
                    <span style={{
                      fontSize: 9, padding: '1px 5px', borderRadius: 3,
                      background: 'var(--bg-base)', border: '1px solid var(--border)', color: 'var(--text-muted)',
                    }}>
                      {item.zone}
                    </span>
                    <Clock size={9} color="var(--text-muted)" style={{ marginLeft: 'auto' }} />
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{item.deadline}</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 3 }}>
                    {item.action}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 4 }}>
                    {item.detail}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>Team: {item.team}</span>
                    <span style={{ fontSize: 8, color: 'var(--text-dim)' }}>· {item.source}</span>
                  </div>
                </div>
              </div>
              {!done && (
                <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                  {['Assign', 'Done', 'Skip'].map(label => (
                    <button
                      key={label}
                      onClick={() => {
                        if (label === 'Done' || label === 'Skip') setResolved(r => ({ ...r, [item.id]: true }));
                        addToast(`${label}: ${item.action.slice(0, 35)}…`, label === 'Done' ? 'success' : 'info');
                      }}
                      style={{
                        padding: '4px 10px', borderRadius: 5, cursor: 'pointer',
                        fontSize: 9, fontWeight: 700, background: `${color}10`,
                        border: `1px solid ${color}40`, color,
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              )}
              {done && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 6 }}>
                  <CheckCircle size={10} color="var(--green)" />
                  <span style={{ fontSize: 9, color: 'var(--green)' }}>Completed</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── TrendComparisonPanel ──────────────────────────────────────────────────────
export function TrendComparisonPanel({ trends }) {
  if (!trends) return null;
  return (
    <div style={{ padding: '16px 18px', borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <TrendingUp size={12} color="var(--blue)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>Trend Comparison</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        {[
          { key: 'vs_yesterday', label: 'vs Yesterday' },
          { key: 'vs_last_week', label: 'vs Last Week' },
        ].map(({ key, label }) => (
          <div key={key}>
            <div style={{ fontSize: 9, fontWeight: 800, color: 'var(--text-muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8, paddingBottom: 5, borderBottom: '1px solid var(--border)' }}>{label}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(trends[key] || []).map((item, i) => {
                const color = item.isGood ? 'var(--green)' : 'var(--red)';
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ flex: 1, fontSize: 11, color: 'var(--text-secondary)' }}>{item.label}</span>
                    <span style={{ fontSize: 10, fontWeight: 800, color, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: 2 }}>
                      {item.direction === 'up' ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                      {item.delta > 0 ? `+${item.delta}` : item.delta}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── OperationalCommandStrip ───────────────────────────────────────────────────
// War-room top-of-page command view — shows the 3 most urgent actions the
// operations team must execute today, with owner, deadline, and confirm button.
const CMD_STYLE = {
  CRITICAL: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.4)',  label: 'CRITICAL' },
  HIGH:     { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.10)',  border: 'rgba(245,158,11,0.38)', label: 'HIGH'     },
  MEDIUM:   { color: 'var(--blue)',   bg: 'rgba(59,130,246,0.09)',  border: 'rgba(59,130,246,0.3)',  label: 'MEDIUM'   },
};

export function OperationalCommandStrip({ priorities }) {
  const { addToast } = useToast();
  const [confirmed, setConfirmed] = useState({});
  const items = (priorities || []).filter(p => !confirmed[p.id]).slice(0, 3);

  if (!items.length) return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '10px 16px', borderRadius: 10, marginBottom: 14,
      background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
    }}>
      <CheckCircle size={14} color="var(--green)" />
      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--green)' }}>All critical actions confirmed. Operations on track.</span>
    </div>
  );

  return (
    <div style={{
      padding: '14px 16px', borderRadius: 12, marginBottom: 14,
      background: 'linear-gradient(135deg, rgba(239,68,68,0.07) 0%, rgba(245,158,11,0.04) 100%)',
      border: '1px solid rgba(239,68,68,0.3)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%', background: 'var(--red)',
          animation: 'pulse-live-red 1.5s ease-in-out infinite', flexShrink: 0,
        }} />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--red)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Operational Command
        </span>
        <span style={{
          fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 4,
          background: 'rgba(239,68,68,0.12)', color: 'var(--red)', border: '1px solid rgba(239,68,68,0.3)',
        }}>
          {items.length} ACTIONS NOW
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 8, color: 'var(--text-dim)' }}>VISHLESHAN · {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {items.map((item, idx) => {
          const st = CMD_STYLE[item.priority] || CMD_STYLE.HIGH;
          return (
            <div key={item.id} style={{
              padding: '12px 14px', borderRadius: 10,
              background: st.bg, border: `1px solid ${st.border}`,
              borderTop: `2px solid ${st.color}`,
              display: 'flex', flexDirection: 'column', gap: 7,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  fontSize: 7, fontWeight: 900, padding: '2px 6px', borderRadius: 4,
                  color: st.color, background: `${st.color}22`, border: `1px solid ${st.border}`,
                  textTransform: 'uppercase', letterSpacing: 0.6,
                }}>
                  {st.label}
                </span>
                <span style={{
                  fontSize: 8, padding: '1px 5px', borderRadius: 3,
                  background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)',
                }}>
                  {item.zone}
                </span>
              </div>

              <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {item.action}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{item.detail}</div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 2 }}>
                <Clock size={9} color="var(--text-muted)" />
                <span style={{ fontSize: 9, color: st.color, fontWeight: 700 }}>{item.deadline}</span>
              </div>

              <div style={{ fontSize: 8, color: 'var(--text-dim)' }}>
                Team: {item.team} · {item.source}
              </div>

              <button
                onClick={() => {
                  setConfirmed(c => ({ ...c, [item.id]: true }));
                  addToast(`Confirmed: ${item.action.slice(0, 40)}…`, 'success');
                }}
                style={{
                  padding: '5px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 10, fontWeight: 700,
                  background: `${st.color}15`, border: `1px solid ${st.border}`, color: st.color, marginTop: 'auto',
                }}
              >
                Confirm Action
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
