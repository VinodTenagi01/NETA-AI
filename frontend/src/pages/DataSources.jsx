import { useEffect, useState } from 'react';
import {
  Database, Activity, FileText, Eye, BarChart2,
  Clock, ChevronDown, ChevronUp, Zap, Globe,
  Shield, Newspaper, Radio, CheckCircle, RefreshCw, Plus, Trash2,
} from 'lucide-react';
import { getNewsSources, pollSource, deleteNewsSource } from '../api/sources';
import { getIngestionLogs } from '../api/ingestion';
import { useToast } from '../store/ToastContext';

const SOURCES = [
  {
    id: 'ec-portal',
    name: 'Election Commission Portal',
    system: 'EC-DATA',
    icon: Globe,
    color: '#f97316',
    type: 'Official Government',
    status: 'active',
    lastSync: '2 hours ago',
    syncInterval: 'Every 6 hours',
    records: '248,432 voters',
    tables: ['voter_rolls', 'booth_assignments', 'candidate_forms'],
    health: 98,
    description: 'Official voter rolls, booth allocations, and candidate affidavit data from the Election Commission of India portal.',
    dataPoints: ['Voter Roll (Form 6)', 'Booth Locations', 'Candidate Affidavits', 'EVM Serial Numbers'],
    ingestionLog: ['2026-05-12 08:00 — Sync OK (0 delta)', '2026-05-12 02:00 — Sync OK (+14 records)', '2026-05-11 20:00 — Sync OK (0 delta)'],
  },
  {
    id: 'vani',
    name: 'VANI News Intelligence',
    system: 'VANI',
    icon: Newspaper,
    color: '#3b82f6',
    type: 'Proprietary Feed',
    status: 'active',
    lastSync: '12 minutes ago',
    syncInterval: 'Every 15 minutes',
    records: '1,847 articles indexed',
    tables: ['news_articles', 'sentiment_scores', 'media_mentions'],
    health: 100,
    description: 'Automated news aggregation and sentiment analysis engine tracking coverage across 40+ regional and national outlets.',
    dataPoints: ['News Headlines', 'Sentiment Scores', 'Candidate Mentions', 'Issue Tracking'],
    ingestionLog: ['2026-05-12 09:48 — 3 new articles', '2026-05-12 09:33 — 7 new articles', '2026-05-12 09:18 — 2 new articles'],
  },
  {
    id: 'vayu',
    name: 'VAYU Field Intelligence',
    system: 'VAYU',
    icon: Activity,
    color: '#10b981',
    type: 'Internal System',
    status: 'active',
    lastSync: '4 minutes ago',
    syncInterval: 'Real-time (WebSocket)',
    records: '3,241 field reports',
    tables: ['field_reports', 'worker_checkins', 'zone_sentiment', 'canvassing_logs'],
    health: 95,
    description: 'Real-time field intelligence from 847 ground workers across all 312 booths. Mood reports, canvassing outcomes, and micro-issue tracking.',
    dataPoints: ['Mood Scores (Zone-level)', 'Worker Check-ins', 'Canvassing Coverage', 'Booth-level Issues'],
    ingestionLog: ['2026-05-12 09:56 — 6 new reports', '2026-05-12 09:52 — 2 new reports', '2026-05-12 09:48 — 11 new reports'],
  },
  {
    id: 'vivek',
    name: 'VIVEK Opposition Tracker',
    system: 'VIVEK',
    icon: Shield,
    color: '#ef4444',
    type: 'Proprietary Feed',
    status: 'active',
    lastSync: '31 minutes ago',
    syncInterval: 'Every 30 minutes',
    records: '892 intel entries',
    tables: ['opposition_intel', 'rally_schedules', 'candidate_movements', 'rumours'],
    health: 87,
    description: 'Opposition candidate movement tracking, rally announcements, rumour monitoring, and threat level assessment for Chandanagar.',
    dataPoints: ['Candidate Movements', 'Rally Schedules', 'Rumour Reports', 'Threat Assessments'],
    ingestionLog: ['2026-05-12 09:30 — 4 new entries', '2026-05-12 09:00 — 1 new entry', '2026-05-12 08:30 — 8 new entries'],
  },
  {
    id: 'vichar',
    name: 'VICHAR Sentiment Engine',
    system: 'VICHAR',
    icon: BarChart2,
    color: '#8b5cf6',
    type: 'Proprietary AI Model',
    status: 'active',
    lastSync: '1 hour ago',
    syncInterval: 'Every hour',
    records: '14-day trend data',
    tables: ['sentiment_daily', 'issue_scores', 'voter_intent_model'],
    health: 92,
    description: 'AI-powered sentiment engine aggregating signals from VANI, VAYU, and social media to produce constituency-level mood scores.',
    dataPoints: ['Daily Mood Index', 'Issue Salience Scores', 'Voter Intent Estimates', 'NLP Topic Clusters'],
    ingestionLog: ['2026-05-12 09:00 — Model run OK', '2026-05-12 08:00 — Model run OK', '2026-05-12 07:00 — Model run OK'],
  },
  {
    id: 'census',
    name: 'Census & Demographic Data',
    system: 'CENSUS',
    icon: Database,
    color: '#f59e0b',
    type: 'Public Dataset',
    status: 'static',
    lastSync: 'Census 2011 (baseline)',
    syncInterval: 'Manual update',
    records: '398,640 population records',
    tables: ['demographics', 'age_distribution', 'community_data', 'literacy_stats'],
    health: 100,
    description: 'Census 2011 baseline demographic data enriched with 2019/2024 voter roll cross-references for Chandanagar constituency.',
    dataPoints: ['Age Distribution', 'Community Composition', 'Literacy Rates', 'Occupation Profiles'],
    ingestionLog: ['2026-01-15 — Manual update applied', '2025-03-20 — Voter roll cross-reference run', '2024-11-02 — Initial import'],
  },
  {
    id: 'public-social',
    name: 'Public Social Signals',
    system: 'SOCIAL',
    icon: Radio,
    color: '#06b6d4',
    type: 'Public Scrape',
    status: 'degraded',
    lastSync: '3 hours ago',
    syncInterval: 'Every 2 hours',
    records: '428 signals (24h)',
    tables: ['social_mentions', 'hashtag_trends'],
    health: 61,
    description: 'Public social media signal monitoring for constituency-level hashtags and candidate mentions. Rate-limited by platform APIs.',
    dataPoints: ['Hashtag Volume', 'Candidate Mentions', 'Sentiment Polarity', 'Viral Content Flags'],
    ingestionLog: ['2026-05-12 07:00 — Rate limited (429)', '2026-05-12 05:00 — 43 signals', '2026-05-12 03:00 — 71 signals'],
  },
];

