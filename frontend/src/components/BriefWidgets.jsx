import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  TrendingUp, TrendingDown, Minus, MapPin, Target,
  Mic, Globe, Copy, ExternalLink, Clock, ChevronRight,
  Newspaper, AlertTriangle, CheckCircle, Zap, Users,
  ArrowUpRight, ArrowDownRight, RefreshCw, Crosshair,
  ShieldAlert, Radio, UserCheck, MessageSquare, Lightbulb,
} from 'lucide-react';
import { getLiveHeadlines } from '../api/news';
import { useToast } from '../store/ToastContext';
import { candidate } from '../data/mockData';
import { generateStrategy } from '../data/responseStrategies';
import { safeText } from '../utils/safeText';

// ── helpers ──────────────────────────────────────────────────────────────────

function SectionLabel({ children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
      <div style={{ height: 1, flex: 1, background: 'linear-gradient(90deg, var(--border-bright), transparent)' }} />
      <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: 2, color: 'var(--text-muted)', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
        {children}
      </span>
      <div style={{ height: 1, flex: 1, background: 'linear-gradient(90deg, transparent, var(--border-bright))' }} />
    </div>
  );
}

function MetricMini({ value, label, color, pct }) {
  return (
    <div style={{
      padding: '10px 12px', borderRadius: 8,
      background: 'var(--bg-elevated)', border: '1px solid var(--border)',
    }}>
      <div style={{ fontSize: 20, fontWeight: 900, fontFamily: 'var(--font-mono)', color, lineHeight: 1, marginBottom: 3 }}>
        {value}
      </div>
      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>{label}</div>
      <div style={{ height: 3, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.min(100, pct || 0)}%`, background: color, borderRadius: 3, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
}

// ── LiveStatusBar ────────────────────────────────────────────────────────────
export function LiveStatusBar({ secondsAgo, isRefreshing, isLive }) {
  const pct = Math.min(100, ((secondsAgo ?? 0) / 60) * 100);
  const barColor = pct > 80 ? 'var(--yellow)' : 'var(--green)';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
      padding: '7px 14px', borderRadius: 8,
      background: 'var(--bg-card)', border: '1px solid var(--border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
        <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--green)', animation: 'pulse-live 1.8s ease-in-out infinite' }} />
        <span style={{ fontSize: 10, fontWeight: 800, color: 'var(--green)', letterSpacing: 1 }}>LIVE</span>
      </div>
      <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
        {isRefreshing ? 'Refreshing…' : `Updated ${secondsAgo ?? 0}s ago`}
      </span>
      {isLive && (
        <span style={{
          fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 8, letterSpacing: 0.8,
          background: 'rgba(16,185,129,0.12)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)',
        }}>
          BACKEND CONNECTED
        </span>
      )}
      <div style={{ flex: 1, height: 2, borderRadius: 2, background: 'var(--bg-elevated)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 2, width: `${pct}%`,
          background: `linear-gradient(90deg, var(--green), ${barColor})`,
          transition: 'width 1s linear',
        }} />
      </div>
      <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', flexShrink: 0 }}>
        {60 - (secondsAgo ?? 0)}s
      </span>
    </div>
  );
}

// ── ZoneSentimentPanel ───────────────────────────────────────────────────────
const ZONE_ST = {
  strong:   { color: '#10b981' },
  good:     { color: '#3b82f6' },
  moderate: { color: '#f59e0b' },
  weak:     { color: '#f97316' },
  critical: { color: '#ef4444' },
};

export function ZoneSentimentPanel({ zones, isLive }) {
  if (!zones?.length) return null;
  const sorted = [...zones].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));

  return (
    <div style={{ padding: '16px 18px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 14 }}>
        <MapPin size={12} color="var(--blue)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Zone Sentiment
        </span>
        {isLive
          ? <span style={{ fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 8, background: 'rgba(16,185,129,0.12)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)', letterSpacing: 0.8, marginLeft: 4 }}>LIVE</span>
          : <span style={{ fontSize: 8, padding: '1px 5px', borderRadius: 6, background: 'var(--bg-elevated)', color: 'var(--text-dim)', border: '1px solid var(--border)', marginLeft: 4 }}>CACHED</span>
        }
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto', fontFamily: 'var(--font-mono)' }}>/100</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {sorted.map((z, i) => {
          const st = ZONE_ST[z.status] || ZONE_ST.moderate;
          const TrendIcon = z.trend === 'up' ? TrendingUp : z.trend === 'down' ? TrendingDown : Minus;
          const trendColor = z.trend === 'up' ? 'var(--green)' : z.trend === 'down' ? 'var(--red)' : 'var(--text-muted)';

          return (
            <div key={z.zone}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                <span style={{
                  fontSize: 9, fontWeight: 800, width: 16, color: 'var(--text-dim)',
                  fontFamily: 'var(--font-mono)', flexShrink: 0,
                }}>
                  {i + 1}
                </span>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', flex: 1 }}>
                  {z.zone}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <TrendIcon size={10} color={trendColor} />
                  {z.delta !== 0 && (
                    <span style={{ fontSize: 9, fontWeight: 700, color: trendColor, fontFamily: 'var(--font-mono)' }}>
                      {z.delta > 0 ? '+' : ''}{z.delta}
                    </span>
                  )}
                  <span style={{
                    fontSize: 12, fontWeight: 900, color: st.color,
                    fontFamily: 'var(--font-mono)', minWidth: 32, textAlign: 'right',
                  }}>
                    {z.score}%
                  </span>
                </div>
              </div>
              <div style={{ marginLeft: 16, height: 5, borderRadius: 5, background: 'var(--bg-elevated)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 5, width: `${z.score}%`,
                  background: `linear-gradient(90deg, ${st.color}, ${st.color}77)`,
                  transition: 'width 0.7s ease',
                }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── BoothPerformancePanel ────────────────────────────────────────────────────
export function BoothPerformancePanel({ metrics }) {
  if (!metrics) return null;
  const total      = Math.max(metrics.total || 1, 1);
  const coveredPct = Math.round(((metrics.covered || 0) / total) * 100);
  const weakPct    = Math.round(((metrics.weak    || 0) / total) * 100);

  return (
    <div style={{ padding: '16px 18px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 14 }}>
        <Target size={12} color="var(--saffron)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Booth Performance
        </span>
        {metrics.lastUpdated && (
          <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto' }}>{metrics.lastUpdated}</span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <MetricMini
          value={`${metrics.covered}/${metrics.total}`}
          label="Booths Covered"
          color="var(--green)"
          pct={coveredPct}
        />
        <MetricMini
          value={metrics.weak}
          label="Weak Booths"
          color="var(--red)"
          pct={weakPct}
        />
        <MetricMini
          value={`${metrics.volunteerAttendance}%`}
          label="Volunteer Attendance"
          color={metrics.volunteerAttendance >= 80 ? 'var(--green)' : 'var(--yellow)'}
          pct={metrics.volunteerAttendance}
        />
        <MetricMini
          value={`${metrics.outreachCompletion}%`}
          label="Outreach Complete"
          color={metrics.outreachCompletion >= 75 ? 'var(--green)' : metrics.outreachCompletion >= 50 ? 'var(--yellow)' : 'var(--red)'}
          pct={metrics.outreachCompletion}
        />
      </div>

      {metrics.voterContactToday != null && (
        <div style={{ marginTop: 10, padding: '8px 10px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Voter Contact Today</span>
            <span style={{ fontSize: 11, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--saffron)' }}>
              {(metrics.voterContactToday || 0).toLocaleString()} / {(metrics.voterContactTarget || 1).toLocaleString()}
            </span>
          </div>
          <div style={{ height: 4, borderRadius: 4, background: 'var(--bg-base)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 4,
              width: `${Math.min(100, Math.round(((metrics.voterContactToday || 0) / Math.max(metrics.voterContactTarget || 1, 1)) * 100))}%`,
              background: 'linear-gradient(90deg, var(--saffron), rgba(249,115,22,0.6))',
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      )}
    </div>
  );
}

// ── SmartResponseCard ────────────────────────────────────────────────────────
const QUICK_ACTIONS = [
  { label: 'Assign Team',          icon: Users,        toast: { type: 'success', message: 'Team assignment request sent to war room.' } },
  { label: 'Mark Urgent',          icon: ShieldAlert,  toast: { type: 'error',   message: 'Issue marked URGENT — war room notified.' } },
  { label: 'Add to Speech',        icon: Mic,          toast: { type: 'success', message: 'Added to speech preparation queue.' } },
  { label: 'Send to War Room',     icon: Radio,        toast: { type: 'success', message: 'Issue escalated to War Room.' } },
  { label: 'Notify Field Team',    icon: UserCheck,    toast: { type: 'success', message: 'Field team notification sent.' } },
  { label: 'Generate Talking Points', icon: Lightbulb, toast: { type: 'success', message: 'Talking points queued for VANI Cell.' } },
];

function SmartResponseCard({ concern, strategy }) {
  const { addToast } = useToast();
  if (!strategy) return null;

  const barColor = strategy.confidenceScore >= 85
    ? 'var(--green)'
    : strategy.confidenceScore >= 70
      ? 'var(--yellow)'
      : 'var(--red)';

  return (
    <div style={{
      marginTop: 12,
      borderRadius: 10,
      border: '1px solid rgba(6,182,212,0.35)',
      background: 'linear-gradient(135deg, rgba(6,182,212,0.06) 0%, rgba(7,13,28,0.97) 100%)',
      boxShadow: '0 0 24px rgba(6,182,212,0.07)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        background: 'linear-gradient(90deg, rgba(6,182,212,0.12), rgba(6,182,212,0.04))',
        borderBottom: '1px solid rgba(6,182,212,0.2)',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        <Zap size={11} color="var(--yellow)" />
        <span style={{ fontSize: 10, fontWeight: 900, color: 'var(--yellow)', letterSpacing: 1.2, textTransform: 'uppercase', flex: 1 }}>
          Instant Response Strategy
        </span>
        <span style={{ fontSize: 9, color: 'rgba(6,182,212,0.7)', fontFamily: 'var(--font-mono)' }}>
          {strategy.category}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginLeft: 8 }}>
          <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>Confidence</span>
          <div style={{ width: 42, height: 5, borderRadius: 3, background: 'var(--bg-base)', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${strategy.confidenceScore}%`, background: barColor, borderRadius: 3 }} />
          </div>
          <span style={{ fontSize: 10, fontWeight: 800, color: barColor, fontFamily: 'var(--font-mono)' }}>
            {strategy.confidenceScore}%
          </span>
        </div>
      </div>

      <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Recommended Actions */}
        <div>
          <div style={{ fontSize: 9, fontWeight: 800, color: 'rgba(6,182,212,0.8)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 }}>
            Recommended Actions
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {strategy.actions.map((action, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{
                  width: 16, height: 16, borderRadius: 4, flexShrink: 0, marginTop: 1,
                  background: 'rgba(6,182,212,0.12)', border: '1px solid rgba(6,182,212,0.25)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 8, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'rgba(6,182,212,0.8)',
                }}>
                  {i + 1}
                </div>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{safeText(action)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Field Response + Comms Strategy */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ padding: '9px 11px', borderRadius: 7, background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
            <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--green)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 5 }}>
              Field Response
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>{strategy.fieldResponse}</div>
          </div>
          <div style={{ padding: '9px 11px', borderRadius: 7, background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.2)' }}>
            <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--purple)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 5 }}>
              Communications
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>{strategy.commsStrategy}</div>
          </div>
        </div>

        {/* Metadata row: Handled By | Deadline | Political Impact */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 2fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--text-muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 5 }}>
              Handled By
            </div>
            {strategy.handlers.map((h, i) => (
              <div key={i} style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{h}</div>
            ))}
          </div>
          <div style={{ padding: '8px 10px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--text-muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 5 }}>
              Deadline
            </div>
            <div style={{ fontSize: 11, fontWeight: 800, color: 'var(--yellow)', lineHeight: 1.5 }}>{strategy.deadline}</div>
          </div>
          <div style={{ padding: '8px 10px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--text-muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 5 }}>
              Political Impact
            </div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--green)', lineHeight: 1.5, marginBottom: 3 }}>{strategy.impactDesc}</div>
            <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>{strategy.impactType}</div>
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div>
          <div style={{ fontSize: 9, fontWeight: 800, color: 'var(--text-muted)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 7 }}>
            Quick Actions
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {QUICK_ACTIONS.map(({ label, icon: Icon, toast: t }) => (
              <button
                key={label}
                onClick={e => { e.stopPropagation(); addToast(t.message, t.type); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 4,
                  padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 10, fontWeight: 700,
                  background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'rgba(6,182,212,0.4)';
                  e.currentTarget.style.color = 'rgba(6,182,212,0.9)';
                  e.currentTarget.style.background = 'rgba(6,182,212,0.07)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                  e.currentTarget.style.background = 'var(--bg-elevated)';
                }}
              >
                <Icon size={9} /> {label}
              </button>
            ))}
          </div>
        </div>

        {/* Next Best Action */}
        <div style={{
          padding: '10px 13px', borderRadius: 8,
          background: 'linear-gradient(135deg, rgba(245,158,11,0.1), rgba(249,115,22,0.06))',
          border: '1px solid rgba(245,158,11,0.4)',
          boxShadow: '0 0 14px rgba(245,158,11,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
            <Crosshair size={10} color="var(--yellow)" />
            <span style={{ fontSize: 9, fontWeight: 900, color: 'var(--yellow)', letterSpacing: 1, textTransform: 'uppercase' }}>
              Next Best Action
            </span>
          </div>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.6 }}>
            {strategy.nextBestAction}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── NextBestActionBanner ─────────────────────────────────────────────────────
const NBA_PRIORITY_STYLE = {
  CRITICAL: { color: 'var(--red)',    border: 'rgba(239,68,68,0.5)',    glow: 'rgba(239,68,68,0.12)',    bg: 'rgba(239,68,68,0.08)' },
  HIGH:     { color: 'var(--red)',    border: 'rgba(239,68,68,0.4)',    glow: 'rgba(239,68,68,0.1)',     bg: 'rgba(239,68,68,0.06)' },
  MEDIUM:   { color: 'var(--yellow)', border: 'rgba(245,158,11,0.45)',  glow: 'rgba(245,158,11,0.1)',   bg: 'rgba(245,158,11,0.07)' },
  LOW:      { color: 'var(--blue)',   border: 'rgba(59,130,246,0.4)',   glow: 'rgba(59,130,246,0.08)', bg: 'rgba(59,130,246,0.05)' },
};

export function NextBestActionBanner({ nba, onDismiss }) {
  const { addToast } = useToast();
  if (!nba) return null;
  const st = NBA_PRIORITY_STYLE[nba.priority] || NBA_PRIORITY_STYLE.MEDIUM;

  return (
    <div style={{
      padding: '14px 18px', marginBottom: 14, borderRadius: 12,
      background: `linear-gradient(135deg, ${st.bg}, rgba(7,13,28,0.97))`,
      border: `1px solid ${st.border}`,
      boxShadow: `0 0 32px ${st.glow}`,
      animation: 'exec-glow-breathe 3s ease-in-out infinite',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
        {/* Icon */}
        <div style={{
          width: 38, height: 38, borderRadius: 10, flexShrink: 0,
          background: `${st.color}18`, border: `1px solid ${st.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 0 12px ${st.glow}`,
        }}>
          <Crosshair size={18} color={st.color} />
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 9, fontWeight: 900, color: st.color, letterSpacing: 1.5, textTransform: 'uppercase' }}>
              Next Best Action
            </span>
            <span style={{
              fontSize: 8, fontWeight: 800, padding: '1px 7px', borderRadius: 10,
              color: st.color, background: `${st.color}18`, border: `1px solid ${st.border}`,
              textTransform: 'uppercase', letterSpacing: 0.8,
            }}>
              {nba.priority}
            </span>
            {nba.zone && nba.zone !== 'All' && (
              <span style={{
                fontSize: 8, padding: '1px 6px', borderRadius: 4,
                background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)',
              }}>
                {nba.zone} Zone
              </span>
            )}
            <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>{nba.issueTitle}</span>
          </div>

          <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: 7 }}>
            {nba.action}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>{nba.impactDesc}</span>
            <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
              Handled by: {nba.handlers?.slice(0, 2).join(', ')}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 32, height: 4, borderRadius: 2, background: 'var(--bg-base)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${nba.confidence}%`, background: 'var(--green)', borderRadius: 2 }} />
              </div>
              <span style={{ fontSize: 9, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{nba.confidence}% confidence</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, flexShrink: 0 }}>
          <button
            onClick={() => addToast('Action escalated to war room command.', 'success')}
            style={{
              padding: '5px 14px', borderRadius: 7, cursor: 'pointer', fontSize: 11, fontWeight: 800,
              background: st.color, border: 'none', color: '#fff',
            }}
          >
            Take Action
          </button>
          <button
            onClick={onDismiss}
            style={{
              padding: '4px 14px', borderRadius: 7, cursor: 'pointer', fontSize: 10, fontWeight: 600,
              background: 'transparent', border: `1px solid ${st.border}`, color: 'var(--text-muted)',
            }}
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

// ── ActionableConcernCard ────────────────────────────────────────────────────
const PRI_STYLE = {
  CRITICAL: { color: 'var(--red)',    bg: 'var(--red-dim)',    border: 'rgba(239,68,68,0.4)',  glow: 'rgba(239,68,68,0.1)' },
  HIGH:     { color: 'var(--red)',    bg: 'var(--red-dim)',    border: 'rgba(239,68,68,0.3)',  glow: 'rgba(239,68,68,0.07)' },
  MEDIUM:   { color: 'var(--yellow)', bg: 'var(--yellow-dim)', border: 'rgba(245,158,11,0.3)', glow: 'rgba(245,158,11,0.05)' },
  LOW:      { color: 'var(--blue)',   bg: 'var(--blue-dim)',   border: 'rgba(59,130,246,0.3)', glow: 'rgba(59,130,246,0.04)' },
};

export function ActionableConcernCard({ concern }) {
  const [open, setOpen] = useState(false);
  const strategy = useMemo(() => generateStrategy(concern), [concern]);
  if (!concern?.title) return null;
  const st = PRI_STYLE[concern.priority] || PRI_STYLE.MEDIUM;

  return (
    <div
      onClick={() => setOpen(v => !v)}
      style={{
        borderRadius: 10, border: `1px solid ${st.border}`,
        background: `linear-gradient(135deg, ${st.glow}, var(--bg-card))`,
        cursor: 'pointer', overflow: 'hidden',
        transition: 'box-shadow 0.2s ease',
        boxShadow: open ? `0 0 20px ${st.glow}` : 'none',
      }}
    >
      {/* Collapsed header */}
      <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          fontSize: 9, fontWeight: 800, padding: '2px 7px', borderRadius: 20, flexShrink: 0,
          color: st.color, background: st.bg, border: `1px solid ${st.border}`,
          textTransform: 'uppercase', letterSpacing: 0.8,
        }}>
          {concern.priority}
        </span>
        <span style={{ flex: 1, fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
          {concern.title}
        </span>
        {concern.zone && (
          <span style={{
            fontSize: 9, padding: '2px 7px', borderRadius: 4, flexShrink: 0,
            background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)',
          }}>
            {concern.zone} Zone
          </span>
        )}
        <div style={{
          color: 'var(--text-muted)', flexShrink: 0, transition: 'transform 0.2s ease',
          transform: open ? 'rotate(90deg)' : 'none',
        }}>
          <ChevronRight size={14} />
        </div>
      </div>

      {/* Expanded body */}
      {open && (
        <div style={{
          padding: '0 16px 14px', borderTop: `1px solid ${st.border}`, paddingTop: 12,
          animation: 'concern-expand 0.15s ease both',
        }}>
          {concern.detail && (
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 12 }}>
              {concern.detail}
            </p>
          )}
          <div style={{
            padding: '10px 12px', borderRadius: 8, marginBottom: 10,
            background: st.bg, border: `1px solid ${st.border}`,
          }}>
            <span style={{ fontSize: 9, fontWeight: 800, color: st.color, textTransform: 'uppercase', letterSpacing: 1 }}>
              ACTION →
            </span>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginTop: 4, lineHeight: 1.5 }}>
              {concern.action}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 7 }}>
            {[
              { label: 'Assigned To', value: concern.team },
              { label: 'Deadline', value: concern.deadline },
              { label: 'Status', value: concern.status },
            ].filter(r => r.value).map(({ label, value }) => (
              <div key={label} style={{ padding: '7px 9px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 8, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 3 }}>
                  {label}
                </div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', lineHeight: 1.3 }}>
                  {value}
                </div>
              </div>
            ))}
          </div>

          {/* Instant Response Strategy */}
          <SmartResponseCard concern={concern} strategy={strategy} />
        </div>
      )}
    </div>
  );
}

