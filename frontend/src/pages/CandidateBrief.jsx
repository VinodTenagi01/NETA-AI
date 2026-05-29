import { useState, useEffect, useCallback, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import {
  candidateBrief, winProbability, candidate,
  executiveDashboardWidgets,
  zoneSentiment, boothPerformance, operationalConcerns,
  keyMessageTranslations, enhancedPositives, campaignRecommendations,
  constituency, antiIncumbencySignals, boothAttentionList,
  workerEscalations, followUpRecommendations,
  changedSinceYesterday, issuePriorityRanking, visitRecommendations,
} from '../data/mockData';
import {
  CheckCircle, AlertTriangle, Calendar, MapPin, MessageSquare,
  RefreshCw, Cpu, AlertCircle, Sparkles, Printer, Copy, Activity,
} from 'lucide-react';
import { getCandidateBrief, generateBrief } from '../api/intelligence';
import { getSentimentSummary, getVayuAlerts } from '../api/vayu';
import { useToast } from '../store/ToastContext';
import { AlertCard, OperationsCard, BriefingPointsCard, RecommendationCard } from '../components/ExecutiveWidgets';
import {
  LiveStatusBar, ZoneSentimentPanel, BoothPerformancePanel,
  ActionableConcernCard, EnhancedPositivesList, SpeechLineCard,
  NextActionsPanel, CampaignTimeline, LiveNewsPanel,
  NextBestActionBanner, PriorityZonePanel, BoothAttentionList,
  WorkerEscalationPanel, RapidResponsePanel,
  WhatChangedPanel, IssuePriorityMatrix, VisitRecommendationPanel,
} from '../components/BriefWidgets';
import { getGlobalNextBestAction } from '../data/responseStrategies';
import ErrorBoundary from '../components/ErrorBoundary';
import { DataSourceStrip } from '../components/SourceBadge';
import { DATA_SOURCES } from '../utils/sourceLabels';

// Module loaded

// ── helpers ───────────────────────────────────────────────────────────────────

function mapApiZones(apiZones) {
  if (!Array.isArray(apiZones) || apiZones.length === 0) return null;
  const toScore  = mood => Math.max(0, Math.min(100, Math.round(((mood ?? 3) / 5) * 100)));
  const toStatus = score => score >= 70 ? 'strong' : score >= 60 ? 'good' : score >= 50 ? 'moderate' : score >= 40 ? 'weak' : 'critical';
  const toTrend  = () => 'flat';
  return apiZones.map(z => ({
    zone:   String(z.zone || 'Unknown'),
    score:  toScore(z.avg_mood),
    delta:  0,
    trend:  toTrend(),
    status: toStatus(toScore(z.avg_mood)),
    booths: z.report_count || 0,
  }));
}

function safeAlertToConcern(alert, index) {
  const meta = alert?.metadata_ || alert?.metadata || {};
  return {
    id:       `live-oc-${index}`,
    priority: alert.alert_type === 'critical' ? 'HIGH' : 'MEDIUM',
    title:    String(alert.title || alert.message || 'Field Alert').slice(0, 120),
    detail:   String(alert.message || ''),
    action:   'Assess situation and coordinate immediate war room response.',
    team:     'War Room',
    deadline: 'Immediate',
    zone:     String(meta.zone || 'All'),
    status:   'Active',
  };
}

const EVENT_TYPE_COLORS = {
  Community:    { color: 'var(--purple)', bg: 'var(--purple-dim)' },
  'Public Event': { color: 'var(--blue)',   bg: 'var(--blue-dim)'   },
  Rally:        { color: 'var(--saffron)', bg: 'var(--saffron-dim)' },
};

function formatTs(ts) {
  if (!ts) return null;
  try {
    return new Date(ts).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch { return null; }
}

function safeStr(v) {
  if (v == null) return '';
  if (typeof v === 'string') return v;
  if (typeof v === 'number') return String(v);
  return '';
}

const trendData = (() => {
  try {
    return winProbability.trendLabels.slice(-7).map((date, i) => ({
      date, prob: winProbability.trend.slice(-7)[i],
    }));
  } catch { return []; }
})();

function SectionDivider({ label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '4px 0 14px' }}>
      <div style={{ height: 1, flex: 1, background: 'linear-gradient(90deg, var(--border-bright), transparent)' }} />
      <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: 2, color: 'var(--text-muted)', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
        {label}
      </span>
      <div style={{ height: 1, flex: 1, background: 'linear-gradient(90deg, transparent, var(--border-bright))' }} />
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function CandidateBrief() {
  const [brief,        setBrief]        = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState(null);
  const [refreshing,   setRefreshing]   = useState(false);
  const [generating,   setGenerating]   = useState(false);
  const [generateMsg,  setGenerateMsg]  = useState(null);
  const [secondsAgo,   setSecondsAgo]   = useState(0);
  const [showNBA,      setShowNBA]      = useState(true);

  // Live backend intelligence
  const [liveZones,   setLiveZones]    = useState(null);
  const [liveBooths,  setLiveBooths]   = useState(null);
  const [liveAlerts,  setLiveAlerts]   = useState([]);
  const [isLive,      setIsLive]       = useState(false);

  const { addToast } = useToast();

  const loadBrief = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    const results = await Promise.allSettled([
      // Primary AI brief
      getCandidateBrief().then(data => {
        if (data && typeof data === 'object') {
          setBrief(data);
          setError(null);
        }
      }).catch(() => {
        setError('Could not load AI brief from server.');
      }),

      // Live zone sentiment
      getSentimentSummary().then(data => {
        if (!data) return;
        const zones = mapApiZones(data.zone_data);
        if (zones?.length) {
          setLiveZones(zones);
          setIsLive(true);
        }
        if (data.booths_covered != null) {
          setLiveBooths({
            ...boothPerformance,
            covered: data.booths_covered,
            lastUpdated: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }),
          });
        }
      }).catch(() => {}),

      // Live VAYU alerts → operational concerns
      getVayuAlerts(8).then(al => {
        const items = Array.isArray(al) ? al : (al?.items || []);
        const critWarning = items.filter(a => a?.alert_type === 'critical' || a?.alert_type === 'warning');
        if (critWarning.length) {
          setLiveAlerts(critWarning);
          setIsLive(true);
        }
      }).catch(() => {}),
    ]);

    setLoading(false);
    setRefreshing(false);
    setSecondsAgo(0);
  }, []);

  // Initial load
  useEffect(() => { loadBrief(); }, [loadBrief]);

  // Live countdown + auto-refresh every 60 s
  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsAgo(s => {
        const next = s + 1;
        if (next >= 60) { loadBrief(true); return 0; }
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [loadBrief]);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateMsg(null);
    try {
      await generateBrief();
      setGenerateMsg({ ok: true, text: 'Brief generation queued. Refresh in 30–60 seconds.' });
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setGenerateMsg({ ok: false, text: safeStr(detail) || 'Generation failed. Insufficient role or server error.' });
    } finally {
      setGenerating(false);
    }
  };

  // Derive displayed data — live API data first, mock fallback
  const displayZones  = liveZones  ?? zoneSentiment;
  const displayBooths = liveBooths ?? boothPerformance;

  // Merge live alerts into operational concerns (live concerns surface first, capped at 6 total)
  const allConcerns = useMemo(() => {
    const liveMapped = liveAlerts.slice(0, 3).map(safeAlertToConcern);
    if (liveMapped.length > 0) {
      return [...liveMapped, ...operationalConcerns].slice(0, 6);
    }
    return operationalConcerns;
  }, [liveAlerts]);

  const nba = useMemo(() => getGlobalNextBestAction(allConcerns), [allConcerns]);

  // Derive executive widgets — API fields first, demo data fallback
  const execAlerts   = brief?.priorityAlerts   ?? executiveDashboardWidgets.priorityAlerts;
  const execOps      = brief?.operations       ?? executiveDashboardWidgets.operations;
  const execBriefing = brief?.briefingPoints   ?? executiveDashboardWidgets.briefingPoints;
  const execRec      = brief?.recommendation   ?? executiveDashboardWidgets.recommendation;

  return (
    <div>
      {/* ── Page Header ─────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <div className="page-title">Candidate Brief</div>
          <div className="page-subtitle">
            {candidate?.name || 'Candidate'} · {constituency?.fullName || 'Serilingampally AC-52'} · NETA-CORE Confidential
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button className="btn btn-outline btn-sm" onClick={handleGenerate}
            disabled={generating || refreshing}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={12} style={{ animation: generating ? 'spin 1s linear infinite' : 'none' }} />
            {generating ? 'Generating…' : 'Generate Brief'}
          </button>
          <button className="btn btn-outline btn-sm" onClick={() => loadBrief(true)}
            disabled={refreshing || generating}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <RefreshCw size={12} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
          <button className="btn btn-outline btn-sm no-print"
            onClick={() => {
              const text = safeStr(brief?.content) || safeStr(candidateBrief?.keyMessage) || 'Brief unavailable';
              navigator.clipboard.writeText(text)
                .then(() => addToast('Brief copied.', 'success'))
                .catch(() => addToast('Clipboard denied.', 'error'));
            }}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Copy size={12} /> Copy
          </button>
          <button className="btn btn-outline btn-sm no-print"
            onClick={() => window.print()}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Printer size={12} /> Print
          </button>
        </div>
      </div>

      <div className="page-body">

        {/* ── Live Status Bar ──────────────────────────────────── */}
        <LiveStatusBar secondsAgo={secondsAgo} isRefreshing={refreshing} isLive={isLive} />
        <DataSourceStrip
          sources={[DATA_SOURCES.VISHLESHAN, DATA_SOURCES.VAYU, DATA_SOURCES.ECI, DATA_SOURCES.CENSUS_2011]}
          live={isLive}
          confidence={isLive ? 91 : 78}
        />

        {/* ── Next Best Action Banner ──────────────────────────── */}
        {showNBA && nba && (
          <ErrorBoundary compact label="Action banner unavailable">
            <NextBestActionBanner nba={nba} onDismiss={() => setShowNBA(false)} />
          </ErrorBoundary>
        )}

        {/* ── Rapid Response Panel ─────────────────────────────── */}
        <ErrorBoundary compact label="Rapid response unavailable">
          <RapidResponsePanel recommendations={followUpRecommendations} />
        </ErrorBoundary>
        {followUpRecommendations?.length > 0 && <div style={{ marginBottom: 14 }} />}

        {/* ── Status Banners ───────────────────────────────────── */}
        {error && (
          <div style={{
            padding: '10px 14px', marginBottom: 14, borderRadius: 8,
            background: 'rgba(217,119,6,0.1)', border: '1px solid rgba(217,119,6,0.3)',
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--yellow)',
          }}>
            <AlertCircle size={13} /> {error} Showing cached intelligence data.
          </div>
        )}
        {generateMsg && (
          <div style={{
            padding: '10px 14px', marginBottom: 14, borderRadius: 8,
            background: generateMsg.ok ? 'rgba(16,185,129,0.1)' : 'rgba(220,38,38,0.1)',
            border: `1px solid ${generateMsg.ok ? 'rgba(16,185,129,0.3)' : 'rgba(220,38,38,0.3)'}`,
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12,
            color: generateMsg.ok ? 'var(--green)' : 'var(--red)',
          }}>
            <Sparkles size={13} /> {generateMsg.text}
          </div>
        )}

        {/* ── AI Brief (API) ───────────────────────────────────── */}
        {brief && brief.content && (
          <div style={{
            padding: '18px 22px', marginBottom: 16,
            background: 'linear-gradient(135deg, #0c1a2e 0%, #101c30 100%)',
            borderRadius: 14, border: '1px solid rgba(99,102,241,0.3)',
            boxShadow: '0 0 32px rgba(99,102,241,0.07)',
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.4)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Cpu size={16} color="var(--purple)" />
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--purple)', letterSpacing: 1, textTransform: 'uppercase' }}>
                    NETA-CORE AI Brief
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                    {safeStr(brief.brief_type) || 'daily'} · {formatTs(brief.generated_at)}
                    {brief.model_used ? ` · ${safeStr(brief.model_used)}` : ''}
                  </div>
                </div>
              </div>
              {brief.is_stale && (
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 12,
                  background: 'rgba(217,119,6,0.15)', border: '1px solid rgba(217,119,6,0.3)',
                  color: 'var(--yellow)',
                }}>
                  STALE DATA
                </span>
              )}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
              {safeStr(brief.content)}
            </div>
          </div>
        )}
        {!loading && !brief && !error && (
          <div style={{
            padding: '16px 22px', marginBottom: 16, borderRadius: 12,
            border: '1px dashed var(--border)', textAlign: 'center', fontSize: 12,
            color: 'var(--text-muted)',
          }}>
            No AI brief for today. Generated nightly by NETA-CORE. Using intelligence briefing below.
          </div>
        )}

        {/* ── Loading skeleton ─────────────────────────────────── */}
        {loading && !brief && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
            {[80, 64, 48].map((h, i) => (
              <div key={i} className="skeleton" style={{ height: h, borderRadius: 10 }} />
            ))}
          </div>
        )}

        {/* ── Win Probability Banner ───────────────────────────── */}
        <div style={{
          padding: '20px 24px', marginBottom: 16,
          background: 'linear-gradient(135deg, #0f2238 0%, #0c1a2f 100%)',
          borderRadius: 14, border: '1px solid var(--border-bright)',
          boxShadow: '0 0 32px rgba(249,115,22,0.07)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>
                {safeStr(candidateBrief?.greeting) || 'Good morning.'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{safeStr(candidateBrief?.date)}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
                {constituency?.fullName} · Election in {constituency?.daysToElection} days
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>Win Probability</div>
              <div style={{ fontSize: 48, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--green)', lineHeight: 1 }}>
                {candidateBrief?.winProbability ?? '—'}%
              </div>
              <div style={{ fontSize: 11, color: 'var(--green)', marginTop: 3 }}>
                {safeStr(candidateBrief?.winTrend)}
              </div>
            </div>
          </div>
          {trendData.length > 0 && (
            <div style={{ marginTop: 14, height: 56 }}>
              <ErrorBoundary compact label="Trend chart unavailable">
                <ResponsiveContainer width="100%" height={56}>
                  <LineChart data={trendData}>
                    <Line type="monotone" dataKey="prob" stroke="var(--green)" strokeWidth={2}
                      dot={false} activeDot={{ r: 4, fill: 'var(--green)' }} />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={[55, 75]} hide />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
                      formatter={v => [`${v}%`, 'Win Prob.']}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ErrorBoundary>
            </div>
          )}
        </div>

        {/* ── What Changed Since Yesterday ─────────────────────── */}
        <ErrorBoundary compact label="Delta metrics unavailable">
          <WhatChangedPanel changes={changedSinceYesterday} />
        </ErrorBoundary>

        {/* ── Situational Awareness ────────────────────────────── */}
        <SectionDivider label="Situational Awareness" />
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 12, marginBottom: 14, alignItems: 'start' }}>
          <ErrorBoundary compact label="Zone sentiment panel unavailable">
            <ZoneSentimentPanel
              zones={displayZones}
              isLive={isLive && !!liveZones}
            />
          </ErrorBoundary>
          <ErrorBoundary compact label="Booth metrics unavailable">
            <BoothPerformancePanel metrics={displayBooths} />
          </ErrorBoundary>
        </div>

        {/* ── Priority Zone + Booth Attention ──────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16, alignItems: 'start' }}>
          <ErrorBoundary compact label="Priority zone unavailable">
            <PriorityZonePanel zones={displayZones} antiIncumbency={antiIncumbencySignals} />
          </ErrorBoundary>
          <ErrorBoundary compact label="Booth list unavailable">
            <BoothAttentionList booths={boothAttentionList} />
          </ErrorBoundary>
        </div>

        {/* ── Issue Intelligence ───────────────────────────────── */}
        <SectionDivider label="Issue Intelligence" />
        <ErrorBoundary compact label="Issue matrix unavailable">
          <IssuePriorityMatrix issues={issuePriorityRanking} />
        </ErrorBoundary>

        {/* ── Visit Recommendations ────────────────────────────── */}
        <ErrorBoundary compact label="Visit recommendations unavailable">
          <VisitRecommendationPanel visits={visitRecommendations} />
        </ErrorBoundary>

        {/* ── Executive Alerts ─────────────────────────────────── */}
        {Array.isArray(execAlerts) && execAlerts.length > 0 && (
          <>
            <SectionDivider label="Priority Alerts" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
              {execAlerts.map((a, i) => (
                <ErrorBoundary key={a?.id || i} compact label="Alert card unavailable">
                  <AlertCard alert={a} />
                </ErrorBoundary>
              ))}
            </div>
          </>
        )}

        {/* ── Operations + Recommendation ──────────────────────── */}
        {(execOps || execRec) && (
          <>
            <SectionDivider label="Operations" />
            <div style={{
              display: 'grid',
              gridTemplateColumns: execOps && execRec ? '3fr 2fr' : '1fr',
              gap: 12, marginBottom: 16, alignItems: 'start',
            }}>
              {execOps && (
                <ErrorBoundary compact label="Operations card unavailable">
                  <OperationsCard ops={execOps} />
                </ErrorBoundary>
              )}
              {execRec && (
                <ErrorBoundary compact label="Recommendation card unavailable">
                  <RecommendationCard rec={execRec} />
                </ErrorBoundary>
              )}
            </div>
          </>
        )}

        {/* ── Operational Concerns + Worker Escalations ─────────── */}
        <SectionDivider label="Operational Priorities" />
        {isLive && liveAlerts.length > 0 && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10,
            padding: '5px 10px', borderRadius: 6, width: 'fit-content',
            background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
          }}>
            <Activity size={10} color="var(--green)" />
            <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--green)', letterSpacing: 0.8 }}>
              {liveAlerts.length} LIVE ALERTS — surfaced from VAYU field intelligence
            </span>
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 12, marginBottom: 16, alignItems: 'start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {allConcerns.map((c, i) => (
              <ErrorBoundary key={c?.id || i} compact label="Concern card unavailable">
                <ActionableConcernCard concern={c} />
              </ErrorBoundary>
            ))}
          </div>
          <ErrorBoundary compact label="Escalations panel unavailable">
            <WorkerEscalationPanel escalations={workerEscalations} />
          </ErrorBoundary>
        </div>

        {/* ── Talking Points briefing ───────────────────────────── */}
        {execBriefing && (
          <>
            <SectionDivider label="Briefing" />
            <div style={{ marginBottom: 16 }}>
              <ErrorBoundary compact label="Briefing unavailable">
                <BriefingPointsCard briefing={execBriefing} />
              </ErrorBoundary>
            </div>
          </>
        )}

        {/* ── Positives + Next Actions ─────────────────────────── */}
        <SectionDivider label="Intelligence" />
        <div style={{ display: 'grid', gridTemplateColumns: '55fr 45fr', gap: 12, marginBottom: 16, alignItems: 'start' }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 10 }}>
              Top Positives
            </div>
            <ErrorBoundary compact label="Positives list unavailable">
              <EnhancedPositivesList positives={enhancedPositives} />
            </ErrorBoundary>
          </div>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 10 }}>
              Recommended Actions
            </div>
            <ErrorBoundary compact label="Actions panel unavailable">
              <NextActionsPanel recommendations={campaignRecommendations} />
            </ErrorBoundary>
          </div>
        </div>

        {/* ── Speech Line ──────────────────────────────────────── */}
        <SectionDivider label="Communications" />
        <div style={{ marginBottom: 16 }}>
          <ErrorBoundary compact label="Speech card unavailable">
            <SpeechLineCard translations={keyMessageTranslations} />
          </ErrorBoundary>
        </div>

        {/* ── Acknowledgements + Avoidances ────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div className="brief-section">
            <div className="brief-section-title" style={{ color: 'var(--green)' }}>
              <CheckCircle size={14} /> Who to Thank
            </div>
            {Array.isArray(candidateBrief?.whoToThank) && candidateBrief.whoToThank.map((item, i) => (
              <div key={i} style={{
                fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8,
                lineHeight: 1.5, paddingLeft: 8, borderLeft: '2px solid var(--green)',
              }}>
                {safeStr(item)}
              </div>
            ))}
          </div>
          <div className="brief-section" style={{ borderColor: 'rgba(239,68,68,0.2)' }}>
            <div className="brief-section-title" style={{ color: 'var(--red)' }}>
              <AlertTriangle size={14} /> Things to Avoid Today
            </div>
            {Array.isArray(candidateBrief?.thingsToAvoid) && candidateBrief.thingsToAvoid.map((item, i) => (
              <div key={i} style={{
                display: 'flex', gap: 6, marginBottom: 8,
                fontSize: 12, color: 'var(--text-secondary)', alignItems: 'flex-start',
              }}>
                <span style={{ color: 'var(--red)', flexShrink: 0, marginTop: 2 }}>✕</span>
                {safeStr(item)}
              </div>
            ))}
          </div>
        </div>

        {/* ── Live News ────────────────────────────────────────── */}
        <SectionDivider label="Constituency News" />
        <div style={{ marginBottom: 16 }}>
          <ErrorBoundary compact label="News feed unavailable">
            <LiveNewsPanel />
          </ErrorBoundary>
        </div>

        {/* ── Campaign Schedule ────────────────────────────────── */}
        <SectionDivider label="Campaign Schedule" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16, alignItems: 'start' }}>
          <ErrorBoundary compact label="Timeline unavailable">
            <CampaignTimeline agenda={candidateBrief?.agenda || []} />
          </ErrorBoundary>

          {/* Detailed agenda */}
          <div className="brief-section">
            <div className="brief-section-title">
              <Calendar size={14} /> Today's Agenda Detail
            </div>
            {Array.isArray(candidateBrief?.agenda) && candidateBrief.agenda.map((event, i) => {
              const typeStyle = EVENT_TYPE_COLORS[event?.type] || { color: 'var(--text-muted)', bg: 'var(--bg-elevated)' };
              return (
                <div key={i} style={{
                  paddingBottom: 14, marginBottom: 14,
                  borderBottom: i < candidateBrief.agenda.length - 1 ? '1px solid var(--border)' : 'none',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{
                      fontSize: 14, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--saffron)',
                    }}>
                      {safeStr(event?.time)}
                    </span>
                    <span style={{
                      fontSize: 9, fontWeight: 700, letterSpacing: 0.5, padding: '2px 7px', borderRadius: 20,
                      color: typeStyle.color, background: typeStyle.bg, border: `1px solid ${typeStyle.color}44`,
                    }}>
                      {safeStr(event?.type).toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>
                    {safeStr(event?.event)}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
                    <MapPin size={10} /> {safeStr(event?.location)}
                  </div>
                  {event?.prep && (
                    <div style={{
                      padding: '8px 12px', background: 'var(--bg-elevated)', borderRadius: 7,
                      border: '1px solid var(--border)', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6,
                    }}>
                      <span style={{ fontWeight: 700, color: 'var(--saffron)', marginRight: 5 }}>PREP:</span>
                      {safeStr(event.prep)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