const PIPELINE_STAGES = [
  { label: 'Ingest', desc: '7 sources' },
  { label: 'Validate', desc: 'Schema check' },
  { label: 'Enrich', desc: 'NLP + GIS' },
  { label: 'Index', desc: 'Vector store' },
  { label: 'Serve', desc: 'API + UI' },
];

function StatusBadge({ status }) {
  const map = {
    active:   { label: 'Active',   color: 'var(--green)', bg: 'rgba(16,185,129,0.12)' },
    static:   { label: 'Static',   color: 'var(--amber)', bg: 'rgba(245,158,11,0.12)' },
    degraded: { label: 'Degraded', color: 'var(--red)',   bg: 'rgba(239,68,68,0.12)'  },
    error:    { label: 'Error',    color: 'var(--red)',   bg: 'rgba(239,68,68,0.12)'  },
  };
  const s = map[status] || map.static;
  return (
    <span style={{
      fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10,
      background: s.bg, color: s.color, textTransform: 'uppercase', letterSpacing: 0.5,
    }}>
      {s.label}
    </span>
  );
}

function HealthBar({ value }) {
  const color = value >= 90 ? 'var(--green)' : value >= 70 ? 'var(--amber)' : 'var(--red)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.4s' }} />
      </div>
      <span style={{ fontSize: 10, color, fontWeight: 700, fontFamily: 'var(--font-mono)', minWidth: 28 }}>{value}%</span>
    </div>
  );
}

