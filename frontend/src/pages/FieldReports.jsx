import { useState, useEffect, useCallback } from 'react';
import { Search, X, AlertTriangle, ChevronLeft, ChevronRight, RefreshCw, AlertCircle, FileText, Plus, CheckCircle, Clock, Shield } from 'lucide-react';
import { getReports, getSentimentSummary, submitReport, getIssueCategories, getAlerts, updateAlertStatus } from '../api/vayu';
import { getBoothHeatmap } from '../api/intelligence';

const CID = '11111111-0052-4000-8000-000000000001';

const ZONES = ['Central', 'North', 'South', 'East', 'West'];

const COMMON_ISSUES = [
  'water supply', 'roads', 'electricity', 'employment',
  'opposition activity', 'cash distribution', 'voter roll', 'healthcare',
  'drainage', 'sanitation', 'candidate visibility', 'women voters',
];

function SubmitReportModal({ booths, onClose, onSuccess }) {
  const [form, setForm] = useState({
    booth_id: '',
    mood_score: 3,
    content: '',
    is_escalated: false,
    opposition_detail: '',
    issues_reported: [],
  });
  const [customIssue, setCustomIssue] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [issueChips, setIssueChips] = useState(COMMON_ISSUES);

  useEffect(() => {
    getIssueCategories().then(d => {
      const cats = Array.isArray(d) ? d : d.categories || d.items || [];
      if (cats.length > 0) {
        setIssueChips(cats.map(c =>
          typeof c === 'string' ? c : c.name || (c.slug || '').replace(/_/g, ' ') || c.label || ''
        ).filter(Boolean));
      }
    }).catch(() => {});
  }, []);

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const toggleIssue = (issue) => {
    setForm(f => ({
      ...f,
      issues_reported: f.issues_reported.includes(issue)
        ? f.issues_reported.filter(i => i !== issue)
        : [...f.issues_reported, issue],
    }));
  };

  const addCustomIssue = () => {
    const trimmed = customIssue.trim().toLowerCase();
    if (trimmed && !form.issues_reported.includes(trimmed)) {
      setForm(f => ({ ...f, issues_reported: [...f.issues_reported, trimmed] }));
    }
    setCustomIssue('');
  };

  const handleSubmit = async () => {
    if (!form.booth_id) { setError('Please select a booth.'); return; }
    if (!form.content.trim()) { setError('Please enter report content.'); return; }
    setSubmitting(true);
    setError(null);
    try {
      await submitReport({
        booth_id: form.booth_id,
        mood_score: Math.round(Number(form.mood_score)),
        top_issues: form.issues_reported,
        notes: form.content.trim(),
        opposition_activity_observed: form.is_escalated,
        opposition_detail: form.is_escalated
          ? (form.opposition_detail.trim() || form.content.trim())
          : undefined,
        source_channel: 'web',
      });
      onSuccess();
    } catch (e) {
      setError(e.response?.data?.detail || 'Submission failed. Check your connection.');
    } finally {
      setSubmitting(false);
    }
  };

  const moodLabels = ['', 'Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive'];
  const moodColors = ['', 'var(--red)', 'var(--red)', 'var(--yellow)', 'var(--green)', 'var(--green)'];

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24,
    }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{
        background: 'var(--bg-surface)', borderRadius: 16, border: '1px solid var(--border)',
        width: '100%', maxWidth: 540, maxHeight: '90vh', overflowY: 'auto',
        boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
      }}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Submit Field Report</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>VAYU Ground Intelligence · Real-time submission</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: '20px' }}>
          {error && (
            <div style={{
              padding: '8px 12px', marginBottom: 14, borderRadius: 6,
              background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.3)',
              fontSize: 12, color: 'var(--red)', display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <AlertCircle size={12} /> {typeof error === 'string' ? error : String(error?.message || error || '')}
            </div>
          )}

          {/* Booth selector */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Booth *
            </label>
            <select
              className="select-input"
              style={{ width: '100%' }}
              value={form.booth_id}
              onChange={e => set('booth_id', e.target.value)}
            >
              <option value="">— Select booth —</option>
              {booths.map(b => (
                <option key={b.booth_id || b.id || b.code} value={b.booth_id || b.id || b.code}>
                  {b.code} — {b.name} ({b.zone})
                </option>
              ))}
            </select>
          </div>

          {/* Mood score */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Voter Mood Score
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="range" min={1} max={5} step={0.5}
                value={form.mood_score}
                onChange={e => set('mood_score', e.target.value)}
                style={{ flex: 1, accentColor: moodColors[Math.round(form.mood_score)] }}
              />
              <div style={{ textAlign: 'center', minWidth: 80 }}>
                <div style={{ fontSize: 22, fontWeight: 900, fontFamily: 'var(--font-mono)', color: moodColors[Math.round(form.mood_score)] }}>
                  {Number(form.mood_score).toFixed(1)}
                </div>
                <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  {moodLabels[Math.round(form.mood_score)]}
                </div>
              </div>
            </div>
          </div>

          {/* Issues */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Issues Reported
            </label>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
              {issueChips.map(issue => (
                <button
                  key={issue}
                  onClick={() => toggleIssue(issue)}
                  style={{
                    padding: '4px 10px', borderRadius: 20, fontSize: 10, fontWeight: 600,
                    border: '1px solid',
                    borderColor: form.issues_reported.includes(issue) ? 'var(--saffron)' : 'var(--border)',
                    background: form.issues_reported.includes(issue) ? 'var(--saffron-dim)' : 'none',
                    color: form.issues_reported.includes(issue) ? 'var(--saffron)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  {issue}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                className="search-input"
                style={{ flex: 1, fontSize: 12 }}
                placeholder="Custom issue…"
                value={customIssue}
                onChange={e => setCustomIssue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addCustomIssue()}
              />
              <button className="btn btn-outline btn-sm" onClick={addCustomIssue} disabled={!customIssue.trim()}>Add</button>
            </div>
            {form.issues_reported.length > 0 && (
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginTop: 6 }}>
                {form.issues_reported.map(issue => (
                  <span key={issue} className="badge badge-blue" style={{ fontSize: 9, display: 'flex', alignItems: 'center', gap: 3 }}>
                    {issue}
                    <button onClick={() => toggleIssue(issue)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0, lineHeight: 1 }}>×</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Content */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Report Details *
            </label>
            <textarea
              value={form.content}
              onChange={e => set('content', e.target.value)}
              rows={4}
              placeholder="Describe what you observed on the ground…"
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 8,
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.6,
                resize: 'vertical', outline: 'none', fontFamily: 'inherit',
                boxSizing: 'border-box',
              }}
              onFocus={e => { e.target.style.borderColor = 'var(--saffron)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border)'; }}
            />
          </div>

          {/* Escalation toggle */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', marginBottom: form.is_escalated ? 10 : 0 }}>
              <input
                type="checkbox"
                checked={form.is_escalated}
                onChange={e => set('is_escalated', e.target.checked)}
                style={{ accentColor: 'var(--red)', width: 14, height: 14 }}
              />
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: form.is_escalated ? 'var(--red)' : 'var(--text-secondary)' }}>
                  Mark as Escalated — Opposition Activity
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                  Use when opposition activity is observed in the field
                </div>
              </div>
            </label>
            {form.is_escalated && (
              <textarea
                value={form.opposition_detail}
                onChange={e => set('opposition_detail', e.target.value)}
                rows={2}
                placeholder="Describe opposition activity observed (required)…"
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 8,
                  background: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.4)',
                  color: 'var(--text-primary)', fontSize: 12, lineHeight: 1.5,
                  resize: 'vertical', outline: 'none', fontFamily: 'inherit',
                  boxSizing: 'border-box',
                }}
              />
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-outline" style={{ flex: 1, justifyContent: 'center' }} onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              style={{ flex: 2, justifyContent: 'center' }}
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Submitting…' : 'Submit Report'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const ZONE_COLORS = {
  Central: 'var(--purple)',
  North:   'var(--blue)',
  South:   'var(--green)',
  East:    'var(--red)',
  West:    'var(--yellow)',
};

function moodColor(score) {
  if (score == null) return 'var(--text-muted)';
  if (score >= 4)   return 'var(--green)';
  if (score >= 3)   return 'var(--yellow)';
  return 'var(--red)';
}

function moodLabel(score) {
  if (score == null) return '—';
  if (score >= 4.5) return 'Very Positive';
  if (score >= 3.5) return 'Positive';
  if (score >= 2.5) return 'Neutral';
  if (score >= 1.5) return 'Negative';
  return 'Very Negative';
}

function formatTs(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  const diff = (Date.now() - d) / 1000;
  if (diff < 60)   return 'Just now';
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

const MOCK_SUMMARY = {
  total_reports: 142,
  booths_covered: 18,
  escalation_count: 4,
  avg_mood: 3.2,
};

const MOCK_REPORTS = {
  items: [
    {
      id: '1', booth_code: 'B007', booth_name: 'Kondapur Primary School', zone: 'North',
      mood_score: 2.1, is_escalated: true, created_at: new Date(Date.now() - 25 * 60000).toISOString(),
      content: 'Opposition vehicles distributing cash near the school gate this morning. Crowd of ~40 people. Took photos.',
      issues_reported: ['cash distribution', 'opposition activity'],
    },
    {
      id: '2', booth_code: 'B014', booth_name: 'Chandanagar Govt High School', zone: 'Central',
      mood_score: 3.8, is_escalated: false, created_at: new Date(Date.now() - 70 * 60000).toISOString(),
      content: 'Good turnout at the panna pramukh meeting. 12 of 15 panna pramus present. Water issue remains biggest concern.',
      issues_reported: ['water supply'],
    },
    {
      id: '3', booth_code: 'B003', booth_name: 'Balanagar Community Hall', zone: 'North',
      mood_score: 1.8, is_escalated: true, created_at: new Date(Date.now() - 3 * 3600000).toISOString(),
      content: 'Large opposition rally planned for evening. BNP workers setting up stage. Estimate 300+ crowd expected.',
      issues_reported: ['opposition rally', 'voter intimidation'],
    },
    {
      id: '4', booth_code: 'B021', booth_name: 'Serilingampally Boys School', zone: 'West',
      mood_score: 4.2, is_escalated: false, created_at: new Date(Date.now() - 5 * 3600000).toISOString(),
      content: 'Voter contact drive completed. Met 67 households today. Strong support in lower colony. Road work positive signal.',
      issues_reported: ['roads', 'voter contact'],
    },
    {
      id: '5', booth_code: 'B031', booth_name: 'Miyapur Public School', zone: 'North',
      mood_score: 2.5, is_escalated: false, created_at: new Date(Date.now() - 8 * 3600000).toISOString(),
      content: 'Mood dipped after opposition promises at yesterday evening rally. Youth asking about unemployment scheme.',
      issues_reported: ['unemployment', 'opposition narrative'],
    },
    {
      id: '6', booth_code: 'B018', booth_name: 'GHMC Ward Office 18', zone: 'South',
      mood_score: 3.5, is_escalated: false, created_at: new Date(Date.now() - 12 * 3600000).toISOString(),
      content: 'Met with local ASHA workers. They are broadly supportive. Asked about health centre upgrade promise.',
      issues_reported: ['healthcare', 'women voters'],
    },
    {
      id: '7', booth_code: 'B009', booth_name: 'Nizampet Govt School', zone: 'East',
      mood_score: 2.0, is_escalated: true, created_at: new Date(Date.now() - 18 * 3600000).toISOString(),
      content: 'Fake voter ID rumour spreading. 5 voters approached saying their names are missing from rolls. Need verification.',
      issues_reported: ['voter roll', 'disenfranchisement'],
    },
    {
      id: '8', booth_code: 'B025', booth_name: 'Hafeezpet Primary School', zone: 'West',
      mood_score: 4.0, is_escalated: false, created_at: new Date(Date.now() - 24 * 3600000).toISOString(),
      content: 'Positive response to candidate visit yesterday. People asking when next visit will be. Strong mood.',
      issues_reported: ['candidate visibility'],
    },
  ],
  total: 142,
  page: 1,
  page_size: 20,
  pages: 8,
};

function ReportCard({ report, expanded, onToggle }) {
  const zone = report.zone || '';
  const zoneColor = ZONE_COLORS[zone] || 'var(--text-muted)';
  const issues = Array.isArray(report.top_issues) && report.top_issues.length
    ? report.top_issues
    : Array.isArray(report.issues_reported) ? report.issues_reported
    : Array.isArray(report.issues) ? report.issues : [];
  const isEscalated = report.is_escalated || report.opposition_activity_observed || false;
  const content = report.notes || report.content || report.description || '';
  const truncated = content.length > 160;

  return (
    <div style={{
      padding: '14px 18px',
      borderBottom: '1px solid var(--border)',
      background: isEscalated ? 'rgba(220,38,38,0.03)' : undefined,
      borderLeft: isEscalated ? '3px solid var(--red)' : '3px solid transparent',
      cursor: truncated ? 'pointer' : undefined,
    }} onClick={truncated ? onToggle : undefined}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        {/* Mood score pill */}
        <div style={{
          flexShrink: 0, width: 40, height: 40, borderRadius: 10,
          background: `${moodColor(report.mood_score)}18`,
          border: `1px solid ${moodColor(report.mood_score)}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column',
        }}>
          <div style={{ fontSize: 15, fontWeight: 900, fontFamily: 'var(--font-mono)', color: moodColor(report.mood_score), lineHeight: 1 }}>
            {report.mood_score != null ? report.mood_score.toFixed(1) : '—'}
          </div>
          <div style={{ fontSize: 7, color: 'var(--text-muted)', textTransform: 'uppercase' }}>/5</div>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Header row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: 13, color: 'var(--saffron)' }}>
              {report.booth_code}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              {report.booth_name}
            </span>
            {zone && (
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 20,
                color: zoneColor, background: `${zoneColor}18`, border: `1px solid ${zoneColor}33`,
              }}>
                {zone}
              </span>
            )}
            {isEscalated && (
              <span style={{
                display: 'flex', alignItems: 'center', gap: 3,
                fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 20,
                color: 'var(--red)', background: 'var(--red-dim)', border: '1px solid rgba(220,38,38,0.3)',
              }}>
                <AlertTriangle size={8} /> ESCALATED
              </span>
            )}
            <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              {formatTs(report.created_at)}
            </span>
          </div>

          {/* Content */}
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8 }}>
            {expanded || !truncated ? content : content.slice(0, 160) + '…'}
            {truncated && (
              <span style={{ fontSize: 11, color: 'var(--blue)', marginLeft: 4 }}>
                {expanded ? ' Show less' : ' Show more'}
              </span>
            )}
          </div>

          {/* Issue tags */}
          {issues.length > 0 && (
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              {issues.map((issue, i) => (
                <span key={i} className="badge badge-blue" style={{ fontSize: 9 }}>{issue}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function FieldReports() {
  const [data, setData] = useState(MOCK_REPORTS);
  const [summary, setSummary] = useState(MOCK_SUMMARY);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [filterZone, setFilterZone] = useState('All');
  const [filterEscalated, setFilterEscalated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [expanded, setExpanded] = useState({});
  const [isLive, setIsLive] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [boothList, setBoothList] = useState([]);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [escalationAlerts, setEscalationAlerts] = useState([]);
  const [updatingAlert, setUpdatingAlert] = useState(null);

  const load = useCallback(async (pg, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const reportData = await getReports(pg, 20, {
        zone: filterZone !== 'All' ? filterZone : undefined,
        escalated: filterEscalated || undefined,
      });

      const d = reportData;
      const items = Array.isArray(d) ? { items: d, total: d.length, page: pg, pages: 1 }
        : d.items ? d : { items: [], total: 0, page: pg, pages: 1 };
      setData(items);
      setIsLive(true);
      setError(null);

      const liveItems = items.items || [];
      const uniqueBooths = new Set(liveItems.map(r => r.booth_id).filter(Boolean)).size;
      const moodVals = liveItems.map(r => r.mood_score).filter(v => v != null);
      setSummary({
        total_reports: items.total,
        booths_covered: uniqueBooths,
        escalation_count: liveItems.filter(r => r.is_escalated).length,
        avg_mood: moodVals.length ? moodVals.reduce((a, b) => a + b, 0) / moodVals.length : null,
      });
    } catch {
      setError('Could not load reports from server. Showing cached data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filterZone, filterEscalated]);

  useEffect(() => { load(1); }, [load]);

  // Load booth list for the submit modal
  useEffect(() => {
    getBoothHeatmap().then(d => {
      const arr = Array.isArray(d) ? d : d.booths || [];
      setBoothList(arr);
    }).catch(() => {});
  }, []);

  // Load escalation alerts
  const loadAlerts = useCallback(async () => {
    getAlerts(true, 30).then(d => {
      setEscalationAlerts(Array.isArray(d) ? d : []);
    }).catch(() => {});
  }, []);

  useEffect(() => { loadAlerts(); }, [loadAlerts]);

  const handleAlertAction = async (alertId, newStatus) => {
    setUpdatingAlert(alertId);
    try {
      await updateAlertStatus(alertId, newStatus);
      setEscalationAlerts(prev =>
        newStatus === 'resolved'
          ? prev.filter(a => a.id !== alertId)
          : prev.map(a => a.id === alertId ? { ...a, escalation_status: newStatus } : a)
      );
    } catch {
      // silent — alert list will refresh on next poll
    } finally {
      setUpdatingAlert(null);
    }
  };

  const handlePageChange = (pg) => {
    setPage(pg);
    load(pg);
  };

  // Client-side search filter on the current page
  const displayItems = search
    ? (data.items || []).filter(r =>
        (r.booth_code || '').toLowerCase().includes(search.toLowerCase()) ||
        (r.booth_name || '').toLowerCase().includes(search.toLowerCase()) ||
        (r.content || r.notes || '').toLowerCase().includes(search.toLowerCase()) ||
        (r.issues_reported || r.issues || []).some(i => i.toLowerCase().includes(search.toLowerCase()))
      )
    : (data.items || []);

  const escalatedCount = (data.items || []).filter(r => r.is_escalated || r.opposition_activity_observed).length;

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Field Reports</div>
          <div className="page-subtitle">VAYU Agent · Ground worker submissions · Real-time field intelligence</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="live-badge"><span className="live-dot" /> VAYU Active</span>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => { setShowModal(true); setSubmitSuccess(false); }}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Plus size={12} /> Submit Report
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => load(page, true)}
            disabled={refreshing}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={12} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      <div className="page-body">
        {submitSuccess && (
          <div style={{
            padding: '10px 14px', marginBottom: 16, borderRadius: 8,
            background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--green)',
          }}>
            <CheckCircle size={13} /> Report submitted successfully. Refresh to see updated data.
          </div>
        )}

        {error && (
          <div style={{
            padding: '10px 14px', marginBottom: 16, borderRadius: 8,
            background: 'rgba(217,119,6,0.1)', border: '1px solid rgba(217,119,6,0.3)',
            display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--yellow)',
          }}>
            <AlertCircle size={13} /> {typeof error === 'string' ? error : String(error?.message || error || '')}
          </div>
        )}

        {/* Summary stats */}
        <div className="grid-4 section-gap">
          {[
            { label: 'Total Reports', value: data.total ?? summary.total_reports ?? '—', color: 'var(--text-primary)' },
            { label: 'Booths Covered', value: summary.booths_covered ?? '—', color: 'var(--blue)' },
            { label: 'Escalated',      value: summary.escalation_count ?? escalatedCount, color: 'var(--red)' },
            {
              label: 'Avg Mood',
              value: summary.avg_mood != null ? `${Number(summary.avg_mood).toFixed(1)}/5` : '—',
              color: summary.avg_mood != null ? moodColor(summary.avg_mood) : 'var(--text-muted)',
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="stat-card" style={{ '--accent-color': color }}>
              <div className="stat-label">{label}</div>
              <div className="stat-value" style={{ fontSize: 28, color, fontFamily: 'var(--font-mono)' }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Escalation Tracker */}
        {escalationAlerts.length > 0 && (
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              <span className="card-title">
                <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 6, color: 'var(--red)' }} />
                Escalation Tracker
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                {escalationAlerts.length} open · Requires action
              </span>
            </div>
            <div>
              {escalationAlerts.map(alert => {
                const statusLabel = alert.escalation_status === 'investigating' ? 'Investigating'
                  : alert.action_done ? 'Resolved' : 'Open';
                const statusColor = alert.escalation_status === 'investigating' ? 'var(--yellow)'
                  : alert.action_done ? 'var(--green)' : 'var(--red)';
                const alertTypeColor = alert.alert_type === 'critical' ? '#ef4444' : '#f59e0b';
                const isUpdating = updatingAlert === alert.id;

                return (
                  <div key={alert.id} style={{
                    padding: '12px 18px', borderBottom: '1px solid var(--border)',
                    borderLeft: `3px solid ${alertTypeColor}`,
                    background: alert.escalation_status === 'investigating' ? 'rgba(245,158,11,0.03)' : undefined,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                          <span style={{
                            fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 10,
                            background: `${alertTypeColor}18`, border: `1px solid ${alertTypeColor}44`,
                            color: alertTypeColor, textTransform: 'uppercase',
                          }}>{alert.alert_type}</span>
                          <span style={{
                            fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 10,
                            color: statusColor, background: `${statusColor}18`, border: `1px solid ${statusColor}33`,
                            display: 'flex', alignItems: 'center', gap: 3,
                          }}>
                            {alert.escalation_status === 'investigating' ? <Clock size={8} /> : <Shield size={8} />}
                            {statusLabel}
                          </span>
                          <span style={{ fontSize: 9, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginLeft: 'auto' }}>
                            {formatTs(alert.created_at)}
                          </span>
                        </div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>
                          {alert.title}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 8 }}>
                          {alert.message}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div style={{ display: 'flex', gap: 6, flexShrink: 0, flexDirection: 'column', alignItems: 'flex-end' }}>
                        {alert.escalation_status === 'open' && !alert.action_done && (
                          <button
                            className="btn btn-outline btn-sm"
                            style={{ fontSize: 10, padding: '4px 10px', color: 'var(--yellow)', borderColor: 'rgba(245,158,11,0.4)', display: 'flex', alignItems: 'center', gap: 4 }}
                            onClick={() => handleAlertAction(alert.id, 'investigating')}
                            disabled={isUpdating}
                          >
                            <Clock size={10} />
                            Investigating
                          </button>
                        )}
                        {!alert.action_done && (
                          <button
                            className="btn btn-outline btn-sm"
                            style={{ fontSize: 10, padding: '4px 10px', color: 'var(--green)', borderColor: 'rgba(16,185,129,0.4)', display: 'flex', alignItems: 'center', gap: 4 }}
                            onClick={() => handleAlertAction(alert.id, 'resolved')}
                            disabled={isUpdating}
                          >
                            <CheckCircle size={10} />
                            Resolve
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Report feed */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="card-title">
                <FileText size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                Report Feed
              </span>
              {isLive
                ? <span className="live-badge"><span className="live-dot" /> Live</span>
                : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 7px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Demo</span>
              }
              {escalatedCount > 0 && (
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
                  color: 'var(--red)', background: 'var(--red-dim)', border: '1px solid rgba(220,38,38,0.3)',
                }}>
                  {escalatedCount} escalated
                </span>
              )}
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Page {data.page ?? 1} of {data.pages ?? 1} · {data.total ?? displayItems.length} total
            </span>
          </div>

          {/* Filter bar */}
          <div style={{
            padding: '10px 16px', borderBottom: '1px solid var(--border)',
            display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
          }}>
            <div style={{ position: 'relative', flex: 1, minWidth: 220 }}>
              <Search size={12} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                className="search-input"
                style={{ paddingLeft: 28 }}
                placeholder="Search booth, content, issue…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <select className="select-input" value={filterZone} onChange={e => { setFilterZone(e.target.value); setPage(1); }}>
              <option value="All">All Zones</option>
              {['Central', 'North', 'South', 'East', 'West'].map(z => <option key={z}>{z}</option>)}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}>
              <input
                type="checkbox"
                checked={filterEscalated}
                onChange={e => { setFilterEscalated(e.target.checked); setPage(1); }}
                style={{ accentColor: 'var(--red)' }}
              />
              Escalated only
            </label>
            {(filterZone !== 'All' || filterEscalated || search) && (
              <button className="btn btn-outline btn-sm" onClick={() => { setSearch(''); setFilterZone('All'); setFilterEscalated(false); setPage(1); }}>
                <X size={10} /> Clear
              </button>
            )}
          </div>

          {/* Report list */}
          <div style={{ minHeight: 200 }}>
            {loading ? (
              <div>
                {[0,1,2,3,4].map(i => (
                  <div key={i} style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12 }}>
                    <div className="skeleton" style={{ width: 40, height: 40, borderRadius: 10, flexShrink: 0 }} />
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <div className="skeleton" style={{ height: 12, width: 60 }} />
                        <div className="skeleton" style={{ height: 12, width: 80 }} />
                        <div className="skeleton" style={{ height: 12, width: 50, marginLeft: 'auto' }} />
                      </div>
                      <div className="skeleton" style={{ height: 12, width: '90%' }} />
                      <div className="skeleton" style={{ height: 12, width: '65%' }} />
                      <div style={{ display: 'flex', gap: 5 }}>
                        <div className="skeleton" style={{ height: 18, width: 70, borderRadius: 20 }} />
                        <div className="skeleton" style={{ height: 18, width: 55, borderRadius: 20 }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : displayItems.length === 0 ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                No reports match the current filters.
              </div>
            ) : (
              displayItems.map(report => (
                <ReportCard
                  key={report.id}
                  report={report}
                  expanded={!!expanded[report.id]}
                  onToggle={() => setExpanded(prev => ({ ...prev, [report.id]: !prev[report.id] }))}
                />
              ))
            )}
          </div>

          {/* Pagination */}
          {(data.pages ?? 1) > 1 && (
            <div style={{
              padding: '12px 18px', borderTop: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => handlePageChange(page - 1)}
                disabled={page <= 1 || loading}
                style={{ display: 'flex', alignItems: 'center', gap: 5 }}
              >
                <ChevronLeft size={13} /> Previous
              </button>

              <div style={{ display: 'flex', gap: 4 }}>
                {Array.from({ length: Math.min(data.pages ?? 1, 7) }, (_, i) => {
                  const pg = i + 1;
                  return (
                    <button
                      key={pg}
                      onClick={() => handlePageChange(pg)}
                      style={{
                        width: 28, height: 28, borderRadius: 6, border: '1px solid',
                        borderColor: pg === page ? 'var(--saffron)' : 'var(--border)',
                        background: pg === page ? 'var(--saffron-dim)' : 'none',
                        color: pg === page ? 'var(--saffron)' : 'var(--text-secondary)',
                        fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      {pg}
                    </button>
                  );
                })}
                {(data.pages ?? 1) > 7 && (
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', alignSelf: 'center', padding: '0 4px' }}>
                    … {data.pages}
                  </span>
                )}
              </div>

              <button
                className="btn btn-outline btn-sm"
                onClick={() => handlePageChange(page + 1)}
                disabled={page >= (data.pages ?? 1) || loading}
                style={{ display: 'flex', alignItems: 'center', gap: 5 }}
              >
                Next <ChevronRight size={13} />
              </button>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <SubmitReportModal
          booths={boothList}
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            setSubmitSuccess(true);
            load(1, true);
          }}
        />
      )}
    </div>
  );
}