// ── EnhancedPositiveItem ─────────────────────────────────────────────────────
export function EnhancedPositivesList({ positives }) {
  if (!positives?.length) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {positives.map((item, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'flex-start', gap: 12,
          padding: '12px 14px', borderRadius: 9,
          background: 'var(--bg-card)', border: '1px solid rgba(16,185,129,0.15)',
          borderLeft: '3px solid var(--green)',
        }}>
          <div style={{
            width: 22, height: 22, borderRadius: 6, flexShrink: 0,
            background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--green)', fontWeight: 800, fontSize: 10,
          }}>
            {i + 1}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {item.text}
            </div>
            {item.growth && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 6 }}>
                <ArrowUpRight size={11} color="var(--green)" />
                <span style={{
                  fontSize: 11, fontWeight: 800, color: 'var(--green)',
                  fontFamily: 'var(--font-mono)',
                }}>
                  {item.growth}
                </span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{item.unit}</span>
                {item.zone && item.zone !== 'All' && (
                  <span style={{
                    fontSize: 9, padding: '1px 5px', borderRadius: 3, marginLeft: 4,
                    background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)',
                  }}>
                    {item.zone} Zone
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── SpeechLineCard ───────────────────────────────────────────────────────────
const LANG_META = {
  hi: { label: 'HI', name: 'Hindi',  fontNote: null },
  en: { label: 'EN', name: 'English', fontNote: null },
  te: { label: 'TE', name: 'Telugu', fontNote: 'font-family: system-ui' },
};

export function SpeechLineCard({ translations }) {
  const [lang, setLang]  = useState('hi');
  const { addToast } = useToast();
  if (!translations) return null;

  const text = translations[lang] || translations.en || '';

  const handleCopy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text).then(
      ()  => addToast('Speech line copied.', 'success'),
      ()  => addToast('Clipboard access denied.', 'error'),
    );
  };

  return (
    <div style={{
      padding: '18px 22px',
      background: 'linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(17,30,48,0.95) 100%)',
      borderRadius: 14, border: '1px solid rgba(139,92,246,0.3)',
      boxShadow: '0 0 28px rgba(139,92,246,0.08)',
      backdropFilter: 'blur(8px)',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Mic size={13} color="var(--purple)" />
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 800, color: 'var(--purple)', letterSpacing: 1, textTransform: 'uppercase' }}>
              Speech Line of the Day
            </div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>
              {LANG_META[lang]?.name} · {candidate?.name || 'Candidate'}
            </div>
          </div>
        </div>

        {/* Language toggle */}
        <div style={{ display: 'flex', gap: 4, marginLeft: 'auto' }}>
          {Object.entries(LANG_META).map(([k, m]) => (
            <button
              key={k}
              onClick={() => setLang(k)}
              style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 800,
                cursor: 'pointer', border: 'none', letterSpacing: 0.5,
                background: lang === k ? 'rgba(139,92,246,0.25)' : 'var(--bg-elevated)',
                color: lang === k ? 'var(--purple)' : 'var(--text-muted)',
                outline: lang === k ? '1px solid rgba(139,92,246,0.4)' : '1px solid var(--border)',
                transition: 'all 0.15s ease',
              }}
            >
              {m.label}
            </button>
          ))}
        </div>

        <button
          onClick={handleCopy}
          style={{
            display: 'flex', alignItems: 'center', gap: 5,
            padding: '4px 10px', borderRadius: 6, cursor: 'pointer',
            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
            color: 'var(--text-muted)', fontSize: 10, fontWeight: 700,
          }}
        >
          <Copy size={10} /> Copy
        </button>
      </div>

      {/* Quote */}
      <div style={{
        padding: '16px 20px', borderRadius: 10,
        background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.2)',
        position: 'relative',
      }}>
        <div style={{
          position: 'absolute', top: 10, left: 14,
          fontSize: 40, color: 'rgba(139,92,246,0.2)', lineHeight: 1,
          fontFamily: 'Georgia, serif', userSelect: 'none',
        }}>
          "
        </div>
        <div style={{
          fontSize: lang === 'te' ? 16 : 18, fontWeight: 700, lineHeight: 1.75,
          color: 'var(--text-primary)', paddingLeft: 24,
          fontStyle: 'italic',
          fontFamily: lang === 'te' ? "'Noto Sans Telugu', system-ui, sans-serif" : 'inherit',
        }}>
          {text}
        </div>
      </div>
    </div>
  );
}

