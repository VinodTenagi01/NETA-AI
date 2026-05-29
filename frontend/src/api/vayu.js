import client from './client';

const CID = '11111111-0052-4000-8000-000000000001';

// ── Field Reports ──────────────────────────────────────────────────────────────

export const submitReport = (payload) =>
  client.post('/v1/ground/reports', payload).then(r => r.data);

const _MOOD_FROM_SENTIMENT = { POSITIVE: 4.5, NEUTRAL: 3.0, NEGATIVE: 1.5, MIXED: 3.0 };

export const getReports = (page = 1, pageSize = 20, filters = {}) => {
  const limit = pageSize;
  const offset = (page - 1) * pageSize;
  const params = new URLSearchParams({ limit, offset, days: 7 });
  if (filters.zone)     params.set('zone_id', filters.zone);
  if (filters.booth_id) params.set('booth_id', filters.booth_id);
  return client.get(`/v1/ground/reports?${params}`).then(r => {
    const d = r.data;
    const raw = d.reports || d.items || (Array.isArray(d) ? d : []);
    const items = raw.map(rep => ({
      ...rep,
      booth_code: rep.booth_code || rep.booth_number || null,
      mood_score: rep.mood_score ?? _MOOD_FROM_SENTIMENT[rep.voter_sentiment] ?? null,
      is_escalated: rep.is_escalated ?? (rep.escalation_id != null),
      zone: rep.zone || rep.zone_name || null,
    }));
    const total = d.total ?? items.length;
    return { items, total, page, pages: Math.max(1, Math.ceil(total / pageSize)) };
  });
};

// ── Booth-level data ───────────────────────────────────────────────────────────
// These granular booth endpoints don't exist in the backend; return empty gracefully.

export const getBoothPulse = () => Promise.resolve(null);
export const getBoothReports = (boothId, limit = 5) =>
  client.get(`/v1/ground/reports?booth_id=${boothId}&limit=${limit}&days=30`)
    .then(r => r.data)
    .catch(() => ({ reports: [], total: 0 }));

export const getIssueCategories = () =>
  Promise.resolve({ categories: ['VOTER_MOOD', 'INFRASTRUCTURE', 'OPPOSITION_ACTIVITY', 'SECURITY', 'LOGISTICS', 'OTHER'] });

// ── Mood / Sentiment ───────────────────────────────────────────────────────────

export const getMoodTrend = (cid = CID, days = 14) =>
  client.get(`/v1/ground/mood/trends?constituency_id=${cid}&days=${days}`).then(r => r.data);

export const getSentimentSummary = (cid = CID) =>
  client.get(`/v1/ground/mood/zones?constituency_id=${cid}`).then(r => r.data);

// ── Dashboard / Alerts ─────────────────────────────────────────────────────────

export const getGroundDashboard = (cid = CID) =>
  client.get(`/v1/ground/mood/zones?constituency_id=${cid}`).then(r => r.data);

export const getBoothList = (cid = CID) =>
  client.get(`/v1/ground/mood/zones?constituency_id=${cid}`)
    .then(r => r.data?.zones || []);

export const getVayuAlerts = (limit = 20) =>
  client.get(`/intelligence/alerts/live?limit=${limit}`).then(r => r.data?.items || []);

export const getAlerts = (unresolvedOnly = true, limit = 50) =>
  client.get(`/intelligence/alerts/live?limit=${limit}`).then(r => r.data?.items || []);

export const updateAlertStatus = (alertId) =>
  client.patch(`/intelligence/alerts/${alertId}/done`).then(r => r.data);

// ── Trending issues ────────────────────────────────────────────────────────────

export const getTrendingIssues = () =>
  client.get('/v1/news/narratives/active').then(r => r.data).catch(() => ({ narratives: [] }));

// ── Sentiment summary ──────────────────────────────────────────────────────────

export const submitMood = (payload) =>
  client.post('/v1/ground/reports', { ...payload, category: 'VOTER_MOOD' }).then(r => r.data);