function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = source.icon;

  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--border)',
      borderRadius: 12, overflow: 'hidden',
      borderLeft: `3px solid ${source.color}`,
    }}>
      <div
        onClick={() => setExpanded(v => !v)}
        style={{ padding: '14px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}
      >
        <div style={{
          width: 36, height: 36, borderRadius: 9, flexShrink: 0,
          background: `${source.color}18`, border: `1px solid ${source.color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={16} color={source.color} />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{source.name}</span>
            <StatusBadge status={source.status} />
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {source.type} · {source.records}
          </div>
        </div>

        <div style={{ textAlign: 'right', flexShrink: 0, marginRight: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end', marginBottom: 5 }}>
            <Clock size={9} color="var(--text-dim)" />
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{source.lastSync}</span>
          </div>
          <div style={{ width: 120 }}>
            <HealthBar value={source.health} />
          </div>
        </div>

        {expanded
          ? <ChevronUp size={14} color="var(--text-muted)" style={{ flexShrink: 0 }} />
          : <ChevronDown size={14} color="var(--text-muted)" style={{ flexShrink: 0 }} />
        }
      </div>

      {expanded && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid var(--border)' }}>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '12px 0 14px', lineHeight: 1.6 }}>
            {source.description}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>
                Data Points
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {source.dataPoints.map(dp => (
                  <div key={dp} style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 11, color: 'var(--text-secondary)' }}>
                    <div style={{ width: 4, height: 4, borderRadius: '50%', background: source.color, flexShrink: 0 }} />
                    {dp}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>
                Recent Ingestion Log
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {source.ingestionLog.map((entry, i) => (
                  <div key={i} style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {entry}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 14, display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: 9, color: 'var(--text-dim)', marginRight: 2 }}>Tables:</span>
            {source.tables.map(t => (
              <span key={t} style={{
                fontSize: 9, padding: '2px 7px', borderRadius: 4,
                background: 'var(--bg-base)', border: '1px solid var(--border)',
                color: 'var(--text-muted)', fontFamily: 'var(--font-mono)',
              }}>
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DataSources() {
  const { showToast } = useToast();
  const [rssSources, setRssSources] = useState([]);
  const [rssLoading, setRssLoading] = useState(true);
  const [recentLogs, setRecentLogs] = useState([]);
  const [pollingId, setPollingId] = useState(null);

  useEffect(() => {
    const load = async () => {
      setRssLoading(true);
      await Promise.allSettled([
        getNewsSources().then(d => {
          const items = Array.isArray(d) ? d : d.items || [];
          if (items.length > 0) setRssSources(items);
        }),
        getIngestionLogs({ page_size: 5 }).then(d => {
          if (d?.items?.length > 0) setRecentLogs(d.items);
        }),
      ]);
      setRssLoading(false);
    };
    load();
  }, []);

  const handlePollSource = async (id, name) => {
    setPollingId(id);
    try {
      await pollSource(id);
      showToast({ type: 'success', message: `Poll triggered: ${name}` });
    } catch (err) {
      showToast({ type: 'error', message: err.response?.data?.detail || 'Poll failed.' });
    } finally {
      setPollingId(null);
    }
  };

  const activeCount  = SOURCES.filter(s => s.status === 'active').length;
  const degradedCount = SOURCES.filter(s => s.status === 'degraded').length;
  const totalHealth  = Math.round(SOURCES.reduce((sum, s) => sum + s.health, 0) / SOURCES.length);

  return (
    <div style={{ padding: '28px 32px', maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <Database size={18} color="var(--saffron)" />
            <h1 style={{ fontSize: 22, fontWeight: 900, color: 'var(--text-primary)', margin: 0 }}>Data Sources</h1>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
            Live ingestion registry for NETA.AI — Chandanagar Assembly Constituency
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="live-dot" />
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Pipeline active</span>
        </div>
      </div>

      {/* Summary stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Total Sources', value: SOURCES.length,     color: 'var(--text-primary)' },
          { label: 'Active',        value: activeCount,         color: 'var(--green)' },
          { label: 'Degraded',      value: degradedCount,       color: 'var(--red)' },
          { label: 'Avg Health',    value: `${totalHealth}%`,   color: totalHealth >= 90 ? 'var(--green)' : 'var(--amber)' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
            borderRadius: 10, padding: '14px 16px',
          }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 4 }}>{label}</div>
            <div style={{ fontSize: 24, fontWeight: 900, color, fontFamily: 'var(--font-mono)' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Ingestion Pipeline */}
      <div style={{
        background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        borderRadius: 12, padding: '16px 20px', marginBottom: 24,
      }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 16 }}>
          Ingestion Pipeline
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {PIPELINE_STAGES.map((stage, i) => (
            <div key={stage.label} style={{ display: 'flex', alignItems: 'center', flex: i < PIPELINE_STAGES.length - 1 ? 1 : 0 }}>
              <div style={{ textAlign: 'center', minWidth: 80 }}>
                <div style={{
                  width: 38, height: 38, borderRadius: '50%', margin: '0 auto 6px',
                  background: 'rgba(249,115,22,0.1)', border: '2px solid var(--saffron)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Zap size={14} color="var(--saffron)" />
                </div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>{stage.label}</div>
                <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>{stage.desc}</div>
              </div>
              {i < PIPELINE_STAGES.length - 1 && (
                <div style={{
                  flex: 1, height: 2, marginBottom: 28, marginLeft: 4, marginRight: 4,
                  background: 'linear-gradient(90deg, var(--saffron), rgba(249,115,22,0.3))',
                  borderRadius: 2,
                }} />
              )}
            </div>
          ))}
        </div>

        <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle size={12} color="var(--green)" />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>All pipeline stages operational · Last full run 09:00 IST</span>
        </div>
      </div>

      {/* Source cards */}
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 12 }}>
          Source Registry — click any row to expand
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {SOURCES.map(source => <SourceCard key={source.id} source={source} />)}
        </div>
      </div>

      {/* Live RSS News Sources from backend */}
      {(rssSources.length > 0 || !rssLoading) && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
              RSS News Sources — Live from Backend
            </div>
            {rssLoading && <RefreshCw size={11} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />}
            {!rssLoading && rssSources.length === 0 && (
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>No sources configured (backend unavailable)</span>
            )}
          </div>
          {rssSources.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {rssSources.map(src => (
                <div key={src.id} style={{
                  display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                  background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)',
                  borderLeft: `3px solid ${src.is_active ? 'var(--blue)' : 'var(--border)'}`,
                }}>
                  <Globe size={13} color={src.is_active ? 'var(--blue)' : 'var(--text-muted)'} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{src.name}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {src.url}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>every {src.poll_interval_minutes}m</span>
                    <span style={{
                      fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 8,
                      background: src.is_active ? 'rgba(59,130,246,0.15)' : 'var(--bg-elevated)',
                      color: src.is_active ? 'var(--blue)' : 'var(--text-muted)',
                      border: `1px solid ${src.is_active ? 'rgba(59,130,246,0.3)' : 'var(--border)'}`,
                    }}>
                      {src.is_active ? 'ACTIVE' : 'PAUSED'}
                    </span>
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => handlePollSource(src.id, src.name)}
                      disabled={pollingId === src.id}
                      style={{ padding: '2px 8px', fontSize: 10, display: 'flex', alignItems: 'center', gap: 4 }}
                    >
                      <RefreshCw size={10} style={{ animation: pollingId === src.id ? 'spin 1s linear infinite' : 'none' }} />
                      Poll
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Recent ingestion logs */}
      {recentLogs.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 12 }}>
            Recent Ingestion Activity
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {recentLogs.map(log => (
              <div key={log.id} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px',
                background: 'var(--bg-elevated)', borderRadius: 6, border: '1px solid var(--border)',
                fontSize: 11,
              }}>
                <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 10, minWidth: 140 }}>
                  {new Date(log.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}
                </span>
                <span style={{ color: 'var(--text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {log.file_name || log.source_type}
                </span>
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 8,
                  color: log.status === 'completed' ? 'var(--green)' : log.status === 'failed' ? 'var(--red)' : 'var(--yellow)',
                  background: log.status === 'completed' ? 'rgba(16,185,129,0.15)' : log.status === 'failed' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                  textTransform: 'uppercase',
                }}>
                  {log.status}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--green)', minWidth: 60, textAlign: 'right' }}>
                  +{log.records_processed?.toLocaleString() || 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer note */}
      <div style={{
        marginTop: 24, padding: '10px 14px', borderRadius: 8,
        background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--text-secondary)' }}>Data governance:</strong> All ingested data is stored within the NETA.AI secure enclave. EC data is consumed read-only via official portal APIs. Field intelligence is end-to-end encrypted in transit. Access is scoped by user role.
      </div>
    </div>
  );
}