// ── NextActionsPanel ─────────────────────────────────────────────────────────
const REC_STYLE = {
  critical: { color: 'var(--red)',    bg: 'var(--red-dim)',    border: 'rgba(239,68,68,0.3)' },
  high:     { color: 'var(--yellow)', bg: 'var(--yellow-dim)', border: 'rgba(245,158,11,0.3)' },
  medium:   { color: 'var(--blue)',   bg: 'var(--blue-dim)',   border: 'rgba(59,130,246,0.3)' },
};

export function NextActionsPanel({ recommendations }) {
  if (!recommendations?.length) return null;

  return (
    <div style={{
      padding: '16px 18px',
      background: 'linear-gradient(135deg, rgba(245,158,11,0.09) 0%, rgba(245,158,11,0.03) 100%)',
      borderRadius: 12, border: '1px solid rgba(245,158,11,0.3)',
      boxShadow: '0 0 20px rgba(245,158,11,0.06)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 14 }}>
        <Zap size={12} color="var(--yellow)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--yellow)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Recommended Next Moves
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {recommendations.map((r, i) => {
          const st = REC_STYLE[r.priority] || REC_STYLE.medium;
          return (
            <div key={i} style={{
              padding: '10px 12px', borderRadius: 8,
              background: st.bg, border: `1px solid ${st.border}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <span style={{
                  fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                  color: st.color, background: `${st.color}22`, border: `1px solid ${st.border}`,
                  textTransform: 'uppercase', letterSpacing: 0.5, flexShrink: 0, marginTop: 1,
                }}>
                  {r.priority}
                </span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 3 }}>
                    {r.action}
                  </div>
                  {r.detail && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>{r.detail}</div>
                  )}
                </div>
              </div>
              {r.eta && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 7 }}>
                  <Clock size={9} color="var(--text-muted)" />
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{r.eta}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── CampaignTimeline ─────────────────────────────────────────────────────────
function parseEventMinutes(timeStr) {
  const m = timeStr?.match(/(\d+):(\d+)\s*(AM|PM)/i);
  if (!m) return -1;
  let h = parseInt(m[1]), mins = parseInt(m[2]);
  const ap = m[3].toUpperCase();
  if (ap === 'PM' && h !== 12) h += 12;
  if (ap === 'AM' && h === 12) h = 0;
  return h * 60 + mins;
}

function getEventStatus(timeStr) {
  const now = new Date();
  const cur = now.getHours() * 60 + now.getMinutes();
  const ev  = parseEventMinutes(timeStr);
  if (ev < 0) return 'upcoming';
  if (cur > ev + 90) return 'done';
  if (cur >= ev - 30) return 'current';
  return 'upcoming';
}

const TYPE_ICON = { Community: '👥', 'Public Event': '📢', Rally: '🎤' };

export function CampaignTimeline({ agenda }) {
  if (!agenda?.length) return null;

  return (
    <div style={{ padding: '16px 18px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 16 }}>
        <Clock size={12} color="var(--saffron)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Campaign Schedule
        </span>
      </div>

      <div style={{ position: 'relative' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: 14, top: 20, bottom: 0,
          width: 1, background: 'var(--border)',
        }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {agenda.map((ev, i) => {
            const status = getEventStatus(ev.time);
            const isLast = i === agenda.length - 1;

            const dotClass =
              status === 'done'    ? 'brief-timeline-dot-done' :
              status === 'current' ? 'brief-timeline-dot-current' :
                                     'brief-timeline-dot-upcoming';

            return (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '30px 1fr',
                gap: 12, paddingBottom: isLast ? 0 : 18,
              }}>
                {/* Dot */}
                <div style={{ position: 'relative', zIndex: 1, paddingTop: 2 }}>
                  <div className={dotClass} style={{ width: 10, height: 10, borderRadius: '50%', margin: '0 auto' }} />
                </div>

                {/* Content */}
                <div style={{
                  padding: '8px 12px', borderRadius: 8,
                  background: status === 'current' ? 'rgba(249,115,22,0.07)' : 'var(--bg-elevated)',
                  border: status === 'current' ? '1px solid rgba(249,115,22,0.3)' : '1px solid var(--border)',
                  opacity: status === 'done' ? 0.55 : 1,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                    <span style={{
                      fontSize: 13, fontWeight: 900, fontFamily: 'var(--font-mono)',
                      color: status === 'current' ? 'var(--saffron)' : status === 'done' ? 'var(--text-muted)' : 'var(--text-primary)',
                    }}>
                      {ev.time}
                    </span>
                    {status === 'current' && (
                      <span style={{
                        fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 20,
                        background: 'rgba(249,115,22,0.2)', color: 'var(--saffron)',
                        border: '1px solid rgba(249,115,22,0.4)', letterSpacing: 0.8,
                      }}>
                        NOW
                      </span>
                    )}
                    {status === 'done' && <CheckCircle size={10} color="var(--green)" />}
                    <span style={{ fontSize: 10, marginLeft: 'auto' }}>
                      {TYPE_ICON[ev.type] || '📌'}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
                    {ev.event}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{ev.location}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── LiveNewsPanel ────────────────────────────────────────────────────────────
function timeAgo(isoStr) {
  if (!isoStr) return '';
  const diff = Math.floor((Date.now() - new Date(isoStr).getTime()) / 60000);
  if (diff < 1)  return 'just now';
  if (diff < 60) return `${diff}m ago`;
  const h = Math.floor(diff / 60);
  return `${h}h ago`;
}

const TIER_BADGE = {
  constituency_specific: { label: 'LOCAL',    color: 'var(--green)',  bg: 'var(--green-dim)',  border: 'rgba(16,185,129,0.3)' },
  regional:              { label: 'REGIONAL', color: 'var(--blue)',   bg: 'var(--blue-dim)',   border: 'rgba(59,130,246,0.3)' },
  state:                 { label: 'STATE',    color: 'var(--purple)', bg: 'var(--purple-dim)', border: 'rgba(139,92,246,0.3)' },
};

function cleanSource(name) {
  if (!name) return '';
  return name.replace(/[-￿]/g, '').replace(/\s+/g, ' ').replace(/^[\s–-]+|[\s–-]+$/g, '').trim();
}

function NewsItem({ item }) {
  const tier = TIER_BADGE[item.relevance_tier] || TIER_BADGE.regional;
  const headline = item.headline || item.title || '';
  const source   = cleanSource(item.source_name || item.source || '');
  return (
    <a
      href={item.url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: 'block', textDecoration: 'none',
        padding: '10px 12px', borderRadius: 8,
        background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        transition: 'border-color 0.15s ease, background 0.15s ease',
        cursor: 'pointer',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--border-bright)';
        e.currentTarget.style.background  = 'var(--bg-hover)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border)';
        e.currentTarget.style.background  = 'var(--bg-elevated)';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: 5 }}>
            {headline}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            {source && (
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{source}</span>
            )}
            {item.published_at && (
              <>
                <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>·</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {timeAgo(item.published_at)}
                </span>
              </>
            )}
            <span style={{
              fontSize: 8, fontWeight: 800, padding: '1px 5px', borderRadius: 4,
              color: tier.color, background: tier.bg, border: `1px solid ${tier.border}`,
              textTransform: 'uppercase', letterSpacing: 0.5,
            }}>
              {tier.label}
            </span>
          </div>
        </div>
        <ExternalLink size={10} color="var(--text-dim)" style={{ flexShrink: 0, marginTop: 2 }} />
      </div>
    </a>
  );
}

export function LiveNewsPanel() {
  const [articles, setArticles]     = useState([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [error, setError]           = useState(false);

  const fetchNews = useCallback((silent = false) => {
    if (!silent) setNewsLoading(true);
    setError(false);
    getLiveHeadlines(8)
      .then(data => {
        const items = Array.isArray(data) ? data : (data?.articles || data?.headlines || []);
        setArticles(items.slice(0, 7));
        setLastRefresh(new Date());
      })
      .catch(() => { setError(true); })
      .finally(() => setNewsLoading(false));
  }, []);

  useEffect(() => {
    fetchNews();
    const id = setInterval(() => fetchNews(true), 60_000);
    return () => clearInterval(id);
  }, [fetchNews]);

  return (
    <div style={{ padding: '16px 18px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 14 }}>
        <Newspaper size={12} color="var(--blue)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Live Constituency News
        </span>
        <span style={{
          fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 10,
          background: 'rgba(16,185,129,0.15)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)',
          letterSpacing: 0.8, marginLeft: 2,
        }}>
          LIVE
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto' }}>
          <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>Serilingampally AC-52 · GHMC</span>
          {lastRefresh && (
            <span style={{ fontSize: 9, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
              {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => fetchNews()}
            style={{
              background: 'none', border: '1px solid var(--border)', borderRadius: 4,
              padding: '2px 7px', cursor: 'pointer', color: 'var(--text-muted)', fontSize: 9,
              display: 'flex', alignItems: 'center', gap: 3,
            }}
          >
            <RefreshCw size={8} /> Refresh
          </button>
        </div>
      </div>

      {newsLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[1,2,3].map(k => (
            <div key={k} className="skeleton" style={{ height: 58, borderRadius: 8 }} />
          ))}
        </div>
      )}

      {!newsLoading && (error || articles.length === 0) && (
        <div className="empty-state" style={{ flexDirection: 'column', gap: 10 }}>
          <Newspaper size={20} color="var(--text-dim)" />
          <span>{error ? 'Could not reach news backend.' : 'No recent articles found.'}</span>
          <button
            onClick={() => fetchNews()}
            style={{
              background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.3)',
              borderRadius: 6, padding: '5px 14px', cursor: 'pointer',
              color: 'var(--blue)', fontSize: 11, fontWeight: 700,
            }}
          >
            Retry
          </button>
        </div>
      )}

      {!newsLoading && !error && articles.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {articles.map((a, i) => <NewsItem key={a.url || i} item={a} />)}
        </div>
      )}
    </div>
  );
}

// ── PriorityZonePanel ─────────────────────────────────────────────────────────
// Shows the single zone requiring the most urgent attention today with
// key risk metrics, top issue, and a clear recommended action.
const ZONE_RISK = {
  critical: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.4)' },
  high:     { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.09)', border: 'rgba(245,158,11,0.38)' },
  medium:   { color: 'var(--blue)',   bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.3)' },
  low:      { color: 'var(--green)',  bg: 'rgba(16,185,129,0.07)', border: 'rgba(16,185,129,0.25)' },
};

export function PriorityZonePanel({ zones, antiIncumbency }) {
  const sorted = [...(zones || [])].sort((a, b) => {
    const rank = { critical: 0, high: 1, medium: 2, weak: 2, moderate: 3, good: 4, strong: 5 };
    return (rank[a.status] ?? 9) - (rank[b.status] ?? 9);
  });
  const worst = sorted[0];
  if (!worst) return null;

  const risk = worst.status === 'critical' ? 'critical' : worst.status === 'weak' ? 'high' : 'medium';
  const st = ZONE_RISK[risk];
  const antiScore = antiIncumbency?.byZone?.find(z => z.zone === worst.zone)?.score;
  const { addToast } = useToast();

  return (
    <div style={{
      padding: '16px 20px',
      background: `linear-gradient(135deg, ${st.bg}, rgba(7,13,28,0.98))`,
      borderRadius: 12, border: `1px solid ${st.border}`,
      boxShadow: `0 0 24px ${st.color}18`,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Crosshair size={13} color={st.color} />
        <span style={{ fontSize: 11, fontWeight: 800, color: st.color, letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Priority Zone Today
        </span>
        <span style={{
          fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 4,
          color: st.color, background: `${st.color}18`, border: `1px solid ${st.border}`,
          textTransform: 'uppercase', letterSpacing: 0.8, marginLeft: 4,
        }}>
          {risk.toUpperCase()} RISK
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>
          Source: VAYU · VISHLESHAN
        </span>
      </div>

      {/* Zone Name + Score Row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
        <div style={{
          width: 52, height: 52, borderRadius: 12, flexShrink: 0,
          background: `${st.color}15`, border: `1px solid ${st.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, fontWeight: 900, fontFamily: 'var(--font-mono)', color: st.color,
        }}>
          {worst.zone[0]}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 2 }}>
            {worst.zone} Zone
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Sentiment: <span style={{ color: st.color, fontWeight: 700 }}>{worst.score ?? worst.delta}%</span>
            </span>
            {worst.booths != null && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {worst.booths} booths at risk
              </span>
            )}
            {worst.delta != null && worst.delta < 0 && (
              <span style={{ fontSize: 11, color: 'var(--red)', fontWeight: 700 }}>
                {worst.delta}pts this week
              </span>
            )}
          </div>
        </div>
        {antiScore != null && (
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 2 }}>Anti-Incumbency</div>
            <div style={{ fontSize: 22, fontWeight: 900, fontFamily: 'var(--font-mono)', color: antiScore >= 50 ? 'var(--red)' : antiScore >= 30 ? 'var(--yellow)' : 'var(--green)', lineHeight: 1 }}>
              {antiScore}
            </div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>/100</div>
          </div>
        )}
      </div>

      {/* Recommended Action */}
      <div style={{
        padding: '10px 14px', borderRadius: 8,
        background: `${st.color}0d`, border: `1px solid ${st.border}`,
        display: 'flex', alignItems: 'flex-start', gap: 8,
      }}>
        <Zap size={11} color={st.color} style={{ flexShrink: 0, marginTop: 2 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: st.color, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 4 }}>
            Recommended Action
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {worst.zone === 'North' && 'Candidate street corner meetings tonight at 3 locations. Counter BNP rally momentum before sentiment permanently declines.'}
            {worst.zone === 'East' && 'Emergency worker redeployment + power cut complaint escalation to TSECPDCL. Deploy ground team to sub-40% contact booths.'}
            {worst.zone === 'South' && 'HMWSSB water tanker emergency deployment. Candidate or team presence to show responsiveness to 11-day shortage.'}
            {!['North', 'East', 'South'].includes(worst.zone) && `Prioritise ${worst.zone} Zone for immediate candidate visit and worker redeployment.`}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 7, marginTop: 10 }}>
        {['Escalate to War Room', 'Schedule Visit', 'Assign Workers'].map(label => (
          <button
            key={label}
            onClick={() => addToast(`${label} — ${worst.zone} Zone`, 'warning')}
            style={{
              padding: '5px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 10, fontWeight: 700,
              background: `${st.color}10`, border: `1px solid ${st.border}`, color: st.color,
              transition: 'opacity 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.opacity = '0.75'; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── BoothAttentionList ────────────────────────────────────────────────────────
// Top 5 booths ranked by composite risk score. Pulls from VISHLESHAN risk
// algorithm combining contact rate, opposition activity, mood, volunteers.
const URGENCY_COLOR = {
  CRITICAL: 'var(--red)',
  HIGH:     'var(--yellow)',
  MEDIUM:   'var(--blue)',
  LOW:      'var(--green)',
};

export function BoothAttentionList({ booths }) {
  const { addToast } = useToast();
  if (!booths?.length) return null;

  return (
    <div style={{ padding: '16px 18px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 12 }}>
        <MapPin size={13} color="var(--saffron)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Booths Needing Attention
        </span>
        <span style={{
          fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
          background: 'rgba(249,115,22,0.12)', color: 'var(--saffron)',
          border: '1px solid rgba(249,115,22,0.3)',
        }}>
          {booths.filter(b => b.urgency === 'CRITICAL').length} CRITICAL
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>Source: VISHLESHAN Risk Score</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {booths.slice(0, 5).map((booth, i) => {
          const urgColor = URGENCY_COLOR[booth.urgency] || 'var(--text-muted)';
          return (
            <div key={booth.id} style={{
              padding: '9px 12px', borderRadius: 8,
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              borderLeft: `3px solid ${urgColor}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {/* Rank */}
                <span style={{
                  fontSize: 11, fontWeight: 900, fontFamily: 'var(--font-mono)',
                  color: i < 2 ? 'var(--red)' : i < 4 ? 'var(--yellow)' : 'var(--text-muted)',
                  minWidth: 18, flexShrink: 0,
                }}>
                  #{i + 1}
                </span>

                {/* Booth ID + Zone */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 13, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--saffron)' }}>
                      {booth.id}
                    </span>
                    <span style={{
                      fontSize: 9, padding: '1px 5px', borderRadius: 3,
                      background: 'var(--bg-base)', border: '1px solid var(--border)',
                      color: 'var(--text-muted)',
                    }}>
                      {booth.zone}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{booth.area}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    {booth.reason}
                  </div>
                </div>

                {/* Risk Score */}
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 18, fontWeight: 900, fontFamily: 'var(--font-mono)', color: urgColor, lineHeight: 1 }}>
                    {booth.riskScore}
                  </div>
                  <div style={{ fontSize: 8, color: 'var(--text-muted)' }}>risk</div>
                  <span style={{
                    fontSize: 7, fontWeight: 800, padding: '1px 5px', borderRadius: 3,
                    color: urgColor, background: `${urgColor}18`, border: `1px solid ${urgColor}44`,
                    textTransform: 'uppercase', letterSpacing: 0.5,
                  }}>
                    {booth.urgency}
                  </span>
                </div>
              </div>

              {/* Volunteer status + action button */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                <span style={{ fontSize: 9, color: booth.volunteers === 0 ? 'var(--red)' : booth.volunteers <= 1 ? 'var(--yellow)' : 'var(--text-muted)' }}>
                  {booth.volunteers === 0 ? '⚠ No volunteers' : `${booth.volunteers} volunteer${booth.volunteers !== 1 ? 's' : ''}`}
                </span>
                <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>·</span>
                <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{booth.voters?.toLocaleString()} voters</span>
                <button
                  onClick={() => addToast(`${booth.id} escalated — field team alerted.`, 'error')}
                  style={{
                    marginLeft: 'auto', padding: '3px 9px', borderRadius: 4, cursor: 'pointer',
                    fontSize: 9, fontWeight: 700, background: `${urgColor}10`,
                    border: `1px solid ${urgColor}44`, color: urgColor,
                  }}
                >
                  Escalate
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── WorkerEscalationPanel ─────────────────────────────────────────────────────
// Displays open worker escalations from the VAYU field pipeline.
// Shows severity, booth, issue description and current resolution status.
const ESCALATION_STYLE = {
  critical: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.4)' },
  high:     { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.35)' },
  medium:   { color: 'var(--blue)',   bg: 'rgba(59,130,246,0.07)', border: 'rgba(59,130,246,0.3)' },
};

const STATUS_STYLE = {
  Open:      { color: 'var(--red)',    label: 'OPEN' },
  Escalated: { color: 'var(--yellow)', label: 'ESCALATED' },
  Resolved:  { color: 'var(--green)',  label: 'RESOLVED' },
};

export function WorkerEscalationPanel({ escalations }) {
  const { addToast } = useToast();
  const items = escalations || [];
  const openCount = items.filter(e => e.status !== 'Resolved').length;

  return (
    <div style={{ padding: '16px 18px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 12 }}>
        <ShieldAlert size={13} color="var(--red)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Worker Escalations
        </span>
        {openCount > 0 && (
          <span style={{
            fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 10,
            background: 'rgba(239,68,68,0.15)', color: 'var(--red)',
            border: '1px solid rgba(239,68,68,0.35)',
          }}>
            {openCount} OPEN
          </span>
        )}
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>
          Source: VAYU pipeline
        </span>
      </div>

      {items.length === 0 ? (
        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
          No open escalations
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {items.map((esc) => {
            const st = ESCALATION_STYLE[esc.severity] || ESCALATION_STYLE.medium;
            const statusSt = STATUS_STYLE[esc.status] || STATUS_STYLE.Open;
            return (
              <div key={esc.id} style={{
                padding: '10px 12px', borderRadius: 8,
                background: esc.status === 'Resolved' ? 'var(--bg-elevated)' : st.bg,
                border: `1px solid ${esc.status === 'Resolved' ? 'var(--border)' : st.border}`,
                opacity: esc.status === 'Resolved' ? 0.6 : 1,
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 3 }}>
                      <span style={{ fontSize: 11, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--saffron)' }}>
                        {esc.booth}
                      </span>
                      <span style={{
                        fontSize: 9, padding: '1px 5px', borderRadius: 3,
                        background: 'var(--bg-base)', border: '1px solid var(--border)', color: 'var(--text-muted)',
                      }}>
                        {esc.zone}
                      </span>
                      <span style={{
                        fontSize: 7, fontWeight: 800, padding: '1px 5px', borderRadius: 3,
                        color: statusSt.color, background: `${statusSt.color}18`,
                        border: `1px solid ${statusSt.color}40`, textTransform: 'uppercase', letterSpacing: 0.5,
                      }}>
                        {statusSt.label}
                      </span>
                      <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {esc.time}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 3 }}>
                      {esc.issue}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      Reported by: {esc.worker}
                    </div>
                  </div>

                  {esc.status !== 'Resolved' && (
                    <button
                      onClick={() => addToast(`${esc.id} marked resolved.`, 'success')}
                      style={{
                        padding: '4px 10px', borderRadius: 5, cursor: 'pointer',
                        fontSize: 9, fontWeight: 700, background: `${st.color}10`,
                        border: `1px solid ${st.border}`, color: st.color, flexShrink: 0,
                      }}
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── RapidResponsePanel ────────────────────────────────────────────────────────
// Emergency decision-support panel. Shows today's top 3 actionable issues
// from the follow-up recommendation engine with one-tap escalation buttons.
export function RapidResponsePanel({ recommendations }) {
  const { addToast } = useToast();
  const items = (recommendations || []).filter(r => r.priority === 'CRITICAL' || r.priority === 'HIGH').slice(0, 4);
  if (!items.length) return null;

  const PRIORITY_ST = {
    CRITICAL: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.4)' },
    HIGH:     { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.35)' },
  };

  return (
    <div style={{
      padding: '16px 20px',
      background: 'linear-gradient(135deg, rgba(239,68,68,0.07) 0%, rgba(7,13,28,0.98) 100%)',
      borderRadius: 12, border: '1px solid rgba(239,68,68,0.3)',
      boxShadow: '0 0 20px rgba(239,68,68,0.07)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%', background: 'var(--red)',
          animation: 'pulse-live-red 1.5s ease-in-out infinite', flexShrink: 0,
        }} />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--red)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Rapid Response Required
        </span>
        <span style={{
          fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
          background: 'rgba(239,68,68,0.12)', color: 'var(--red)',
          border: '1px solid rgba(239,68,68,0.3)',
        }}>
          {items.length} ACTIONS TODAY
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>VISHLESHAN engine</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.map((item) => {
          const st = PRIORITY_ST[item.priority] || PRIORITY_ST.HIGH;
          return (
            <div key={item.id} style={{
              padding: '10px 14px', borderRadius: 9,
              background: st.bg, border: `1px solid ${st.border}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, flexWrap: 'wrap' }}>
                    <span style={{
                      fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                      color: st.color, background: `${st.color}22`, border: `1px solid ${st.border}`,
                      textTransform: 'uppercase', letterSpacing: 0.5,
                    }}>
                      {item.priority}
                    </span>
                    <span style={{
                      fontSize: 9, padding: '1px 5px', borderRadius: 3,
                      background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-muted)',
                    }}>
                      {item.zone} Zone
                    </span>
                    <Clock size={9} color="var(--text-muted)" style={{ marginLeft: 'auto' }} />
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{item.deadline}</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 3 }}>
                    {item.action}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 6 }}>
                    {item.detail}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>
                      Team: {item.team}
                    </span>
                    <span style={{ fontSize: 8, color: 'var(--text-dim)' }}>· {item.source}</span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                {['Assign Team', 'Mark Done', 'Escalate'].map(label => (
                  <button
                    key={label}
                    onClick={() => addToast(`${label}: ${item.action.slice(0, 30)}…`, label === 'Escalate' ? 'error' : 'success')}
                    style={{
                      padding: '4px 10px', borderRadius: 5, cursor: 'pointer',
                      fontSize: 9, fontWeight: 700, background: `${st.color}10`,
                      border: `1px solid ${st.border}`, color: st.color,
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── WhatChangedPanel ──────────────────────────────────────────────────────────
// Shows key metric deltas since yesterday — the first thing a war-room analyst
// scans each morning to understand if the campaign is moving forward or back.
export function WhatChangedPanel({ changes }) {
  if (!changes?.length) return null;

  return (
    <div style={{
      padding: '14px 18px', marginBottom: 16, borderRadius: 12,
      background: 'var(--bg-card)', border: '1px solid var(--border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <ArrowUpRight size={12} color="var(--saffron)" />
        <span style={{ fontSize: 10, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 1, textTransform: 'uppercase' }}>
          What Changed Since Yesterday
        </span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto' }}>VISHLESHAN · Daily delta</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        {changes.map((c) => {
          const isUp   = c.direction === 'up';
          const isDown = c.direction === 'down';
          const color  = isUp ? 'var(--green)' : isDown ? 'var(--red)' : 'var(--text-muted)';
          const Icon   = isUp ? ArrowUpRight : isDown ? ArrowDownRight : Minus;
          return (
            <div key={c.metric} style={{
              padding: '10px 12px', borderRadius: 9,
              background: `${color}08`, border: `1px solid ${color}2a`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 9, color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6 }}>
                  {c.metric}
                </span>
                <Icon size={10} color={color} />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 3 }}>
                <span style={{ fontSize: 17, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', lineHeight: 1 }}>
                  {c.current}
                </span>
                <span style={{ fontSize: 10, fontWeight: 800, color, fontFamily: 'var(--font-mono)' }}>
                  {c.delta}
                </span>
              </div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.4 }}>{c.context}</div>
              <div style={{ fontSize: 8, color: 'var(--text-dim)', marginTop: 3 }}>Source: {c.agent}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── IssuePriorityMatrix ───────────────────────────────────────────────────────
// Ranked table of constituency issues with source, severity, zone, impact,
// suggested action, and expected political effect — the core intelligence brief.
const ISSUE_SEV = {
  CRITICAL: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.4)',  icon: '🔴' },
  HIGH:     { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.09)', border: 'rgba(245,158,11,0.38)', icon: '🟡' },
  MEDIUM:   { color: 'var(--blue)',   bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.3)',  icon: '🔵' },
  LOW:      { color: 'var(--green)',  bg: 'rgba(16,185,129,0.07)', border: 'rgba(16,185,129,0.25)', icon: '🟢' },
};

export function IssuePriorityMatrix({ issues }) {
  const { addToast } = useToast();
  if (!issues?.length) return null;

  return (
    <div style={{
      padding: '16px 18px', marginBottom: 16,
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <Zap size={12} color="var(--red)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Issue Priority Matrix
        </span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 4 }}>
          {issues.filter(i => i.severity === 'CRITICAL').length} critical · {issues.filter(i => i.severity === 'HIGH').length} high
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 8, color: 'var(--text-dim)' }}>VISHLESHAN · Multi-signal synthesis</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {issues.map((iss) => {
          const sev = ISSUE_SEV[iss.severity] || ISSUE_SEV.MEDIUM;
          const trendColor = iss.trend === 'worsening' ? 'var(--red)' : iss.trend === 'improving' ? 'var(--green)' : 'var(--text-muted)';
          const TrendIc = iss.trend === 'worsening' ? TrendingDown : iss.trend === 'improving' ? TrendingUp : Minus;
          return (
            <div key={iss.rank} style={{
              padding: '12px 14px', borderRadius: 10,
              background: sev.bg, border: `1px solid ${sev.border}`,
              borderLeft: `3px solid ${sev.color}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                {/* Rank */}
                <div style={{
                  width: 22, height: 22, borderRadius: 6, flexShrink: 0, marginTop: 1,
                  background: `${sev.color}20`, border: `1px solid ${sev.border}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 10, fontWeight: 900, color: sev.color, fontFamily: 'var(--font-mono)',
                }}>
                  {iss.rank}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Header row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 5 }}>
                    <span style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.3, flex: 1 }}>
                      {iss.issue}
                    </span>
                    <span style={{
                      fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 4, flexShrink: 0,
                      color: sev.color, background: `${sev.color}18`, border: `1px solid ${sev.border}`,
                      textTransform: 'uppercase', letterSpacing: 0.5,
                    }}>
                      {iss.severity}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
                      <TrendIc size={10} color={trendColor} />
                      <span style={{ fontSize: 9, color: trendColor, fontWeight: 700, textTransform: 'capitalize' }}>
                        {iss.trend}
                      </span>
                    </div>
                  </div>

                  {/* Meta tags */}
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 8 }}>
                    <span style={{ fontSize: 8, padding: '1px 6px', borderRadius: 4, background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                      <MapPin size={8} style={{ display: 'inline', marginRight: 3 }} />{iss.zone}
                    </span>
                    <span style={{ fontSize: 8, padding: '1px 6px', borderRadius: 4, background: 'var(--bg-elevated)', color: 'var(--text-dim)', border: '1px solid var(--border)' }}>
                      {iss.source}
                    </span>
                  </div>

                  {/* 3-column detail */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                    <div>
                      <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--text-dim)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 3 }}>Impact</div>
                      <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{iss.impact}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--yellow)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 3 }}>
                        <Lightbulb size={8} style={{ display: 'inline', marginRight: 3 }} />Action
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{iss.suggestedAction}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 8, fontWeight: 800, color: 'var(--green)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 3 }}>Expected Effect</div>
                      <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{iss.politicalEffect}</div>
                    </div>
                  </div>

                  {/* Action row */}
                  <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                    {['Brief Team', 'Add to War Room', 'Generate Talking Points'].map(lbl => (
                      <button
                        key={lbl}
                        onClick={() => addToast(`${lbl}: ${iss.issue.slice(0, 25)}… queued`, lbl === 'Add to War Room' ? 'warning' : 'success')}
                        style={{
                          padding: '3px 9px', borderRadius: 5, cursor: 'pointer', fontSize: 9, fontWeight: 700,
                          background: `${sev.color}10`, border: `1px solid ${sev.border}`, color: sev.color,
                        }}
                      >
                        {lbl}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── VisitRecommendationPanel ──────────────────────────────────────────────────
// Derived from VISHLESHAN strategic analysis — shows exactly where the
// candidate should physically visit and when, with impact estimates.
const VISIT_PRIO = {
  CRITICAL: { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.4)'  },
  HIGH:     { color: 'var(--yellow)', bg: 'rgba(245,158,11,0.09)', border: 'rgba(245,158,11,0.38)' },
  MEDIUM:   { color: 'var(--blue)',   bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.3)'  },
};

export function VisitRecommendationPanel({ visits }) {
  const { addToast } = useToast();
  if (!visits?.length) return null;

  return (
    <div style={{
      padding: '16px 18px', marginBottom: 16,
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <MapPin size={12} color="var(--saffron)" />
        <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: 0.8, textTransform: 'uppercase' }}>
          Recommended Candidate Visits
        </span>
        <span style={{
          fontSize: 8, fontWeight: 800, padding: '1px 6px', borderRadius: 6, marginLeft: 4,
          background: 'rgba(249,115,22,0.12)', color: 'var(--saffron)', border: '1px solid rgba(249,115,22,0.3)',
        }}>
          {visits.filter(v => v.priority === 'CRITICAL').length} CRITICAL TODAY
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 8, color: 'var(--text-dim)' }}>VISHLESHAN strategic analysis</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {visits.map((v) => {
          const st = VISIT_PRIO[v.priority] || VISIT_PRIO.MEDIUM;
          return (
            <div key={v.zone} style={{
              padding: '12px 14px', borderRadius: 10,
              background: st.bg, border: `1px solid ${st.border}`,
              display: 'flex', flexDirection: 'column', gap: 8,
            }}>
              {/* Zone + Priority */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{
                  fontSize: 14, fontWeight: 900, color: st.color,
                  fontFamily: 'var(--font-mono)', letterSpacing: 0.5,
                }}>
                  {v.zone}
                </span>
                <span style={{
                  fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                  color: st.color, background: `${st.color}22`, border: `1px solid ${st.border}`,
                  textTransform: 'uppercase', letterSpacing: 0.5,
                }}>
                  {v.priority}
                </span>
              </div>

              {/* Location */}
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {v.location}
              </div>

              {/* Rationale */}
              <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {v.rationale}
              </div>

              {/* Meta */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <Clock size={9} color="var(--text-muted)" />
                  <span style={{ fontSize: 9, color: 'var(--saffron)', fontWeight: 700 }}>{v.recommendedTime}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <Users size={9} color="var(--text-muted)" />
                  <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{v.voters?.toLocaleString()} voters · {v.boothRange}</span>
                </div>
                <div style={{ fontSize: 9, color: 'var(--green)', fontWeight: 600, marginTop: 2 }}>
                  ↑ {v.expectedImpact}
                </div>
              </div>

              <button
                onClick={() => addToast(`Visit to ${v.zone} Zone added to campaign schedule`, 'success')}
                style={{
                  padding: '5px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 10, fontWeight: 700,
                  background: `${st.color}15`, border: `1px solid ${st.border}`, color: st.color,
                  marginTop: 2,
                }}
              >
                Confirm Visit
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
